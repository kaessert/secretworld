"""Tests for USE objective type for quests.

Tests the USE objective type which allows quests to require players
to use specific items (e.g., "Use a Health Potion to heal yourself").
"""

import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType


class TestUseObjectiveType:
    """Test that USE objective type exists and has correct value."""

    def test_use_objective_type_exists(self):
        """Test ObjectiveType.USE enum exists."""
        assert hasattr(ObjectiveType, "USE")

    def test_use_objective_type_value(self):
        """Test ObjectiveType.USE has value 'use'."""
        assert ObjectiveType.USE.value == "use"


class TestRecordUse:
    """Test record_use() method on Character."""

    @pytest.fixture
    def character(self):
        """Create a test character."""
        return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)

    @pytest.fixture
    def health_potion(self):
        """Create a test health potion."""
        return Item(
            name="Health Potion",
            description="Restores 50 health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=50,
            value=10,
        )

    @pytest.fixture
    def use_quest(self):
        """Create a test USE quest."""
        return Quest(
            name="Heal Yourself",
            description="Use a Health Potion to recover",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )

    def test_record_use_increments_progress(self, character, use_quest):
        """Test record_use() increments progress for matching ACTIVE USE quests."""
        character.quests.append(use_quest)

        messages = character.record_use("Health Potion")

        assert use_quest.current_count == 1
        assert len(messages) > 0

    def test_record_use_case_insensitive(self, character, use_quest):
        """Test record_use() matches item names case-insensitively."""
        character.quests.append(use_quest)

        # Test various case combinations
        character.record_use("health potion")
        assert use_quest.current_count == 1

    def test_record_use_case_insensitive_uppercase(self, character):
        """Test record_use() matches item names with uppercase target."""
        quest = Quest(
            name="Heal Yourself",
            description="Use a Health Potion to recover",
            objective_type=ObjectiveType.USE,
            target="HEALTH POTION",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )
        character.quests.append(quest)

        character.record_use("Health Potion")
        assert quest.current_count == 1

    def test_record_use_non_matching_item_no_progress(self, character, use_quest):
        """Test record_use() does not progress for non-matching items."""
        character.quests.append(use_quest)

        messages = character.record_use("Mana Potion")

        assert use_quest.current_count == 0
        assert len(messages) == 0

    def test_record_use_only_active_quests_progress(self, character):
        """Test record_use() only progresses ACTIVE quests."""
        # Create quests with various statuses
        available_quest = Quest(
            name="Available Quest",
            description="Test",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.AVAILABLE,
        )
        completed_quest = Quest(
            name="Completed Quest",
            description="Test",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.COMPLETED,
        )
        active_quest = Quest(
            name="Active Quest",
            description="Test",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )

        character.quests.extend([available_quest, completed_quest, active_quest])

        messages = character.record_use("Health Potion")

        assert available_quest.current_count == 0
        assert completed_quest.current_count == 0
        assert active_quest.current_count == 1
        assert len(messages) == 1

    def test_record_use_only_use_objective_type_progresses(self, character):
        """Test record_use() only progresses USE objective type quests."""
        # Create quests with different objective types but same target
        kill_quest = Quest(
            name="Kill Quest",
            description="Test",
            objective_type=ObjectiveType.KILL,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )
        collect_quest = Quest(
            name="Collect Quest",
            description="Test",
            objective_type=ObjectiveType.COLLECT,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )
        use_quest = Quest(
            name="Use Quest",
            description="Test",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )

        character.quests.extend([kill_quest, collect_quest, use_quest])

        character.record_use("Health Potion")

        assert kill_quest.current_count == 0
        assert collect_quest.current_count == 0
        assert use_quest.current_count == 1

    def test_record_use_status_changes_to_ready_on_completion(self, character, use_quest):
        """Test status changes to READY_TO_TURN_IN when quest is completed."""
        character.quests.append(use_quest)

        messages = character.record_use("Health Potion")

        assert use_quest.status == QuestStatus.READY_TO_TURN_IN
        assert "Quest objectives complete" in messages[0]

    def test_record_use_multiple_quests_can_progress(self, character):
        """Test multiple USE quests can progress from single item use."""
        quest1 = Quest(
            name="Quest One",
            description="First quest",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=2,
            status=QuestStatus.ACTIVE,
        )
        quest2 = Quest(
            name="Quest Two",
            description="Second quest",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )

        character.quests.extend([quest1, quest2])

        messages = character.record_use("Health Potion")

        assert quest1.current_count == 1
        assert quest2.current_count == 1
        assert len(messages) == 2

    def test_record_use_progress_message_format(self, character):
        """Test progress message format for in-progress quest."""
        quest = Quest(
            name="Heal Lots",
            description="Use many potions",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=3,
            status=QuestStatus.ACTIVE,
        )
        character.quests.append(quest)

        messages = character.record_use("Health Potion")

        assert "Quest progress: Heal Lots [1/3]" in messages[0]

    def test_record_use_completion_message_with_quest_giver(self, character):
        """Test completion message includes quest giver name."""
        quest = Quest(
            name="Heal Quest",
            description="Test",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
            quest_giver="Healer Bob",
        )
        character.quests.append(quest)

        messages = character.record_use("Health Potion")

        assert "Return to Healer Bob" in messages[0]


