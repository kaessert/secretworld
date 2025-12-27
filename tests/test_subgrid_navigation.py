"""Tests for GameState sub-location navigation using SubGrid.

These tests verify GameState integration with the SubGrid system:
- New fields: in_sub_location, current_sub_grid
- enter() with sub_grid: enters interior grid and tracks state
- move() inside sub_grid: uses sub-grid coordinates
- exit_location() with is_exit_point: only allows exit from marked rooms
- get_current_location(): resolves from sub_grid when inside one
- Persistence: in_sub_location state survives save/load
"""

import pytest
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid


def make_character() -> Character:
    """Create a basic test character."""
    return Character(
        name="TestHero",
        strength=10,
        dexterity=10,
        intelligence=10,
    )


def make_simple_world() -> dict[str, Location]:
    """Create a simple world with an overworld location and sub-grid."""
    # Create overworld town with sub_grid
    sub_grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Town Square")

    # Entry room at (0, 0) - also an exit point
    entrance = Location(
        name="Town Hall Entrance",
        description="The entrance to the town hall.",
        is_exit_point=True,
    )
    sub_grid.add_location(entrance, 0, 0)

    # Inner room at (0, 1) - NOT an exit point
    council_chamber = Location(
        name="Council Chamber",
        description="A grand chamber for town meetings.",
        is_exit_point=False,
    )
    sub_grid.add_location(council_chamber, 0, 1)

    # Another room at (1, 0)
    treasury = Location(
        name="Treasury",
        description="The town treasury.",
        is_exit_point=False,
    )
    sub_grid.add_location(treasury, 1, 0)

    # Create overworld location with sub_grid
    town_square = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0),
        is_overworld=True,
        sub_grid=sub_grid,
        sub_locations=["Town Hall Entrance"],  # for enter() to find it
        entry_point="Town Hall Entrance",
    )

    # Create adjacent overworld location
    # Movement between Town Square (0,0) and Market (1,0) is based on coordinate adjacency
    market = Location(
        name="Market",
        description="The town market.",
        coordinates=(1, 0),
        is_overworld=True,
    )

    return {
        "Town Square": town_square,
        "Market": market,
    }


class TestGameStateSubLocationFields:
    """Test new GameState fields for sub-location tracking - spec: Phase 1 Step 3."""

    def test_game_state_has_in_sub_location_field(self):
        """Test GameState has in_sub_location field defaulting to False."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        assert hasattr(game_state, "in_sub_location")
        assert game_state.in_sub_location is False

    def test_game_state_has_current_sub_grid_field(self):
        """Test GameState has current_sub_grid field defaulting to None."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        assert hasattr(game_state, "current_sub_grid")
        assert game_state.current_sub_grid is None


