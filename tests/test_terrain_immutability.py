"""Tests for terrain immutability after initial generation.

These tests verify the terrain immutability contract:
- After sync_with_locations() is called, no code path should modify terrain in _chunks
- Location.terrain must match ChunkManager.get_tile_at() for the same coordinates
- Post-sync modifications are logged as warnings (defensive guard)
"""

import logging
import pytest
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import TileRegistry
from cli_rpg.models.location import Location


# --- Test Fixtures ---


@pytest.fixture
def tile_registry():
    """Create a TileRegistry for testing."""
    return TileRegistry()


@pytest.fixture
def chunk_manager(tile_registry):
    """Create a ChunkManager with a specific seed for determinism."""
    return ChunkManager(tile_registry=tile_registry, world_seed=42)


@pytest.fixture
def synced_chunk_manager(chunk_manager):
    """Create a ChunkManager that has already been synced with locations."""
    # Create a simple world with one location
    location = Location(
        name="Test Town",
        description="A test location",
        terrain="plains",
        coordinates=(0, 0),
    )
    world = {"Test Town": location}

    # Sync with locations (this marks the chunk manager as synced)
    chunk_manager.sync_with_locations(world)
    return chunk_manager


# --- Defensive Guard Tests (spec: detect post-sync modifications) ---


def test_synced_flag_initially_false(chunk_manager):
    """ChunkManager._synced should be False before sync_with_locations() is called."""
    assert chunk_manager._synced is False


def test_synced_flag_true_after_sync(synced_chunk_manager):
    """ChunkManager._synced should be True after sync_with_locations() is called."""
    assert synced_chunk_manager._synced is True


def test_set_tile_at_before_sync_no_warning(chunk_manager, caplog):
    """Calling set_tile_at before sync should NOT log a warning."""
    # Generate a chunk first
    chunk_manager.get_or_generate_chunk(0, 0)

    with caplog.at_level(logging.WARNING):
        chunk_manager.set_tile_at(0, 0, "forest")

    # Should not have any immutability warnings
    assert "after sync" not in caplog.text.lower()
    assert "immutability" not in caplog.text.lower()


def test_set_tile_at_after_sync_logs_warning(synced_chunk_manager, caplog):
    """Calling set_tile_at after sync should log a warning (defensive guard)."""
    with caplog.at_level(logging.WARNING):
        synced_chunk_manager.set_tile_at(0, 0, "mountain")

    # Should have a warning about post-sync modification
    assert "synced" in caplog.text.lower() or "immutability" in caplog.text.lower()


# --- Terrain Consistency Tests (spec: Location.terrain matches chunk terrain) ---


def test_terrain_matches_chunk_on_location_sync(chunk_manager):
    """When sync_with_locations is called, terrain at location coords matches location.terrain."""
    location = Location(
        name="Forest Clearing",
        description="A clearing in the forest",
        terrain="forest",
        coordinates=(5, 5),
    )
    world = {"Forest Clearing": location}

    # Sync locations with chunk manager
    chunk_manager.sync_with_locations(world)

    # Terrain in chunk should match location's terrain
    assert chunk_manager.get_tile_at(5, 5) == "forest"


def test_location_terrain_matches_chunk_terrain():
    """Location.terrain should always match ChunkManager.get_tile_at() for same coords."""
    tile_registry = TileRegistry()
    cm = ChunkManager(tile_registry=tile_registry, world_seed=123)

    # Generate terrain first
    cm.get_or_generate_chunk(0, 0)
    original_terrain = cm.get_tile_at(3, 3)

    # Create a location with matching terrain
    location = Location(
        name="Matching Location",
        description="Has matching terrain",
        terrain=original_terrain,
        coordinates=(3, 3),
    )
    world = {"Matching Location": location}

    # After sync, terrain should still match
    cm.sync_with_locations(world)
    assert location.terrain == cm.get_tile_at(3, 3)


