"""Tests for multi-stage quest objectives.

This module tests the QuestStage dataclass and multi-stage quest functionality.
"""

import pytest
from cli_rpg.models.quest import (
    Quest,
    QuestStage,
    QuestStatus,
    ObjectiveType,
    QuestDifficulty,
)
from cli_rpg.models.character import Character


# =============================================================================
# Section 1: QuestStage Model Tests
# =============================================================================


class TestQuestStageCreation:
    """Tests for QuestStage basic creation and defaults."""

    def test_quest_stage_creation(self):
        """Test basic creation with required fields."""
        stage = QuestStage(
            name="Find the Witness",
            description="Track down the eyewitness in the village",
            objective_type=ObjectiveType.TALK,
            target="Village Elder",
        )
        assert stage.name == "Find the Witness"
        assert stage.description == "Track down the eyewitness in the village"
        assert stage.objective_type == ObjectiveType.TALK
        assert stage.target == "Village Elder"

    def test_quest_stage_defaults(self):
        """Test that target_count=1 and current_count=0 are defaults."""
        stage = QuestStage(
            name="Kill Goblins",
            description="Slay the goblins",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert stage.target_count == 1
        assert stage.current_count == 0

    def test_quest_stage_is_complete_false(self):
        """Test is_complete returns False when current < target."""
        stage = QuestStage(
            name="Kill Goblins",
            description="Slay 3 goblins",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            current_count=2,
        )
        assert stage.is_complete is False

    def test_quest_stage_is_complete_true(self):
        """Test is_complete returns True when current >= target."""
        stage = QuestStage(
            name="Kill Goblins",
            description="Slay 3 goblins",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            current_count=3,
        )
        assert stage.is_complete is True

    def test_quest_stage_is_complete_over_target(self):
        """Test is_complete returns True when current > target."""
        stage = QuestStage(
            name="Kill Goblins",
            description="Slay 3 goblins",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            current_count=5,
        )
        assert stage.is_complete is True

    def test_quest_stage_progress(self):
        """Test progress increments count and returns completion status."""
        stage = QuestStage(
            name="Kill Goblins",
            description="Slay 2 goblins",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=2,
            current_count=0,
        )
        # First progress - not complete
        result = stage.progress()
        assert result is False
        assert stage.current_count == 1

        # Second progress - now complete
        result = stage.progress()
        assert result is True
        assert stage.current_count == 2


class TestQuestStageValidation:
    """Tests for QuestStage validation."""

    def test_quest_stage_validation_empty_name(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Stage name cannot be empty"):
            QuestStage(
                name="",
                description="Some description",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
            )

    def test_quest_stage_validation_whitespace_name(self):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Stage name cannot be empty"):
            QuestStage(
                name="   ",
                description="Some description",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
            )

    def test_quest_stage_validation_empty_target(self):
        """Test that empty target raises ValueError."""
        with pytest.raises(ValueError, match="Stage target cannot be empty"):
            QuestStage(
                name="Kill Goblins",
                description="Slay them",
                objective_type=ObjectiveType.KILL,
                target="",
            )

    def test_quest_stage_validation_whitespace_target(self):
        """Test that whitespace-only target raises ValueError."""
        with pytest.raises(ValueError, match="Stage target cannot be empty"):
            QuestStage(
                name="Kill Goblins",
                description="Slay them",
                objective_type=ObjectiveType.KILL,
                target="   ",
            )

    def test_quest_stage_validation_negative_count(self):
        """Test that negative target_count raises ValueError."""
        with pytest.raises(ValueError, match="Stage target_count must be at least 1"):
            QuestStage(
                name="Kill Goblins",
                description="Slay them",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                target_count=-1,
            )

    def test_quest_stage_validation_zero_count(self):
        """Test that zero target_count raises ValueError."""
        with pytest.raises(ValueError, match="Stage target_count must be at least 1"):
            QuestStage(
                name="Kill Goblins",
                description="Slay them",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                target_count=0,
            )

    def test_quest_stage_validation_negative_current_count(self):
        """Test that negative current_count raises ValueError."""
        with pytest.raises(ValueError, match="Stage current_count must be non-negative"):
            QuestStage(
                name="Kill Goblins",
                description="Slay them",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                current_count=-1,
            )

    def test_quest_stage_name_strips_whitespace(self):
        """Test that name is stripped of leading/trailing whitespace."""
        stage = QuestStage(
            name="  Find the Key  ",
            description="Find it",
            objective_type=ObjectiveType.EXPLORE,
            target="Dark Cave",
        )
        assert stage.name == "Find the Key"

    def test_quest_stage_target_strips_whitespace(self):
        """Test that target is stripped of leading/trailing whitespace."""
        stage = QuestStage(
            name="Find the Key",
            description="Find it",
            objective_type=ObjectiveType.EXPLORE,
            target="  Dark Cave  ",
        )
        assert stage.target == "Dark Cave"


# =============================================================================
# Section 2: QuestStage Serialization Tests
# =============================================================================


class TestQuestStageSerialization:
    """Tests for QuestStage serialization and deserialization."""

    def test_quest_stage_to_dict(self):
        """Test that to_dict serializes all fields correctly."""
        stage = QuestStage(
            name="Find the Witness",
            description="Track down the eyewitness",
            objective_type=ObjectiveType.TALK,
            target="Village Elder",
            target_count=1,
            current_count=0,
        )
        data = stage.to_dict()
        assert data == {
            "name": "Find the Witness",
            "description": "Track down the eyewitness",
            "objective_type": "talk",
            "target": "Village Elder",
            "target_count": 1,
            "current_count": 0,
        }

    def test_quest_stage_from_dict(self):
        """Test that from_dict deserializes correctly."""
        data = {
            "name": "Kill the Boss",
            "description": "Defeat the final boss",
            "objective_type": "kill",
            "target": "Dragon",
            "target_count": 1,
            "current_count": 0,
        }
        stage = QuestStage.from_dict(data)
        assert stage.name == "Kill the Boss"
        assert stage.description == "Defeat the final boss"
        assert stage.objective_type == ObjectiveType.KILL
        assert stage.target == "Dragon"
        assert stage.target_count == 1
        assert stage.current_count == 0

    def test_quest_stage_from_dict_defaults(self):
        """Test from_dict handles missing optional fields with defaults."""
        data = {
            "name": "Explore Cave",
            "objective_type": "explore",
            "target": "Dark Cave",
        }
        stage = QuestStage.from_dict(data)
        assert stage.description == ""
        assert stage.target_count == 1
        assert stage.current_count == 0

    def test_quest_stage_roundtrip(self):
        """Test that to_dict and from_dict round-trip correctly."""
        original = QuestStage(
            name="Collect Herbs",
            description="Gather rare herbs",
            objective_type=ObjectiveType.COLLECT,
            target="Moonflower",
            target_count=5,
            current_count=3,
        )
        data = original.to_dict()
        restored = QuestStage.from_dict(data)
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.objective_type == original.objective_type
        assert restored.target == original.target
        assert restored.target_count == original.target_count
        assert restored.current_count == original.current_count


# =============================================================================
# Section 3: Quest with Stages Tests
# =============================================================================


class TestQuestWithStages:
    """Tests for Quest with multi-stage support."""

    def test_quest_stages_defaults_empty(self):
        """Test that new quests have empty stages list by default."""
        quest = Quest(
            name="Simple Quest",
            description="A basic quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert quest.stages == []

    def test_quest_current_stage_defaults_zero(self):
        """Test that current_stage starts at 0."""
        quest = Quest(
            name="Simple Quest",
            description="A basic quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert quest.current_stage == 0

    def test_quest_without_stages_works_normally(self):
        """Test backward compatibility - quests without stages work as before."""
        quest = Quest(
            name="Kill Goblins",
            description="Slay 3 goblins",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=3,
            status=QuestStatus.ACTIVE,
        )
        # Should be able to progress normally
        quest.progress()
        assert quest.current_count == 1
        assert quest.is_complete is False

    def test_quest_with_stages_created(self):
        """Test that quests can be created with stages."""
        stages = [
            QuestStage(
                name="Find Witness",
                description="Track down the witness",
                objective_type=ObjectiveType.TALK,
                target="Village Elder",
            ),
            QuestStage(
                name="Search Crime Scene",
                description="Investigate the scene",
                objective_type=ObjectiveType.EXPLORE,
                target="Abandoned Mill",
            ),
        ]
        quest = Quest(
            name="Murder Mystery",
            description="Solve the case",
            objective_type=ObjectiveType.TALK,
            target="Mayor",
            stages=stages,
        )
        assert len(quest.stages) == 2
        assert quest.stages[0].name == "Find Witness"
        assert quest.stages[1].name == "Search Crime Scene"

    def test_quest_get_active_stage_returns_current(self):
        """Test get_active_stage returns the current stage."""
        stages = [
            QuestStage(
                name="Stage 1",
                description="First",
                objective_type=ObjectiveType.TALK,
                target="NPC1",
            ),
            QuestStage(
                name="Stage 2",
                description="Second",
                objective_type=ObjectiveType.KILL,
                target="Enemy1",
            ),
        ]
        quest = Quest(
            name="Test Quest",
            description="Testing",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
            current_stage=0,
        )
        active = quest.get_active_stage()
        assert active is not None
        assert active.name == "Stage 1"

        quest.current_stage = 1
        active = quest.get_active_stage()
        assert active is not None
        assert active.name == "Stage 2"

    def test_quest_get_active_stage_returns_none_when_no_stages(self):
        """Test get_active_stage returns None when quest has no stages."""
        quest = Quest(
            name="Simple Quest",
            description="No stages",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert quest.get_active_stage() is None

    def test_quest_get_active_stage_returns_none_when_past_stages(self):
        """Test get_active_stage returns None when current_stage >= len(stages)."""
        stages = [
            QuestStage(
                name="Only Stage",
                description="The only one",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Test Quest",
            description="Testing",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            current_stage=1,  # Past the only stage
        )
        assert quest.get_active_stage() is None

    def test_quest_get_active_objective_uses_stage(self):
        """Test get_active_objective returns stage objective when stages exist."""
        stages = [
            QuestStage(
                name="Find Clue",
                description="Look for clues",
                objective_type=ObjectiveType.EXPLORE,
                target="Crime Scene",
                target_count=1,
                current_count=0,
            ),
        ]
        quest = Quest(
            name="Mystery",
            description="Solve it",
            objective_type=ObjectiveType.TALK,  # Root objective differs
            target="Mayor",
            target_count=1,
            stages=stages,
        )
        obj_type, target, target_count, current_count = quest.get_active_objective()
        assert obj_type == ObjectiveType.EXPLORE
        assert target == "Crime Scene"
        assert target_count == 1
        assert current_count == 0

    def test_quest_get_active_objective_uses_root_when_no_stages(self):
        """Test get_active_objective uses root fields when no stages."""
        quest = Quest(
            name="Simple Quest",
            description="Basic quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=5,
            current_count=2,
        )
        obj_type, target, target_count, current_count = quest.get_active_objective()
        assert obj_type == ObjectiveType.KILL
        assert target == "Goblin"
        assert target_count == 5
        assert current_count == 2


# =============================================================================
# Section 4: Stage Progression Tests
# =============================================================================


class TestStageProgression:
    """Tests for stage advancement mechanics."""

    def test_advance_stage_moves_to_next(self):
        """Test that advance_stage increments current_stage."""
        stages = [
            QuestStage(
                name="Stage 1",
                description="First",
                objective_type=ObjectiveType.TALK,
                target="NPC1",
            ),
            QuestStage(
                name="Stage 2",
                description="Second",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Multi-stage",
            description="Test",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
            current_stage=0,
        )
        quest_complete = quest.advance_stage()
        assert quest_complete is False
        assert quest.current_stage == 1

    def test_final_stage_completion_returns_true(self):
        """Test advance_stage returns True when all stages complete."""
        stages = [
            QuestStage(
                name="Only Stage",
                description="The only one",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Short Quest",
            description="Quick",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            current_stage=0,
        )
        quest_complete = quest.advance_stage()
        assert quest_complete is True
        assert quest.current_stage == 1

    def test_advance_stage_returns_false_when_no_stages(self):
        """Test advance_stage returns False for stageless quests."""
        quest = Quest(
            name="Simple Quest",
            description="No stages",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        result = quest.advance_stage()
        assert result is False
        assert quest.current_stage == 0


# =============================================================================
# Section 5: Character Progress Recording Tests
# =============================================================================


class TestCharacterStageProgress:
    """Tests for Character recording progress on staged quests."""

    def _create_character(self) -> Character:
        """Create a test character."""
        return Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )

    def test_record_kill_progresses_active_stage(self):
        """Test that record_kill updates the current stage for staged quests."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Kill Goblins",
                description="Slay goblins",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                target_count=2,
            ),
            QuestStage(
                name="Kill Boss",
                description="Defeat the boss",
                objective_type=ObjectiveType.KILL,
                target="Goblin King",
            ),
        ]
        quest = Quest(
            name="Goblin Hunt",
            description="Hunt goblins",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        # First kill - progress stage
        messages = char.record_kill("Goblin")
        assert quest.stages[0].current_count == 1
        assert quest.current_stage == 0  # Still on stage 1
        assert any("Quest progress" in m for m in messages)

    def test_record_kill_advances_stage_on_completion(self):
        """Test record_kill advances to next stage when stage completes."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Kill Goblin",
                description="Slay goblin",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
                target_count=1,
            ),
            QuestStage(
                name="Kill Boss",
                description="Defeat boss",
                objective_type=ObjectiveType.KILL,
                target="Goblin King",
            ),
        ]
        quest = Quest(
            name="Goblin Hunt",
            description="Hunt goblins",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_kill("Goblin")
        assert quest.current_stage == 1
        assert any("Stage complete" in m for m in messages)
        assert any("Next:" in m for m in messages)

    def test_record_talk_progresses_active_stage(self):
        """Test that record_talk updates the current stage."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Talk to Elder",
                description="Speak with elder",
                objective_type=ObjectiveType.TALK,
                target="Village Elder",
            ),
        ]
        quest = Quest(
            name="Village Quest",
            description="Help village",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_talk("Village Elder")
        assert quest.stages[0].current_count == 1
        assert quest.status == QuestStatus.READY_TO_TURN_IN

    def test_record_explore_progresses_active_stage(self):
        """Test that record_explore updates the current stage."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Explore Cave",
                description="Investigate",
                objective_type=ObjectiveType.EXPLORE,
                target="Dark Cave",
            ),
        ]
        quest = Quest(
            name="Exploration",
            description="Explore",
            objective_type=ObjectiveType.EXPLORE,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_explore("Dark Cave")
        assert quest.stages[0].current_count == 1
        assert quest.status == QuestStatus.READY_TO_TURN_IN

    def test_record_kill_ignores_wrong_stage_target(self):
        """Test that killing wrong target doesn't progress stage."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Kill Goblin",
                description="Kill goblin",
                objective_type=ObjectiveType.KILL,
                target="Goblin",
            ),
        ]
        quest = Quest(
            name="Hunt",
            description="Hunt",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_kill("Orc")  # Wrong target
        assert quest.stages[0].current_count == 0
        assert quest.current_stage == 0
        assert len(messages) == 0

    def test_record_kill_ignores_wrong_objective_type(self):
        """Test that action matching wrong objective type doesn't progress."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Talk to Elder",
                description="Talk",
                objective_type=ObjectiveType.TALK,
                target="Elder",
            ),
        ]
        quest = Quest(
            name="Chat Quest",
            description="Chat",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_kill("Elder")  # Wrong action type
        assert quest.stages[0].current_count == 0
        assert len(messages) == 0

    def test_final_stage_completion_marks_quest_ready(self):
        """Test completing final stage marks quest as READY_TO_TURN_IN."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Final Stage",
                description="The end",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Boss Fight",
            description="Beat boss",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_kill("Boss")
        assert quest.status == QuestStatus.READY_TO_TURN_IN
        assert any("complete" in m.lower() for m in messages)

    def test_middle_stage_completion_keeps_active(self):
        """Test completing middle stage keeps quest ACTIVE."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Stage 1",
                description="First",
                objective_type=ObjectiveType.KILL,
                target="Minion",
            ),
            QuestStage(
                name="Stage 2",
                description="Second",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Two Stage Quest",
            description="Do both",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        char.record_kill("Minion")
        assert quest.status == QuestStatus.ACTIVE
        assert quest.current_stage == 1

    def test_stage_progress_message_includes_stage_name(self):
        """Test that progress messages mention the stage name."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Find the Hidden Key",
                description="Search carefully",
                objective_type=ObjectiveType.KILL,
                target="Guardian",
                target_count=2,
            ),
        ]
        quest = Quest(
            name="Key Quest",
            description="Find key",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        messages = char.record_kill("Guardian")
        # Progress message should include quest name
        assert any("Key Quest" in m for m in messages)

    def test_record_collection_progresses_stage(self):
        """Test record_collection progresses staged quest."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Collect Herbs",
                description="Gather herbs",
                objective_type=ObjectiveType.COLLECT,
                target="Moonflower",
                target_count=3,
            ),
        ]
        quest = Quest(
            name="Herb Gathering",
            description="Gather",
            objective_type=ObjectiveType.COLLECT,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        char.record_collection("Moonflower")
        assert quest.stages[0].current_count == 1

    def test_record_use_progresses_stage(self):
        """Test record_use progresses staged quest."""
        char = self._create_character()
        stages = [
            QuestStage(
                name="Use the Potion",
                description="Drink it",
                objective_type=ObjectiveType.USE,
                target="Magic Potion",
            ),
        ]
        quest = Quest(
            name="Potion Quest",
            description="Use potion",
            objective_type=ObjectiveType.USE,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        char.record_use("Magic Potion")
        assert quest.stages[0].current_count == 1
        assert quest.status == QuestStatus.READY_TO_TURN_IN


# =============================================================================
# Section 6: Quest Serialization with Stages Tests
# =============================================================================


class TestQuestSerializationWithStages:
    """Tests for Quest serialization including stages."""

    def test_quest_to_dict_includes_stages(self):
        """Test that to_dict serializes stages."""
        stages = [
            QuestStage(
                name="Stage 1",
                description="First",
                objective_type=ObjectiveType.TALK,
                target="NPC",
            ),
        ]
        quest = Quest(
            name="Test Quest",
            description="Testing",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
        )
        data = quest.to_dict()
        assert "stages" in data
        assert len(data["stages"]) == 1
        assert data["stages"][0]["name"] == "Stage 1"

    def test_quest_to_dict_includes_current_stage(self):
        """Test that to_dict serializes current_stage."""
        stages = [
            QuestStage(
                name="Stage 1",
                description="First",
                objective_type=ObjectiveType.TALK,
                target="NPC",
            ),
            QuestStage(
                name="Stage 2",
                description="Second",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Test Quest",
            description="Testing",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
            current_stage=1,
        )
        data = quest.to_dict()
        assert "current_stage" in data
        assert data["current_stage"] == 1

    def test_quest_from_dict_restores_stages(self):
        """Test that from_dict deserializes stages."""
        data = {
            "name": "Test Quest",
            "description": "Testing",
            "status": "active",
            "objective_type": "talk",
            "target": "Fallback",
            "stages": [
                {
                    "name": "Stage 1",
                    "description": "First",
                    "objective_type": "talk",
                    "target": "NPC",
                    "target_count": 1,
                    "current_count": 0,
                }
            ],
            "current_stage": 0,
        }
        quest = Quest.from_dict(data)
        assert len(quest.stages) == 1
        assert quest.stages[0].name == "Stage 1"
        assert quest.current_stage == 0

    def test_quest_from_dict_handles_missing_stages(self):
        """Test backward compatibility - missing stages defaults to empty list."""
        data = {
            "name": "Old Quest",
            "description": "From before stages",
            "status": "active",
            "objective_type": "kill",
            "target": "Goblin",
        }
        quest = Quest.from_dict(data)
        assert quest.stages == []
        assert quest.current_stage == 0

    def test_quest_roundtrip_with_stages(self):
        """Test full round-trip serialization with stages."""
        stages = [
            QuestStage(
                name="Find Clue",
                description="Investigate",
                objective_type=ObjectiveType.EXPLORE,
                target="Crime Scene",
                target_count=1,
                current_count=1,
            ),
            QuestStage(
                name="Confront Suspect",
                description="Face them",
                objective_type=ObjectiveType.TALK,
                target="Shady Character",
                target_count=1,
                current_count=0,
            ),
        ]
        original = Quest(
            name="Mystery",
            description="Solve it",
            objective_type=ObjectiveType.TALK,
            target="Mayor",
            stages=stages,
            current_stage=1,
            status=QuestStatus.ACTIVE,
        )
        data = original.to_dict()
        restored = Quest.from_dict(data)

        assert len(restored.stages) == 2
        assert restored.stages[0].name == "Find Clue"
        assert restored.stages[0].current_count == 1
        assert restored.stages[1].name == "Confront Suspect"
        assert restored.current_stage == 1


# =============================================================================
# Section 7: Integration Tests
# =============================================================================


class TestQuestStageIntegration:
    """Integration tests for quest stage mechanics."""

    def test_full_multi_stage_quest_completion(self):
        """Test completing a full multi-stage quest from start to finish."""
        char = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        stages = [
            QuestStage(
                name="Find Witness",
                description="Track down witness",
                objective_type=ObjectiveType.TALK,
                target="Witness",
            ),
            QuestStage(
                name="Investigate Scene",
                description="Search the area",
                objective_type=ObjectiveType.EXPLORE,
                target="Crime Scene",
            ),
            QuestStage(
                name="Confront Culprit",
                description="Face the criminal",
                objective_type=ObjectiveType.KILL,
                target="Criminal",
            ),
        ]
        quest = Quest(
            name="Murder Mystery",
            description="Solve the case",
            objective_type=ObjectiveType.TALK,
            target="Mayor",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        # Complete stage 1
        char.record_talk("Witness")
        assert quest.current_stage == 1
        assert quest.status == QuestStatus.ACTIVE

        # Complete stage 2
        char.record_explore("Crime Scene")
        assert quest.current_stage == 2
        assert quest.status == QuestStatus.ACTIVE

        # Complete stage 3 (final)
        char.record_kill("Criminal")
        assert quest.current_stage == 3
        assert quest.status == QuestStatus.READY_TO_TURN_IN

    def test_staged_quest_with_target_counts(self):
        """Test stage with target_count > 1."""
        char = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        stages = [
            QuestStage(
                name="Kill Minions",
                description="Slay 3 minions",
                objective_type=ObjectiveType.KILL,
                target="Minion",
                target_count=3,
            ),
            QuestStage(
                name="Kill Boss",
                description="Slay the boss",
                objective_type=ObjectiveType.KILL,
                target="Boss",
            ),
        ]
        quest = Quest(
            name="Dungeon Clear",
            description="Clear dungeon",
            objective_type=ObjectiveType.KILL,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        # Kill 3 minions
        char.record_kill("Minion")
        assert quest.stages[0].current_count == 1
        assert quest.current_stage == 0

        char.record_kill("Minion")
        assert quest.stages[0].current_count == 2
        assert quest.current_stage == 0

        char.record_kill("Minion")
        assert quest.stages[0].current_count == 3
        assert quest.current_stage == 1  # Advanced

        # Kill boss
        char.record_kill("Boss")
        assert quest.status == QuestStatus.READY_TO_TURN_IN

    def test_case_insensitive_target_matching(self):
        """Test that target matching is case-insensitive."""
        char = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        stages = [
            QuestStage(
                name="Talk to Elder",
                description="Speak",
                objective_type=ObjectiveType.TALK,
                target="Village Elder",
            ),
        ]
        quest = Quest(
            name="Chat",
            description="Chat",
            objective_type=ObjectiveType.TALK,
            target="Fallback",
            stages=stages,
            status=QuestStatus.ACTIVE,
        )
        char.quests.append(quest)

        # Use different case
        char.record_talk("VILLAGE ELDER")
        assert quest.stages[0].current_count == 1
        assert quest.status == QuestStatus.READY_TO_TURN_IN
