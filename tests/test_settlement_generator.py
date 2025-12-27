"""Tests for settlement generator module.

Tests the district generation functions for mega-settlements.
"""

import pytest
from random import Random

from cli_rpg.settlement_generator import (
    MEGA_SETTLEMENT_CATEGORIES,
    MEGA_SETTLEMENT_THRESHOLD,
    generate_districts,
    get_district_at_coords,
)
from cli_rpg.models.district import District, DistrictType


class TestMegaSettlementConstants:
    """Tests for settlement generator constants."""

    def test_mega_settlement_categories(self):
        """MEGA_SETTLEMENT_CATEGORIES includes city, metropolis, capital."""
        # Spec: MEGA_SETTLEMENT_CATEGORIES = {"city", "metropolis", "capital"}
        assert "city" in MEGA_SETTLEMENT_CATEGORIES
        assert "metropolis" in MEGA_SETTLEMENT_CATEGORIES
        assert "capital" in MEGA_SETTLEMENT_CATEGORIES
        # Should be exactly these three
        assert len(MEGA_SETTLEMENT_CATEGORIES) == 3

    def test_mega_settlement_threshold(self):
        """MEGA_SETTLEMENT_THRESHOLD is minimum size for districts."""
        # Spec: Minimum size (17x17) to qualify
        assert MEGA_SETTLEMENT_THRESHOLD == 17


class TestGenerateDistricts:
    """Tests for generate_districts function."""

    def test_generate_districts_for_city(self):
        """generate_districts creates 2-4 districts for city-sized settlements."""
        # Spec: generate_districts creates appropriate number of districts
        rng = Random(42)
        bounds = (-8, 8, -8, 8, 0, 0)  # 17x17 city

        districts = generate_districts(bounds, "city", "Ironhaven", rng)

        assert 2 <= len(districts) <= 4
        assert all(isinstance(d, District) for d in districts)

    def test_generate_districts_for_metropolis(self):
        """generate_districts creates 4-6 districts for metropolis."""
        rng = Random(42)
        bounds = (-12, 12, -12, 12, 0, 0)  # 25x25 metropolis

        districts = generate_districts(bounds, "metropolis", "Grandcity", rng)

        assert 4 <= len(districts) <= 6

    def test_generate_districts_for_capital(self):
        """generate_districts creates 5-8 districts for capital."""
        rng = Random(42)
        bounds = (-16, 16, -16, 16, 0, 0)  # 33x33 capital

        districts = generate_districts(bounds, "capital", "Imperial City", rng)

        assert 5 <= len(districts) <= 8

    def test_generate_districts_returns_valid_districts(self):
        """Each generated district has valid attributes."""
        rng = Random(123)
        bounds = (-8, 8, -8, 8, 0, 0)

        districts = generate_districts(bounds, "city", "Testville", rng)

        for district in districts:
            # Check required fields
            assert district.name
            assert isinstance(district.district_type, DistrictType)
            assert district.description
            assert len(district.bounds) == 4
            # Check optional fields have valid values
            assert district.atmosphere
            assert district.prosperity
            assert isinstance(district.notable_features, list)

    def test_generate_districts_covers_bounds(self):
        """Districts cover the settlement bounds without gaps."""
        # Spec: Districts cover the settlement bounds without gaps
        rng = Random(42)
        bounds = (-8, 8, -8, 8, 0, 0)
        min_x, max_x, min_y, max_y, _, _ = bounds

        districts = generate_districts(bounds, "city", "Coverton", rng)

        # Check that each corner of the settlement is covered by some district
        corners = [
            (min_x, min_y),
            (min_x, max_y),
            (max_x, min_y),
            (max_x, max_y),
            (0, 0),  # Center
        ]

        for x, y in corners:
            found = any(d.contains(x, y) for d in districts)
            assert found, f"Point ({x}, {y}) not covered by any district"

    def test_generate_districts_no_type_duplicates(self):
        """Districts have unique types (no duplicate district types)."""
        rng = Random(42)
        bounds = (-8, 8, -8, 8, 0, 0)

        districts = generate_districts(bounds, "city", "Uniquetown", rng)

        types = [d.district_type for d in districts]
        assert len(types) == len(set(types)), "District types should be unique"

    def test_generate_districts_deterministic(self):
        """Same RNG seed produces same district layout."""
        # Spec: Same RNG seed produces same district layout
        bounds = (-8, 8, -8, 8, 0, 0)

        rng1 = Random(999)
        districts1 = generate_districts(bounds, "city", "Seedtown", rng1)

        rng2 = Random(999)
        districts2 = generate_districts(bounds, "city", "Seedtown", rng2)

        assert len(districts1) == len(districts2)
        for d1, d2 in zip(districts1, districts2):
            assert d1.name == d2.name
            assert d1.district_type == d2.district_type
            assert d1.bounds == d2.bounds
            assert d1.atmosphere == d2.atmosphere
            assert d1.prosperity == d2.prosperity

    def test_generate_districts_uses_settlement_name(self):
        """District names may incorporate settlement name."""
        rng = Random(42)
        bounds = (-8, 8, -8, 8, 0, 0)

        districts = generate_districts(bounds, "city", "Goldbrook", rng)

        # At least one district should reference the settlement name
        # (depending on templates selected)
        # This is a soft check - just verify districts are named
        assert all(d.name for d in districts)


