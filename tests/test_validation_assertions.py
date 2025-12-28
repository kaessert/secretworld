"""Tests for validation assertions framework.

Tests the AssertionType enum, Assertion dataclass, AssertionResult dataclass,
and AssertionChecker class for automated validation of game state during playtesting.
"""

import pytest

from scripts.validation.assertions import (
    Assertion,
    AssertionChecker,
    AssertionResult,
    AssertionType,
)


# ===== AssertionType Enum Tests =====


class TestAssertionType:
    """Tests for AssertionType enum."""

    def test_assertion_type_has_all_types(self):
        """Test that enum has all 8 assertion types.

        Spec: AssertionType includes STATE_EQUALS, STATE_CONTAINS, STATE_RANGE,
        NARRATIVE_MATCH, COMMAND_VALID, COMMAND_EFFECT, CONTENT_PRESENT, CONTENT_QUALITY
        """
        expected_types = {
            "STATE_EQUALS",
            "STATE_CONTAINS",
            "STATE_RANGE",
            "NARRATIVE_MATCH",
            "COMMAND_VALID",
            "COMMAND_EFFECT",
            "CONTENT_PRESENT",
            "CONTENT_QUALITY",
        }
        actual_types = {t.name for t in AssertionType}
        assert actual_types == expected_types

    def test_assertion_type_values_are_unique(self):
        """Test that all enum values are distinct.

        Spec: Each assertion type must have a unique value.
        """
        values = [t.value for t in AssertionType]
        assert len(values) == len(set(values))


# ===== Assertion Dataclass Tests =====


