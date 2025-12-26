"""Tests for WFC ChunkManager for infinite terrain generation.

These tests verify the ChunkManager spec from ISSUES.md lines 398-428.
"""

import pytest
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import TileRegistry, ADJACENCY_RULES


# --- Test Fixtures ---


@pytest.fixture
def tile_registry():
    """Create a TileRegistry for testing."""
    return TileRegistry()


@pytest.fixture
def chunk_manager(tile_registry):
    """Create a ChunkManager with default settings."""
    return ChunkManager(tile_registry=tile_registry)


@pytest.fixture
def seeded_chunk_manager(tile_registry):
    """Create a ChunkManager with a specific world seed."""
    return ChunkManager(tile_registry=tile_registry, world_seed=12345)


# --- Chunk Manager Creation Tests (spec: ChunkManager dataclass) ---


def test_chunk_manager_creation(tile_registry):
    """ChunkManager has correct default values (spec: default chunk_size=8, empty chunks)."""
    cm = ChunkManager(tile_registry=tile_registry)
    assert cm.chunk_size == 8
    assert cm.world_seed == 0
    assert len(cm._chunks) == 0


def test_chunk_manager_with_custom_seed(tile_registry):
    """ChunkManager accepts custom world_seed (spec: custom world seed)."""
    cm = ChunkManager(tile_registry=tile_registry, world_seed=99999)
    assert cm.world_seed == 99999


# --- Deterministic Seeding Tests (spec: chunk boundary tests) ---


def test_chunk_seed_deterministic(tile_registry):
    """Same world_seed + chunk coords = same terrain (spec: deterministic seeding)."""
    cm1 = ChunkManager(tile_registry=tile_registry, world_seed=42)
    cm2 = ChunkManager(tile_registry=tile_registry, world_seed=42)

    chunk1 = cm1.get_or_generate_chunk(3, 5)
    chunk2 = cm2.get_or_generate_chunk(3, 5)

    assert chunk1 == chunk2


def test_different_chunks_different_terrain(seeded_chunk_manager):
    """Different chunk coords = different terrain (spec: unique chunk seeding)."""
    chunk_00 = seeded_chunk_manager.get_or_generate_chunk(0, 0)
    chunk_11 = seeded_chunk_manager.get_or_generate_chunk(1, 1)

    # Different chunks should have different terrain layouts
    # (extremely unlikely to be identical by chance)
    assert chunk_00 != chunk_11


def test_different_world_seeds_different_terrain(tile_registry):
    """Different world_seed = different terrain (spec: world seed affects generation)."""
    cm1 = ChunkManager(tile_registry=tile_registry, world_seed=111)
    cm2 = ChunkManager(tile_registry=tile_registry, world_seed=222)

    chunk1 = cm1.get_or_generate_chunk(0, 0)
    chunk2 = cm2.get_or_generate_chunk(0, 0)

    assert chunk1 != chunk2


# --- Chunk Caching Tests (spec: chunk caching works correctly) ---


def test_get_or_generate_caches_chunk(seeded_chunk_manager):
    """Second call returns cached chunk, no regeneration (spec: chunk caching)."""
    chunk1 = seeded_chunk_manager.get_or_generate_chunk(2, 3)
    chunk2 = seeded_chunk_manager.get_or_generate_chunk(2, 3)

    # Should be the exact same object (cached)
    assert chunk1 is chunk2
    # Cache should have exactly one entry
    assert len(seeded_chunk_manager._chunks) == 1


def test_cached_chunk_unchanged(seeded_chunk_manager):
    """Cached chunk is identical to original (spec: cache integrity)."""
    chunk_original = seeded_chunk_manager.get_or_generate_chunk(0, 0)
    original_copy = dict(chunk_original)

    # Access other chunks
    seeded_chunk_manager.get_or_generate_chunk(1, 0)
    seeded_chunk_manager.get_or_generate_chunk(0, 1)

    # Original chunk should be unchanged
    chunk_retrieved = seeded_chunk_manager.get_or_generate_chunk(0, 0)
    assert chunk_retrieved == original_copy


# --- Coordinate Conversion Tests (spec: world-to-chunk coordinate conversion) ---


def test_get_tile_at_positive_coords(seeded_chunk_manager):
    """World (5, 3) in chunk (0, 0) returns correct tile (spec: coordinate mapping)."""
    tile = seeded_chunk_manager.get_tile_at(5, 3)

    # Verify by checking the chunk directly
    chunk = seeded_chunk_manager.get_or_generate_chunk(0, 0)
    assert tile == chunk[(5, 3)]


def test_get_tile_at_negative_coords(seeded_chunk_manager):
    """World (-3, -5) maps to correct chunk (spec: negative coordinate handling)."""
    # For chunk_size=8: -3 // 8 = -1, -5 // 8 = -1
    tile = seeded_chunk_manager.get_tile_at(-3, -5)

    # Should generate chunk (-1, -1)
    assert (-1, -1) in seeded_chunk_manager._chunks

    # Verify tile is in that chunk
    chunk = seeded_chunk_manager.get_or_generate_chunk(-1, -1)
    assert tile == chunk[(-3, -5)]


def test_get_tile_at_chunk_boundary(seeded_chunk_manager):
    """World (8, 0) is in chunk (1, 0) (spec: boundary coordinate handling)."""
    tile = seeded_chunk_manager.get_tile_at(8, 0)

    # 8 // 8 = 1, so should be in chunk (1, 0)
    assert (1, 0) in seeded_chunk_manager._chunks

    chunk = seeded_chunk_manager.get_or_generate_chunk(1, 0)
    assert tile == chunk[(8, 0)]


