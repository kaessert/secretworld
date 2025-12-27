"""Integration tests for faction-based content gating.

Tests the integration of faction_content module with main.py (talk command)
and game_state.py (enter command).
"""

import pytest

from cli_rpg.game_state import GameState
from cli_rpg.models.faction import Faction
from cli_rpg.models.npc import NPC
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.game_time import GameTime
from cli_rpg.world_grid import SubGrid


def create_test_game_state_with_factions():
    """Create a minimal GameState for testing faction content."""
    # Create character
    character = Character(
        name="Test Hero",
        character_class=CharacterClass.WARRIOR,
        strength=10,
        dexterity=10,
        intelligence=10,
    )

    # Create initial location (required by GameState constructor)
    initial_location = Location(
        name="Town Square",
        description="The central square of the town",
        coordinates=(0, 0),
    )
    world = {"Town Square": initial_location}

    # Create game state with correct constructor arguments
    game_state = GameState(
        character=character,
        world=world,
        starting_location="Town Square",
        theme="fantasy",
    )

    return game_state


class TestTalkCommandFactionGating:
    """Test faction gating integration in the talk command."""

    def test_talk_command_blocked_by_npc_faction_requirement(self):
        """Spec: Talk command is blocked when player doesn't meet NPC's faction requirement."""
        game_state = create_test_game_state_with_factions()

        # Create an NPC with faction requirement
        npc = NPC(
            name="Guild Master",
            description="The head of the merchant guild",
            dialogue="Welcome!",
            faction="Merchant Guild",
            required_reputation=60,  # Requires FRIENDLY standing
        )

        # Create location with the NPC
        location = Location(
            name="Town Square",
            description="The central square",
            npcs=[npc],
            coordinates=(0, 0),
        )
        game_state.world = {"Town Square": location}

        # Set player's faction standing to be too low
        game_state.factions = [
            Faction(name="Merchant Guild", description="Traders", reputation=40)  # NEUTRAL
        ]

        # Import and call handle_exploration_command
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "talk", ["Guild", "Master"])

        # Should be blocked
        assert "refuses to speak" in message.lower() or "reputation" in message.lower()

    def test_talk_command_allowed_when_reputation_met(self):
        """Spec: Talk command is allowed when player meets NPC's faction requirement."""
        game_state = create_test_game_state_with_factions()

        # Create an NPC with faction requirement
        npc = NPC(
            name="Guild Master",
            description="The head of the merchant guild",
            dialogue="Welcome, friend!",
            faction="Merchant Guild",
            required_reputation=60,  # Requires FRIENDLY standing
        )

        # Create location with the NPC
        location = Location(
            name="Town Square",
            description="The central square",
            npcs=[npc],
            coordinates=(0, 0),
        )
        game_state.world = {"Town Square": location}

        # Set player's faction standing to be sufficient
        game_state.factions = [
            Faction(name="Merchant Guild", description="Traders", reputation=70)  # FRIENDLY
        ]

        # Import and call handle_exploration_command
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "talk", ["Guild", "Master"])

        # Should not be blocked - should contain greeting
        assert "Guild Master" in message
        assert "refuses" not in message.lower()

    def test_talk_command_blocked_by_hostile_faction(self):
        """Spec: Talk command is blocked when NPC's faction is hostile to player."""
        game_state = create_test_game_state_with_factions()

        # Create an NPC with faction (no required_reputation needed)
        npc = NPC(
            name="Faction Guard",
            description="A guard loyal to the faction",
            dialogue="Get lost!",
            faction="Enemy Faction",
        )

        # Create location with the NPC
        location = Location(
            name="Town Square",
            description="The central square",
            npcs=[npc],
            coordinates=(0, 0),
        )
        game_state.world = {"Town Square": location}

        # Set player's faction standing to HOSTILE
        game_state.factions = [
            Faction(name="Enemy Faction", description="Enemies", reputation=10)  # HOSTILE
        ]

        # Import and call handle_exploration_command
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "talk", ["Faction", "Guard"])

        # Should be blocked
        assert "refuses" in message.lower() or "hostile" in message.lower()

    def test_talk_command_shows_friendly_faction_greeting(self):
        """Spec: Talk command shows warm greeting when player has FRIENDLY standing."""
        game_state = create_test_game_state_with_factions()

        # Create an NPC with faction
        npc = NPC(
            name="Guild Friend",
            description="A friendly merchant",
            dialogue="Default greeting",
            faction="Merchant Guild",
        )

        # Create location with the NPC
        location = Location(
            name="Town Square",
            description="The central square",
            npcs=[npc],
            coordinates=(0, 0),
        )
        game_state.world = {"Town Square": location}

        # Set player's faction standing to FRIENDLY
        game_state.factions = [
            Faction(name="Merchant Guild", description="Traders", reputation=70)  # FRIENDLY
        ]

        # Import and call handle_exploration_command
        from cli_rpg.main import handle_exploration_command

        success, message = handle_exploration_command(game_state, "talk", ["Guild", "Friend"])

        # Should show friendly greeting
        assert "friend" in message.lower() or "welcome" in message.lower()