class TestUseItemIntegration:
    """Test use_item() integration with record_use()."""

    @pytest.fixture
    def character(self):
        """Create a test character with reduced health."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        char.health = 50  # Reduce health so potion can be used
        return char

    @pytest.fixture
    def health_potion(self):
        """Create a test health potion."""
        return Item(
            name="Health Potion",
            description="Restores 50 health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=50,
        )

    def test_use_item_triggers_quest_progress(self, character, health_potion):
        """Test that using an item triggers quest progress via record_use()."""
        quest = Quest(
            name="Heal Yourself",
            description="Use a Health Potion",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )
        character.quests.append(quest)
        character.inventory.add_item(health_potion)

        success, message = character.use_item(health_potion)

        assert success
        assert quest.current_count == 1
        assert quest.status == QuestStatus.READY_TO_TURN_IN

    def test_use_item_includes_quest_message(self, character, health_potion):
        """Test that use_item() return message includes quest progress."""
        quest = Quest(
            name="Heal Yourself",
            description="Use a Health Potion",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=1,
            status=QuestStatus.ACTIVE,
        )
        character.quests.append(quest)
        character.inventory.add_item(health_potion)

        success, message = character.use_item(health_potion)

        assert success
        assert "Quest objectives complete" in message


class TestQuestSerializationWithUse:
    """Test quest serialization round-trips with USE type."""

    def test_use_quest_to_dict(self):
        """Test USE quest serializes correctly."""
        quest = Quest(
            name="Use Test",
            description="Test serialization",
            objective_type=ObjectiveType.USE,
            target="Health Potion",
            target_count=3,
            current_count=1,
            status=QuestStatus.ACTIVE,
        )

        data = quest.to_dict()

        assert data["objective_type"] == "use"

    def test_use_quest_from_dict(self):
        """Test USE quest deserializes correctly."""
        data = {
            "name": "Use Test",
            "description": "Test deserialization",
            "objective_type": "use",
            "target": "Health Potion",
            "target_count": 3,
            "current_count": 1,
            "status": "active",
        }

        quest = Quest.from_dict(data)

        assert quest.objective_type == ObjectiveType.USE

    def test_use_quest_round_trip(self):
        """Test USE quest survives serialization round-trip."""
        original = Quest(
            name="Round Trip Test",
            description="Test full cycle",
            objective_type=ObjectiveType.USE,
            target="Magic Scroll",
            target_count=5,
            current_count=2,
            status=QuestStatus.ACTIVE,
            quest_giver="Wizard",
        )

        data = original.to_dict()
        restored = Quest.from_dict(data)

        assert restored.name == original.name
        assert restored.objective_type == ObjectiveType.USE
        assert restored.target == original.target
        assert restored.target_count == original.target_count
        assert restored.current_count == original.current_count
        assert restored.status == original.status
        assert restored.quest_giver == original.quest_giver