class TestGetDistrictAtCoords:
    """Tests for get_district_at_coords function."""

    def test_get_district_at_coords_inside(self):
        """get_district_at_coords returns correct district for given coordinates."""
        # Spec: get_district_at_coords returns correct district
        market = District(
            name="Market",
            district_type=DistrictType.MARKET,
            description="Market area",
            bounds=(-8, -1, -8, -1),
        )
        temple = District(
            name="Temple",
            district_type=DistrictType.TEMPLE,
            description="Temple area",
            bounds=(0, 8, 0, 8),
        )
        districts = [market, temple]

        result = get_district_at_coords(districts, -4, -4)
        assert result == market

        result = get_district_at_coords(districts, 4, 4)
        assert result == temple

    def test_get_district_at_coords_boundary(self):
        """get_district_at_coords works on district boundaries."""
        district = District(
            name="Test",
            district_type=DistrictType.RESIDENTIAL,
            description="Test",
            bounds=(0, 5, 0, 5),
        )
        districts = [district]

        # On boundary
        assert get_district_at_coords(districts, 0, 0) == district
        assert get_district_at_coords(districts, 5, 5) == district
        assert get_district_at_coords(districts, 0, 5) == district
        assert get_district_at_coords(districts, 5, 0) == district

    def test_get_district_at_coords_outside_bounds(self):
        """get_district_at_coords returns None for coords outside all districts."""
        # Spec: Returns None for coords outside all districts
        district = District(
            name="Test",
            district_type=DistrictType.RESIDENTIAL,
            description="Test",
            bounds=(0, 5, 0, 5),
        )
        districts = [district]

        result = get_district_at_coords(districts, -1, 0)
        assert result is None

        result = get_district_at_coords(districts, 6, 3)
        assert result is None

        result = get_district_at_coords(districts, 100, 100)
        assert result is None

    def test_get_district_at_coords_empty_list(self):
        """get_district_at_coords returns None for empty district list."""
        result = get_district_at_coords([], 0, 0)
        assert result is None

    def test_get_district_at_coords_first_match(self):
        """get_district_at_coords returns first matching district if overlapping."""
        # Edge case: overlapping districts (shouldn't happen in practice)
        d1 = District(
            name="First",
            district_type=DistrictType.MARKET,
            description="First",
            bounds=(0, 5, 0, 5),
        )
        d2 = District(
            name="Second",
            district_type=DistrictType.TEMPLE,
            description="Second",
            bounds=(0, 5, 0, 5),  # Same bounds
        )

        result = get_district_at_coords([d1, d2], 2, 2)
        assert result == d1  # First match


class TestDistrictGeneration:
    """Integration tests for district generation."""

    def test_full_city_generation(self):
        """Full test of city district generation and lookup."""
        rng = Random(42)
        bounds = (-8, 8, -8, 8, 0, 0)

        districts = generate_districts(bounds, "city", "Testopolis", rng)

        # Should have districts
        assert len(districts) >= 2

        # Each district should be locatable
        for district in districts:
            min_x, max_x, min_y, max_y = district.bounds
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2

            found = get_district_at_coords(districts, center_x, center_y)
            assert found is not None
            assert found.contains(center_x, center_y)
