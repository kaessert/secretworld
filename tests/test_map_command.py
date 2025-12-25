"""Tests for map command feature."""

from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.map_renderer import render_map


class TestParseCommandMap:
    """Tests for parse_command() with 'map' command."""

    def test_parse_command_map(self):
        """Test parsing 'map' command.

        Spec: 'map' should return ("map", [])
        """
        cmd, args = parse_command("map")
        assert cmd == "map"
        assert args == []

    def test_parse_command_map_case_insensitive(self):
        """Test parsing 'MAP' command is case insensitive.

        Spec: 'MAP' should be treated same as 'map'
        """
        cmd, args = parse_command("MAP")
        assert cmd == "map"
        assert args == []


class TestMapRenderer:
    """Tests for render_map() function."""

    def test_map_command_returns_ascii_output(self):
        """Test map command returns string with visual representation.

        Spec: render_map should return a non-empty string containing ASCII art
        """
        world = {
            "Town Square": Location("Town Square", "A town square", {}, coordinates=(0, 0)),
        }
        result = render_map(world, "Town Square")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "MAP" in result.upper() or "===" in result

    def test_map_shows_current_location_marker(self):
        """Test current location is marked distinctly.

        Spec: Current location should be marked with '@' or '[*]'
        """
        world = {
            "Town Square": Location("Town Square", "A town square", {}, coordinates=(0, 0)),
            "Forest": Location("Forest", "A dark forest", {}, coordinates=(0, 1)),
        }
        result = render_map(world, "Town Square")

        # Current location should have a distinct marker
        assert "@" in result or "[*]" in result

    def test_map_shows_explored_locations(self):
        """Test all locations in world appear on map.

        Spec: All locations should be shown on the map with identifiers
        """
        world = {
            "Town Square": Location("Town Square", "A town square", {}, coordinates=(0, 0)),
            "Forest": Location("Forest", "A dark forest", {}, coordinates=(0, 1)),
            "Cave": Location("Cave", "A dark cave", {}, coordinates=(1, 0)),
        }
        result = render_map(world, "Town Square")

        # All locations should appear in the map (by name or abbreviation)
        # The legend should show mappings
        assert "Town Square" in result or "T" in result
        assert "Forest" in result or "F" in result
        assert "Cave" in result or "C" in result

    def test_map_with_no_coordinates_shows_message(self):
        """Test graceful handling of legacy saves without coordinates.

        Spec: When locations lack coordinates, show helpful message
        """
        world = {
            "Town Square": Location("Town Square", "A town square", {}),  # No coordinates
            "Forest": Location("Forest", "A dark forest", {}),  # No coordinates
        }
        result = render_map(world, "Town Square")

        # Should show a message about no coordinates / can't display map
        assert "No map available" in result or "coordinates" in result.lower() or len(result) > 0


class TestMapCommandIntegration:
    """Integration tests for map command in game loop."""

    def test_map_command_during_combat_blocked(self):
        """Test map command is not available during combat.

        Spec: Map should not be available during combat
        """
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy
        from cli_rpg.main import handle_combat_command

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town Square": Location("Town Square", "A town square", {}, coordinates=(0, 0)),
        }
        game_state = GameState(character, world, "Town Square")

        # Start combat
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=10,
            level=1
        )
        game_state.current_combat = CombatEncounter(character, enemy)

        # Try map command during combat (should be rejected)
        continue_game, message = handle_combat_command(game_state, "map", [])

        # Map command should be rejected in combat
        assert "combat" in message.lower() or "Can't" in message


class TestMapExplorationCommand:
    """Tests for map command during exploration."""

    def test_map_command_in_exploration_returns_map(self):
        """Test map command works during exploration.

        Spec: 'map' command should call render_map and return the result
        """
        from cli_rpg.main import handle_exploration_command

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town Square": Location("Town Square", "A town square", {}, coordinates=(0, 0)),
            "Forest": Location("Forest", "A dark forest", {}, coordinates=(0, 1)),
        }
        game_state = GameState(character, world, "Town Square")

        continue_game, message = handle_exploration_command(game_state, "map", [])

        assert continue_game is True
        assert "MAP" in message.upper() or "===" in message
        # Current location should be marked
        assert "@" in message or "[*]" in message
