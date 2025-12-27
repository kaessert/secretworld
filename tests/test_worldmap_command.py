"""Tests for worldmap command feature."""

from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.map_renderer import render_worldmap


class TestParseCommandWorldmap:
    """Tests for parse_command() with 'worldmap' command."""

    def test_parse_command_worldmap(self):
        """Test parsing 'worldmap' command.

        Spec: 'worldmap' should return ("worldmap", [])
        """
        cmd, args = parse_command("worldmap")
        assert cmd == "worldmap"
        assert args == []

    def test_parse_command_worldmap_alias_wm(self):
        """Test parsing 'wm' command (alias for worldmap).

        Spec: 'wm' should be treated same as 'worldmap'
        """
        cmd, args = parse_command("wm")
        assert cmd == "worldmap"
        assert args == []


class TestRenderWorldmap:
    """Tests for render_worldmap() function."""

    def test_worldmap_shows_only_overworld_locations(self):
        """Test worldmap filters to only is_overworld=True locations.

        Spec: Only locations with is_overworld=True and is_named=True should appear on the worldmap
        """
        world = {
            "Eldoria": Location(
                "Eldoria",
                "A grand city",
                coordinates=(0, 0),
                is_overworld=True,
                is_named=True,  # Named locations show in legend
            ),
            "Eldoria Market": Location(
                "Eldoria Market",
                "The city market",
                coordinates=None,  # Sub-locations typically have no grid coordinates
                parent_location="Eldoria"
            ),
            "Dark Forest": Location(
                "Dark Forest",
                "A dark forest",
                coordinates=(1, 0),
                is_overworld=True,
                is_named=True,  # Named locations show in legend
            ),
        }
        result = render_worldmap(world, "Eldoria")

        # Overworld locations should appear
        assert "Eldoria" in result
        assert "Dark Forest" in result
        # Sub-location should NOT appear (not is_overworld)
        assert "Eldoria Market" not in result
        # Should have WORLD MAP header
        assert "WORLD MAP" in result

    def test_worldmap_no_overworld_shows_message(self):
        """Test worldmap with no overworld locations shows helpful message.

        Spec: When no is_overworld=True locations exist, show helpful message
        """
        world = {
            "Dungeon Room 1": Location(
                "Dungeon Room 1",
                "A dark room",
                coordinates=(0, 0),
                is_overworld=False  # Not an overworld location
            ),
        }
        result = render_worldmap(world, "Dungeon Room 1")

        # Should show a message about no overworld map
        assert "No overworld map available" in result or "overworld" in result.lower()

    def test_worldmap_from_sublocation_shows_parent_context(self):
        """Test worldmap from sub-location shows parent context message.

        Spec: When player is in a sub-location, show message about parent landmark
        """
        world = {
            "Eldoria": Location(
                "Eldoria",
                "A grand city",
                coordinates=(0, 0),
                is_overworld=True,
                sub_locations=["Eldoria Market"]
            ),
            "Eldoria Market": Location(
                "Eldoria Market",
                "The city market",
                coordinates=None,
                parent_location="Eldoria",
                is_overworld=False
            ),
            "Dark Forest": Location(
                "Dark Forest",
                "A dark forest",
                coordinates=(1, 0),
                is_overworld=True
            ),
        }
        # Player is in a sub-location
        result = render_worldmap(world, "Eldoria Market")

        # Should show parent context
        assert "Eldoria" in result
        # Should still show the overworld map
        assert "WORLD MAP" in result

    def test_worldmap_blocked_during_combat(self):
        """Test worldmap command is not available during combat.

        Spec: Worldmap should not be available during combat
        """
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy
        from cli_rpg.main import handle_combat_command

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town Square": Location(
                "Town Square",
                "A town square",
                coordinates=(0, 0),
                is_overworld=True
            ),
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

        # Try worldmap command during combat (should be rejected)
        continue_game, message = handle_combat_command(game_state, "worldmap", [])

        # Worldmap command should be rejected in combat
        assert "combat" in message.lower() or "Can't" in message


class TestWorldmapExplorationCommand:
    """Tests for worldmap command during exploration."""

    def test_worldmap_command_in_exploration_returns_worldmap(self):
        """Test worldmap command works during exploration.

        Spec: 'worldmap' command should call render_worldmap and return the result
        """
        from cli_rpg.main import handle_exploration_command

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town Square": Location(
                "Town Square",
                "A town square",
                coordinates=(0, 0),
                is_overworld=True
            ),
            "Forest": Location(
                "Forest",
                "A dark forest",
                coordinates=(0, 1),
                is_overworld=True
            ),
        }
        game_state = GameState(character, world, "Town Square")

        continue_game, message = handle_exploration_command(game_state, "worldmap", [])

        assert continue_game is True
        assert "WORLD MAP" in message.upper()
        # Current location should be marked
        assert "@" in message or "[*]" in message

    def test_worldmap_command_inside_subgrid_uses_parent_location(self):
        """Test worldmap command inside SubGrid uses parent location.

        Spec: When player is inside a SubGrid, 'worldmap' command should render
        the overworld map centered on the parent location.
        """
        from cli_rpg.main import handle_exploration_command
        from cli_rpg.world_grid import SubGrid

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create main world with overworld location
        town = Location(
            "Town Square",
            "A busy town square",
            {},
            coordinates=(0, 0),
            is_overworld=True,
        )
        town.sub_grid = SubGrid(parent_name="Town Square", bounds=(-2, 2, -2, 2))

        # Create interior location with parent reference
        market = Location(
            "Market Stall",
            "A market stall",
            {},
            parent_location="Town Square",
        )
        town.sub_grid.add_location(market, 0, 0)

        world = {"Town Square": town}

        # Set up game state - start at Town Square, then simulate entering SubGrid
        game_state = GameState(character, world, "Town Square")
        # Simulate being inside the SubGrid (normally done by enter())
        game_state.in_sub_location = True
        game_state.current_sub_grid = town.sub_grid
        game_state.current_location = "Market Stall"

        continue_game, message = handle_exploration_command(game_state, "worldmap", [])

        assert continue_game is True
        # Should show WORLD MAP (not fail)
        assert "WORLD MAP" in message.upper(), f"Expected 'WORLD MAP' in output. Got:\n{message}"
        # Should not show the error message about location not found
        assert "not found" not in message.lower()
