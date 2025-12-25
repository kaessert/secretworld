"""Tests for infinite world expansion without AI service.

Spec: The world should be truly infinite even without AI service.
When a player moves in a valid cardinal direction, a new location should be
generated on-demand if one doesn't exist at the target coordinates.

This ensures players never hit a "You can't go that way" message in valid
directions, making the world feel infinite.
"""

import pytest
from unittest.mock import Mock

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.world import generate_fallback_location
from cli_rpg.world_grid import WorldGrid, DIRECTION_OFFSETS


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def basic_character():
    """Create a basic test character."""
    return Character(name="Test Hero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def world_with_coordinates():
    """Create a world with coordinate-based locations (no AI).

    The starting location has only one connection (north to Forest).
    East and West have no connections - they should trigger fallback generation.
    """
    grid = WorldGrid()

    town = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center."
    )
    forest = Location(
        name="Forest",
        description="A dense forest with tall trees."
    )

    grid.add_location(town, 0, 0)
    grid.add_location(forest, 0, 1)

    return grid.as_dict(), "Town Square"


@pytest.fixture
def single_location_world():
    """Create a world with only the starting location.

    This simulates the worst case - a player starting in a location with
    no pre-existing exits should still be able to explore in any direction.
    """
    grid = WorldGrid()

    town = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center."
    )
    grid.add_location(town, 0, 0)

    return grid.as_dict(), "Town Square"


# ============================================================================
# Test: generate_fallback_location()
# ============================================================================


class TestGenerateFallbackLocation:
    """Tests for the fallback location generation function."""

    def test_generates_location_with_valid_name(self):
        """Spec: Fallback locations must have valid names."""
        source = Location(
            name="Town Square",
            description="A town square.",
            coordinates=(0, 0)
        )

        new_location = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1)
        )

        assert new_location.name is not None
        assert len(new_location.name) >= 2
        assert new_location.name != source.name

    def test_generates_location_with_valid_description(self):
        """Spec: Fallback locations must have valid descriptions."""
        source = Location(
            name="Town Square",
            description="A town square.",
            coordinates=(0, 0)
        )

        new_location = generate_fallback_location(
            direction="east",
            source_location=source,
            target_coords=(1, 0)
        )

        assert new_location.description is not None
        assert len(new_location.description) >= 1

    def test_generates_location_with_correct_coordinates(self):
        """Spec: Fallback locations must have correct coordinates."""
        source = Location(
            name="Town Square",
            description="A town square.",
            coordinates=(0, 0)
        )

        new_location = generate_fallback_location(
            direction="south",
            source_location=source,
            target_coords=(0, -1)
        )

        assert new_location.coordinates == (0, -1)

    def test_generates_location_with_back_connection(self):
        """Spec: Fallback locations must have connection back to source."""
        source = Location(
            name="Town Square",
            description="A town square.",
            coordinates=(0, 0)
        )

        new_location = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1)
        )

        # Moving north means back connection is south
        assert new_location.has_connection("south")
        assert new_location.get_connection("south") == "Town Square"

    def test_generates_location_with_frontier_exits(self):
        """Spec: Fallback locations must have at least one frontier exit for expansion."""
        source = Location(
            name="Town Square",
            description="A town square.",
            coordinates=(0, 0)
        )

        new_location = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1)
        )

        # Should have more than just the back connection
        assert len(new_location.connections) >= 2, \
            "Fallback location must have at least 2 exits (back + frontier)"


# ============================================================================
# Test: Movement to unexplored directions creates location
# ============================================================================


class TestMoveToUnexploredDirection:
    """Tests for movement that creates fallback locations."""

    def test_move_to_unexplored_direction_succeeds(
        self, basic_character, world_with_coordinates
    ):
        """Spec: Moving in a valid direction with no exit creates a new location."""
        world, starting_location = world_with_coordinates

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None  # No AI service
        )

        # East has no connection, should create fallback location
        initial_world_size = len(game_state.world)
        success, message = game_state.move("east")

        assert success is True, f"Move should succeed, got: {message}"
        assert len(game_state.world) > initial_world_size, "New location should be added"
        assert game_state.current_location != starting_location, "Should have moved"

    def test_move_to_unexplored_creates_location_at_correct_coords(
        self, basic_character, world_with_coordinates
    ):
        """Spec: Created location must be at correct coordinates."""
        world, starting_location = world_with_coordinates

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Move east from (0, 0) should create location at (1, 0)
        success, _ = game_state.move("east")
        assert success is True

        new_location = game_state.get_current_location()
        assert new_location.coordinates == (1, 0)

    def test_move_to_unexplored_creates_bidirectional_connection(
        self, basic_character, world_with_coordinates
    ):
        """Spec: Moving to unexplored direction creates bidirectional connections."""
        world, starting_location = world_with_coordinates

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        success, _ = game_state.move("west")
        assert success is True

        new_location = game_state.get_current_location()
        source_location = game_state.world[starting_location]

        # Verify bidirectional connections
        assert source_location.has_connection("west")
        assert source_location.get_connection("west") == new_location.name
        assert new_location.has_connection("east")
        assert new_location.get_connection("east") == starting_location

    def test_return_to_previous_location_works(
        self, basic_character, world_with_coordinates
    ):
        """Spec: After moving to generated location, returning works correctly."""
        world, starting_location = world_with_coordinates

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Move to unexplored direction
        success1, _ = game_state.move("east")
        assert success1 is True

        new_location_name = game_state.current_location

        # Return to starting location
        success2, _ = game_state.move("west")
        assert success2 is True
        assert game_state.current_location == starting_location

        # Move back to the generated location
        success3, _ = game_state.move("east")
        assert success3 is True
        assert game_state.current_location == new_location_name


