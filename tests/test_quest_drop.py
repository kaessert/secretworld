"""Tests for DROP quest objective type.

These tests verify the DROP objective type which requires both a specific enemy
kill AND a specific item drop to progress the quest.
"""


from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.character import Character


class TestDropObjectiveType:
    """Tests for ObjectiveType.DROP enum value."""

    # Spec: ObjectiveType.DROP exists and works
    def test_drop_objective_type_exists(self):
        """Verify ObjectiveType.DROP is valid."""
        assert ObjectiveType.DROP.value == "drop"

    def test_quest_with_drop_objective_type(self):
        """Test creating a quest with DROP objective type."""
        quest = Quest(
            name="Wolf Pelts",
            description="Collect wolf pelts from wolves",
            objective_type=ObjectiveType.DROP,
            target="Wolf",
            drop_item="Wolf Pelt",
            target_count=3,
        )
        assert quest.objective_type == ObjectiveType.DROP
        assert quest.target == "Wolf"
        assert quest.drop_item == "Wolf Pelt"


class TestDropItemField:
    """Tests for the drop_item field on Quest."""

    # Spec: Quest can have optional drop_item field
    def test_quest_with_drop_item_field(self):
        """Create quest with drop_item set."""
        quest = Quest(
            name="Collect Fangs",
            description="Collect spider fangs from giant spiders",
            objective_type=ObjectiveType.DROP,
            target="Giant Spider",
            drop_item="Spider Fang",
            target_count=5,
        )
        assert quest.drop_item == "Spider Fang"

    def test_quest_without_drop_item_defaults_to_none(self):
        """Test that drop_item defaults to None when not specified."""
        quest = Quest(
            name="Kill Wolves",
            description="Defeat wolves",
            objective_type=ObjectiveType.KILL,
            target="Wolf",
        )
        assert quest.drop_item is None


class TestDropItemSerialization:
    """Tests for drop_item serialization."""

    # Spec: to_dict()/from_dict() round-trip preserves drop_item
    def test_quest_drop_item_serialization(self):
        """to_dict()/from_dict() round-trip preserves drop_item."""
        original = Quest(
            name="Wolf Pelts",
            description="Collect wolf pelts from wolves",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.DROP,
            target="Wolf",
            drop_item="Wolf Pelt",
            target_count=3,
            current_count=1,
        )
        data = original.to_dict()

        # Verify drop_item is in serialized data
        assert data["drop_item"] == "Wolf Pelt"

        # Verify roundtrip
        restored = Quest.from_dict(data)
        assert restored.drop_item == original.drop_item
        assert restored.objective_type == original.objective_type
        assert restored.target == original.target

    def test_quest_serialization_without_drop_item(self):
        """Test serialization works when drop_item is None."""
        original = Quest(
            name="Kill Wolves",
            description="Defeat wolves",
            objective_type=ObjectiveType.KILL,
            target="Wolf",
        )
        data = original.to_dict()
        assert data["drop_item"] is None

        restored = Quest.from_dict(data)
        assert restored.drop_item is None

    def test_from_dict_without_drop_item_key(self):
        """Test from_dict handles missing drop_item key (backward compatibility)."""
        data = {
            "name": "Old Quest",
            "description": "An old quest without drop_item",
            "status": "active",
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "current_count": 0,
        }
        quest = Quest.from_dict(data)
        assert quest.drop_item is None


