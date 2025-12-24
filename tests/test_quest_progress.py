"""Tests for quest progress tracking from combat.

Spec: When defeating an enemy in combat, increment current_count on any active KILL quests
where the enemy's name matches the quest's target. When a quest reaches target_count,
mark it as COMPLETED and notify the player.
"""

import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType


@pytest.fixture
def character():
    """Create a basic character for testing."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def kill_quest():
    """Create a basic kill quest."""
    return Quest(
        name="Goblin Slayer",
        description="Kill 3 goblins",
        status=QuestStatus.ACTIVE,
        objective_type=ObjectiveType.KILL,
        target="Goblin",
        target_count=3,
        current_count=0,
    )


class TestRecordKill:
    """Tests for Character.record_kill() method."""

    # Spec: Defeating enemy increments matching quest progress
    def test_record_kill_increments_matching_quest_progress(self, character, kill_quest):
        """Test that killing an enemy increments matching quest's current_count."""
        character.quests.append(kill_quest)

        character.record_kill("Goblin")

        assert kill_quest.current_count == 1

    # Spec: Player receives notification on quest progress
    def test_record_kill_returns_progress_message(self, character, kill_quest):
        """Test that record_kill returns progress notification."""
        character.quests.append(kill_quest)

        messages = character.record_kill("Goblin")

        assert len(messages) == 1
        assert "Quest progress: Goblin Slayer [1/3]" in messages[0]

    # Spec: Quest completion detected and status updated to COMPLETED
    def test_record_kill_marks_quest_completed_when_target_reached(self, character):
        """Test that quest status is set to COMPLETED when target_count is reached."""
        quest = Quest(
            name="Goblin Slayer",
            description="Kill 1 goblin",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=1,
            current_count=0,
        )
        character.quests.append(quest)

        character.record_kill("Goblin")

        assert quest.status == QuestStatus.COMPLETED
        assert quest.current_count == 1

    # Spec: Player receives special notification on quest completion
    def test_record_kill_returns_completion_message(self, character):
        """Test that record_kill returns completion notification when quest completes."""
        quest = Quest(
            name="Goblin Slayer",
            description="Kill 1 goblin",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=1,
            current_count=0,
        )
        character.quests.append(quest)

        messages = character.record_kill("Goblin")

        assert len(messages) == 1
        assert "Quest Complete: Goblin Slayer!" in messages[0]

    # Spec: Compare enemy name to quest target (case-insensitive)
    def test_record_kill_matches_case_insensitive(self, character, kill_quest):
        """Test that enemy name matching is case-insensitive."""
        character.quests.append(kill_quest)

        # Kill with different case
        character.record_kill("GOBLIN")
        assert kill_quest.current_count == 1

        character.record_kill("goblin")
        assert kill_quest.current_count == 2

        character.record_kill("GoBLiN")
        assert kill_quest.current_count == 3

    # Spec: Non-matching enemy names don't increment progress
    def test_record_kill_does_not_increment_non_matching_quest(self, character, kill_quest):
        """Test that killing non-matching enemies doesn't increment quest progress."""
        character.quests.append(kill_quest)

        messages = character.record_kill("Dragon")

        assert kill_quest.current_count == 0
        assert len(messages) == 0

    # Spec: Only ACTIVE quests get progress (not COMPLETED, AVAILABLE, FAILED)
    def test_record_kill_only_affects_active_quests(self, character):
        """Test that only ACTIVE quests get progress, not other statuses."""
        statuses_to_test = [
            QuestStatus.AVAILABLE,
            QuestStatus.COMPLETED,
            QuestStatus.FAILED,
        ]

        for status in statuses_to_test:
            quest = Quest(
                name=f"Quest {status.value}",
                description="Kill goblins",
                status=status,
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                target_count=3,
                current_count=0,
            )
            character.quests.append(quest)

        character.record_kill("Goblin")

        # None of the non-active quests should have progress
        for quest in character.quests:
            assert quest.current_count == 0

    # Spec: Only KILL objective type quests get progress
    def test_record_kill_only_affects_kill_objective_quests(self, character):
        """Test that only KILL objective type quests get progress."""
        objective_types_to_test = [
            ObjectiveType.COLLECT,
            ObjectiveType.EXPLORE,
            ObjectiveType.TALK,
        ]

        for obj_type in objective_types_to_test:
            quest = Quest(
                name=f"Quest {obj_type.value}",
                description="Quest description",
                status=QuestStatus.ACTIVE,
                objective_type=obj_type,
                target="Goblin",
                target_count=3,
                current_count=0,
            )
            character.quests.append(quest)

        character.record_kill("Goblin")

        # None of the non-KILL quests should have progress
        for quest in character.quests:
            assert quest.current_count == 0

    # Spec: Multiple quests can progress from same kill
    def test_record_kill_progresses_multiple_matching_quests(self, character):
        """Test that multiple quests matching the same enemy all get progress."""
        quest1 = Quest(
            name="Goblin Hunt",
            description="Kill 5 goblins",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=5,
            current_count=0,
        )
        quest2 = Quest(
            name="Monster Slayer",
            description="Kill 3 goblins",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            current_count=2,  # One kill away from completion
        )
        character.quests.extend([quest1, quest2])

        messages = character.record_kill("Goblin")

        # Both quests should progress
        assert quest1.current_count == 1
        assert quest2.current_count == 3
        # Quest 2 should be completed
        assert quest2.status == QuestStatus.COMPLETED
        # Should have 2 messages (one progress, one completion)
        assert len(messages) == 2

    def test_record_kill_returns_empty_list_when_no_matching_quests(self, character):
        """Test that record_kill returns empty list when no quests match."""
        messages = character.record_kill("Dragon")

        assert messages == []

    def test_record_kill_with_no_quests(self, character):
        """Test that record_kill works when character has no quests."""
        messages = character.record_kill("Goblin")

        assert messages == []
        assert character.quests == []
