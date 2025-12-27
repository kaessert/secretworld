"""Integration tests for grid-based world system."""

from unittest.mock import Mock
from cli_rpg.world import create_default_world
from cli_rpg.world_grid import WorldGrid
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


class TestDefaultWorldGridIntegration:
    """Integration tests for default world with grid coordinates."""

    def test_default_world_uses_grid_layout(self):
        """Test that default world has spatially consistent grid layout.

        Spec: Default world locations should have correct coordinates.
        """
        world, starting_location = create_default_world()

        # Town Square at origin
        assert world["Town Square"].coordinates == (0, 0)
        # Forest north of Town Square
        assert world["Forest"].coordinates == (0, 1)
        # Cave east of Town Square
        assert world["Cave"].coordinates == (1, 0)

    def test_movement_returns_to_start_after_north_south(self):
        """Test that going north then south returns to starting location.

        Spec: Bidirectional consistency - roundtrip movement returns to origin.
        """
        world, starting_location = create_default_world()
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, world, starting_location)

        # Start at Town Square
        assert game_state.current_location == "Town Square"

        # Go north to Forest
        success, _ = game_state.move("north")
        assert success is True
        assert game_state.current_location == "Forest"

        # Go south back to Town Square
        success, _ = game_state.move("south")
        assert success is True
        assert game_state.current_location == "Town Square"

    def test_movement_returns_to_start_after_east_west(self):
        """Test that going east then west returns to starting location.

        Spec: Bidirectional consistency - roundtrip movement returns to origin.
        """
        world, starting_location = create_default_world()
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, world, starting_location)

        # Start at Town Square
        assert game_state.current_location == "Town Square"

        # Go east to Cave
        success, _ = game_state.move("east")
        assert success is True
        assert game_state.current_location == "Cave"

        # Go west back to Town Square
        success, _ = game_state.move("west")
        assert success is True
        assert game_state.current_location == "Town Square"


class TestGameStateWithWorldGrid:
    """Integration tests for GameState using grid-aware world."""

    def test_game_state_with_grid_world(self):
        """Test GameState works with grid-based world dictionary.

        Spec: GameState should work with world dict containing locations with coordinates.
        """
        grid = WorldGrid()
        grid.add_location(
            Location("Start", "Starting location"), 0, 0
        )
        grid.add_location(
            Location("North", "Northern location"), 0, 1
        )

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, grid.as_dict(), "Start")

        # Verify we can navigate
        assert game_state.current_location == "Start"
        success, _ = game_state.move("north")
        assert success is True
        assert game_state.current_location == "North"

    def test_game_state_look_shows_correct_exits(self):
        """Test GameState.look() shows grid-consistent exits.

        Spec: Look should show exits based on grid connections.
        """
        grid = WorldGrid()
        grid.add_location(
            Location("Center", "Central location"), 0, 0
        )
        grid.add_location(
            Location("North", "Northern location"), 0, 1
        )
        grid.add_location(
            Location("East", "Eastern location"), 1, 0
        )

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, grid.as_dict(), "Center")

        look_result = game_state.look()
        assert "north" in look_result.lower()
        assert "east" in look_result.lower()


class TestComplexGridNavigation:
    """Integration tests for complex grid navigation scenarios."""

    def test_square_navigation_returns_to_origin(self):
        """Test that navigating in a square (N, E, S, W) returns to origin.

        Spec: Grid ensures geographic consistency for complex paths.
        """
        grid = WorldGrid()
        # Create a 2x2 grid
        grid.add_location(Location("SW", "Southwest"), 0, 0)
        grid.add_location(Location("NW", "Northwest"), 0, 1)
        grid.add_location(Location("NE", "Northeast"), 1, 1)
        grid.add_location(Location("SE", "Southeast"), 1, 0)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, grid.as_dict(), "SW")

        # Navigate in a square: N -> E -> S -> W
        game_state.move("north")
        assert game_state.current_location == "NW"

        game_state.move("east")
        assert game_state.current_location == "NE"

        game_state.move("south")
        assert game_state.current_location == "SE"

        game_state.move("west")
        assert game_state.current_location == "SW"

    def test_grid_prevents_impossible_connections(self):
        """Test that grid placement ensures consistent coordinate adjacency.

        Spec: Two locations adjacent on grid should be at adjacent coordinates.
        """
        grid = WorldGrid()
        loc_a = Location("Room A", "Location A")
        loc_b = Location("Room B", "Location B")

        grid.add_location(loc_a, 0, 0)
        grid.add_location(loc_b, 1, 0)  # East of Room A

        # Room A and Room B should have adjacent coordinates
        assert loc_a.coordinates == (0, 0)
        assert loc_b.coordinates == (1, 0)

        # Using get_available_directions, Room A should show east exit
        world = grid.as_dict()
        assert "east" in loc_a.get_available_directions(world=world)
        # Room B should show west exit
        assert "west" in loc_b.get_available_directions(world=world)


class TestGridSerializationIntegration:
    """Integration tests for grid serialization through game flow."""

    def test_save_load_preserves_grid_navigation(self, tmp_path):
        """Test that save/load preserves grid navigation capability.

        Spec: After save/load, navigation should work identically.
        """
        from cli_rpg.persistence import save_game_state, load_game_state

        world, starting_location = create_default_world()
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, world, starting_location)

        # Navigate to Forest
        game_state.move("north")
        assert game_state.current_location == "Forest"

        # Save
        filepath = save_game_state(game_state, str(tmp_path))

        # Load
        loaded_state = load_game_state(filepath)

        # Verify we're at Forest
        assert loaded_state.current_location == "Forest"

        # Verify we can navigate back
        success, _ = loaded_state.move("south")
        assert success is True
        assert loaded_state.current_location == "Town Square"

        # Verify coordinates preserved
        assert loaded_state.world["Town Square"].coordinates == (0, 0)
        assert loaded_state.world["Forest"].coordinates == (0, 1)


class TestAIWorldGridIntegration:
    """Integration tests for AI world generation with grid."""

    def test_ai_world_generation_uses_grid(self):
        """Test that AI world generation creates grid-consistent world.

        Spec: AI-generated world should have locations with coordinates.
        """
        from cli_rpg.ai_world import create_ai_world

        mock_ai_service = Mock()
        mock_ai_service.generate_location.return_value = {
            "name": "Town Square",
            "description": "A bustling town square.",
            "connections": {}
        }

        world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

        # Starting location should have coordinates at origin
        assert world["Town Square"].coordinates == (0, 0)

    def test_ai_expand_world_maintains_grid_consistency(self):
        """Test that expand_world maintains grid coordinate consistency.

        Spec: Expanded locations should have correct coordinates.
        """
        from cli_rpg.ai_world import expand_world

        # Start with a world that has coordinates
        world = {
            "Town Square": Location("Town Square", "A town square.", coordinates=(0, 0))
        }

        mock_ai_service = Mock()
        mock_ai_service.generate_location.return_value = {
            "name": "Forest",
            "description": "A dark forest.",
            "connections": {"south": "Town Square"}
        }

        expand_world(
            world=world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy"
        )

        # New location should be at (0, 1) - north of origin
        assert world["Forest"].coordinates == (0, 1)

        # Locations are connected via coordinate adjacency
        town_square = world["Town Square"]
        forest = world["Forest"]

        # Town Square at (0,0) and Forest at (0,1) are adjacent north-south
        assert "north" in town_square.get_available_directions(world=world)
        assert "south" in forest.get_available_directions(world=world)