# --- Terrain Immutability Tests (spec: cached terrain doesn't change) ---


def test_terrain_unchanged_after_repeated_access(chunk_manager):
    """Accessing a tile multiple times should return the same terrain."""
    # Generate and access
    terrain1 = chunk_manager.get_tile_at(4, 4)
    terrain2 = chunk_manager.get_tile_at(4, 4)
    terrain3 = chunk_manager.get_tile_at(4, 4)

    assert terrain1 == terrain2 == terrain3


def test_cached_chunk_terrain_immutable(chunk_manager):
    """After chunk generation, the terrain values in _chunks don't change on their own."""
    # Generate a chunk
    chunk = chunk_manager.get_or_generate_chunk(0, 0)

    # Store a copy of the terrain values
    original_terrain = {coord: terrain for coord, terrain in chunk.items()}

    # Access multiple times via get_tile_at
    for x in range(8):
        for y in range(8):
            chunk_manager.get_tile_at(x, y)

    # Get the chunk again
    chunk_after = chunk_manager.get_or_generate_chunk(0, 0)

    # Terrain should be unchanged
    for coord, terrain in original_terrain.items():
        assert chunk_after[coord] == terrain, f"Terrain at {coord} changed from {terrain} to {chunk_after[coord]}"


def test_terrain_unchanged_after_movement_simulation(chunk_manager):
    """Simulating player movement does not change terrain in ChunkManager."""
    # Generate initial terrain
    initial_terrains = {}
    for x in range(-2, 3):
        for y in range(-2, 3):
            initial_terrains[(x, y)] = chunk_manager.get_tile_at(x, y)

    # Simulate movement by accessing tiles in sequence (like a player would)
    path = [(0, 0), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (0, 0)]
    for x, y in path:
        chunk_manager.get_tile_at(x, y)

    # Verify terrain hasn't changed
    for coord, expected_terrain in initial_terrains.items():
        actual_terrain = chunk_manager.get_tile_at(*coord)
        assert actual_terrain == expected_terrain, f"Terrain at {coord} changed"


# --- Serialization Tests (spec: _synced flag persists across save/load) ---


def test_synced_flag_serialized(synced_chunk_manager, tile_registry):
    """_synced flag should be included in to_dict() output."""
    data = synced_chunk_manager.to_dict()
    assert "synced" in data
    assert data["synced"] is True


def test_synced_flag_deserialized(synced_chunk_manager, tile_registry):
    """_synced flag should be restored from from_dict()."""
    data = synced_chunk_manager.to_dict()

    # Restore from serialized data
    restored = ChunkManager.from_dict(data, tile_registry)

    assert restored._synced is True


def test_unsynced_flag_deserialized(chunk_manager, tile_registry):
    """Unsynced ChunkManager should restore with _synced=False."""
    # Generate a chunk but don't sync
    chunk_manager.get_or_generate_chunk(0, 0)
    data = chunk_manager.to_dict()

    # Restore from serialized data
    restored = ChunkManager.from_dict(data, tile_registry)

    assert restored._synced is False


# --- Assert Helper Tests (spec: assert_terrain_unchanged helper method) ---


def test_assert_terrain_unchanged_passes_when_matching(chunk_manager):
    """assert_terrain_unchanged should not raise when terrain matches expected."""
    # Generate terrain
    terrain = chunk_manager.get_tile_at(2, 2)

    # Should not raise
    chunk_manager.assert_terrain_unchanged((2, 2), terrain)


def test_assert_terrain_unchanged_raises_when_different(chunk_manager):
    """assert_terrain_unchanged should raise AssertionError when terrain doesn't match."""
    # Generate terrain
    chunk_manager.get_tile_at(2, 2)

    # Should raise with mismatched terrain
    with pytest.raises(AssertionError):
        chunk_manager.assert_terrain_unchanged((2, 2), "nonexistent_terrain_type_xyz")
