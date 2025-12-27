"""Tests for terrain-biased WFC generation.

These tests verify that WFC chunk generation respects region themes
to create coherent mega-biomes (e.g., mountain regions generate mostly
mountain/foothills/hills terrain).

Tests the spec:
- get_biased_weights() returns modified weights based on region theme
- WFCGenerator accepts weight_overrides parameter
- ChunkManager passes bias to generator via region context
- Statistical tests verify biased terrain distribution
- Biased generation still respects adjacency rules
"""

import pytest
from collections import Counter

from cli_rpg.world_tiles import (
    TERRAIN_WEIGHTS,
    TileRegistry,
    ADJACENCY_RULES,
    get_biased_weights,
    REGION_TERRAIN_BIASES,
)
from cli_rpg.wfc import WFCGenerator
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.models.region_context import RegionContext


class TestGetBiasedWeights:
    """Tests for get_biased_weights() function in world_tiles.py."""

    def test_get_biased_weights_returns_modified_weights(self):
        """Test 1: get_biased_weights("mountains") returns dict with mountain/foothills/hills at 3x base weight.

        Spec: When generating a chunk, WFC should apply terrain biases based on the region's
        theme/terrain_hint. A "mountains" region should have 3-4x weight for mountain/foothills/hills
        tiles and reduced weights for incompatible terrain like beach/swamp.
        """
        biased = get_biased_weights("mountains")

        # Mountain-family terrain should be boosted (3x)
        assert biased["mountain"] == pytest.approx(TERRAIN_WEIGHTS["mountain"] * 3.0)
        assert biased["foothills"] == pytest.approx(TERRAIN_WEIGHTS["foothills"] * 3.0)
        assert biased["hills"] == pytest.approx(TERRAIN_WEIGHTS["hills"] * 3.0)

        # Incompatible terrain should be reduced (0.3x)
        assert biased["beach"] == pytest.approx(TERRAIN_WEIGHTS["beach"] * 0.3)
        assert biased["swamp"] == pytest.approx(TERRAIN_WEIGHTS["swamp"] * 0.3)
        assert biased["desert"] == pytest.approx(TERRAIN_WEIGHTS["desert"] * 0.3)

        # Normal terrain unchanged (1x)
        assert biased["plains"] == pytest.approx(TERRAIN_WEIGHTS["plains"] * 1.0)
        assert biased["forest"] == pytest.approx(TERRAIN_WEIGHTS["forest"] * 1.0)

    def test_get_biased_weights_unknown_theme_returns_base(self):
        """Test 2: Unknown theme returns unmodified base weights.

        Spec: Graceful fallback - if region theme is unknown, return base TERRAIN_WEIGHTS.
        """
        biased = get_biased_weights("unknown_theme_xyz")

        # Should return same values as base weights
        for terrain, weight in TERRAIN_WEIGHTS.items():
            assert biased[terrain] == pytest.approx(weight)

    def test_get_biased_weights_forest_theme(self):
        """Additional test for forest theme bias mapping."""
        biased = get_biased_weights("forest")

        # Forest boosted
        assert biased["forest"] == pytest.approx(TERRAIN_WEIGHTS["forest"] * 3.0)

        # Normal
        assert biased["plains"] == pytest.approx(TERRAIN_WEIGHTS["plains"] * 1.0)
        assert biased["hills"] == pytest.approx(TERRAIN_WEIGHTS["hills"] * 1.0)
        assert biased["swamp"] == pytest.approx(TERRAIN_WEIGHTS["swamp"] * 1.0)

        # Reduced
        assert biased["mountain"] == pytest.approx(TERRAIN_WEIGHTS["mountain"] * 0.3)
        assert biased["desert"] == pytest.approx(TERRAIN_WEIGHTS["desert"] * 0.3)
        assert biased["beach"] == pytest.approx(TERRAIN_WEIGHTS["beach"] * 0.3)


