"""Tests for companion-specific quests and storylines.

These tests verify the implementation of personal quests for companions that unlock
at higher bond levels. Each companion can have a personal quest that becomes available
when their bond reaches TRUSTED (50+ points).
"""
import pytest
from cli_rpg.models.companion import Companion, BondLevel
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.companion_quests import (
    is_quest_available,
    accept_companion_quest,
    check_companion_quest_completion,
    QUEST_COMPLETION_BOND_BONUS,
)


class TestCompanionPersonalQuest:
    """Test companion personal_quest field."""

    # Spec: Companions can have a `personal_quest` field (optional Quest)
    def test_companion_has_personal_quest_field(self):
        """Companions can have an optional personal_quest."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
            target_count=1,
        )
        companion = Companion(
            name="Kira",
            description="A disgraced warrior",
            recruited_at="Arena",
            personality="warrior",
            personal_quest=quest,
        )
        assert companion.personal_quest is not None
        assert companion.personal_quest.name == "Kira's Honor"

    def test_companion_personal_quest_defaults_to_none(self):
        """Companions without personal quest have None."""
        companion = Companion(
            name="Sage",
            description="A wise scholar",
            recruited_at="Library",
        )
        assert companion.personal_quest is None


class TestQuestAvailability:
    """Test when companion quests become available.

    Spec: Quest unlocks at TRUSTED bond level (50+ points)
    """

    def test_quest_not_available_at_stranger(self):
        """Personal quest unavailable at STRANGER bond level."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=10,  # STRANGER
            personal_quest=quest,
        )
        assert not is_quest_available(companion)

    def test_quest_not_available_at_acquaintance(self):
        """Personal quest unavailable at ACQUAINTANCE bond level."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=40,  # ACQUAINTANCE
            personal_quest=quest,
        )
        assert not is_quest_available(companion)

    def test_quest_available_at_trusted(self):
        """Personal quest becomes available at TRUSTED bond level."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=50,  # TRUSTED
            personal_quest=quest,
        )
        assert is_quest_available(companion)

    def test_quest_available_at_devoted(self):
        """Personal quest remains available at DEVOTED bond level."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=80,  # DEVOTED
            personal_quest=quest,
        )
        assert is_quest_available(companion)

    def test_no_quest_means_not_available(self):
        """Companion without personal quest returns False."""
        companion = Companion(
            name="Sage",
            description="A scholar",
            recruited_at="Library",
            bond_points=75,
        )
        assert not is_quest_available(companion)


class TestAcceptCompanionQuest:
    """Test accepting a companion's personal quest."""

    def test_accept_quest_returns_active_quest(self):
        """Accepting quest returns an ACTIVE copy for character."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=50,
            personal_quest=quest,
        )
        accepted = accept_companion_quest(companion)
        assert accepted is not None
        assert accepted.status == QuestStatus.ACTIVE
        assert accepted.quest_giver == "Kira"

    def test_accept_quest_fails_if_not_available(self):
        """Cannot accept quest if bond too low."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=30,  # Too low
            personal_quest=quest,
        )
        accepted = accept_companion_quest(companion)
        assert accepted is None

    def test_accept_quest_fails_if_no_quest(self):
        """Cannot accept if companion has no personal quest."""
        companion = Companion(
            name="Sage",
            description="A scholar",
            recruited_at="Library",
            bond_points=75,
        )
        accepted = accept_companion_quest(companion)
        assert accepted is None


class TestCompanionQuestCompletion:
    """Test companion quest completion bonuses.

    Spec: Quest completion grants +15 bond points (significant relationship boost)
    """

    def test_completing_companion_quest_grants_bond_bonus(self):
        """Completing personal quest gives QUEST_COMPLETION_BOND_BONUS."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=50,
            personal_quest=quest,
        )
        initial_bond = companion.bond_points
        messages = check_companion_quest_completion(companion, "Kira's Honor")
        assert companion.bond_points == initial_bond + QUEST_COMPLETION_BOND_BONUS

    def test_completion_returns_message(self):
        """Completion returns flavor message about strengthened bond."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=50,
            personal_quest=quest,
        )
        messages = check_companion_quest_completion(companion, "Kira's Honor")
        assert len(messages) > 0
        assert "Kira" in messages[0]

    def test_non_matching_quest_no_bonus(self):
        """Completing unrelated quest gives no companion bonus."""
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            bond_points=50,
            personal_quest=Quest(
                name="Kira's Honor",
                description="Test",
                objective_type=ObjectiveType.COLLECT,
                target="Sword",
            ),
        )
        initial_bond = companion.bond_points
        messages = check_companion_quest_completion(companion, "Kill Goblins")
        assert companion.bond_points == initial_bond
        assert len(messages) == 0


class TestCompanionQuestSerialization:
    """Test serialization of companions with personal quests.

    Spec: Uses existing Quest model serialization for personal_quest field
    """

    def test_companion_with_quest_to_dict(self):
        """Companion with personal_quest serializes correctly."""
        quest = Quest(
            name="Kira's Honor",
            description="Help Kira reclaim her family sword.",
            objective_type=ObjectiveType.COLLECT,
            target="Family Sword",
        )
        companion = Companion(
            name="Kira",
            description="A warrior",
            recruited_at="Arena",
            personal_quest=quest,
        )
        data = companion.to_dict()
        assert "personal_quest" in data
        assert data["personal_quest"]["name"] == "Kira's Honor"

    def test_companion_with_quest_from_dict(self):
        """Companion with personal_quest deserializes correctly."""
        data = {
            "name": "Kira",
            "description": "A warrior",
            "recruited_at": "Arena",
            "bond_points": 50,
            "personality": "warrior",
            "personal_quest": {
                "name": "Kira's Honor",
                "description": "Help Kira reclaim her family sword.",
                "objective_type": "collect",
                "target": "Family Sword",
                "status": "available",
                "target_count": 1,
                "current_count": 0,
                "gold_reward": 0,
                "xp_reward": 0,
                "item_rewards": [],
                "quest_giver": None,
                "drop_item": None,
            },
        }
        companion = Companion.from_dict(data)
        assert companion.personal_quest is not None
        assert companion.personal_quest.name == "Kira's Honor"

    def test_companion_without_quest_roundtrip(self):
        """Companion without quest serializes/deserializes to None."""
        companion = Companion(
            name="Sage",
            description="A scholar",
            recruited_at="Library",
        )
        data = companion.to_dict()
        restored = Companion.from_dict(data)
        assert restored.personal_quest is None
