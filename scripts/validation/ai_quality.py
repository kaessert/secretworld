"""AI content quality validation for automated playtesting.

This module provides quality checks for AI-generated content, including:
- ContentType: Enum of content types (location, npc, quest, item)
- QualityResult: Dataclass representing the result of quality checks
- ContentQualityChecker: Class that validates content meets quality standards
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Tuple
import re


class ContentType(Enum):
    """Types of AI-generated content for quality validation."""

    LOCATION = auto()
    NPC = auto()
    QUEST = auto()
    ITEM = auto()


@dataclass
class QualityResult:
    """Result of running quality checks on content."""

    passed: bool
    content_type: ContentType
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    details: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "passed": self.passed,
            "content_type": self.content_type.name,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityResult":
        """Deserialize result from dictionary."""
        return cls(
            passed=data["passed"],
            content_type=ContentType[data["content_type"]],
            checks_passed=data.get("checks_passed", []),
            checks_failed=data.get("checks_failed", []),
            details=data.get("details", {}),
        )


class ContentQualityChecker:
    """Checks AI-generated content for quality standards."""

    # Length thresholds
    LOCATION_NAME_MIN = 3
    LOCATION_NAME_MAX = 50
    LOCATION_DESC_MIN = 20
    LOCATION_DESC_MAX = 500
    NPC_NAME_MIN = 2
    NPC_NAME_MAX = 40
    QUEST_DESC_MIN = 10
    QUEST_DESC_MAX = 300

    # Placeholder patterns to detect (case-insensitive)
    PLACEHOLDER_PATTERNS = [
        r"^unknown\b",
        r"^todo\b",
        r"\bplaceholder\b",
        r"^test\s+",
        r"^example\s+",
    ]

    # Valid categories for locations
    VALID_LOCATION_CATEGORIES = {
        "forest",
        "dungeon",
        "town",
        "city",
        "cave",
        "mountain",
        "plains",
        "desert",
        "swamp",
        "coast",
        "village",
        "castle",
        "ruins",
        "temple",
        "tower",
        "wilderness",
        "road",
        "bridge",
        "camp",
        "settlement",
    }

    # Valid objective types for quests
    VALID_OBJECTIVE_TYPES = {
        "fetch",
        "kill",
        "escort",
        "explore",
        "deliver",
        "talk",
        "investigate",
        "collect",
        "rescue",
        "defend",
    }

    # Valid item types
    VALID_ITEM_TYPES = {
        "weapon",
        "armor",
        "consumable",
        "material",
        "key",
        "quest",
        "tool",
        "accessory",
        "scroll",
        "potion",
    }

    def _check_min_length(
        self, value: str, min_len: int, field_name: str
    ) -> Tuple[bool, str]:
        """Check if string meets minimum length requirement."""
        if value is None or len(value) < min_len:
            return False, f"{field_name} too short ({len(value or '')} chars, min {min_len})"
        return True, ""

    def _check_max_length(
        self, value: str, max_len: int, field_name: str
    ) -> Tuple[bool, str]:
        """Check if string meets maximum length requirement."""
        if value is not None and len(value) > max_len:
            return False, f"{field_name} too long ({len(value)} chars, max {max_len})"
        return True, ""

    def _check_non_empty(self, value: Any, field_name: str) -> Tuple[bool, str]:
        """Check if value is non-empty."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name} is empty"
        return True, ""

    def _check_valid_values(
        self, value: str, valid_set: set, field_name: str
    ) -> Tuple[bool, str]:
        """Check if value is in the valid set."""
        if value is None or value.lower() not in {v.lower() for v in valid_set}:
            return False, f"{field_name} '{value}' is not valid"
        return True, ""

    def _check_no_placeholder(self, value: str, field_name: str) -> Tuple[bool, str]:
        """Check if value contains placeholder text."""
        if value is None:
            return True, ""  # None is not a placeholder
        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return False, f"{field_name} contains placeholder text"
        return True, ""

    def check_location(self, content: Dict[str, Any]) -> QualityResult:
        """Check quality of a location content.

        Args:
            content: Dict with name, description, category fields

        Returns:
            QualityResult with checks passed/failed
        """
        checks_passed = []
        checks_failed = []
        details = {}

        name = content.get("name", "")
        description = content.get("description", "")
        category = content.get("category", "")

        # Check name length
        passed, msg = self._check_min_length(name, self.LOCATION_NAME_MIN, "name")
        if passed:
            checks_passed.append("name_min_length")
        else:
            checks_failed.append("min_length")
            details["min_length"] = msg

        passed, msg = self._check_max_length(name, self.LOCATION_NAME_MAX, "name")
        if passed:
            checks_passed.append("name_max_length")
        else:
            checks_failed.append("max_length")
            details["max_length"] = msg

        # Check description length
        passed, msg = self._check_min_length(description, self.LOCATION_DESC_MIN, "description")
        if passed:
            checks_passed.append("desc_min_length")
        else:
            checks_failed.append("desc_min_length")
            details["desc_min_length"] = msg

        passed, msg = self._check_max_length(description, self.LOCATION_DESC_MAX, "description")
        if passed:
            checks_passed.append("desc_max_length")
        else:
            checks_failed.append("desc_max_length")
            details["desc_max_length"] = msg

        # Check category validity
        passed, msg = self._check_valid_values(category, self.VALID_LOCATION_CATEGORIES, "category")
        if passed:
            checks_passed.append("valid_values")
        else:
            checks_failed.append("valid_values")
            details["valid_values"] = msg

        # Check for placeholders in name
        passed, msg = self._check_no_placeholder(name, "name")
        if passed:
            checks_passed.append("no_placeholder")
        else:
            checks_failed.append("no_placeholder")
            details["no_placeholder"] = msg

        return QualityResult(
            passed=len(checks_failed) == 0,
            content_type=ContentType.LOCATION,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
        )

    def check_npc(self, content: Dict[str, Any]) -> QualityResult:
        """Check quality of an NPC content.

        Args:
            content: Dict with name, description, dialogue fields

        Returns:
            QualityResult with checks passed/failed
        """
        checks_passed = []
        checks_failed = []
        details = {}

        name = content.get("name", "")
        description = content.get("description", "")
        dialogue = content.get("dialogue", "")

        # Check name length
        passed, msg = self._check_min_length(name, self.NPC_NAME_MIN, "name")
        if passed:
            checks_passed.append("name_min_length")
        else:
            checks_failed.append("min_length")
            details["min_length"] = msg

        passed, msg = self._check_max_length(name, self.NPC_NAME_MAX, "name")
        if passed:
            checks_passed.append("name_max_length")
        else:
            checks_failed.append("max_length")
            details["max_length"] = msg

        # Check description non-empty
        passed, msg = self._check_non_empty(description, "description")
        if passed:
            checks_passed.append("desc_non_empty")
        else:
            checks_failed.append("non_empty")
            details["desc_non_empty"] = msg

        # Check dialogue non-empty
        passed, msg = self._check_non_empty(dialogue, "dialogue")
        if passed:
            checks_passed.append("dialogue_non_empty")
        else:
            checks_failed.append("non_empty")
            details["dialogue_non_empty"] = msg

        # Check for placeholders
        passed, msg = self._check_no_placeholder(name, "name")
        if passed:
            checks_passed.append("no_placeholder")
        else:
            checks_failed.append("no_placeholder")
            details["no_placeholder"] = msg

        return QualityResult(
            passed=len(checks_failed) == 0,
            content_type=ContentType.NPC,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
        )

    def check_quest(self, content: Dict[str, Any]) -> QualityResult:
        """Check quality of a quest content.

        Args:
            content: Dict with name, description, objective_type fields

        Returns:
            QualityResult with checks passed/failed
        """
        checks_passed = []
        checks_failed = []
        details = {}

        name = content.get("name", "")
        description = content.get("description", "")
        objective_type = content.get("objective_type", "")

        # Check name non-empty
        passed, msg = self._check_non_empty(name, "name")
        if passed:
            checks_passed.append("name_non_empty")
        else:
            checks_failed.append("non_empty")
            details["name_non_empty"] = msg

        # Check description length
        passed, msg = self._check_min_length(description, self.QUEST_DESC_MIN, "description")
        if passed:
            checks_passed.append("desc_min_length")
        else:
            checks_failed.append("desc_min_length")
            details["desc_min_length"] = msg

        passed, msg = self._check_max_length(description, self.QUEST_DESC_MAX, "description")
        if passed:
            checks_passed.append("desc_max_length")
        else:
            checks_failed.append("desc_max_length")
            details["desc_max_length"] = msg

        # Check objective_type validity
        passed, msg = self._check_valid_values(
            objective_type, self.VALID_OBJECTIVE_TYPES, "objective_type"
        )
        if passed:
            checks_passed.append("valid_values")
        else:
            checks_failed.append("valid_values")
            details["valid_values"] = msg

        # Check for placeholders
        passed, msg = self._check_no_placeholder(name, "name")
        if passed:
            checks_passed.append("no_placeholder")
        else:
            checks_failed.append("no_placeholder")
            details["no_placeholder"] = msg

        return QualityResult(
            passed=len(checks_failed) == 0,
            content_type=ContentType.QUEST,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
        )

    def check_item(self, content: Dict[str, Any]) -> QualityResult:
        """Check quality of an item content.

        Args:
            content: Dict with name, description, item_type fields

        Returns:
            QualityResult with checks passed/failed
        """
        checks_passed = []
        checks_failed = []
        details = {}

        name = content.get("name", "")
        description = content.get("description", "")
        item_type = content.get("item_type", "")

        # Check name non-empty
        passed, msg = self._check_non_empty(name, "name")
        if passed:
            checks_passed.append("name_non_empty")
        else:
            checks_failed.append("non_empty")
            details["name_non_empty"] = msg

        # Check description non-empty
        passed, msg = self._check_non_empty(description, "description")
        if passed:
            checks_passed.append("desc_non_empty")
        else:
            checks_failed.append("non_empty")
            details["desc_non_empty"] = msg

        # Check item_type validity
        passed, msg = self._check_valid_values(item_type, self.VALID_ITEM_TYPES, "item_type")
        if passed:
            checks_passed.append("valid_values")
        else:
            checks_failed.append("valid_values")
            details["valid_values"] = msg

        # Check for placeholders
        passed, msg = self._check_no_placeholder(name, "name")
        if passed:
            checks_passed.append("no_placeholder")
        else:
            checks_failed.append("no_placeholder")
            details["no_placeholder"] = msg

        return QualityResult(
            passed=len(checks_failed) == 0,
            content_type=ContentType.ITEM,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
        )

    def check(self, content_type: ContentType, content: Dict[str, Any]) -> QualityResult:
        """Check quality of content based on type.

        Args:
            content_type: The type of content to check
            content: Dict with content fields

        Returns:
            QualityResult with checks passed/failed
        """
        checkers = {
            ContentType.LOCATION: self.check_location,
            ContentType.NPC: self.check_npc,
            ContentType.QUEST: self.check_quest,
            ContentType.ITEM: self.check_item,
        }

        checker_fn = checkers.get(content_type)
        if checker_fn is None:
            raise ValueError(f"Content type {content_type.name} not supported")

        return checker_fn(content)

    def check_batch(
        self, items: List[Tuple[ContentType, Dict[str, Any]]]
    ) -> List[QualityResult]:
        """Check quality of multiple content items.

        Args:
            items: List of (content_type, content) tuples

        Returns:
            List of QualityResult for each item
        """
        return [self.check(content_type, content) for content_type, content in items]