class TestWFCGeneratorWeightOverrides:
    """Tests for WFCGenerator weight_overrides parameter."""

    def test_wfc_generator_accepts_tile_weight_overrides(self):
        """Test 3: WFCGenerator can accept custom weights that override registry defaults.

        Spec: Add optional weight_overrides: Optional[Dict[str, float]] = None
        parameter to __init__. In _collapse_cell(), use overrides when available
        instead of registry weights.
        """
        registry = TileRegistry()

        # Create weight overrides that heavily favor mountains
        weight_overrides = {
            "mountain": 100.0,  # Very high weight
            "plains": 0.01,  # Very low weight
            "forest": 0.01,
            "hills": 0.01,
            "foothills": 0.01,
            "beach": 0.01,
            "swamp": 0.01,
            "desert": 0.01,
            "water": 0.01,
        }

        # Create generator with overrides
        generator = WFCGenerator(registry, seed=42, weight_overrides=weight_overrides)

        # Generate a chunk
        chunk = generator.generate_chunk((0, 0), size=4)

        # Count terrain types
        terrain_counts = Counter(chunk.values())

        # With extremely skewed weights, mountain should dominate
        # (adjacent cells may force some non-mountain due to adjacency rules,
        # but mountain should still be the most common)
        most_common = terrain_counts.most_common(1)[0]
        assert most_common[0] == "mountain", (
            f"Expected mountain to be most common, got {most_common[0]} "
            f"(counts: {terrain_counts})"
        )


class TestChunkManagerRegionContext:
    """Tests for ChunkManager region context integration."""

    def test_chunk_manager_passes_bias_to_generator(self):
        """Test 4: ChunkManager passes region bias when generating new chunks.

        Spec: Add optional region_context: Optional[RegionContext] = None field.
        Add set_region_context(region: RegionContext) method.
        In _generate_chunk(), compute biased weights from region context and pass
        to WFCGenerator.
        """
        registry = TileRegistry()
        manager = ChunkManager(tile_registry=registry, world_seed=123)

        # Create a mountain region context
        region_ctx = RegionContext(
            name="Iron Peaks",
            theme="mountains",
            danger_level="dangerous",
            landmarks=["Mount Doom"],
            coordinates=(0, 0),
        )

        # Set region context
        manager.set_region_context(region_ctx)

        # Generate a chunk - should use biased weights
        chunk = manager.get_or_generate_chunk(0, 0)

        # Verify we got a valid chunk (basic sanity check)
        assert len(chunk) == manager.chunk_size * manager.chunk_size

        # Count mountain-family terrain
        terrain_counts = Counter(chunk.values())
        mountain_family = (
            terrain_counts.get("mountain", 0)
            + terrain_counts.get("foothills", 0)
            + terrain_counts.get("hills", 0)
        )

        # With mountain bias, expect more mountain-family terrain than baseline
        # (baseline is ~15%, we expect >30% with bias)
        total_tiles = sum(terrain_counts.values())
        mountain_family_ratio = mountain_family / total_tiles
        assert mountain_family_ratio > 0.25, (
            f"Expected >25% mountain-family terrain with mountains bias, "
            f"got {mountain_family_ratio:.1%} (counts: {terrain_counts})"
        )


