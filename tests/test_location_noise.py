"""Tests for location_noise.py - Pure-Python simplex noise for location density.

Tests the SimplexNoise and LocationNoiseManager classes per spec in thoughts/current_plan.md.
"""

import pytest

from cli_rpg.location_noise import SimplexNoise, LocationNoiseManager


class TestSimplexNoise:
    """Tests for SimplexNoise class."""

    # Test 1: noise2d returns value in [-1, 1]
    def test_simplex_returns_float_in_range(self):
        """noise2d should return a float value in the range [-1, 1]."""
        noise = SimplexNoise(seed=42)

        # Test multiple coordinates
        test_coords = [
            (0.0, 0.0),
            (1.5, 2.3),
            (-10.0, 5.0),
            (100.5, -50.2),
            (0.001, 0.001),
        ]

        for x, y in test_coords:
            value = noise.noise2d(x, y)
            assert isinstance(value, float), f"Expected float, got {type(value)}"
            assert -1.0 <= value <= 1.0, f"Value {value} out of range [-1, 1] at ({x}, {y})"

    # Test 2: Same seed + coords = same value (determinism)
    def test_simplex_deterministic_same_seed(self):
        """Same seed and coordinates should produce identical values."""
        noise1 = SimplexNoise(seed=12345)
        noise2 = SimplexNoise(seed=12345)

        test_coords = [(0.0, 0.0), (5.5, 3.2), (-7.1, 8.9)]

        for x, y in test_coords:
            val1 = noise1.noise2d(x, y)
            val2 = noise2.noise2d(x, y)
            assert val1 == val2, f"Values differ for same seed at ({x}, {y}): {val1} vs {val2}"

    # Test 3: Different seeds produce different values
    def test_simplex_different_seeds_differ(self):
        """Different seeds should produce different noise patterns."""
        noise1 = SimplexNoise(seed=111)
        noise2 = SimplexNoise(seed=222)

        # Test at multiple points - at least some should differ
        differences_found = 0
        test_coords = [(0.0, 0.0), (1.0, 1.0), (5.5, 3.2), (10.0, 10.0)]

        for x, y in test_coords:
            val1 = noise1.noise2d(x, y)
            val2 = noise2.noise2d(x, y)
            if val1 != val2:
                differences_found += 1

        assert differences_found > 0, "Different seeds should produce different patterns"

    # Test 4: Adjacent coords produce different values
    def test_simplex_varies_with_position(self):
        """Adjacent coordinates should produce different values."""
        noise = SimplexNoise(seed=42)

        # Values at different positions should generally differ
        val_origin = noise.noise2d(0.0, 0.0)
        val_right = noise.noise2d(1.0, 0.0)
        val_up = noise.noise2d(0.0, 1.0)
        val_diagonal = noise.noise2d(1.0, 1.0)

        values = [val_origin, val_right, val_up, val_diagonal]
        unique_values = set(values)

        # At least 2 unique values (highly likely with noise)
        assert len(unique_values) >= 2, "Noise should vary with position"

    # Test 5: Nearby coords have similar values (continuity/smoothness)
    def test_simplex_gradient_smoothness(self):
        """Nearby coordinates should have similar values (continuity)."""
        noise = SimplexNoise(seed=42)

        # Check that small steps produce small changes
        base_val = noise.noise2d(5.0, 5.0)

        small_step = 0.01
        nearby_val = noise.noise2d(5.0 + small_step, 5.0 + small_step)

        # Small step should produce small change (< 0.5 is reasonable for very small step)
        difference = abs(base_val - nearby_val)
        assert difference < 0.5, f"Nearby values should be similar, got diff={difference}"


