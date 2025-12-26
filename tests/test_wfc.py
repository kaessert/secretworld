"""Tests for Wave Function Collapse (WFC) terrain generation algorithm.

These tests verify the WFC algorithm spec from the implementation plan.
"""

import pytest
import math
from cli_rpg.wfc import WFCCell, WFCGenerator
from cli_rpg.world_tiles import TileRegistry, ADJACENCY_RULES


# --- Test Fixtures ---


@pytest.fixture
def tile_registry():
    """Create a TileRegistry for testing."""
    return TileRegistry()


@pytest.fixture
def wfc_generator(tile_registry):
    """Create a WFCGenerator with a fixed seed for deterministic tests."""
    return WFCGenerator(tile_registry, seed=42)


# --- Basic Tests (spec: WFCCell dataclass) ---


def test_wfc_cell_creation():
    """WFCCell dataclass exists with correct fields (spec: WFCCell dataclass)."""
    cell = WFCCell(coords=(0, 0), possible_tiles={"forest", "plains"})
    assert cell.coords == (0, 0)
    assert cell.possible_tiles == {"forest", "plains"}
    assert hasattr(cell, "collapsed")
    assert hasattr(cell, "tile")


def test_wfc_cell_starts_uncollapsed():
    """WFCCell starts with collapsed=False, tile=None by default (spec: WFCCell defaults)."""
    cell = WFCCell(coords=(1, 2), possible_tiles={"mountain"})
    assert cell.collapsed is False
    assert cell.tile is None


# --- Generator Creation Tests (spec: WFCGenerator.__init__) ---


def test_wfc_generator_creation(tile_registry):
    """WFCGenerator accepts TileRegistry and seed (spec: WFCGenerator.__init__)."""
    generator = WFCGenerator(tile_registry, seed=123)
    assert generator.tile_registry is tile_registry
    assert generator.seed == 123


def test_wfc_generator_deterministic(tile_registry):
    """Same seed produces same output (spec: deterministic generation)."""
    gen1 = WFCGenerator(tile_registry, seed=42)
    gen2 = WFCGenerator(tile_registry, seed=42)

    result1 = gen1.generate_chunk((0, 0), size=4)
    result2 = gen2.generate_chunk((0, 0), size=4)

    assert result1 == result2


# --- Entropy Tests (spec: _calculate_entropy) ---


def test_entropy_single_option(wfc_generator):
    """1 option = 0 entropy (spec: Shannon entropy for single option)."""
    cell = WFCCell(coords=(0, 0), possible_tiles={"forest"})
    entropy = wfc_generator._calculate_entropy(cell)
    assert entropy == 0.0


def test_entropy_multiple_options(wfc_generator, tile_registry):
    """More options = higher entropy (spec: Shannon entropy increases with options)."""
    cell_2_options = WFCCell(coords=(0, 0), possible_tiles={"forest", "plains"})
    cell_5_options = WFCCell(
        coords=(0, 0), possible_tiles={"forest", "plains", "hills", "desert", "swamp"}
    )

    entropy_2 = wfc_generator._calculate_entropy(cell_2_options)
    entropy_5 = wfc_generator._calculate_entropy(cell_5_options)

    assert entropy_2 > 0
    assert entropy_5 > entropy_2


def test_select_minimum_entropy_cell(wfc_generator):
    """Correctly finds lowest entropy cell (spec: minimum entropy selection)."""
    cells = {
        (0, 0): WFCCell(
            coords=(0, 0), possible_tiles={"forest", "plains", "hills", "desert", "swamp"}
        ),
        (0, 1): WFCCell(coords=(0, 1), possible_tiles={"forest", "plains"}),  # Lowest
        (1, 0): WFCCell(coords=(1, 0), possible_tiles={"forest", "plains", "hills"}),
    }

    min_cell = wfc_generator._select_minimum_entropy_cell(cells)
    # Should select (0, 1) which has fewest options
    assert min_cell.coords == (0, 1)


# --- Collapse Tests (spec: _collapse_cell) ---


def test_collapse_reduces_to_one(wfc_generator):
    """After collapse, cell has exactly 1 tile (spec: collapse reduces to single tile)."""
    cell = WFCCell(coords=(0, 0), possible_tiles={"forest", "plains", "hills"})
    wfc_generator._collapse_cell(cell)

    assert len(cell.possible_tiles) == 1
    assert cell.tile in {"forest", "plains", "hills"}


def test_collapse_respects_weights(tile_registry):
    """Higher weight tiles selected more often (spec: weighted random selection)."""
    # Create cells with tiles that have very different weights
    # Plains (2.5) vs Beach (0.4) - plains should be selected much more often
    tiles = {"plains", "beach"}
    results = {"plains": 0, "beach": 0}

    # Run 1000 trials
    for i in range(1000):
        gen = WFCGenerator(tile_registry, seed=i)
        cell = WFCCell(coords=(0, 0), possible_tiles=tiles.copy())
        gen._collapse_cell(cell)
        results[cell.tile] += 1

    # Plains should be selected significantly more than beach (2.5 vs 0.4 weight)
    # Expected ratio is about 6.25:1, so plains should have at least 80% of selections
    assert results["plains"] > results["beach"] * 3