def test_world_to_chunk_conversion(chunk_manager):
    """Verify chunk_x/chunk_y calculation (spec: coordinate conversion formula)."""
    # Test various coordinates
    test_cases = [
        # (world_x, world_y) -> expected (chunk_x, chunk_y)
        ((0, 0), (0, 0)),
        ((7, 7), (0, 0)),
        ((8, 0), (1, 0)),
        ((0, 8), (0, 1)),
        ((15, 15), (1, 1)),
        ((-1, 0), (-1, 0)),
        ((-8, -8), (-1, -1)),
        ((-9, -9), (-2, -2)),
    ]

    for (wx, wy), (expected_cx, expected_cy) in test_cases:
        chunk_manager.get_tile_at(wx, wy)
        assert (expected_cx, expected_cy) in chunk_manager._chunks, \
            f"World ({wx}, {wy}) should be in chunk ({expected_cx}, {expected_cy})"


# --- Boundary Constraints Tests (spec: chunk boundary consistency) ---


def test_adjacent_chunks_share_compatible_edges(seeded_chunk_manager):
    """East edge of (0,0) compatible with west edge of (1,0) (spec: boundary consistency)."""
    # Generate both chunks
    chunk_00 = seeded_chunk_manager.get_or_generate_chunk(0, 0)
    chunk_10 = seeded_chunk_manager.get_or_generate_chunk(1, 0)

    # Check east edge of chunk (0,0) against west edge of chunk (1,0)
    chunk_size = seeded_chunk_manager.chunk_size

    for y in range(chunk_size):
        # East edge of (0,0): x = 7
        east_tile = chunk_00[(7, y)]
        # West edge of (1,0): x = 8
        west_tile = chunk_10[(8, y)]

        # Tiles should be compatible according to adjacency rules
        assert west_tile in ADJACENCY_RULES[east_tile], \
            f"Boundary incompatibility at y={y}: {east_tile} -> {west_tile}"
        assert east_tile in ADJACENCY_RULES[west_tile], \
            f"Boundary incompatibility at y={y}: {west_tile} -> {east_tile}"


def test_boundary_constraints_applied_vertical(seeded_chunk_manager):
    """North edge of (0,0) compatible with south edge of (0,1) (spec: vertical boundaries)."""
    # Generate both chunks
    chunk_00 = seeded_chunk_manager.get_or_generate_chunk(0, 0)
    chunk_01 = seeded_chunk_manager.get_or_generate_chunk(0, 1)

    chunk_size = seeded_chunk_manager.chunk_size

    for x in range(chunk_size):
        # North edge of (0,0): y = 7
        north_tile = chunk_00[(x, 7)]
        # South edge of (0,1): y = 8
        south_tile = chunk_01[(x, 8)]

        # Tiles should be compatible
        assert south_tile in ADJACENCY_RULES[north_tile], \
            f"Boundary incompatibility at x={x}: {north_tile} -> {south_tile}"


# --- Integration Tests ---


def test_large_area_traversal(seeded_chunk_manager):
    """Walk across chunk boundaries, terrain is coherent (spec: seamless traversal)."""
    # Walk from (-5, -5) to (15, 15) checking all adjacencies
    visited_tiles = {}

    for x in range(-5, 16):
        for y in range(-5, 16):
            tile = seeded_chunk_manager.get_tile_at(x, y)
            visited_tiles[(x, y)] = tile

    # Verify all adjacencies are valid
    for (x, y), tile in visited_tiles.items():
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_coords = (x + dx, y + dy)
            if neighbor_coords in visited_tiles:
                neighbor_tile = visited_tiles[neighbor_coords]
                assert neighbor_tile in ADJACENCY_RULES[tile], \
                    f"Invalid adjacency at ({x},{y})->{neighbor_coords}: {tile} -> {neighbor_tile}"


def test_serialization_to_dict(seeded_chunk_manager):
    """ChunkManager.to_dict() serializes world_seed and cached chunks (spec: persistence)."""
    # Generate some chunks
    seeded_chunk_manager.get_or_generate_chunk(0, 0)
    seeded_chunk_manager.get_or_generate_chunk(1, 0)

    data = seeded_chunk_manager.to_dict()

    assert "world_seed" in data
    assert data["world_seed"] == 12345
    assert "chunk_size" in data
    assert data["chunk_size"] == 8
    assert "chunks" in data
    assert len(data["chunks"]) == 2


def test_deserialization_from_dict(tile_registry):
    """ChunkManager.from_dict() restores state (spec: persistence restore)."""
    # Create original and generate chunks
    original = ChunkManager(tile_registry=tile_registry, world_seed=777)
    chunk_00 = original.get_or_generate_chunk(0, 0)
    chunk_11 = original.get_or_generate_chunk(1, 1)

    # Serialize
    data = original.to_dict()

    # Deserialize
    restored = ChunkManager.from_dict(data, tile_registry)

    # Verify state matches
    assert restored.world_seed == 777
    assert restored.chunk_size == 8
    assert len(restored._chunks) == 2

    # Chunks should be identical
    assert restored.get_or_generate_chunk(0, 0) == chunk_00
    assert restored.get_or_generate_chunk(1, 1) == chunk_11


def test_chunk_contains_correct_coordinates(seeded_chunk_manager):
    """Generated chunk contains all expected coordinate keys (spec: chunk structure)."""
    chunk = seeded_chunk_manager.get_or_generate_chunk(1, 2)
    chunk_size = seeded_chunk_manager.chunk_size

    # Chunk (1, 2) should have coordinates from (8, 16) to (15, 23)
    expected_coords = set()
    for x in range(8, 16):
        for y in range(16, 24):
            expected_coords.add((x, y))

    assert set(chunk.keys()) == expected_coords