class TestEnterWithSubGrid:
    """Test enter() method with sub_grid support - spec: enter updates sub-grid state."""

    def test_enter_with_sub_grid_sets_in_sub_location_true(self):
        """Test entering location with sub_grid sets in_sub_location=True."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        success, _ = game_state.enter("Town Hall")
        assert success
        assert game_state.in_sub_location is True

    def test_enter_with_sub_grid_sets_current_sub_grid(self):
        """Test entering location with sub_grid sets current_sub_grid."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        success, _ = game_state.enter("Town Hall")
        assert success
        assert game_state.current_sub_grid is not None
        assert game_state.current_sub_grid.parent_name == "Town Square"

    def test_enter_with_sub_grid_moves_to_entry_location(self):
        """Test entering sub_grid moves player to (0, 0) entry location."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        success, _ = game_state.enter("Town Hall")
        assert success
        assert game_state.current_location == "Town Hall Entrance"

    def test_enter_with_target_name_goes_to_specific_sub_location(self):
        """Test entering with target name goes to that sub-location if it exists."""
        character = make_character()
        world = make_simple_world()
        # Add Council Chamber to sub_locations list for it to be enterable
        world["Town Square"].sub_locations.append("Council Chamber")
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter Council Chamber directly
        success, _ = game_state.enter("Council Chamber")
        assert success
        assert game_state.current_location == "Council Chamber"
        assert game_state.in_sub_location is True


class TestMoveInsideSubGrid:
    """Test move() inside sub_grid - spec: sub-grid movement uses internal coordinates."""

    def test_move_inside_sub_grid_uses_sub_grid_coordinates(self):
        """Test movement inside sub_grid follows sub-grid connections."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")
        assert game_state.current_location == "Town Hall Entrance"

        # Move north to Council Chamber
        success, message = game_state.move("north")
        assert success, f"Move failed: {message}"
        assert game_state.current_location == "Council Chamber"

    def test_move_inside_sub_grid_respects_connections(self):
        """Test movement inside sub_grid respects location connections."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid at entrance
        game_state.enter("Town Hall")

        # Move east to Treasury
        success, message = game_state.move("east")
        assert success, f"Move failed: {message}"
        assert game_state.current_location == "Treasury"

    def test_move_inside_sub_grid_blocks_at_bounds(self):
        """Test movement blocked when no adjacent location exists."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid at entrance
        game_state.enter("Town Hall")

        # Try to move west (no location at (-1, 0))
        success, message = game_state.move("west")
        assert not success
        assert "blocked" in message.lower() or "can't go that way" in message.lower()

    def test_move_inside_sub_grid_stays_in_sub_location(self):
        """Test movement inside sub_grid keeps in_sub_location True."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")
        assert game_state.in_sub_location is True

        # Move within sub-grid
        game_state.move("north")
        assert game_state.in_sub_location is True
        assert game_state.current_sub_grid is not None


class TestExitWithExitPoint:
    """Test exit_location() with is_exit_point check - spec: only exit from marked rooms."""

    def test_exit_from_exit_point_succeeds(self):
        """Test exit succeeds from location marked is_exit_point=True."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid at entrance (which is an exit point)
        game_state.enter("Town Hall")
        assert game_state.current_location == "Town Hall Entrance"
        assert game_state.in_sub_location is True

        # Exit should succeed
        success, message = game_state.exit_location()
        assert success, f"Exit failed: {message}"
        assert game_state.current_location == "Town Square"

    def test_exit_from_non_exit_point_fails(self):
        """Test exit fails from location marked is_exit_point=False."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")

        # Move to non-exit point
        game_state.move("north")  # Council Chamber is not an exit point
        assert game_state.current_location == "Council Chamber"

        # Exit should fail
        success, message = game_state.exit_location()
        assert not success
        assert "exit" in message.lower() or "cannot" in message.lower()

    def test_exit_clears_in_sub_location(self):
        """Test successful exit clears in_sub_location to False."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")
        assert game_state.in_sub_location is True

        # Exit
        game_state.exit_location()
        assert game_state.in_sub_location is False

    def test_exit_clears_current_sub_grid(self):
        """Test successful exit clears current_sub_grid to None."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")
        assert game_state.current_sub_grid is not None

        # Exit
        game_state.exit_location()
        assert game_state.current_sub_grid is None

    def test_exit_returns_to_parent(self):
        """Test exit returns player to parent overworld location."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")

        # Exit
        success, _ = game_state.exit_location()
        assert success
        assert game_state.current_location == "Town Square"


class TestGetCurrentLocationWithSubGrid:
    """Test get_current_location() with sub_grid - spec: resolves from sub_grid when inside."""

    def test_get_current_location_inside_sub_grid_returns_sub_grid_location(self):
        """Test get_current_location returns sub_grid location when inside."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")

        # get_current_location should return sub_grid location
        location = game_state.get_current_location()
        assert location.name == "Town Hall Entrance"
        assert location.parent_location == "Town Square"

    def test_get_current_location_overworld_returns_world_location(self):
        """Test get_current_location returns world location when not in sub-grid."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        location = game_state.get_current_location()
        assert location.name == "Town Square"
        assert location.is_overworld is True


class TestSubLocationPersistence:
    """Test persistence of sub-location state - spec: save/load preserves state."""

    def test_in_sub_location_persists_in_save(self):
        """Test in_sub_location is included in to_dict()."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")

        # Serialize
        data = game_state.to_dict()
        assert "in_sub_location" in data
        assert data["in_sub_location"] is True

    def test_in_sub_location_restored_from_save(self):
        """Test in_sub_location is restored from from_dict()."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")

        # Round-trip
        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        assert restored.in_sub_location is True

    def test_current_sub_grid_restored_from_save(self):
        """Test current_sub_grid is properly restored from from_dict()."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid
        game_state.enter("Town Hall")

        # Round-trip
        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        # current_sub_grid should be restored by finding it from the location
        assert restored.current_sub_grid is not None
        assert restored.current_sub_grid.parent_name == "Town Square"

    def test_sub_location_state_round_trip(self):
        """Test full round-trip of sub-location state."""
        character = make_character()
        world = make_simple_world()
        game_state = GameState(character, world, starting_location="Town Square")

        # Enter sub-grid and move around
        game_state.enter("Town Hall")
        game_state.move("north")  # Move to Council Chamber

        # Round-trip
        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        # All state should be preserved
        assert restored.in_sub_location is True
        assert restored.current_location == "Council Chamber"
        assert restored.current_sub_grid is not None
        assert restored.get_current_location().name == "Council Chamber"