class TestStatisticalTerrainDistribution:
    """Statistical tests for biased terrain generation."""

    def test_mountain_region_generates_more_mountains(self):
        """Test 5: Statistical test - chunk in "mountains" region has >40% mountain-family tiles.

        Spec: A "mountains" region should have 3-4x weight for mountain/foothills/hills tiles.
        Run multiple trials to account for RNG variance.
        """
        registry = TileRegistry()

        # Track mountain-family ratio across multiple seeds
        mountain_family_ratios = []

        for seed in range(10):  # 10 trials
            manager = ChunkManager(tile_registry=registry, world_seed=seed)

            region_ctx = RegionContext(
                name="Mountain Region",
                theme="mountains",
                danger_level="moderate",
                landmarks=[],
                coordinates=(0, 0),
            )
            manager.set_region_context(region_ctx)

            chunk = manager.get_or_generate_chunk(0, 0)

            terrain_counts = Counter(chunk.values())
            mountain_family = (
                terrain_counts.get("mountain", 0)
                + terrain_counts.get("foothills", 0)
                + terrain_counts.get("hills", 0)
            )
            total = sum(terrain_counts.values())
            mountain_family_ratios.append(mountain_family / total)

        # Average ratio should be >40%
        avg_ratio = sum(mountain_family_ratios) / len(mountain_family_ratios)
        assert avg_ratio > 0.40, (
            f"Expected avg >40% mountain-family terrain in mountain regions, "
            f"got {avg_ratio:.1%} (ratios: {[f'{r:.1%}' for r in mountain_family_ratios]})"
        )

    def test_forest_region_generates_more_forest(self):
        """Test 6: Statistical test - chunk in "forest" region has >50% forest tiles.

        Spec: Forest regions should heavily favor forest terrain.
        """
        registry = TileRegistry()

        forest_ratios = []

        for seed in range(10):  # 10 trials
            manager = ChunkManager(tile_registry=registry, world_seed=seed)

            region_ctx = RegionContext(
                name="Dark Woods",
                theme="forest",
                danger_level="moderate",
                landmarks=[],
                coordinates=(0, 0),
            )
            manager.set_region_context(region_ctx)

            chunk = manager.get_or_generate_chunk(0, 0)

            terrain_counts = Counter(chunk.values())
            forest_count = terrain_counts.get("forest", 0)
            total = sum(terrain_counts.values())
            forest_ratios.append(forest_count / total)

        # Average ratio should be >50%
        avg_ratio = sum(forest_ratios) / len(forest_ratios)
        assert avg_ratio > 0.50, (
            f"Expected avg >50% forest terrain in forest regions, "
            f"got {avg_ratio:.1%} (ratios: {[f'{r:.1%}' for r in forest_ratios]})"
        )


class TestAdjacencyRulesRespected:
    """Tests verifying biased generation maintains valid adjacency."""

    def test_bias_respects_adjacency_rules(self):
        """Test 7: Biased generation still produces valid terrain (all tiles have valid neighbors).

        Spec: Even with terrain biases, the WFC algorithm must still respect
        ADJACENCY_RULES to produce coherent terrain.
        """
        registry = TileRegistry()

        # Test with extreme bias (mountains)
        manager = ChunkManager(tile_registry=registry, world_seed=42)

        region_ctx = RegionContext(
            name="Extreme Mountains",
            theme="mountains",
            danger_level="deadly",
            landmarks=[],
            coordinates=(0, 0),
        )
        manager.set_region_context(region_ctx)

        chunk = manager.get_or_generate_chunk(0, 0)

        # Check every tile has valid neighbors
        for (x, y), terrain in chunk.items():
            valid_neighbors = ADJACENCY_RULES.get(terrain, set())

            # Check all 4 cardinal neighbors (if they exist in chunk)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_coords = (x + dx, y + dy)
                if neighbor_coords in chunk:
                    neighbor_terrain = chunk[neighbor_coords]
                    assert neighbor_terrain in valid_neighbors, (
                        f"Invalid adjacency at {(x, y)}: {terrain} cannot be "
                        f"adjacent to {neighbor_terrain} at {neighbor_coords}"
                    )

    def test_bias_respects_adjacency_for_all_themes(self):
        """Verify adjacency rules for all defined region themes."""
        registry = TileRegistry()

        for theme in REGION_TERRAIN_BIASES.keys():
            manager = ChunkManager(tile_registry=registry, world_seed=99)

            region_ctx = RegionContext(
                name=f"Test {theme.title()} Region",
                theme=theme,
                danger_level="moderate",
                landmarks=[],
                coordinates=(0, 0),
            )
            manager.set_region_context(region_ctx)

            # Clear chunk cache for fresh generation each time
            manager._chunks.clear()

            chunk = manager.get_or_generate_chunk(0, 0)

            # Validate adjacencies
            for (x, y), terrain in chunk.items():
                valid_neighbors = ADJACENCY_RULES.get(terrain, set())

                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    neighbor_coords = (x + dx, y + dy)
                    if neighbor_coords in chunk:
                        neighbor_terrain = chunk[neighbor_coords]
                        assert neighbor_terrain in valid_neighbors, (
                            f"Theme '{theme}': Invalid adjacency at {(x, y)}: "
                            f"{terrain} cannot be adjacent to {neighbor_terrain}"
                        )