class TestRecordDrop:
    """Tests for Character.record_drop() method."""

    def _create_character_with_drop_quest(
        self,
        enemy_name: str = "Wolf",
        drop_item: str = "Wolf Pelt",
        target_count: int = 3,
        status: QuestStatus = QuestStatus.ACTIVE,
        quest_giver: str = None,
    ) -> Character:
        """Helper to create a character with a DROP quest."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        quest = Quest(
            name="Wolf Pelts",
            description="Collect wolf pelts",
            status=status,
            objective_type=ObjectiveType.DROP,
            target=enemy_name,
            drop_item=drop_item,
            target_count=target_count,
            quest_giver=quest_giver,
        )
        character.quests.append(quest)
        return character

    # Spec: record_drop increments progress when both enemy AND item match
    def test_record_drop_increments_matching_quest(self):
        """Both enemy + item match -> progress increments."""
        character = self._create_character_with_drop_quest()
        messages = character.record_drop("Wolf", "Wolf Pelt")

        assert character.quests[0].current_count == 1
        assert len(messages) == 1
        assert "Quest progress: Wolf Pelts [1/3]" in messages[0]

    # Spec: record_drop does NOT increment when enemy doesn't match
    def test_record_drop_enemy_mismatch_no_progress(self):
        """Wrong enemy, right item -> no progress."""
        character = self._create_character_with_drop_quest()
        messages = character.record_drop("Bear", "Wolf Pelt")

        assert character.quests[0].current_count == 0
        assert len(messages) == 0

    # Spec: record_drop does NOT increment when item doesn't match
    def test_record_drop_item_mismatch_no_progress(self):
        """Right enemy, wrong item -> no progress."""
        character = self._create_character_with_drop_quest()
        messages = character.record_drop("Wolf", "Bear Claw")

        assert character.quests[0].current_count == 0
        assert len(messages) == 0

    # Spec: Both enemy and item matching is case-insensitive
    def test_record_drop_case_insensitive(self):
        """Both matches are case-insensitive."""
        character = self._create_character_with_drop_quest(
            enemy_name="Giant Spider", drop_item="Spider Fang"
        )

        # Different case combinations should all match
        character.record_drop("giant spider", "spider fang")
        assert character.quests[0].current_count == 1

        character.record_drop("GIANT SPIDER", "SPIDER FANG")
        assert character.quests[0].current_count == 2

        character.record_drop("GiAnT sPiDeR", "SpIdEr FaNg")
        assert character.quests[0].current_count == 3

    # Spec: Only ACTIVE quests get progress
    def test_record_drop_only_active_quests(self):
        """Only ACTIVE status gets progress."""
        # Test with various non-ACTIVE statuses
        for status in [
            QuestStatus.AVAILABLE,
            QuestStatus.COMPLETED,
            QuestStatus.FAILED,
            QuestStatus.READY_TO_TURN_IN,
        ]:
            character = self._create_character_with_drop_quest(status=status)
            messages = character.record_drop("Wolf", "Wolf Pelt")

            assert character.quests[0].current_count == 0
            assert len(messages) == 0

    # Spec: Completion sets status to READY_TO_TURN_IN
    def test_record_drop_marks_ready_to_turn_in(self):
        """Completion sets READY_TO_TURN_IN status."""
        character = self._create_character_with_drop_quest(target_count=1)
        character.record_drop("Wolf", "Wolf Pelt")

        assert character.quests[0].status == QuestStatus.READY_TO_TURN_IN
        assert character.quests[0].current_count == 1

    # Spec: Returns proper notification messages
    def test_record_drop_returns_progress_messages(self):
        """Returns proper notifications for progress."""
        character = self._create_character_with_drop_quest(target_count=3)

        # Progress message
        messages = character.record_drop("Wolf", "Wolf Pelt")
        assert len(messages) == 1
        assert "Quest progress: Wolf Pelts [1/3]" in messages[0]

    def test_record_drop_returns_completion_message_with_quest_giver(self):
        """Returns completion message mentioning quest giver."""
        character = self._create_character_with_drop_quest(
            target_count=1, quest_giver="Hunter Bob"
        )
        messages = character.record_drop("Wolf", "Wolf Pelt")

        assert len(messages) == 1
        assert "Quest objectives complete: Wolf Pelts!" in messages[0]
        assert "Return to Hunter Bob" in messages[0]

    def test_record_drop_returns_completion_message_without_quest_giver(self):
        """Returns generic completion message when no quest giver."""
        character = self._create_character_with_drop_quest(
            target_count=1, quest_giver=None
        )
        messages = character.record_drop("Wolf", "Wolf Pelt")

        assert len(messages) == 1
        assert "Quest objectives complete: Wolf Pelts!" in messages[0]
        assert "Return to the quest giver" in messages[0]

    # Spec: Multiple DROP quests can progress together
    def test_record_drop_multiple_quests(self):
        """Multiple DROP quests can progress together."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Add two DROP quests for the same enemy/item combo
        quest1 = Quest(
            name="Wolf Pelts for Bob",
            description="Collect wolf pelts for Bob",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.DROP,
            target="Wolf",
            drop_item="Wolf Pelt",
            target_count=3,
        )
        quest2 = Quest(
            name="Wolf Pelts for Alice",
            description="Collect wolf pelts for Alice",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.DROP,
            target="Wolf",
            drop_item="Wolf Pelt",
            target_count=2,
        )
        character.quests.append(quest1)
        character.quests.append(quest2)

        messages = character.record_drop("Wolf", "Wolf Pelt")

        # Both quests should progress
        assert quest1.current_count == 1
        assert quest2.current_count == 1
        assert len(messages) == 2

    def test_record_drop_does_not_affect_kill_quests(self):
        """DROP tracking doesn't affect KILL quests for the same enemy."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        kill_quest = Quest(
            name="Kill Wolves",
            description="Defeat wolves",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Wolf",
            target_count=5,
        )
        drop_quest = Quest(
            name="Wolf Pelts",
            description="Collect wolf pelts",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.DROP,
            target="Wolf",
            drop_item="Wolf Pelt",
            target_count=3,
        )
        character.quests.append(kill_quest)
        character.quests.append(drop_quest)

        # record_drop should only affect DROP quests
        messages = character.record_drop("Wolf", "Wolf Pelt")

        assert kill_quest.current_count == 0  # Not affected
        assert drop_quest.current_count == 1  # Affected
        assert len(messages) == 1

    def test_record_drop_does_not_affect_collect_quests(self):
        """DROP tracking doesn't affect COLLECT quests for the same item."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        collect_quest = Quest(
            name="Collect Pelts",
            description="Collect any pelts",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.COLLECT,
            target="Wolf Pelt",
            target_count=5,
        )
        drop_quest = Quest(
            name="Wolf Pelts",
            description="Collect wolf pelts from wolves",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.DROP,
            target="Wolf",
            drop_item="Wolf Pelt",
            target_count=3,
        )
        character.quests.append(collect_quest)
        character.quests.append(drop_quest)

        # record_drop should only affect DROP quests
        messages = character.record_drop("Wolf", "Wolf Pelt")

        assert collect_quest.current_count == 0  # Not affected by record_drop
        assert drop_quest.current_count == 1  # Affected
        assert len(messages) == 1
