"""Tests for quest prerequisites based on NPC arc stage."""

import pytest

from cli_rpg.models.quest import Quest, ObjectiveType, QuestStatus
from cli_rpg.models.npc_arc import NPCArc, NPCArcStage


class TestNpcArcQuestsHelper:
    """Tests for npc_arc_quests helper functions."""

    def test_arc_stage_order_contains_all_stages(self):
        """ARC_STAGE_ORDER should contain all stages in correct order."""
        from cli_rpg.npc_arc_quests import ARC_STAGE_ORDER

        # Verify order from lowest to highest trust
        expected = ["enemy", "hostile", "wary", "stranger", "acquaintance", "trusted", "devoted"]
        assert ARC_STAGE_ORDER == expected

    def test_get_arc_stage_index_returns_correct_indices(self):
        """get_arc_stage_index should return correct index for each stage."""
        from cli_rpg.npc_arc_quests import get_arc_stage_index

        assert get_arc_stage_index("enemy") == 0
        assert get_arc_stage_index("hostile") == 1
        assert get_arc_stage_index("wary") == 2
        assert get_arc_stage_index("stranger") == 3
        assert get_arc_stage_index("acquaintance") == 4
        assert get_arc_stage_index("trusted") == 5
        assert get_arc_stage_index("devoted") == 6

    def test_get_arc_stage_index_case_insensitive(self):
        """get_arc_stage_index should be case insensitive."""
        from cli_rpg.npc_arc_quests import get_arc_stage_index

        assert get_arc_stage_index("STRANGER") == 3
        assert get_arc_stage_index("Trusted") == 5

    def test_get_arc_stage_index_unknown_returns_stranger(self):
        """Unknown stage should return stranger index as fallback."""
        from cli_rpg.npc_arc_quests import get_arc_stage_index

        assert get_arc_stage_index("unknown") == 3  # stranger index


class TestCheckArcStageRequirement:
    """Tests for check_arc_stage_requirement function."""

    def test_quest_no_arc_requirement_always_available(self):
        """Quest with no required_arc_stage should always pass."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        arc = NPCArc(arc_points=0)  # stranger
        allowed, reason = check_arc_stage_requirement(arc, None)
        assert allowed is True
        assert reason is None

    def test_quest_requires_stranger_accepts_stranger(self):
        """Stranger arc should pass stranger requirement."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        arc = NPCArc(arc_points=0)  # stranger
        allowed, reason = check_arc_stage_requirement(arc, "stranger")
        assert allowed is True
        assert reason is None

    def test_quest_requires_trusted_rejects_stranger(self):
        """Stranger arc should fail trusted requirement."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        arc = NPCArc(arc_points=0)  # stranger
        allowed, reason = check_arc_stage_requirement(arc, "trusted")
        assert allowed is False
        assert "trusted" in reason.lower()

    def test_quest_requires_trusted_accepts_trusted(self):
        """Trusted arc should pass trusted requirement."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        arc = NPCArc(arc_points=55)  # trusted (50-74)
        allowed, reason = check_arc_stage_requirement(arc, "trusted")
        assert allowed is True
        assert reason is None

    def test_quest_requires_acquaintance_accepts_higher(self):
        """Trusted arc should pass acquaintance requirement (higher stage)."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        arc = NPCArc(arc_points=55)  # trusted
        allowed, reason = check_arc_stage_requirement(arc, "acquaintance")
        assert allowed is True
        assert reason is None

    def test_quest_requires_devoted_rejects_trusted(self):
        """Trusted arc should fail devoted requirement."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        arc = NPCArc(arc_points=55)  # trusted
        allowed, reason = check_arc_stage_requirement(arc, "devoted")
        assert allowed is False
        assert "devoted" in reason.lower()

    def test_npc_no_arc_treated_as_stranger(self):
        """NPC with no arc (None) should be treated as STRANGER."""
        from cli_rpg.npc_arc_quests import check_arc_stage_requirement

        # None arc should pass stranger requirement
        allowed, reason = check_arc_stage_requirement(None, "stranger")
        assert allowed is True
        assert reason is None

        # None arc should fail trusted requirement
        allowed, reason = check_arc_stage_requirement(None, "trusted")
        assert allowed is False
        assert "trusted" in reason.lower()


class TestQuestModelArcRequirement:
    """Tests for required_arc_stage field on Quest model."""

    def test_quest_serialization_with_required_arc_stage(self):
        """to_dict should include required_arc_stage field."""
        quest = Quest(
            name="Test Quest",
            description="A test quest requiring trust",
            objective_type=ObjectiveType.TALK,
            target="Elder",
            required_arc_stage="trusted",
        )
        data = quest.to_dict()
        assert data["required_arc_stage"] == "trusted"

    def test_quest_deserialization_with_required_arc_stage(self):
        """from_dict should parse required_arc_stage field."""
        data = {
            "name": "Test Quest",
            "description": "A test quest requiring trust",
            "objective_type": "talk",
            "target": "Elder",
            "status": "available",
            "required_arc_stage": "devoted",
        }
        quest = Quest.from_dict(data)
        assert quest.required_arc_stage == "devoted"

    def test_quest_deserialization_without_required_arc_stage(self):
        """from_dict should default required_arc_stage to None."""
        data = {
            "name": "Test Quest",
            "description": "A test quest",
            "objective_type": "talk",
            "target": "Elder",
            "status": "available",
        }
        quest = Quest.from_dict(data)
        assert quest.required_arc_stage is None

    def test_quest_default_required_arc_stage_is_none(self):
        """New Quest should have required_arc_stage=None by default."""
        quest = Quest(
            name="Basic Quest",
            description="A basic quest",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
        )
        assert quest.required_arc_stage is None