class TestAssertion:
    """Tests for Assertion dataclass."""

    def test_assertion_creation(self):
        """Test creating an Assertion with all fields.

        Spec: Assertion has type, field, expected, and message attributes.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="character.health",
            expected=100,
            message="Health should be 100",
        )

        assert assertion.type == AssertionType.STATE_EQUALS
        assert assertion.field == "character.health"
        assert assertion.expected == 100
        assert assertion.message == "Health should be 100"

    def test_assertion_serialization(self):
        """Test to_dict/from_dict roundtrip for Assertion.

        Spec: Assertion must support to_dict() and from_dict() for persistence.
        """
        original = Assertion(
            type=AssertionType.STATE_RANGE,
            field="character.level",
            expected={"min": 1, "max": 10},
            message="Level must be 1-10",
        )

        data = original.to_dict()
        restored = Assertion.from_dict(data)

        assert restored.type == original.type
        assert restored.field == original.field
        assert restored.expected == original.expected
        assert restored.message == original.message


# ===== AssertionResult Dataclass Tests =====


class TestAssertionResult:
    """Tests for AssertionResult dataclass."""

    def test_assertion_result_passed(self):
        """Test result for a passing assertion.

        Spec: AssertionResult stores passed=True with no error message.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="character.name",
            expected="Hero",
        )
        result = AssertionResult(
            assertion=assertion,
            passed=True,
            actual="Hero",
        )

        assert result.passed is True
        assert result.error == ""
        assert result.actual == "Hero"

    def test_assertion_result_failed(self):
        """Test result for a failing assertion.

        Spec: AssertionResult stores passed=False with error message.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="character.health",
            expected=100,
            message="Health check",
        )
        result = AssertionResult(
            assertion=assertion,
            passed=False,
            actual=50,
            error="Expected 100 but got 50",
        )

        assert result.passed is False
        assert result.actual == 50
        assert result.error == "Expected 100 but got 50"

    def test_assertion_result_serialization(self):
        """Test to_dict/from_dict roundtrip for AssertionResult.

        Spec: AssertionResult must support to_dict() and from_dict().
        """
        assertion = Assertion(
            type=AssertionType.STATE_CONTAINS,
            field="inventory",
            expected="sword",
        )
        original = AssertionResult(
            assertion=assertion,
            passed=False,
            actual=["shield", "potion"],
            error="sword not in inventory",
        )

        data = original.to_dict()
        restored = AssertionResult.from_dict(data)

        assert restored.passed == original.passed
        assert restored.actual == original.actual
        assert restored.error == original.error
        assert restored.assertion.field == original.assertion.field


# ===== AssertionChecker Tests =====


class TestAssertionChecker:
    """Tests for AssertionChecker class."""

    @pytest.fixture
    def checker(self):
        """Create an AssertionChecker instance."""
        return AssertionChecker()

    @pytest.fixture
    def sample_state(self):
        """Create a sample game state for testing."""
        return {
            "character": {
                "name": "Hero",
                "health": 80,
                "level": 5,
                "inventory": ["sword", "shield", "potion"],
            },
            "location": {
                "name": "Dark Forest",
                "description": "A shadowy forest filled with ancient trees.",
            },
            "narrative": "You enter the dark forest. The trees loom overhead.",
        }

    # STATE_EQUALS tests

    def test_check_state_equals_passes(self, checker, sample_state):
        """Test STATE_EQUALS with exact match.

        Spec: STATE_EQUALS passes when field equals expected value.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="character.name",
            expected="Hero",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True
        assert result.actual == "Hero"

    def test_check_state_equals_fails(self, checker, sample_state):
        """Test STATE_EQUALS with mismatch.

        Spec: STATE_EQUALS fails when field does not equal expected value.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="character.health",
            expected=100,
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is False
        assert result.actual == 80
        assert "Expected 100" in result.error

    def test_check_state_equals_nested_field(self, checker, sample_state):
        """Test STATE_EQUALS with dot notation for nested fields.

        Spec: STATE_EQUALS supports dot notation for nested field access.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="location.name",
            expected="Dark Forest",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True
        assert result.actual == "Dark Forest"

    # STATE_CONTAINS tests

    def test_check_state_contains_passes(self, checker, sample_state):
        """Test STATE_CONTAINS with substring.

        Spec: STATE_CONTAINS passes when field contains expected substring.
        """
        assertion = Assertion(
            type=AssertionType.STATE_CONTAINS,
            field="location.description",
            expected="shadowy",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True

    def test_check_state_contains_list(self, checker, sample_state):
        """Test STATE_CONTAINS with list element.

        Spec: STATE_CONTAINS passes when list contains expected element.
        """
        assertion = Assertion(
            type=AssertionType.STATE_CONTAINS,
            field="character.inventory",
            expected="sword",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True

    def test_check_state_contains_fails(self, checker, sample_state):
        """Test STATE_CONTAINS with missing element.

        Spec: STATE_CONTAINS fails when field does not contain expected.
        """
        assertion = Assertion(
            type=AssertionType.STATE_CONTAINS,
            field="character.inventory",
            expected="helmet",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is False
        assert "helmet" in result.error

    # STATE_RANGE tests

    def test_check_state_range_passes(self, checker, sample_state):
        """Test STATE_RANGE with value in range.

        Spec: STATE_RANGE passes when min <= value <= max.
        """
        assertion = Assertion(
            type=AssertionType.STATE_RANGE,
            field="character.health",
            expected={"min": 50, "max": 100},
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True
        assert result.actual == 80

    def test_check_state_range_below(self, checker, sample_state):
        """Test STATE_RANGE with value below min.

        Spec: STATE_RANGE fails when value < min.
        """
        assertion = Assertion(
            type=AssertionType.STATE_RANGE,
            field="character.health",
            expected={"min": 90, "max": 100},
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is False
        assert "below" in result.error.lower() or "less" in result.error.lower()

    def test_check_state_range_above(self, checker, sample_state):
        """Test STATE_RANGE with value above max.

        Spec: STATE_RANGE fails when value > max.
        """
        assertion = Assertion(
            type=AssertionType.STATE_RANGE,
            field="character.health",
            expected={"min": 10, "max": 50},
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is False
        assert "above" in result.error.lower() or "greater" in result.error.lower()

    # NARRATIVE_MATCH tests

    def test_check_narrative_match_passes(self, checker, sample_state):
        """Test NARRATIVE_MATCH with matching regex.

        Spec: NARRATIVE_MATCH passes when regex matches narrative text.
        """
        assertion = Assertion(
            type=AssertionType.NARRATIVE_MATCH,
            field="narrative",
            expected=r"dark\s+forest",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True

    def test_check_narrative_match_fails(self, checker, sample_state):
        """Test NARRATIVE_MATCH with non-matching regex.

        Spec: NARRATIVE_MATCH fails when regex does not match.
        """
        assertion = Assertion(
            type=AssertionType.NARRATIVE_MATCH,
            field="narrative",
            expected=r"bright\s+meadow",
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is False
        assert "pattern" in result.error.lower() or "match" in result.error.lower()

    # COMMAND_VALID tests

    def test_check_command_valid_passes(self, checker, sample_state):
        """Test COMMAND_VALID with valid command output.

        Spec: COMMAND_VALID passes when output has no error message.
        """
        assertion = Assertion(
            type=AssertionType.COMMAND_VALID,
            field="",
            expected=None,
        )
        output = "You move north. The forest opens into a clearing."

        result = checker.check(assertion, sample_state, output=output)

        assert result.passed is True

    def test_check_command_valid_fails(self, checker, sample_state):
        """Test COMMAND_VALID with error in output.

        Spec: COMMAND_VALID fails when output contains error message.
        """
        assertion = Assertion(
            type=AssertionType.COMMAND_VALID,
            field="",
            expected=None,
        )
        output = "Error: Unknown command 'xyz'"

        result = checker.check(assertion, sample_state, output=output)

        assert result.passed is False
        assert "error" in result.error.lower()

    # COMMAND_EFFECT tests

    def test_check_command_effect_passes(self, checker, sample_state):
        """Test COMMAND_EFFECT with expected state change.

        Spec: COMMAND_EFFECT passes when state change occurred.
        """
        prev_state = {
            "character": {"health": 100},
        }
        new_state = {
            "character": {"health": 80},
        }
        assertion = Assertion(
            type=AssertionType.COMMAND_EFFECT,
            field="character.health",
            expected={"from": 100, "to": 80},
        )

        result = checker.check(assertion, new_state, prev_state=prev_state)

        assert result.passed is True

    def test_check_command_effect_fails(self, checker, sample_state):
        """Test COMMAND_EFFECT when state change did not occur.

        Spec: COMMAND_EFFECT fails when expected state change did not happen.
        """
        prev_state = {
            "character": {"health": 100},
        }
        new_state = {
            "character": {"health": 100},  # No change
        }
        assertion = Assertion(
            type=AssertionType.COMMAND_EFFECT,
            field="character.health",
            expected={"from": 100, "to": 80},
        )

        result = checker.check(assertion, new_state, prev_state=prev_state)

        assert result.passed is False

    # CONTENT_PRESENT tests

    def test_check_content_present_passes(self, checker, sample_state):
        """Test CONTENT_PRESENT with non-empty content.

        Spec: CONTENT_PRESENT passes when content exists and is not empty.
        """
        assertion = Assertion(
            type=AssertionType.CONTENT_PRESENT,
            field="location.description",
            expected=None,
        )

        result = checker.check(assertion, sample_state)

        assert result.passed is True

    def test_check_content_present_fails(self, checker):
        """Test CONTENT_PRESENT with empty/None content.

        Spec: CONTENT_PRESENT fails when content is empty or None.
        """
        state = {
            "location": {
                "description": None,
            }
        }
        assertion = Assertion(
            type=AssertionType.CONTENT_PRESENT,
            field="location.description",
            expected=None,
        )

        result = checker.check(assertion, state)

        assert result.passed is False
        assert "empty" in result.error.lower() or "none" in result.error.lower()

    # General tests

    def test_check_returns_result_object(self, checker, sample_state):
        """Test that all checks return AssertionResult.

        Spec: All check methods must return an AssertionResult instance.
        """
        assertion = Assertion(
            type=AssertionType.STATE_EQUALS,
            field="character.name",
            expected="Hero",
        )

        result = checker.check(assertion, sample_state)

        assert isinstance(result, AssertionResult)
        assert result.assertion == assertion

    def test_check_unknown_type_raises(self, checker, sample_state):
        """Test that invalid assertion type raises ValueError.

        Spec: Unknown assertion types should raise ValueError.
        """
        # Create an assertion with a mock invalid type
        assertion = Assertion(
            type=AssertionType.CONTENT_QUALITY,  # Placeholder type for future
            field="test",
            expected=None,
        )

        # CONTENT_QUALITY is not yet implemented, should raise
        with pytest.raises(ValueError, match="not implemented"):
            checker.check(assertion, sample_state)
