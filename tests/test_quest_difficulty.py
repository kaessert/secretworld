"""Tests for quest difficulty indicators.

These tests verify:
- QuestDifficulty enum values and serialization (Spec item 1)
- Quest difficulty and recommended_level fields (Spec item 2)
- Serialization roundtrip for difficulty features
"""

import pytest

from cli_rpg.models.quest import (
    ObjectiveType,
    Quest,
    QuestDifficulty,
    QuestStatus,
)


class TestQuestDifficultyEnum:
    """Tests for QuestDifficulty enum - Spec item 1."""

    def test_difficulty_enum_values(self):
        """Test that all expected difficulty enum values exist."""
        # Spec: QuestDifficulty enum with TRIVIAL, EASY, NORMAL, HARD, DEADLY
        assert QuestDifficulty.TRIVIAL.value == "trivial"
        assert QuestDifficulty.EASY.value == "easy"
        assert QuestDifficulty.NORMAL.value == "normal"
        assert QuestDifficulty.HARD.value == "hard"
        assert QuestDifficulty.DEADLY.value == "deadly"

    def test_difficulty_enum_serialization(self):
        """Test that difficulty enum values can be serialized and deserialized."""
        # Spec: Difficulty should serialize correctly for save/load
        for difficulty in QuestDifficulty:
            value = difficulty.value
            restored = QuestDifficulty(value)
            assert restored == difficulty


class TestQuestDifficultyFields:
    """Tests for Quest difficulty and recommended_level fields - Spec item 2."""

    def _create_minimal_quest(self, **overrides) -> Quest:
        """Create a minimal valid quest for testing."""
        defaults = {
            "name": "Test Quest",
            "description": "A test quest description",
            "objective_type": ObjectiveType.KILL,
            "target": "goblin",
        }
        defaults.update(overrides)
        return Quest(**defaults)

    def test_difficulty_defaults_to_normal(self):
        """Test that difficulty defaults to NORMAL when not specified."""
        # Spec: difficulty field with default NORMAL
        quest = self._create_minimal_quest()
        assert quest.difficulty == QuestDifficulty.NORMAL

    def test_recommended_level_defaults_to_1(self):
        """Test that recommended_level defaults to 1 when not specified."""
        # Spec: recommended_level field with default 1
        quest = self._create_minimal_quest()
        assert quest.recommended_level == 1

    def test_quest_with_custom_difficulty(self):
        """Test that quest can be created with custom difficulty."""
        # Spec: Quest fields should accept custom difficulty values
        quest = self._create_minimal_quest(difficulty=QuestDifficulty.DEADLY)
        assert quest.difficulty == QuestDifficulty.DEADLY

    def test_quest_with_custom_recommended_level(self):
        """Test that quest can be created with custom recommended level."""
        # Spec: Quest fields should accept custom recommended_level values
        quest = self._create_minimal_quest(recommended_level=10)
        assert quest.recommended_level == 10

    def test_recommended_level_must_be_positive(self):
        """Test that recommended_level must be at least 1."""
        # Spec: Validation - recommended_level should be a positive integer
        with pytest.raises(ValueError, match="recommended_level must be at least 1"):
            self._create_minimal_quest(recommended_level=0)

        with pytest.raises(ValueError, match="recommended_level must be at least 1"):
            self._create_minimal_quest(recommended_level=-5)

    def test_difficulty_serialization_roundtrip(self):
        """Test that difficulty is properly serialized and deserialized."""
        # Spec: Serialization roundtrip for difficulty
        quest = self._create_minimal_quest(difficulty=QuestDifficulty.HARD)
        data = quest.to_dict()
        assert data["difficulty"] == "hard"

        restored = Quest.from_dict(data)
        assert restored.difficulty == QuestDifficulty.HARD

    def test_recommended_level_serialization_roundtrip(self):
        """Test that recommended_level is properly serialized and deserialized."""
        # Spec: Serialization roundtrip for recommended_level
        quest = self._create_minimal_quest(recommended_level=15)
        data = quest.to_dict()
        assert data["recommended_level"] == 15

        restored = Quest.from_dict(data)
        assert restored.recommended_level == 15

    def test_difficulty_defaults_in_from_dict(self):
        """Test that from_dict uses default difficulty when not in data."""
        # Spec: Backward compatibility - older saves without difficulty should work
        data = {
            "name": "Old Quest",
            "description": "An old quest without difficulty",
            "status": "available",
            "objective_type": "kill",
            "target": "troll",
        }
        quest = Quest.from_dict(data)
        assert quest.difficulty == QuestDifficulty.NORMAL
        assert quest.recommended_level == 1

    def test_all_difficulties_with_recommended_levels(self):
        """Test various difficulty/level combinations."""
        # Spec: All difficulty levels should work with any valid recommended_level
        test_cases = [
            (QuestDifficulty.TRIVIAL, 1),
            (QuestDifficulty.EASY, 3),
            (QuestDifficulty.NORMAL, 5),
            (QuestDifficulty.HARD, 10),
            (QuestDifficulty.DEADLY, 20),
        ]
        for difficulty, level in test_cases:
            quest = self._create_minimal_quest(
                difficulty=difficulty, recommended_level=level
            )
            assert quest.difficulty == difficulty
            assert quest.recommended_level == level

            # Verify roundtrip
            restored = Quest.from_dict(quest.to_dict())
            assert restored.difficulty == difficulty
            assert restored.recommended_level == level