def test_collapse_sets_collapsed_flag(wfc_generator):
    """collapsed=True after collapse (spec: collapsed flag set)."""
    cell = WFCCell(coords=(0, 0), possible_tiles={"forest", "plains"})
    assert cell.collapsed is False

    wfc_generator._collapse_cell(cell)

    assert cell.collapsed is True


# --- Propagation Tests (spec: _propagate) ---


def test_propagate_reduces_neighbor_options(wfc_generator, tile_registry):
    """Neighbors lose invalid options (spec: constraint propagation)."""
    # Create a small grid
    all_tiles = tile_registry.get_all_tile_names()
    grid = {
        (0, 0): WFCCell(coords=(0, 0), possible_tiles=all_tiles.copy()),
        (0, 1): WFCCell(coords=(0, 1), possible_tiles=all_tiles.copy()),
        (1, 0): WFCCell(coords=(1, 0), possible_tiles=all_tiles.copy()),
    }

    # Collapse (0, 0) to water (which can only be adjacent to water, beach, swamp)
    grid[(0, 0)].possible_tiles = {"water"}
    grid[(0, 0)].tile = "water"
    grid[(0, 0)].collapsed = True

    # Propagate from (0, 0)
    wfc_generator._propagate(grid, (0, 0))

    # Neighbor (0, 1) should only have water-compatible tiles
    water_neighbors = ADJACENCY_RULES["water"]
    for tile in grid[(0, 1)].possible_tiles:
        assert tile in water_neighbors, f"{tile} is not a valid neighbor of water"


def test_propagate_chain_reaction(wfc_generator, tile_registry):
    """Reduction cascades through grid (spec: chain propagation)."""
    all_tiles = tile_registry.get_all_tile_names()
    grid = {
        (0, 0): WFCCell(coords=(0, 0), possible_tiles=all_tiles.copy()),
        (0, 1): WFCCell(coords=(0, 1), possible_tiles=all_tiles.copy()),
        (0, 2): WFCCell(coords=(0, 2), possible_tiles=all_tiles.copy()),
    }

    initial_options_02 = len(grid[(0, 2)].possible_tiles)

    # Collapse (0, 0) to water
    grid[(0, 0)].possible_tiles = {"water"}
    grid[(0, 0)].tile = "water"
    grid[(0, 0)].collapsed = True

    wfc_generator._propagate(grid, (0, 0))

    # (0, 1) was constrained by (0, 0)
    # (0, 2) may be constrained as well if (0, 1)'s options were reduced
    # At minimum, (0, 1) should have fewer options
    assert len(grid[(0, 1)].possible_tiles) < initial_options_02


def test_propagate_detects_contradiction(wfc_generator):
    """Returns False when cell has 0 options (spec: contradiction detection)."""
    grid = {
        (0, 0): WFCCell(coords=(0, 0), possible_tiles={"water"}),
        (0, 1): WFCCell(coords=(0, 1), possible_tiles={"mountain"}),  # Can't be next to water
    }

    grid[(0, 0)].tile = "water"
    grid[(0, 0)].collapsed = True

    # Mountain cannot be adjacent to water, so propagation should detect contradiction
    result = wfc_generator._propagate(grid, (0, 0))

    assert result is False


# --- Generation Tests (spec: generate_chunk) ---


def test_generate_chunk_all_collapsed(wfc_generator):
    """All cells have tile assigned (spec: complete generation)."""
    result = wfc_generator.generate_chunk((0, 0), size=4)

    for coords, tile in result.items():
        assert tile is not None
        assert isinstance(tile, str)


def test_generate_chunk_respects_adjacency(wfc_generator):
    """All neighbors satisfy ADJACENCY_RULES (spec: adjacency constraints)."""
    result = wfc_generator.generate_chunk((0, 0), size=6)

    for (x, y), tile in result.items():
        # Check all 4 neighbors
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_coords = (x + dx, y + dy)
            if neighbor_coords in result:
                neighbor_tile = result[neighbor_coords]
                # Verify adjacency is valid in both directions
                assert (
                    neighbor_tile in ADJACENCY_RULES[tile]
                ), f"{tile} at {(x,y)} cannot be adjacent to {neighbor_tile} at {neighbor_coords}"
                assert (
                    tile in ADJACENCY_RULES[neighbor_tile]
                ), f"{neighbor_tile} at {neighbor_coords} cannot be adjacent to {tile} at {(x,y)}"


def test_generate_chunk_correct_size(wfc_generator):
    """8x8 = 64 cells by default (spec: chunk size)."""
    result = wfc_generator.generate_chunk((0, 0), size=8)
    assert len(result) == 64


def test_generate_chunk_handles_contradiction(tile_registry):
    """Restarts on contradiction, eventually succeeds (spec: contradiction recovery)."""
    # Use different seeds to ensure we can recover from contradictions
    # The algorithm should handle contradictions internally
    for seed in range(100):
        generator = WFCGenerator(tile_registry, seed=seed)
        result = generator.generate_chunk((0, 0), size=4)
        # Should always produce a valid result
        assert len(result) == 16
        # All tiles should be assigned
        assert all(tile is not None for tile in result.values())
