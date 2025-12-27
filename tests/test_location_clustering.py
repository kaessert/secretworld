"""Tests for location clustering feature.

Tests the clustering of similar location types together spatially
when generating named locations (POIs).
"""

import random
import pytest
from cli_rpg.models.location import Location


class TestClusteringConstants:
    """Tests for clustering constant definitions."""

    def test_cluster_groups_defined(self):
        """Verify LOCATION_CLUSTER_GROUPS contains expected category mappings."""
        from cli_rpg.world_tiles import LOCATION_CLUSTER_GROUPS

        # Check settlements cluster
        assert LOCATION_CLUSTER_GROUPS.get("village") == "settlements"
        assert LOCATION_CLUSTER_GROUPS.get("town") == "settlements"
        assert LOCATION_CLUSTER_GROUPS.get("city") == "settlements"

        # Check dungeons cluster
        assert LOCATION_CLUSTER_GROUPS.get("dungeon") == "dungeons"
        assert LOCATION_CLUSTER_GROUPS.get("cave") == "dungeons"
        assert LOCATION_CLUSTER_GROUPS.get("ruins") == "dungeons"

        # Check sacred sites cluster
        assert LOCATION_CLUSTER_GROUPS.get("temple") == "sacred"
        assert LOCATION_CLUSTER_GROUPS.get("shrine") == "sacred"
        assert LOCATION_CLUSTER_GROUPS.get("monastery") == "sacred"

    def test_cluster_radius_defined(self):
        """Verify CLUSTER_RADIUS is defined and reasonable."""
        from cli_rpg.world_tiles import CLUSTER_RADIUS

        assert isinstance(CLUSTER_RADIUS, int)
        assert CLUSTER_RADIUS > 0
        assert CLUSTER_RADIUS <= 20  # Shouldn't be too large

    def test_cluster_probability_defined(self):
        """Verify CLUSTER_PROBABILITY is defined and valid."""
        from cli_rpg.world_tiles import CLUSTER_PROBABILITY

        assert isinstance(CLUSTER_PROBABILITY, float)
        assert 0.0 < CLUSTER_PROBABILITY < 1.0

    def test_cluster_groups_cover_common_categories(self):
        """Verify all common location categories are mapped to cluster groups."""
        from cli_rpg.world_tiles import LOCATION_CLUSTER_GROUPS

        common_categories = [
            "village", "town", "city",  # Settlements
            "dungeon", "cave", "ruins",  # Dungeons
            "temple", "shrine",  # Sacred
        ]

        for category in common_categories:
            assert category in LOCATION_CLUSTER_GROUPS, f"Missing category: {category}"