# ============================================================================
# Test: World never becomes closed
# ============================================================================


class TestWorldNeverBecomesClosed:
    """Tests ensuring the world always has expansion options."""

    def test_fallback_location_has_frontier_exits(
        self, basic_character, single_location_world
    ):
        """Spec: Generated fallback locations have frontier exits."""
        world, starting_location = single_location_world

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Move to create fallback location
        success, _ = game_state.move("north")
        assert success is True

        new_location = game_state.get_current_location()

        # Should have more than just back connection
        non_back = [d for d in new_location.connections if d != "south"]
        assert len(non_back) >= 1, \
            "Generated location must have at least one forward exit"

    def test_multiple_expansions_maintain_frontier(
        self, basic_character, single_location_world
    ):
        """Spec: World always has frontier exits after multiple expansions."""
        world, starting_location = single_location_world

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Perform multiple expansions
        moves = ["north", "east", "south"]
        for direction in moves:
            success, _ = game_state.move(direction)
            assert success is True

        # After all moves, should still be able to explore
        # (there should be unexplored directions available)
        current = game_state.get_current_location()
        available_dirs = current.get_available_directions()
        assert len(available_dirs) >= 1, "Should have at least one direction available"

    def test_single_location_start_allows_all_directions(
        self, basic_character, single_location_world
    ):
        """Spec: Starting with single location allows movement in all directions."""
        world, starting_location = single_location_world

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Should be able to move in all cardinal directions
        for direction in ["north", "south", "east", "west"]:
            game_state.current_location = starting_location  # Reset
            success, msg = game_state.move(direction)
            assert success is True, f"Move {direction} should succeed, got: {msg}"


# ============================================================================
# Test: Integration scenarios
# ============================================================================


class TestInfiniteWorldIntegration:
    """Integration tests for infinite world behavior."""

    def test_circular_path_exploration(
        self, basic_character, single_location_world
    ):
        """Spec: Can explore in a circular path creating locations as needed."""
        world, starting_location = single_location_world

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Move in a square pattern
        # Start at (0,0), go north (0,1), east (1,1), south (1,0), west returns to (0,0)
        initial_size = len(game_state.world)

        success1, _ = game_state.move("north")
        assert success1 is True
        success2, _ = game_state.move("east")
        assert success2 is True
        success3, _ = game_state.move("south")
        assert success3 is True
        success4, _ = game_state.move("west")
        assert success4 is True

        # Should have created 3 new locations (the 4th move returns to start)
        # Path: (0,0) -> (0,1) -> (1,1) -> (1,0) -> (0,0)
        assert len(game_state.world) == initial_size + 3
        # Should be back at starting location
        assert game_state.current_location == starting_location

    def test_long_straight_path(
        self, basic_character, single_location_world
    ):
        """Spec: Can explore in a straight line indefinitely."""
        world, starting_location = single_location_world

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Move north 5 times
        for i in range(5):
            success, msg = game_state.move("north")
            assert success is True, f"Move {i+1} north should succeed, got: {msg}"

        # Should be at coordinates (0, 5)
        current = game_state.get_current_location()
        assert current.coordinates == (0, 5)

        # Should be able to return
        for i in range(5):
            success, _ = game_state.move("south")
            assert success is True

        assert game_state.current_location == starting_location

    def test_existing_connections_still_work(
        self, basic_character, world_with_coordinates
    ):
        """Spec: Existing connections work normally alongside fallback generation."""
        world, starting_location = world_with_coordinates

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Move to existing connection (north to Forest)
        success1, _ = game_state.move("north")
        assert success1 is True
        assert game_state.current_location == "Forest"

        # Move back
        success2, _ = game_state.move("south")
        assert success2 is True
        assert game_state.current_location == starting_location

        # Now move to unexplored direction (east)
        success3, _ = game_state.move("east")
        assert success3 is True
        assert game_state.current_location != starting_location
        assert game_state.current_location != "Forest"

    def test_generated_locations_have_unique_names(
        self, basic_character, single_location_world
    ):
        """Spec: All generated locations should have unique names."""
        world, starting_location = single_location_world

        game_state = GameState(
            character=basic_character,
            world=world,
            starting_location=starting_location,
            ai_service=None
        )

        # Generate several locations
        game_state.move("north")
        game_state.move("east")
        game_state.move("south")
        game_state.move("west")

        # All names should be unique
        names = list(game_state.world.keys())
        assert len(names) == len(set(names)), "All location names should be unique"
