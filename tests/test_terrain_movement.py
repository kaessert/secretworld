"""Tests for terrain-based movement in game_state.py.

These tests verify that the `go` command uses WFC terrain passability
as the primary movement validation (Step 3 of terrain-based movement).

Test Cases:
1. Movement to passable terrain succeeds (no connection required)
2. Movement to impassable terrain blocked (even with connection)
3. Movement without ChunkManager uses connections (legacy)
4. Movement blocked when no terrain and no connection
5. All cardinal directions check terrain passability
"""

import pytest
from dataclasses import replace
from unittest.mock import MagicMock, patch

from cli_rpg.game_state import GameState
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character
from cli_rpg.world_tiles import DIRECTION_OFFSETS, is_passable


# --- Helper Functions ---


def create_test_character():
    """Create a minimal character for testing."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


def create_test_location(name: str = "Test Start", coords: tuple = (0, 0), **kwargs):
    """Create a location with specified properties."""
    defaults = {
        "name": name,
        "description": "A test location",
        "coordinates": coords,
        "connections": {},
    }
    defaults.update(kwargs)
    return Location(**defaults)


# --- Fixtures ---


@pytest.fixture
def mock_chunk_manager():
    """Create a mock ChunkManager."""
    chunk_manager = MagicMock()
    # Default: return plains (passable) for all tiles
    chunk_manager.get_tile_at = MagicMock(return_value="plains")
    return chunk_manager


# --- Test 1: Movement to passable terrain succeeds without explicit connection ---


def test_move_to_passable_terrain_without_connection(mock_chunk_manager):
    """Player can move to passable terrain even without explicit connection.

    Spec: Movement should check WFC terrain passability first. If terrain is
    passable (e.g., forest at target), movement should succeed regardless of
    connection dict status.
    """
    # Setup: Location at (0,0), no connection north, but forest at (0,1)
    start_loc = create_test_location("Test Start", (0, 0), connections={})
    mock_chunk_manager.get_tile_at = MagicMock(return_value="forest")  # Passable

    # Create GameState with WFC enabled
    character = create_test_character()
    game_state = GameState(character, {"Test Start": start_loc}, "Test Start")
    game_state.chunk_manager = mock_chunk_manager

    # Verify no connection exists
    assert not start_loc.has_connection("north")

    # Action: Move north
    with patch("cli_rpg.game_state.autosave"):
        success, message = game_state.move("north")

    # Verify move succeeded
    assert success, f"Move should succeed but got: {message}"
    assert game_state.current_location != "Test Start"  # Moved to new location


# --- Test 2: Movement to impassable terrain blocked (even with connection) ---


def test_move_to_impassable_terrain_blocked(mock_chunk_manager):
    """Player cannot move to impassable terrain (water) even with connection.

    Spec: When WFC shows impassable terrain (water) at target coordinates,
    movement should be blocked with appropriate message, even if connections
    dict has an entry for that direction.
    """
    # Setup: Location at (0,0), connection north exists, but water at (0,1)
    start_loc = create_test_location(
        "Test Start", (0, 0), connections={"north": "Fake Destination"}
    )
    mock_chunk_manager.get_tile_at = MagicMock(return_value="water")  # Impassable

    character = create_test_character()
    game_state = GameState(character, {"Test Start": start_loc}, "Test Start")
    game_state.chunk_manager = mock_chunk_manager

    # Verify connection exists
    assert start_loc.has_connection("north")

    # Action: Move north
    success, message = game_state.move("north")

    # Verify move blocked
    assert not success, f"Move should be blocked but succeeded: {message}"
    assert "water" in message.lower(), f"Message should mention water: {message}"
    assert "impassable" in message.lower(), f"Message should mention impassable: {message}"
    assert game_state.current_location == "Test Start"  # Didn't move


# --- Test 3: Movement without ChunkManager uses connections (legacy) ---


def test_move_without_chunk_manager_uses_connections():
    """Without WFC, movement uses traditional connection-based logic.

    Spec: When chunk_manager is None (legacy saves, non-WFC mode), the game
    should fall back to connection dict-based movement validation.
    """
    # Setup: Location at (0,0), no chunk_manager, connection north exists
    start_loc = create_test_location(
        "Test Start", (0, 0), connections={"north": "Northern Area"}
    )
    target_loc = create_test_location("Northern Area", (0, 1))

    character = create_test_character()
    game_state = GameState(
        character,
        {"Test Start": start_loc, "Northern Area": target_loc},
        "Test Start",
    )
    game_state.chunk_manager = None  # No WFC

    # Action: Move north (using connection)
    with patch("cli_rpg.game_state.autosave"):
        success, message = game_state.move("north")

    # Verify move succeeded via connection
    assert success, f"Legacy move should succeed: {message}"
    assert game_state.current_location == "Northern Area"


# --- Test 4: Movement blocked when no terrain and no connection ---


def test_move_blocked_no_terrain_no_connection():
    """Movement fails when no WFC terrain and no connection.

    Spec: Without chunk_manager and without connection, movement should fail
    with "You can't go that way."
    """
    # Setup: No chunk_manager, no connection in direction
    start_loc = create_test_location("Test Start", (0, 0), connections={})

    character = create_test_character()
    game_state = GameState(character, {"Test Start": start_loc}, "Test Start")
    game_state.chunk_manager = None  # No WFC

    # Action: Move north (no connection, no WFC)
    success, message = game_state.move("north")

    # Verify move blocked
    assert not success, f"Move should fail but succeeded: {message}"
    assert "can't go that way" in message.lower(), f"Wrong error message: {message}"


# --- Test 5: All cardinal directions check terrain passability ---


def test_all_directions_check_terrain(mock_chunk_manager):
    """All four directions check terrain passability.

    Spec: North, south, east, west should all validate movement against
    WFC terrain passability before allowing movement.
    """
    # Setup: Different terrain in each direction
    def terrain_by_coords(x, y):
        """Return terrain based on coordinates relative to (0, 0)."""
        terrain_map = {
            (0, 1): "forest",    # north - passable
            (0, -1): "water",    # south - impassable
            (1, 0): "plains",    # east - passable
            (-1, 0): "water",    # west - impassable
        }
        return terrain_map.get((x, y), "plains")

    mock_chunk_manager.get_tile_at = MagicMock(side_effect=terrain_by_coords)

    # Test each direction
    directions_expected = {
        "north": True,   # forest = passable
        "south": False,  # water = impassable
        "east": True,    # plains = passable
        "west": False,   # water = impassable
    }

    for direction, expected_success in directions_expected.items():
        # Create fresh game state for each test (avoids shared state issues)
        start_loc = create_test_location("Test Start", (0, 0), connections={})
        character = create_test_character()
        game_state = GameState(character, {"Test Start": start_loc}, "Test Start")
        game_state.chunk_manager = mock_chunk_manager

        # Action: Move in direction
        with patch("cli_rpg.game_state.autosave"):
            success, message = game_state.move(direction)

        # Verify expected result
        assert success == expected_success, (
            f"Direction {direction}: expected success={expected_success}, "
            f"got success={success}, message={message}"
        )
