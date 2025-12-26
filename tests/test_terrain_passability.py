"""Tests for terrain-based passability in world_tiles.py.

These tests verify:
- PASSABLE_TERRAIN frozenset contains traversable terrain types
- IMPASSABLE_TERRAIN frozenset contains blocking terrain types
- DIRECTION_OFFSETS dict has correct cardinal direction mappings
- is_passable() function returns correct boolean for terrain types
- get_valid_moves() function returns valid movement directions
"""

import pytest
from unittest.mock import MagicMock

from cli_rpg.world_tiles import (
    PASSABLE_TERRAIN,
    IMPASSABLE_TERRAIN,
    DIRECTION_OFFSETS,
    is_passable,
    get_valid_moves,
)
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import TileRegistry


# --- PASSABLE_TERRAIN Tests ---


def test_passable_terrain_is_frozenset():
    """PASSABLE_TERRAIN should be an immutable frozenset."""
    assert isinstance(PASSABLE_TERRAIN, frozenset)


def test_passable_terrain_contains_expected_types():
    """PASSABLE_TERRAIN should contain all expected traversable terrain types."""
    expected = {"forest", "plains", "hills", "desert", "swamp", "beach", "foothills", "mountain"}
    assert PASSABLE_TERRAIN == expected


def test_passable_terrain_excludes_water():
    """PASSABLE_TERRAIN should not contain water."""
    assert "water" not in PASSABLE_TERRAIN


# --- IMPASSABLE_TERRAIN Tests ---


def test_impassable_terrain_is_frozenset():
    """IMPASSABLE_TERRAIN should be an immutable frozenset."""
    assert isinstance(IMPASSABLE_TERRAIN, frozenset)


def test_impassable_terrain_contains_water():
    """IMPASSABLE_TERRAIN should contain water."""
    assert "water" in IMPASSABLE_TERRAIN


def test_passable_and_impassable_no_overlap():
    """PASSABLE_TERRAIN and IMPASSABLE_TERRAIN should not share any terrain types."""
    overlap = PASSABLE_TERRAIN & IMPASSABLE_TERRAIN
    assert len(overlap) == 0, f"Found overlap: {overlap}"


# --- DIRECTION_OFFSETS Tests ---


def test_direction_offsets_has_cardinal_directions():
    """DIRECTION_OFFSETS should have all four cardinal directions."""
    assert set(DIRECTION_OFFSETS.keys()) == {"north", "south", "east", "west"}


def test_direction_offsets_correct_values():
    """DIRECTION_OFFSETS should have correct coordinate offsets."""
    assert DIRECTION_OFFSETS["north"] == (0, 1)
    assert DIRECTION_OFFSETS["south"] == (0, -1)
    assert DIRECTION_OFFSETS["east"] == (1, 0)
    assert DIRECTION_OFFSETS["west"] == (-1, 0)


# --- is_passable() Tests ---


def test_is_passable_returns_true_for_forest():
    """forest terrain should be passable."""
    assert is_passable("forest") is True


def test_is_passable_returns_true_for_plains():
    """plains terrain should be passable."""
    assert is_passable("plains") is True


def test_is_passable_returns_true_for_mountain():
    """mountain terrain should be passable."""
    assert is_passable("mountain") is True


def test_is_passable_returns_false_for_water():
    """water terrain should be impassable."""
    assert is_passable("water") is False


def test_is_passable_returns_false_for_unknown():
    """Unknown terrain should return False as a safe default."""
    assert is_passable("lava") is False
    assert is_passable("void") is False
    assert is_passable("") is False


# --- get_valid_moves() Tests ---


def test_get_valid_moves_all_directions_passable():
    """Returns all 4 directions when surrounded by passable terrain."""
    # Create mock ChunkManager
    chunk_manager = MagicMock(spec=ChunkManager)

    # Position (5, 5), all neighbors are plains (passable)
    chunk_manager.get_tile_at.side_effect = lambda x, y: "plains"

    moves = get_valid_moves(chunk_manager, 5, 5)

    assert moves == ["east", "north", "south", "west"]


def test_get_valid_moves_excludes_water_north():
    """Excludes north when water is to the north."""
    chunk_manager = MagicMock(spec=ChunkManager)

    # Water to the north (0, 1), plains elsewhere
    def get_terrain(x, y):
        if (x, y) == (0, 1):  # north of (0, 0)
            return "water"
        return "plains"

    chunk_manager.get_tile_at.side_effect = get_terrain

    moves = get_valid_moves(chunk_manager, 0, 0)

    assert "north" not in moves
    assert moves == ["east", "south", "west"]


def test_get_valid_moves_empty_when_surrounded_by_water():
    """Returns empty list when all neighbors are water."""
    chunk_manager = MagicMock(spec=ChunkManager)
    chunk_manager.get_tile_at.side_effect = lambda x, y: "water"

    moves = get_valid_moves(chunk_manager, 5, 5)

    assert moves == []


def test_get_valid_moves_returns_sorted_list():
    """Returned directions should be in sorted order."""
    chunk_manager = MagicMock(spec=ChunkManager)
    chunk_manager.get_tile_at.side_effect = lambda x, y: "forest"

    moves = get_valid_moves(chunk_manager, 0, 0)

    assert moves == sorted(moves)
    assert moves == ["east", "north", "south", "west"]


def test_get_valid_moves_integration_with_chunk_manager():
    """Works with real ChunkManager instance."""
    # Create real ChunkManager with default registry
    tile_registry = TileRegistry()
    chunk_manager = ChunkManager(tile_registry=tile_registry, world_seed=42)

    # Get moves from origin (0, 0)
    moves = get_valid_moves(chunk_manager, 0, 0)

    # Should return a list of strings
    assert isinstance(moves, list)
    assert all(isinstance(m, str) for m in moves)
    # All returned moves should be valid cardinal directions
    assert all(m in DIRECTION_OFFSETS for m in moves)
    # List should be sorted
    assert moves == sorted(moves)
