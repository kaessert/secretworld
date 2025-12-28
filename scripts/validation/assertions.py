"""Core assertion types for automated validation of game state during playtesting.

This module provides the foundation for the validation framework, including:
- AssertionType: Enum of all assertion types
- Assertion: Dataclass representing a single assertion
- AssertionResult: Dataclass representing the result of checking an assertion
- AssertionChecker: Class that checks assertions against game state
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional
import re


class AssertionType(Enum):
    """Types of assertions for state validation."""

    STATE_EQUALS = auto()  # Exact match of state field to expected value
    STATE_CONTAINS = auto()  # State field contains expected substring/element
    STATE_RANGE = auto()  # State field value within min/max bounds
    NARRATIVE_MATCH = auto()  # Regex pattern matching on narrative text
    COMMAND_VALID = auto()  # Command was accepted (no error)
    COMMAND_EFFECT = auto()  # Command produced expected state change
    CONTENT_PRESENT = auto()  # AI-generated content exists (not empty/None)
    CONTENT_QUALITY = auto()  # AI content meets quality threshold (future)


@dataclass
class Assertion:
    """Single assertion to validate against game state."""

    type: AssertionType
    field: str  # State field to check (dot notation for nested)
    expected: Any  # Expected value/pattern/range
    message: str = ""  # Custom failure message

    def to_dict(self) -> Dict[str, Any]:
        """Serialize assertion to dictionary."""
        return {
            "type": self.type.name,
            "field": self.field,
            "expected": self.expected,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Assertion":
        """Deserialize assertion from dictionary."""
        return cls(
            type=AssertionType[data["type"]],
            field=data["field"],
            expected=data["expected"],
            message=data.get("message", ""),
        )


@dataclass
class AssertionResult:
    """Result of running an assertion."""

    assertion: Assertion
    passed: bool
    actual: Any = None
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "assertion": self.assertion.to_dict(),
            "passed": self.passed,
            "actual": self.actual,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssertionResult":
        """Deserialize result from dictionary."""
        return cls(
            assertion=Assertion.from_dict(data["assertion"]),
            passed=data["passed"],
            actual=data.get("actual"),
            error=data.get("error", ""),
        )


class AssertionChecker:
    """Checks assertions against game state."""

    # Error patterns that indicate a command failed
    ERROR_PATTERNS = [
        r"(?i)^error:",
        r"(?i)^unknown command",
        r"(?i)^invalid",
        r"(?i)^cannot",
        r"(?i)^you can't",
    ]

    def check(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any] = None,
        output: str = "",
    ) -> AssertionResult:
        """Check an assertion against the current state.

        Args:
            assertion: The assertion to check
            state: Current game state (dict or object)
            prev_state: Previous game state (for COMMAND_EFFECT)
            output: Command output text (for COMMAND_VALID, NARRATIVE_MATCH)

        Returns:
            AssertionResult with passed status and details
        """
        # Dispatch to type-specific checker
        checkers = {
            AssertionType.STATE_EQUALS: self._check_state_equals,
            AssertionType.STATE_CONTAINS: self._check_state_contains,
            AssertionType.STATE_RANGE: self._check_state_range,
            AssertionType.NARRATIVE_MATCH: self._check_narrative_match,
            AssertionType.COMMAND_VALID: self._check_command_valid,
            AssertionType.COMMAND_EFFECT: self._check_command_effect,
            AssertionType.CONTENT_PRESENT: self._check_content_present,
            AssertionType.CONTENT_QUALITY: self._check_content_quality,
        }

        checker_fn = checkers.get(assertion.type)
        if checker_fn is None:
            raise ValueError(f"Assertion type {assertion.type.name} not implemented")

        return checker_fn(assertion, state, prev_state, output)

    def _get_field_value(self, state: Any, field: str) -> Any:
        """Get a field value from state using dot notation.

        Args:
            state: State dict or object
            field: Field path (e.g., "character.health")

        Returns:
            Field value or None if not found
        """
        if not field:
            return state

        parts = field.split(".")
        value = state

        for part in parts:
            if value is None:
                return None
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)

        return value

    def _check_state_equals(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check STATE_EQUALS assertion."""
        actual = self._get_field_value(state, assertion.field)

        if actual == assertion.expected:
            return AssertionResult(
                assertion=assertion,
                passed=True,
                actual=actual,
            )
        else:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=actual,
                error=f"Expected {assertion.expected} but got {actual}",
            )

    def _check_state_contains(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check STATE_CONTAINS assertion."""
        actual = self._get_field_value(state, assertion.field)

        try:
            if assertion.expected in actual:
                return AssertionResult(
                    assertion=assertion,
                    passed=True,
                    actual=actual,
                )
            else:
                return AssertionResult(
                    assertion=assertion,
                    passed=False,
                    actual=actual,
                    error=f"{assertion.expected} not found in {assertion.field}",
                )
        except TypeError:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=actual,
                error=f"Cannot check contains on {type(actual).__name__}",
            )

    def _check_state_range(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check STATE_RANGE assertion."""
        actual = self._get_field_value(state, assertion.field)
        min_val = assertion.expected.get("min")
        max_val = assertion.expected.get("max")

        if actual is None:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=actual,
                error=f"Field {assertion.field} is None",
            )

        if min_val is not None and actual < min_val:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=actual,
                error=f"Value {actual} is below minimum {min_val}",
            )

        if max_val is not None and actual > max_val:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=actual,
                error=f"Value {actual} is above maximum {max_val}",
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            actual=actual,
        )

    def _check_narrative_match(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check NARRATIVE_MATCH assertion using regex."""
        text = self._get_field_value(state, assertion.field)
        if text is None:
            text = ""

        pattern = assertion.expected
        match = re.search(pattern, str(text), re.IGNORECASE)

        if match:
            return AssertionResult(
                assertion=assertion,
                passed=True,
                actual=text,
            )
        else:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=text,
                error=f"Pattern '{pattern}' did not match",
            )

    def _check_command_valid(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check COMMAND_VALID assertion."""
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, output):
                return AssertionResult(
                    assertion=assertion,
                    passed=False,
                    actual=output,
                    error=f"Error detected in output: {output[:100]}",
                )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            actual=output,
        )

    def _check_command_effect(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check COMMAND_EFFECT assertion."""
        if prev_state is None:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=None,
                error="No previous state provided for COMMAND_EFFECT",
            )

        expected_from = assertion.expected.get("from")
        expected_to = assertion.expected.get("to")

        prev_value = self._get_field_value(prev_state, assertion.field)
        curr_value = self._get_field_value(state, assertion.field)

        from_matches = expected_from is None or prev_value == expected_from
        to_matches = expected_to is None or curr_value == expected_to

        if from_matches and to_matches:
            return AssertionResult(
                assertion=assertion,
                passed=True,
                actual={"from": prev_value, "to": curr_value},
            )
        else:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual={"from": prev_value, "to": curr_value},
                error=f"Expected change from {expected_from} to {expected_to}, "
                f"got {prev_value} to {curr_value}",
            )

    def _check_content_present(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check CONTENT_PRESENT assertion."""
        content = self._get_field_value(state, assertion.field)

        if content is None:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=content,
                error=f"Content at {assertion.field} is None",
            )

        if isinstance(content, str) and not content.strip():
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=content,
                error=f"Content at {assertion.field} is empty",
            )

        if isinstance(content, (list, dict)) and len(content) == 0:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                actual=content,
                error=f"Content at {assertion.field} is empty",
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            actual=content,
        )

    def _check_content_quality(
        self,
        assertion: Assertion,
        state: Any,
        prev_state: Optional[Any],
        output: str,
    ) -> AssertionResult:
        """Check CONTENT_QUALITY assertion using ContentQualityChecker.

        Args:
            assertion: The assertion to check (expected contains content_type config)
            state: Current game state
            prev_state: Previous game state (unused)
            output: Command output text (unused)

        Returns:
            AssertionResult with passed status and details
        """
        from scripts.validation.ai_quality import ContentQualityChecker, ContentType

        content = self._get_field_value(state, assertion.field)
        config = assertion.expected or {}
        content_type_str = config.get("content_type", "location")
        content_type = ContentType[content_type_str.upper()]

        checker = ContentQualityChecker()
        result = checker.check(content_type, content)

        if result.passed:
            return AssertionResult(assertion=assertion, passed=True, actual=content)
        else:
            error = f"Quality checks failed: {', '.join(result.checks_failed)}"
            return AssertionResult(assertion=assertion, passed=False, actual=content, error=error)