class TestEnterCommandFactionGating:
    """Test faction gating integration in the enter command."""

    def test_enter_command_blocked_by_location_faction_requirement(self):
        """Spec: Enter command is blocked when player doesn't meet location's faction requirement."""
        game_state = create_test_game_state_with_factions()

        # Create sub-location with faction requirement (coordinates set by add_location)
        inner_sanctum = Location(
            name="Inner Sanctum",
            description="The private chambers",
            is_exit_point=True,
            required_faction="Merchant Guild",
            required_reputation=80,  # Requires HONORED standing
        )

        # Create SubGrid with the restricted location
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0))
        sub_grid.add_location(inner_sanctum, 0, 0, 0)

        # Create overworld location with sub_grid
        guild_hall = Location(
            name="Guild Hall",
            description="The merchant guild's headquarters",
            coordinates=(0, 0),
            is_overworld=True,
            sub_grid=sub_grid,
            entry_point="Inner Sanctum",
        )
        game_state.world = {"Guild Hall": guild_hall}
        game_state.current_location = "Guild Hall"

        # Set player's faction standing to be too low
        game_state.factions = [
            Faction(name="Merchant Guild", description="Traders", reputation=60)  # FRIENDLY
        ]

        # Try to enter
        success, message = game_state.enter("Inner Sanctum")

        # Should be blocked
        assert not success
        assert "Merchant Guild" in message
        assert "standing" in message.lower() or "enter" in message.lower()

    def test_enter_command_allowed_when_reputation_met(self):
        """Spec: Enter command is allowed when player meets location's faction requirement."""
        game_state = create_test_game_state_with_factions()

        # Create sub-location with faction requirement (coordinates set by add_location)
        inner_sanctum = Location(
            name="Inner Sanctum",
            description="The private chambers",
            is_exit_point=True,
            required_faction="Merchant Guild",
            required_reputation=80,  # Requires HONORED standing
        )

        # Create SubGrid with the restricted location
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0))
        sub_grid.add_location(inner_sanctum, 0, 0, 0)

        # Create overworld location with sub_grid
        guild_hall = Location(
            name="Guild Hall",
            description="The merchant guild's headquarters",
            coordinates=(0, 0),
            is_overworld=True,
            sub_grid=sub_grid,
            entry_point="Inner Sanctum",
        )
        game_state.world = {"Guild Hall": guild_hall}
        game_state.current_location = "Guild Hall"

        # Set player's faction standing to be sufficient
        game_state.factions = [
            Faction(name="Merchant Guild", description="Traders", reputation=90)  # HONORED
        ]

        # Try to enter
        success, message = game_state.enter("Inner Sanctum")

        # Should succeed
        assert success
        assert "Inner Sanctum" in message

    def test_enter_command_allowed_when_no_faction_requirement(self):
        """Spec: Enter command is allowed when location has no faction requirement."""
        game_state = create_test_game_state_with_factions()

        # Create sub-location without faction requirement (coordinates set by add_location)
        common_room = Location(
            name="Common Room",
            description="A public gathering area",
            is_exit_point=True,
            # No required_faction or required_reputation
        )

        # Create SubGrid
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0))
        sub_grid.add_location(common_room, 0, 0, 0)

        # Create overworld location
        tavern = Location(
            name="Tavern",
            description="A cozy tavern",
            coordinates=(0, 0),
            is_overworld=True,
            sub_grid=sub_grid,
            entry_point="Common Room",
        )
        game_state.world = {"Tavern": tavern}
        game_state.current_location = "Tavern"

        # No factions needed
        game_state.factions = []

        # Try to enter
        success, message = game_state.enter("Common Room")

        # Should succeed
        assert success
        assert "Common Room" in message


class TestLocationDisplayFactionFiltering:
    """Test that location display respects faction-based NPC visibility."""

    def test_location_display_hides_gated_npcs(self):
        """Spec: Location display should hide NPCs the player can't access due to faction."""
        # This test verifies the filter_visible_npcs function works correctly
        # The actual integration with get_layered_description is optional per the plan
        from cli_rpg.faction_content import filter_visible_npcs

        npcs = [
            NPC(
                name="Guild Master",
                description="The leader",
                dialogue="Welcome!",
                faction="Merchant Guild",
                required_reputation=80,  # High requirement
            ),
            NPC(
                name="Common Clerk",
                description="A clerk",
                dialogue="Hello!",
                # No faction requirement
            ),
        ]

        factions = [
            Faction(name="Merchant Guild", description="Traders", reputation=50)  # NEUTRAL
        ]

        visible = filter_visible_npcs(npcs, factions)

        # Guild Master should be hidden, Common Clerk should be visible
        assert len(visible) == 1
        assert visible[0].name == "Common Clerk"
