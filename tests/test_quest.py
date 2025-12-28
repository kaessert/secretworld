"""Tests for the Quest model."""

import pytest

from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType


class TestQuestCreation:
    """Tests for Quest creation and validation."""

    # Spec: Quest creation with all valid attributes
    def test_create_quest_with_valid_attributes(self):
        """Test creating a quest with all valid attributes."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon terrorizing the village",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            target_count=1,
            current_count=0,
        )
        assert quest.name == "Slay the Dragon"
        assert quest.description == "Defeat the dragon terrorizing the village"
        assert quest.status == QuestStatus.ACTIVE
        assert quest.objective_type == ObjectiveType.KILL
        assert quest.target == "Dragon"
        assert quest.target_count == 1
        assert quest.current_count == 0

    # Spec: Status defaults to AVAILABLE
    def test_status_defaults_to_available(self):
        """Test that status defaults to AVAILABLE if not specified."""
        quest = Quest(
            name="Find Treasure",
            description="Locate the hidden treasure",
            objective_type=ObjectiveType.EXPLORE,
            target="Hidden Cave",
        )
        assert quest.status == QuestStatus.AVAILABLE

    # Spec: target_count defaults to 1, current_count defaults to 0
    def test_count_defaults(self):
        """Test that target_count defaults to 1 and current_count to 0."""
        quest = Quest(
            name="Find Treasure",
            description="Locate the hidden treasure",
            objective_type=ObjectiveType.EXPLORE,
            target="Hidden Cave",
        )
        assert quest.target_count == 1
        assert quest.current_count == 0


class TestNameValidation:
    """Tests for name validation (2-30 chars)."""

    # Spec: Name validation - reject outside range
    def test_name_too_short(self):
        """Test that name with less than 2 characters is rejected."""
        with pytest.raises(ValueError, match="at least 2 characters"):
            Quest(
                name="A",
                description="A valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_name_empty(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Quest(
                name="",
                description="A valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_name_whitespace_only(self):
        """Test that whitespace-only name is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Quest(
                name="   ",
                description="A valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_name_too_long(self):
        """Test that name with more than 30 characters is rejected."""
        with pytest.raises(ValueError, match="at most 30 characters"):
            Quest(
                name="A" * 31,
                description="A valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_name_minimum_length(self):
        """Test that name with exactly 2 characters is accepted."""
        quest = Quest(
            name="AB",
            description="A valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.name == "AB"

    def test_name_maximum_length(self):
        """Test that name with exactly 30 characters is accepted."""
        name = "A" * 30
        quest = Quest(
            name=name,
            description="A valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.name == name

    def test_name_is_stripped(self):
        """Test that name whitespace is stripped."""
        quest = Quest(
            name="  Quest Name  ",
            description="A valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.name == "Quest Name"


class TestDescriptionValidation:
    """Tests for description validation (1-200 chars)."""

    # Spec: Description validation - reject outside range
    def test_description_empty(self):
        """Test that empty description is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Quest(
                name="Valid Name",
                description="",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_description_whitespace_only(self):
        """Test that whitespace-only description is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Quest(
                name="Valid Name",
                description="   ",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_description_too_long(self):
        """Test that description with more than 200 characters is rejected."""
        with pytest.raises(ValueError, match="at most 200 characters"):
            Quest(
                name="Valid Name",
                description="A" * 201,
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )

    def test_description_minimum_length(self):
        """Test that description with exactly 1 character is accepted."""
        quest = Quest(
            name="Valid Name",
            description="A",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.description == "A"

    def test_description_maximum_length(self):
        """Test that description with exactly 200 characters is accepted."""
        desc = "A" * 200
        quest = Quest(
            name="Valid Name",
            description=desc,
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.description == desc

    def test_description_is_stripped(self):
        """Test that description whitespace is stripped."""
        quest = Quest(
            name="Valid Name",
            description="  Some description  ",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.description == "Some description"


class TestQuestStatusEnum:
    """Tests for QuestStatus enum values."""

    # Spec: All QuestStatus values work
    def test_all_quest_status_values(self):
        """Test that all QuestStatus enum values exist and work."""
        assert QuestStatus.AVAILABLE.value == "available"
        assert QuestStatus.ACTIVE.value == "active"
        assert QuestStatus.COMPLETED.value == "completed"
        assert QuestStatus.FAILED.value == "failed"

    def test_quest_with_each_status(self):
        """Test creating quests with each status value."""
        for status in QuestStatus:
            quest = Quest(
                name="Test Quest",
                description="A test quest",
                status=status,
                objective_type=ObjectiveType.KILL,
                target="Enemy",
            )
            assert quest.status == status


class TestObjectiveTypeEnum:
    """Tests for ObjectiveType enum values."""

    # Spec: All ObjectiveType values work
    def test_all_objective_type_values(self):
        """Test that all ObjectiveType enum values exist and work."""
        assert ObjectiveType.KILL.value == "kill"
        assert ObjectiveType.COLLECT.value == "collect"
        assert ObjectiveType.EXPLORE.value == "explore"
        assert ObjectiveType.TALK.value == "talk"

    def test_quest_with_each_objective_type(self):
        """Test creating quests with each objective type."""
        for obj_type in ObjectiveType:
            quest = Quest(
                name="Test Quest",
                description="A test quest",
                objective_type=obj_type,
                target="Target",
            )
            assert quest.objective_type == obj_type


class TestCountValidation:
    """Tests for target_count and current_count validation."""

    # Spec: target_count must be >= 1
    def test_target_count_zero_rejected(self):
        """Test that target_count of 0 is rejected."""
        with pytest.raises(ValueError, match="target_count must be at least 1"):
            Quest(
                name="Valid Name",
                description="Valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                target_count=0,
            )

    def test_target_count_negative_rejected(self):
        """Test that negative target_count is rejected."""
        with pytest.raises(ValueError, match="target_count must be at least 1"):
            Quest(
                name="Valid Name",
                description="Valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                target_count=-1,
            )

    def test_target_count_one_accepted(self):
        """Test that target_count of 1 is accepted."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=1,
        )
        assert quest.target_count == 1

    # Spec: current_count must be >= 0
    def test_current_count_negative_rejected(self):
        """Test that negative current_count is rejected."""
        with pytest.raises(ValueError, match="current_count must be at least 0"):
            Quest(
                name="Valid Name",
                description="Valid description",
                objective_type=ObjectiveType.KILL,
                target="Enemy",
                current_count=-1,
            )

    def test_current_count_zero_accepted(self):
        """Test that current_count of 0 is accepted."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            current_count=0,
        )
        assert quest.current_count == 0


class TestIsComplete:
    """Tests for is_complete property."""

    # Spec: is_complete property returns current_count >= target_count
    def test_is_complete_when_equal(self):
        """Test is_complete returns True when current_count equals target_count."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=3,
        )
        assert quest.is_complete is True

    def test_is_complete_when_exceeded(self):
        """Test is_complete returns True when current_count exceeds target_count."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=5,
        )
        assert quest.is_complete is True

    def test_is_not_complete_when_under(self):
        """Test is_complete returns False when current_count is less than target_count."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=2,
        )
        assert quest.is_complete is False


class TestProgress:
    """Tests for progress() method."""

    # Spec: progress() method increments current_count and returns True when complete
    def test_progress_increments_count(self):
        """Test that progress() increments current_count by 1."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=0,
        )
        quest.progress()
        assert quest.current_count == 1

    def test_progress_returns_false_when_not_complete(self):
        """Test that progress() returns False when quest is not complete."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=0,
        )
        result = quest.progress()
        assert result is False
        assert quest.current_count == 1

    def test_progress_returns_true_when_complete(self):
        """Test that progress() returns True when quest becomes complete."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=2,
        )
        result = quest.progress()
        assert result is True
        assert quest.current_count == 3

    def test_progress_multiple_times(self):
        """Test calling progress() multiple times."""
        quest = Quest(
            name="Valid Name",
            description="Valid description",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
            target_count=3,
            current_count=0,
        )
        assert quest.progress() is False  # 1/3
        assert quest.progress() is False  # 2/3
        assert quest.progress() is True   # 3/3 - complete!
        assert quest.current_count == 3


class TestSerialization:
    """Tests for to_dict() and from_dict() serialization."""

    # Spec: Serialization roundtrip (to_dict -> from_dict)
    def test_to_dict(self):
        """Test that to_dict() returns correct dictionary representation."""
        quest = Quest(
            name="Slay the Dragon",
            description="Defeat the dragon",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.KILL,
            target="Dragon",
            target_count=1,
            current_count=0,
        )
        data = quest.to_dict()
        assert data == {
            "name": "Slay the Dragon",
            "description": "Defeat the dragon",
            "status": "active",
            "objective_type": "kill",
            "target": "Dragon",
            "target_count": 1,
            "current_count": 0,
            "gold_reward": 0,
            "xp_reward": 0,
            "item_rewards": [],
            "quest_giver": None,
            "drop_item": None,
            "faction_affiliation": None,
            "faction_reward": 0,
            "faction_penalty": 0,
            "required_reputation": None,
            "required_arc_stage": None,
            "chain_id": None,
            "chain_position": 0,
            "prerequisite_quests": [],
            "unlocks_quests": [],
            "alternative_branches": [],
            "completed_branch_id": None,
            "difficulty": "normal",
            "recommended_level": 1,
            "time_limit_hours": None,
            "accepted_at": None,
            "stages": [],
            "current_stage": 0,
            "world_effects": [],
        }

    def test_from_dict(self):
        """Test that from_dict() creates correct Quest instance."""
        data = {
            "name": "Slay the Dragon",
            "description": "Defeat the dragon",
            "status": "active",
            "objective_type": "kill",
            "target": "Dragon",
            "target_count": 1,
            "current_count": 0,
        }
        quest = Quest.from_dict(data)
        assert quest.name == "Slay the Dragon"
        assert quest.description == "Defeat the dragon"
        assert quest.status == QuestStatus.ACTIVE
        assert quest.objective_type == ObjectiveType.KILL
        assert quest.target == "Dragon"
        assert quest.target_count == 1
        assert quest.current_count == 0

    def test_serialization_roundtrip(self):
        """Test that to_dict -> from_dict roundtrip preserves all data."""
        original = Quest(
            name="Collect Herbs",
            description="Gather healing herbs from the forest",
            status=QuestStatus.ACTIVE,
            objective_type=ObjectiveType.COLLECT,
            target="Healing Herb",
            target_count=5,
            current_count=2,
        )
        data = original.to_dict()
        restored = Quest.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.status == original.status
        assert restored.objective_type == original.objective_type
        assert restored.target == original.target
        assert restored.target_count == original.target_count
        assert restored.current_count == original.current_count

    def test_from_dict_with_all_statuses(self):
        """Test from_dict works with all status string values."""
        base_data = {
            "name": "Test Quest",
            "description": "Test description",
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "current_count": 0,
        }

        for status in QuestStatus:
            data = {**base_data, "status": status.value}
            quest = Quest.from_dict(data)
            assert quest.status == status

    def test_from_dict_with_all_objective_types(self):
        """Test from_dict works with all objective type string values."""
        base_data = {
            "name": "Test Quest",
            "description": "Test description",
            "status": "available",
            "target": "Target",
            "target_count": 1,
            "current_count": 0,
        }

        for obj_type in ObjectiveType:
            data = {**base_data, "objective_type": obj_type.value}
            quest = Quest.from_dict(data)
            assert quest.objective_type == obj_type


class TestQuestChainFields:
    """Tests for quest chain and prerequisite fields."""

    # Spec: New fields have safe defaults
    def test_quest_chain_fields_default_to_none_and_empty(self):
        """Test that chain fields have safe defaults."""
        quest = Quest(
            name="Simple Quest",
            description="A basic quest",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.chain_id is None
        assert quest.chain_position == 0
        assert quest.prerequisite_quests == []
        assert quest.unlocks_quests == []

    # Spec: Chain metadata set correctly
    def test_quest_with_chain_id_and_position(self):
        """Test that chain_id and chain_position are set correctly."""
        quest = Quest(
            name="Goblin War Part 1",
            description="First part of the goblin war arc",
            objective_type=ObjectiveType.KILL,
            target="Goblin Scout",
            chain_id="goblin_war",
            chain_position=1,
        )
        assert quest.chain_id == "goblin_war"
        assert quest.chain_position == 1

    # Spec: prerequisite_quests list stored correctly
    def test_quest_with_prerequisites(self):
        """Test that prerequisite_quests are stored correctly."""
        quest = Quest(
            name="Goblin War Part 2",
            description="Second part of the goblin war arc",
            objective_type=ObjectiveType.KILL,
            target="Goblin Leader",
            prerequisite_quests=["Goblin War Part 1"],
        )
        assert quest.prerequisite_quests == ["Goblin War Part 1"]

    # Spec: unlocks_quests list stored correctly
    def test_quest_with_unlocks(self):
        """Test that unlocks_quests are stored correctly."""
        quest = Quest(
            name="Goblin War Part 1",
            description="First part of the goblin war arc",
            objective_type=ObjectiveType.KILL,
            target="Goblin Scout",
            unlocks_quests=["Goblin War Part 2", "Goblin Spy Mission"],
        )
        assert quest.unlocks_quests == ["Goblin War Part 2", "Goblin Spy Mission"]

    # Spec: to_dict/from_dict preserves all chain fields
    def test_chain_fields_serialization_roundtrip(self):
        """Test that chain fields are preserved through serialization."""
        original = Quest(
            name="Goblin War Part 2",
            description="Second part of the goblin war arc",
            objective_type=ObjectiveType.KILL,
            target="Goblin Leader",
            chain_id="goblin_war",
            chain_position=2,
            prerequisite_quests=["Goblin War Part 1"],
            unlocks_quests=["Goblin War Part 3"],
        )
        data = original.to_dict()
        restored = Quest.from_dict(data)

        assert restored.chain_id == original.chain_id
        assert restored.chain_position == original.chain_position
        assert restored.prerequisite_quests == original.prerequisite_quests
        assert restored.unlocks_quests == original.unlocks_quests


class TestPrerequisiteValidation:
    """Tests for prerequisite validation logic."""

    # Spec: Always returns True when list empty
    def test_prerequisites_met_with_no_prerequisites(self):
        """Test that prerequisites_met returns True when no prerequisites."""
        quest = Quest(
            name="Simple Quest",
            description="A quest with no prerequisites",
            objective_type=ObjectiveType.KILL,
            target="Enemy",
        )
        assert quest.prerequisites_met([]) is True
        assert quest.prerequisites_met(["Some Quest"]) is True

    # Spec: Returns True when all prereqs COMPLETED
    def test_prerequisites_met_with_completed_quest(self):
        """Test that prerequisites_met returns True when prereqs are in completed list."""
        quest = Quest(
            name="Advanced Quest",
            description="A quest with prerequisites",
            objective_type=ObjectiveType.KILL,
            target="Boss",
            prerequisite_quests=["Basic Quest", "Tutorial Quest"],
        )
        completed = ["Basic Quest", "Tutorial Quest", "Other Quest"]
        assert quest.prerequisites_met(completed) is True

    # Spec: Returns False when prereq still ACTIVE (not in completed list)
    def test_prerequisites_not_met_with_active_quest(self):
        """Test that prerequisites_met returns False when prereq not completed."""
        quest = Quest(
            name="Advanced Quest",
            description="A quest with prerequisites",
            objective_type=ObjectiveType.KILL,
            target="Boss",
            prerequisite_quests=["Basic Quest", "Tutorial Quest"],
        )
        # Only one prerequisite completed
        completed = ["Basic Quest"]
        assert quest.prerequisites_met(completed) is False

    # Spec: Returns False when prereq not in player's quests
    def test_prerequisites_not_met_with_missing_quest(self):
        """Test that prerequisites_met returns False when prereq missing entirely."""
        quest = Quest(
            name="Advanced Quest",
            description="A quest with prerequisites",
            objective_type=ObjectiveType.KILL,
            target="Boss",
            prerequisite_quests=["Never Seen Quest"],
        )
        completed = ["Some Other Quest"]
        assert quest.prerequisites_met(completed) is False

    # Spec: Case-insensitive matching
    def test_prerequisites_met_case_insensitive(self):
        """Test that prerequisite matching is case-insensitive."""
        quest = Quest(
            name="Advanced Quest",
            description="A quest with prerequisites",
            objective_type=ObjectiveType.KILL,
            target="Boss",
            prerequisite_quests=["Basic Quest"],
        )
        # Different case should still match
        completed = ["basic quest"]
        assert quest.prerequisites_met(completed) is True