class TestLocationNoiseManager:
    """Tests for LocationNoiseManager class."""

    # Test 6: get_location_density returns [0, 1]
    def test_density_returns_float_in_range(self):
        """get_location_density should return a float in [0, 1]."""
        manager = LocationNoiseManager(world_seed=42)

        test_coords = [(0, 0), (10, -5), (-100, 50), (1000, 1000)]

        for x, y in test_coords:
            density = manager.get_location_density(x, y)
            assert isinstance(density, float), f"Expected float, got {type(density)}"
            assert 0.0 <= density <= 1.0, f"Density {density} out of range [0, 1] at ({x}, {y})"

    # Test 7: Same seed = same density map (determinism)
    def test_density_deterministic_same_seed(self):
        """Same world seed should produce identical density values."""
        manager1 = LocationNoiseManager(world_seed=99999)
        manager2 = LocationNoiseManager(world_seed=99999)

        test_coords = [(0, 0), (25, -13), (-7, 88)]

        for x, y in test_coords:
            d1 = manager1.get_location_density(x, y)
            d2 = manager2.get_location_density(x, y)
            assert d1 == d2, f"Density differs for same seed at ({x}, {y}): {d1} vs {d2}"

    # Test 8: Different coords produce different densities
    def test_density_varies_spatially(self):
        """Different coordinates should produce different density values."""
        manager = LocationNoiseManager(world_seed=42)

        densities = [
            manager.get_location_density(0, 0),
            manager.get_location_density(10, 0),
            manager.get_location_density(0, 10),
            manager.get_location_density(50, 50),
        ]

        unique = set(densities)
        assert len(unique) >= 2, "Density should vary spatially"

    # Test 9: High density = higher spawn chance
    def test_should_spawn_respects_density(self):
        """Higher density areas should have higher spawn probability."""
        manager = LocationNoiseManager(world_seed=42)

        # Collect coordinates grouped by density level
        high_density_coords = []  # density > 0.7
        low_density_coords = []   # density < 0.3

        for x in range(-100, 100):
            for y in range(-100, 100):
                d = manager.get_location_density(x, y)
                if d > 0.7:
                    high_density_coords.append((x, y))
                elif d < 0.3:
                    low_density_coords.append((x, y))

        # Need enough samples for statistical comparison
        assert len(high_density_coords) > 100, "Need enough high-density samples"
        assert len(low_density_coords) > 100, "Need enough low-density samples"

        # Count spawns across different coordinates (deterministic per coord)
        high_spawns = sum(
            1 for x, y in high_density_coords[:500]
            if manager.should_spawn_location(x, y, "plains")
        )
        low_spawns = sum(
            1 for x, y in low_density_coords[:500]
            if manager.should_spawn_location(x, y, "plains")
        )

        # High density areas should spawn more often than low density areas
        assert high_spawns > low_spawns, f"High density should spawn more: {high_spawns} vs {low_spawns}"

    # Test 10: Mountain terrain increases spawn chance
    def test_should_spawn_terrain_modifiers(self):
        """Mountain terrain should increase spawn probability vs plains."""
        manager = LocationNoiseManager(world_seed=42)

        # Test across many coordinates to observe probability difference
        # Mountain has 0.6 modifier (more likely), plains has 1.2 (less likely)
        coords = [(x, y) for x in range(-50, 50) for y in range(-50, 50)]

        mountain_spawns = sum(
            1 for x, y in coords
            if manager.should_spawn_location(x, y, "mountain")
        )
        plains_spawns = sum(
            1 for x, y in coords
            if manager.should_spawn_location(x, y, "plains")
        )

        # Mountain should spawn more often due to lower modifier (0.6 vs 1.2)
        assert mountain_spawns > plains_spawns, (
            f"Mountain should spawn more than plains: {mountain_spawns} vs {plains_spawns}"
        )

    # Test 11: Same inputs = same result (determinism)
    def test_should_spawn_deterministic(self):
        """Same inputs should produce the same spawn decision."""
        manager1 = LocationNoiseManager(world_seed=42)
        manager2 = LocationNoiseManager(world_seed=42)

        # Test multiple coordinates and terrains
        test_cases = [
            (0, 0, "plains"),
            (10, -5, "mountain"),
            (-7, 8, "forest"),
        ]

        for x, y, terrain in test_cases:
            result1 = manager1.should_spawn_location(x, y, terrain)
            result2 = manager2.should_spawn_location(x, y, terrain)
            assert result1 == result2, f"Spawn decision differs at ({x}, {y}, {terrain})"

    # Test 12: Adjacent tiles have similar density (clustering)
    def test_clustering_nearby_coords_similar(self):
        """Adjacent tiles should have similar density values (clustering effect)."""
        manager = LocationNoiseManager(world_seed=42)

        # Sample a 3x3 area and check variance is low
        center_x, center_y = 25, 25
        densities = []

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                densities.append(manager.get_location_density(center_x + dx, center_y + dy))

        # Check that variance is reasonable (densities are similar)
        mean_density = sum(densities) / len(densities)
        variance = sum((d - mean_density) ** 2 for d in densities) / len(densities)

        # Variance should be relatively low for adjacent cells (< 0.1 is reasonable)
        # This tests the smoothness/clustering property
        assert variance < 0.1, f"Adjacent densities should be similar, variance={variance}"