def create_test_game_state():
    """Create a minimal game state for testing."""
    from cli_rpg.game_state import GameState
    from cli_rpg.models.character import Character, CharacterClass
    from cli_rpg.models.location import Location

    character = Character(
        name="TestHero",
        strength=10,
        dexterity=10,
        intelligence=10,
        charisma=10,
        perception=10,
        character_class=CharacterClass.WARRIOR,
    )
    location = Location(name="Town Square", description="A test location")
    world = {"Town Square": location}
    return GameState(character=character, world=world, starting_location="Town Square")


class TestAcceptCommandArcRequirement:
    """Integration tests for accept command with arc requirements."""

    def test_accept_command_rejects_insufficient_arc(self):
        """Accept command should reject quest when arc stage is insufficient."""
        from cli_rpg.models.npc import NPC
        from cli_rpg.models.npc_arc import NPCArc

        # Create game state
        game_state = create_test_game_state()

        # Create NPC with arc as STRANGER
        npc = NPC(name="Elder", description="A wise elder", dialogue="Hello traveler.")
        npc.is_quest_giver = True
        npc.arc = NPCArc(arc_points=0)  # stranger

        # Create quest requiring TRUSTED
        quest = Quest(
            name="Secret Task",
            description="A task for trusted allies only",
            objective_type=ObjectiveType.TALK,
            target="Merchant",
            required_arc_stage="trusted",
        )
        npc.offered_quests = [quest]
        game_state.current_npc = npc

        # Try to accept the quest
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "accept", ["Secret Task"])

        assert success is True  # Command processed successfully
        assert "trust" in message.lower() or "trusted" in message.lower()
        # Quest should NOT be added
        assert not game_state.current_character.has_quest("Secret Task")

    def test_accept_command_accepts_sufficient_arc(self):
        """Accept command should accept quest when arc stage is sufficient."""
        from cli_rpg.models.npc import NPC
        from cli_rpg.models.npc_arc import NPCArc

        # Create game state
        game_state = create_test_game_state()

        # Create NPC with arc as TRUSTED
        npc = NPC(name="Elder", description="A wise elder", dialogue="Hello traveler.")
        npc.is_quest_giver = True
        npc.arc = NPCArc(arc_points=55)  # trusted

        # Create quest requiring TRUSTED
        quest = Quest(
            name="Secret Task",
            description="A task for trusted allies",
            objective_type=ObjectiveType.TALK,
            target="Merchant",
            required_arc_stage="trusted",
        )
        npc.offered_quests = [quest]
        game_state.current_npc = npc

        # Accept the quest
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "accept", ["Secret Task"])

        assert success is True
        assert "accepted" in message.lower()
        # Quest should be added
        assert game_state.current_character.has_quest("Secret Task")

    def test_accept_command_accepts_quest_without_arc_requirement(self):
        """Accept command should accept quest without required_arc_stage."""
        from cli_rpg.models.npc import NPC
        from cli_rpg.models.npc_arc import NPCArc

        # Create game state
        game_state = create_test_game_state()

        # Create NPC (arc doesn't matter for quest without requirement)
        npc = NPC(name="Elder", description="A wise elder", dialogue="Hello traveler.")
        npc.is_quest_giver = True
        npc.arc = NPCArc(arc_points=0)  # stranger

        # Create quest without arc requirement
        quest = Quest(
            name="Simple Task",
            description="A simple task for anyone",
            objective_type=ObjectiveType.TALK,
            target="Merchant",
            # No required_arc_stage set
        )
        npc.offered_quests = [quest]
        game_state.current_npc = npc

        # Accept the quest
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "accept", ["Simple Task"])

        assert success is True
        assert "accepted" in message.lower()
        assert game_state.current_character.has_quest("Simple Task")

    def test_accept_command_npc_without_arc_treated_as_stranger(self):
        """Accept command should treat NPC without arc as STRANGER."""
        from cli_rpg.models.npc import NPC

        # Create game state
        game_state = create_test_game_state()

        # Create NPC without arc (None)
        npc = NPC(name="Elder", description="A wise elder", dialogue="Hello traveler.")
        npc.is_quest_giver = True
        npc.arc = None  # No arc - treated as stranger

        # Create quest requiring ACQUAINTANCE
        quest = Quest(
            name="Acquaintance Task",
            description="A task for acquaintances",
            objective_type=ObjectiveType.TALK,
            target="Merchant",
            required_arc_stage="acquaintance",
        )
        npc.offered_quests = [quest]
        game_state.current_npc = npc

        # Try to accept the quest
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "accept", ["Acquaintance Task"])

        assert success is True
        # Should be rejected - stranger < acquaintance
        assert "trust" in message.lower() or "acquaintance" in message.lower()
        assert not game_state.current_character.has_quest("Acquaintance Task")
