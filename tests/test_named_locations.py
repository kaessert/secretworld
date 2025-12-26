"""Tests for the named vs unnamed location system.

Tests that:
- Location.is_named field defaults to False
- Serialization (to_dict/from_dict) preserves is_named
- Named location triggers work based on tile count and terrain type
- Fallback generation creates unnamed locations by default
"""

import pytest
import random

from cli_rpg.models.location import Location


class TestLocationIsNamedField:
    """Tests for the Location.is_named field."""

    def test_location_is_named_defaults_false(self):
        """Location.is_named defaults to False."""
        loc = Location(
            name="Test Location",
            description="A test location description."
        )
        assert loc.is_named is False

    def test_location_is_named_can_be_set_true(self):
        """Location.is_named can be explicitly set to True."""
        loc = Location(
            name="Named POI",
            description="A named point of interest.",
            is_named=True
        )
        assert loc.is_named is True

    def test_location_serialization_with_is_named_true(self):
        """is_named=True survives to_dict/from_dict round-trip."""
        loc = Location(
            name="Named Location",
            description="A named location.",
            is_named=True,
            coordinates=(10, 20)
        )
        data = loc.to_dict()
        restored = Location.from_dict(data)
        assert restored.is_named is True

    def test_location_serialization_with_is_named_false(self):
        """is_named=False survives to_dict/from_dict round-trip (default)."""
        loc = Location(
            name="Unnamed Location",
            description="An unnamed location.",
            is_named=False,
            coordinates=(5, 5)
        )
        data = loc.to_dict()
        restored = Location.from_dict(data)
        assert restored.is_named is False

    def test_location_serialization_without_is_named_key(self):
        """Deserializing old data without is_named key defaults to False."""
        data = {
            "name": "Old Location",
            "description": "A location from before is_named was added.",
            "connections": {}
        }
        loc = Location.from_dict(data)
        assert loc.is_named is False


class TestShouldGenerateNamedLocation:
    """Tests for the named location trigger logic."""

    def test_should_generate_named_zero_tiles(self):
        """At 0 tiles since named, probability is very low (near 0%)."""
        from cli_rpg.world_tiles import should_generate_named_location

        rng = random.Random(42)
        # With 0 tiles since named, probability should be 0
        result = should_generate_named_location(0, "plains", rng)
        assert result is False

    def test_should_generate_named_at_interval(self):
        """At the base interval, probability is around 50%."""
        from cli_rpg.world_tiles import (
            should_generate_named_location,
            NAMED_LOCATION_CONFIG
        )

        base_interval = NAMED_LOCATION_CONFIG["base_interval"]

        # Run many trials at the interval point
        successes = 0
        trials = 1000
        for i in range(trials):
            rng = random.Random(i)  # Different seed each trial
            if should_generate_named_location(base_interval, "plains", rng):
                successes += 1

        # At interval, probability should be around 50% (tolerance for randomness)
        assert 0.30 < successes / trials < 0.70

    def test_should_generate_named_at_double_interval(self):
        """At 2x the interval, probability is 100%."""
        from cli_rpg.world_tiles import (
            should_generate_named_location,
            NAMED_LOCATION_CONFIG
        )

        base_interval = NAMED_LOCATION_CONFIG["base_interval"]
        double_interval = base_interval * 2

        rng = random.Random(42)
        result = should_generate_named_location(double_interval, "plains", rng)
        assert result is True

    def test_should_generate_named_mountain_terrain_more_likely(self):
        """Mountain terrain has higher named location chance (lower modifier)."""
        from cli_rpg.world_tiles import (
            should_generate_named_location,
            NAMED_LOCATION_CONFIG
        )

        base_interval = NAMED_LOCATION_CONFIG["base_interval"]

        # Mountain has modifier 0.6, so effective interval is 9 tiles (at base 15)
        # At 10 tiles, mountain should have higher probability than plains
        tiles = 10

        mountain_successes = 0
        plains_successes = 0
        trials = 1000

        for i in range(trials):
            rng = random.Random(i)
            if should_generate_named_location(tiles, "mountain", rng):
                mountain_successes += 1

            rng = random.Random(i)
            if should_generate_named_location(tiles, "plains", rng):
                plains_successes += 1

        # Mountain should have more successes than plains
        assert mountain_successes > plains_successes

    def test_should_generate_named_water_never(self):
        """Water terrain should never generate named locations."""
        from cli_rpg.world_tiles import should_generate_named_location

        # Even at very high tile count, water should never trigger
        rng = random.Random(42)
        result = should_generate_named_location(1000, "water", rng)
        assert result is False


class TestFallbackLocationCreatesUnnamed:
    """Tests that generate_fallback_location creates unnamed locations."""

    def test_fallback_creates_unnamed_location(self):
        """generate_fallback_location creates unnamed locations by default."""
        from cli_rpg.world import generate_fallback_location

        source = Location(
            name="Origin",
            description="Starting point.",
            coordinates=(0, 0)
        )

        # Create a fallback location (no tiles_since_named, defaults to 0)
        new_loc = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1),
            terrain="forest"
        )

        # Should be unnamed by default
        assert new_loc.is_named is False

    def test_fallback_location_has_terrain(self):
        """Fallback location should have terrain field set."""
        from cli_rpg.world import generate_fallback_location

        source = Location(
            name="Origin",
            description="Starting point.",
            coordinates=(0, 0)
        )

        new_loc = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1),
            terrain="plains"
        )

        assert new_loc.terrain == "plains"