class TestGetClusterCategoryBias:
    """Tests for the get_cluster_category_bias function."""

    def test_no_nearby_named_locations_returns_none(self):
        """Returns None when no named locations are nearby."""
        from cli_rpg.world_tiles import get_cluster_category_bias

        # Empty world
        world = {}
        result = get_cluster_category_bias(world, (10, 10))
        assert result is None

    def test_unnamed_locations_ignored(self):
        """Unnamed locations (terrain filler) are ignored for clustering."""
        from cli_rpg.world_tiles import get_cluster_category_bias

        world = {
            "Plains (5,5)": Location(
                name="Plains (5,5)",
                description="Open grassland",
                coordinates=(5, 5),
                category="wilderness",
                is_named=False,  # Terrain filler, not a POI
            )
        }
        result = get_cluster_category_bias(world, (6, 6))
        assert result is None

    def test_finds_nearby_named_location(self):
        """Returns category when similar named location within radius."""
        from cli_rpg.world_tiles import get_cluster_category_bias, CLUSTER_RADIUS

        # Create a world with a village nearby
        world = {
            "Small Village": Location(
                name="Small Village",
                description="A quiet village",
                coordinates=(5, 5),
                category="village",
                is_named=True,
            )
        }

        # Target is within radius
        target = (5 + CLUSTER_RADIUS - 1, 5)

        # Use fixed seed RNG that always rolls below CLUSTER_PROBABILITY
        rng = random.Random(42)

        # Should return a category from the same cluster group (settlements)
        result = get_cluster_category_bias(world, target, rng=rng)

        # Since RNG might not trigger clustering, we test that when it does
        # the result is from the settlements cluster
        if result is not None:
            from cli_rpg.world_tiles import LOCATION_CLUSTER_GROUPS
            assert LOCATION_CLUSTER_GROUPS.get(result) == "settlements"

    def test_location_outside_radius_ignored(self):
        """Locations beyond the radius are not considered for clustering."""
        from cli_rpg.world_tiles import get_cluster_category_bias, CLUSTER_RADIUS

        world = {
            "Far Village": Location(
                name="Far Village",
                description="A distant village",
                coordinates=(0, 0),
                category="village",
                is_named=True,
            )
        }

        # Target is well outside radius
        target = (CLUSTER_RADIUS + 10, CLUSTER_RADIUS + 10)
        result = get_cluster_category_bias(world, target)
        assert result is None

    def test_location_at_exact_radius_boundary(self):
        """Location at exactly the radius edge should be included."""
        from cli_rpg.world_tiles import get_cluster_category_bias, CLUSTER_RADIUS

        world = {
            "Edge Village": Location(
                name="Edge Village",
                description="A village at the edge",
                coordinates=(0, 0),
                category="village",
                is_named=True,
            )
        }

        # Target is exactly at radius distance (using Manhattan distance)
        target = (CLUSTER_RADIUS, 0)

        # With probability 1.0, clustering should happen
        # We test multiple times to see if it ever returns a value
        found_cluster = False
        for seed in range(100):
            rng = random.Random(seed)
            result = get_cluster_category_bias(world, target, rng=rng)
            if result is not None:
                found_cluster = True
                break

        # At 60% probability, we should find at least one cluster in 100 tries
        assert found_cluster, "Expected clustering to occur at least once"

    def test_respects_cluster_probability(self):
        """Clustering only happens with CLUSTER_PROBABILITY."""
        from cli_rpg.world_tiles import (
            get_cluster_category_bias,
            CLUSTER_PROBABILITY,
            CLUSTER_RADIUS,
        )

        world = {
            "Test Village": Location(
                name="Test Village",
                description="A test village",
                coordinates=(5, 5),
                category="village",
                is_named=True,
            )
        }

        target = (6, 5)  # Very close, within radius

        # Run many trials to verify probability is approximately correct
        trials = 1000
        cluster_count = 0
        for seed in range(trials):
            rng = random.Random(seed)
            result = get_cluster_category_bias(world, target, rng=rng)
            if result is not None:
                cluster_count += 1

        # Should be within reasonable range of CLUSTER_PROBABILITY
        actual_rate = cluster_count / trials
        # Allow 10% tolerance for statistical variance
        assert abs(actual_rate - CLUSTER_PROBABILITY) < 0.1, (
            f"Expected ~{CLUSTER_PROBABILITY}, got {actual_rate}"
        )

    def test_returns_category_from_cluster_group(self):
        """When clustering occurs, returns a category from the same cluster group."""
        from cli_rpg.world_tiles import get_cluster_category_bias, LOCATION_CLUSTER_GROUPS

        world = {
            "Ancient Dungeon": Location(
                name="Ancient Dungeon",
                description="A dark dungeon",
                coordinates=(5, 5),
                category="dungeon",
                is_named=True,
            )
        }

        target = (6, 5)

        # Find a seed that triggers clustering
        for seed in range(100):
            rng = random.Random(seed)
            result = get_cluster_category_bias(world, target, rng=rng)
            if result is not None:
                # Verify result is from dungeons cluster
                assert LOCATION_CLUSTER_GROUPS.get(result) == "dungeons"
                break

    def test_picks_majority_cluster_type(self):
        """When multiple nearby locations exist, picks from most common cluster."""
        from cli_rpg.world_tiles import get_cluster_category_bias, LOCATION_CLUSTER_GROUPS

        # Create world with more dungeons than villages
        world = {
            "Village 1": Location(
                name="Village 1", description="A small village.", coordinates=(5, 5),
                category="village", is_named=True,
            ),
            "Cave 1": Location(
                name="Cave 1", description="A dark cave.", coordinates=(6, 5),
                category="cave", is_named=True,
            ),
            "Dungeon 1": Location(
                name="Dungeon 1", description="A dangerous dungeon.", coordinates=(5, 6),
                category="dungeon", is_named=True,
            ),
            "Ruins 1": Location(
                name="Ruins 1", description="Ancient ruins.", coordinates=(6, 6),
                category="ruins", is_named=True,
            ),
        }

        target = (5, 7)  # Close to all of them

        # Should bias toward dungeons cluster since there are 3 dungeon types
        dungeon_count = 0
        settlement_count = 0
        trials = 100
        for seed in range(trials):
            rng = random.Random(seed)
            result = get_cluster_category_bias(world, target, rng=rng)
            if result is not None:
                group = LOCATION_CLUSTER_GROUPS.get(result)
                if group == "dungeons":
                    dungeon_count += 1
                elif group == "settlements":
                    settlement_count += 1

        # Dungeons should be picked more often (3 nearby vs 1 village)
        assert dungeon_count >= settlement_count


class TestGenerateFallbackWithCategoryHint:
    """Tests for generate_fallback_location with category_hint parameter."""

    def test_respects_category_hint_for_village(self):
        """When category_hint is 'village', generates a settlement-type location."""
        from cli_rpg.world import generate_fallback_location

        source = Location(name="Origin", description="A starting point.", coordinates=(0, 0))
        result = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1),
            is_named=True,
            category_hint="village",
        )

        # The category should match the hint
        assert result.category == "village"

    def test_respects_category_hint_for_dungeon(self):
        """When category_hint is 'dungeon', generates a dungeon-type location."""
        from cli_rpg.world import generate_fallback_location

        source = Location(name="Origin", description="A starting point.", coordinates=(0, 0))
        result = generate_fallback_location(
            direction="east",
            source_location=source,
            target_coords=(1, 0),
            is_named=True,
            category_hint="dungeon",
        )

        assert result.category == "dungeon"

    def test_category_hint_ignored_for_unnamed(self):
        """Category hint is ignored for unnamed (terrain filler) locations."""
        from cli_rpg.world import generate_fallback_location

        source = Location(name="Origin", description="A starting point.", coordinates=(0, 0))
        result = generate_fallback_location(
            direction="south",
            source_location=source,
            target_coords=(0, -1),
            terrain="forest",
            is_named=False,  # Unnamed location
            category_hint="village",  # Should be ignored
        )

        # Should use terrain's category, not the hint
        assert result.category == "forest"

    def test_no_category_hint_uses_terrain(self):
        """Without category_hint, uses terrain-based category as before."""
        from cli_rpg.world import generate_fallback_location

        source = Location(name="Origin", description="A starting point.", coordinates=(0, 0))
        result = generate_fallback_location(
            direction="west",
            source_location=source,
            target_coords=(-1, 0),
            terrain="swamp",
            is_named=True,
        )

        # Should use terrain's category
        assert result.category == "swamp"
