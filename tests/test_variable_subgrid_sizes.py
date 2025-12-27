"""Tests for variable SubGrid sizes based on location category."""

import pytest
from cli_rpg.world_grid import SUBGRID_BOUNDS, get_subgrid_bounds, SubGrid


class TestSubGridBoundsConfig:
    """Tests for SUBGRID_BOUNDS configuration dict."""

    def test_bounds_config_has_default(self):
        """SUBGRID_BOUNDS must have a 'default' entry."""
        assert "default" in SUBGRID_BOUNDS

    def test_bounds_config_has_town(self):
        """Town should have large 11x11 bounds (single level)."""
        # 6-tuple: (min_x, max_x, min_y, max_y, min_z, max_z)
        assert SUBGRID_BOUNDS["town"] == (-5, 5, -5, 5, 0, 0)

    def test_bounds_config_has_dungeon(self):
        """Dungeon should have medium 7x7 bounds with multi-level down."""
        # 6-tuple: (min_x, max_x, min_y, max_y, min_z, max_z)
        assert SUBGRID_BOUNDS["dungeon"] == (-3, 3, -3, 3, -2, 0)

    def test_bounds_config_has_cave(self):
        """Cave should have tiny 3x3 bounds with one level down."""
        # 6-tuple: (min_x, max_x, min_y, max_y, min_z, max_z)
        assert SUBGRID_BOUNDS["cave"] == (-1, 1, -1, 1, -1, 0)

    def test_bounds_config_has_city(self):
        """City should have huge 17x17 bounds (single level)."""
        # 6-tuple: (min_x, max_x, min_y, max_y, min_z, max_z)
        assert SUBGRID_BOUNDS["city"] == (-8, 8, -8, 8, 0, 0)

    def test_bounds_config_has_house(self):
        """House should have tiny 3x3 bounds (single level)."""
        # 6-tuple: (min_x, max_x, min_y, max_y, min_z, max_z)
        assert SUBGRID_BOUNDS["house"] == (-1, 1, -1, 1, 0, 0)


class TestGetSubgridBounds:
    """Tests for get_subgrid_bounds() helper function."""

    def test_returns_default_for_none(self):
        """None category should return default bounds (6-tuple)."""
        assert get_subgrid_bounds(None) == (-2, 2, -2, 2, 0, 0)

    def test_returns_town_bounds(self):
        """Town category should return large bounds (6-tuple)."""
        assert get_subgrid_bounds("town") == (-5, 5, -5, 5, 0, 0)

    def test_returns_dungeon_bounds(self):
        """Dungeon category should return medium bounds with multi-level down (6-tuple)."""
        assert get_subgrid_bounds("dungeon") == (-3, 3, -3, 3, -2, 0)

    def test_returns_city_bounds(self):
        """City category should return huge bounds (6-tuple)."""
        assert get_subgrid_bounds("city") == (-8, 8, -8, 8, 0, 0)

    def test_case_insensitive(self):
        """Category lookup should be case-insensitive."""
        assert get_subgrid_bounds("TOWN") == (-5, 5, -5, 5, 0, 0)
        assert get_subgrid_bounds("Town") == (-5, 5, -5, 5, 0, 0)
        assert get_subgrid_bounds("ToWn") == (-5, 5, -5, 5, 0, 0)

    def test_returns_default_for_unknown(self):
        """Unknown category should return default bounds (6-tuple)."""
        assert get_subgrid_bounds("unknown_category") == (-2, 2, -2, 2, 0, 0)
        assert get_subgrid_bounds("xyz123") == (-2, 2, -2, 2, 0, 0)

    def test_all_configured_categories_return_valid_bounds(self):
        """All configured categories should return valid 6-tuple bounds."""
        for category in SUBGRID_BOUNDS:
            bounds = get_subgrid_bounds(category)
            assert len(bounds) == 6
            min_x, max_x, min_y, max_y, min_z, max_z = bounds
            assert min_x <= max_x, f"{category}: min_x should be <= max_x"
            assert min_y <= max_y, f"{category}: min_y should be <= max_y"
            assert min_z <= max_z, f"{category}: min_z should be <= max_z"


class TestSubGridWithVariableBounds:
    """Integration tests for SubGrid with variable bounds."""

    def test_subgrid_respects_tiny_bounds(self):
        """SubGrid with tiny bounds should reject out-of-bounds coordinates."""
        from cli_rpg.models.location import Location

        bounds = get_subgrid_bounds("cave")  # 3x3
        subgrid = SubGrid(bounds=bounds, parent_name="Cave Entrance")

        # Valid placement at (0, 0)
        loc = Location(name="Inner Cave", description="Dark interior")
        subgrid.add_location(loc, 0, 0)
        assert subgrid.get_by_coordinates(0, 0) == loc

        # Invalid placement at (2, 2) - outside 3x3 bounds
        loc2 = Location(name="Far Corner", description="Too far")
        with pytest.raises(ValueError, match="outside bounds"):
            subgrid.add_location(loc2, 2, 2)

    def test_subgrid_respects_large_bounds(self):
        """SubGrid with large bounds should allow wider placements."""
        from cli_rpg.models.location import Location

        bounds = get_subgrid_bounds("city")  # 17x17
        subgrid = SubGrid(bounds=bounds, parent_name="City Gates")

        # Valid placement at (7, 7) - within 17x17 bounds
        loc = Location(name="Far District", description="Distant area")
        subgrid.add_location(loc, 7, 7)
        assert subgrid.get_by_coordinates(7, 7) == loc

        # Invalid placement at (9, 9) - outside 17x17 bounds
        loc2 = Location(name="Outside", description="Too far")
        with pytest.raises(ValueError, match="outside bounds"):
            subgrid.add_location(loc2, 9, 9)
