"""Tests for AI content quality validation.

Tests the ContentType enum, QualityResult dataclass, and ContentQualityChecker class
for validating AI-generated content meets quality standards.
"""

import pytest

from scripts.validation.ai_quality import (
    ContentQualityChecker,
    ContentType,
    QualityResult,
)


# ===== ContentType Enum Tests =====


class TestContentType:
    """Tests for ContentType enum."""

    def test_content_type_enum_values(self):
        """Test that ContentType enum has location, npc, quest, item.

        Spec: ContentType includes LOCATION, NPC, QUEST, ITEM
        """
        expected_types = {"LOCATION", "NPC", "QUEST", "ITEM"}
        actual_types = {t.name for t in ContentType}
        assert actual_types == expected_types


# ===== QualityResult Tests =====


class TestQualityResult:
    """Tests for QualityResult dataclass."""

    def test_quality_result_serialization(self):
        """Test QualityResult to_dict/from_dict roundtrip.

        Spec: QualityResult must support to_dict() and from_dict() for persistence.
        """
        original = QualityResult(
            passed=False,
            content_type=ContentType.LOCATION,
            checks_passed=["min_length"],
            checks_failed=["max_length", "valid_values"],
            details={"max_length": "Description too long (600 chars, max 500)"},
        )

        data = original.to_dict()
        restored = QualityResult.from_dict(data)

        assert restored.passed == original.passed
        assert restored.content_type == original.content_type
        assert restored.checks_passed == original.checks_passed
        assert restored.checks_failed == original.checks_failed
        assert restored.details == original.details


# ===== ContentQualityChecker Tests =====


class TestContentQualityChecker:
    """Tests for ContentQualityChecker class."""

    @pytest.fixture
    def checker(self):
        """Create a ContentQualityChecker instance."""
        return ContentQualityChecker()

    # Location tests

    def test_quality_check_location_valid(self, checker):
        """Test location with valid name/desc/category passes.

        Spec: Location with name 3-50 chars, desc 20-500 chars, valid category passes.
        """
        content = {
            "name": "Dark Forest Clearing",
            "description": "A shadowy clearing surrounded by ancient trees that tower overhead.",
            "category": "forest",
        }

        result = checker.check_location(content)

        assert result.passed is True
        assert len(result.checks_failed) == 0

    def test_quality_check_location_short_name(self, checker):
        """Test location with 2-char name fails.

        Spec: Location name must be >= 3 chars.
        """
        content = {
            "name": "Go",  # 2 chars, too short
            "description": "A valid description that is long enough.",
            "category": "forest",
        }

        result = checker.check_location(content)

        assert result.passed is False
        assert "min_length" in result.checks_failed or "name_min_length" in result.checks_failed

    def test_quality_check_location_invalid_category(self, checker):
        """Test location with bad category fails.

        Spec: Location category must be a valid value.
        """
        content = {
            "name": "Valid Location Name",
            "description": "A valid description that meets length requirements.",
            "category": "invalid_xyz_category",  # Invalid category
        }

        result = checker.check_location(content)

        assert result.passed is False
        assert "valid_values" in result.checks_failed or "category" in result.checks_failed

    # NPC tests

    def test_quality_check_npc_valid(self, checker):
        """Test NPC with name/desc/dialogue passes.

        Spec: NPC with name 2-40 chars, non-empty description and dialogue passes.
        """
        content = {
            "name": "Mysterious Traveler",
            "description": "A cloaked figure with keen eyes.",
            "dialogue": "Greetings, traveler. What brings you here?",
        }

        result = checker.check_npc(content)

        assert result.passed is True
        assert len(result.checks_failed) == 0

    def test_quality_check_npc_empty_dialogue(self, checker):
        """Test NPC with empty dialogue fails.

        Spec: NPC dialogue must be non-empty.
        """
        content = {
            "name": "Silent Guard",
            "description": "A stoic guard standing at attention.",
            "dialogue": "",  # Empty dialogue
        }

        result = checker.check_npc(content)

        assert result.passed is False
        assert "non_empty" in result.checks_failed or "dialogue" in result.checks_failed

    # Quest tests

    def test_quality_check_quest_valid(self, checker):
        """Test quest with valid fields passes.

        Spec: Quest with non-empty name, desc 10-300 chars, valid objective_type passes.
        """
        content = {
            "name": "The Lost Artifact",
            "description": "Find the ancient artifact hidden in the ruins.",
            "objective_type": "fetch",
        }

        result = checker.check_quest(content)

        assert result.passed is True
        assert len(result.checks_failed) == 0

    # Item tests

    def test_quality_check_item_valid(self, checker):
        """Test item with valid fields passes.

        Spec: Item with non-empty name, non-empty description, valid item_type passes.
        """
        content = {
            "name": "Iron Sword",
            "description": "A sturdy blade forged from iron.",
            "item_type": "weapon",
        }

        result = checker.check_item(content)

        assert result.passed is True
        assert len(result.checks_failed) == 0

    # Placeholder detection test

    def test_quality_check_placeholder_detection(self, checker):
        """Test content with placeholder text fails.

        Spec: Content with "Unknown", "TODO", "placeholder" text fails.
        """
        content = {
            "name": "Unknown Chamber",  # Placeholder pattern
            "description": "A mysterious chamber awaits exploration.",
            "category": "dungeon",
        }

        result = checker.check_location(content)

        assert result.passed is False
        assert "no_placeholder" in result.checks_failed or "placeholder" in result.checks_failed

    # Batch check test

    def test_quality_checker_batch(self, checker):
        """Test batch check returns all results.

        Spec: check_batch() processes multiple items and returns all results.
        """
        items = [
            (
                ContentType.LOCATION,
                {
                    "name": "Valid Forest",
                    "description": "A beautiful forest with tall trees.",
                    "category": "forest",
                },
            ),
            (
                ContentType.NPC,
                {
                    "name": "Valid NPC",
                    "description": "A friendly merchant.",
                    "dialogue": "Welcome to my shop!",
                },
            ),
        ]

        results = checker.check_batch(items)

        assert len(results) == 2
        assert all(isinstance(r, QualityResult) for r in results)

    # Generic check method test

    def test_quality_check_dispatches_correctly(self, checker):
        """Test check() dispatches to correct type-specific method.

        Spec: check() method dispatches based on content_type parameter.
        """
        content = {
            "name": "Test Quest",
            "description": "A quest to test the dispatch functionality.",
            "objective_type": "kill",
        }

        result = checker.check(ContentType.QUEST, content)

        assert isinstance(result, QualityResult)
        assert result.content_type == ContentType.QUEST
