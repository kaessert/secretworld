"""Tests for multiple NPCs per location feature.

Spec tests:
- talk with no args at single-NPC location auto-starts conversation
- talk with no args at multi-NPC location lists available NPCs
- talk <name> at multi-NPC location selects specific NPC
"""
import pytest
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character


class TestTalkCommandMultipleNPCs:
    """Test talk command with multiple NPCs."""

    def test_talk_no_args_single_npc_auto_starts(self):
        """talk with no args at single-NPC location starts conversation directly.

        Spec: When `talk` is called with no arguments at a location with 1 NPC,
        auto-start conversation.
        """
        npc = NPC(name="Merchant", description="Sells goods", dialogue="Welcome!")
        location = Location(
            name="Town Square",
            description="A busy square.",
            npcs=[npc],
            coordinates=(0, 0)
        )
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town Square": location}, "Town Square")

        from cli_rpg.main import handle_exploration_command
        _, msg = handle_exploration_command(game_state, "talk", [])
        assert "Welcome!" in msg
        assert game_state.current_npc == npc

    def test_talk_no_args_multiple_npcs_lists_all(self):
        """talk with no args at multi-NPC location lists available NPCs.

        Spec: When `talk` is called with no arguments at a location with 2+ NPCs,
        list available NPCs.
        """
        npc1 = NPC(name="Merchant", description="Sells goods", dialogue="Hello!")
        npc2 = NPC(name="Guard", description="Watches gate", dialogue="Move along.")
        location = Location(
            name="Town Square",
            description="A busy square.",
            npcs=[npc1, npc2],
            coordinates=(0, 0)
        )
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town Square": location}, "Town Square")

        from cli_rpg.main import handle_exploration_command
        _, msg = handle_exploration_command(game_state, "talk", [])
        assert "Merchant" in msg
        assert "Guard" in msg
        assert game_state.current_npc is None  # No conversation started

    def test_talk_with_name_selects_specific_npc(self):
        """talk <name> talks to the named NPC among multiple.

        Spec: Users can still specify NPC name to talk to specific NPC.
        """
        npc1 = NPC(name="Merchant", description="Sells goods", dialogue="Buy something!")
        npc2 = NPC(name="Guard", description="Watches gate", dialogue="Move along.")
        location = Location(
            name="Town Square",
            description="A busy square.",
            npcs=[npc1, npc2],
            coordinates=(0, 0)
        )
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town Square": location}, "Town Square")

        from cli_rpg.main import handle_exploration_command
        _, msg = handle_exploration_command(game_state, "talk", ["Guard"])
        assert "Move along." in msg
        assert game_state.current_npc == npc2
