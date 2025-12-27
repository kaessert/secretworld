"""Tests for the SubGrid class (bounded grid for sub-location interiors)."""

import pytest
from cli_rpg.world_grid import SubGrid
from cli_rpg.models.location import Location


class TestSubGridBasics:
    """Test basic SubGrid operations."""

    def test_create_subgrid_default_bounds(self):
        """Test creating SubGrid with default bounds - spec: SubGrid class exists with defaults."""
        grid = SubGrid()
        # Default bounds should be (-2, 2, -2, 2)
        assert grid.bounds == (-2, 2, -2, 2)
        assert grid.parent_name == ""

    def test_create_subgrid_custom_bounds(self):
        """Test creating SubGrid with custom bounds - spec: bounds customization."""
        grid = SubGrid(bounds=(-5, 5, -3, 3), parent_name="Castle")
        assert grid.bounds == (-5, 5, -3, 3)
        assert grid.parent_name == "Castle"

    def test_add_location_within_bounds(self):
        """Test adding location within bounds succeeds - spec: coordinate-based storage."""
        grid = SubGrid(parent_name="Castle")
        location = Location(name="Great Hall", description="A vast hall.")
        grid.add_location(location, 0, 0)
        assert grid.get_by_coordinates(0, 0) == location

    def test_add_location_sets_coordinates(self):
        """Test adding location sets its coordinates - spec: location coordinate assignment."""
        grid = SubGrid(parent_name="Castle")
        location = Location(name="Great Hall", description="A vast hall.")
        grid.add_location(location, 1, 2)
        assert location.coordinates == (1, 2)

    def test_add_location_sets_parent_location(self):
        """Test adding location sets its parent_location - spec: parent tracking."""
        grid = SubGrid(parent_name="Castle")
        location = Location(name="Great Hall", description="A vast hall.")
        grid.add_location(location, 0, 0)
        assert location.parent_location == "Castle"

    def test_add_location_outside_bounds_raises(self):
        """Test adding location outside bounds raises ValueError - spec: bounds enforcement."""
        grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Castle")
        location = Location(name="Far Away", description="Too far.")

        # X too low
        with pytest.raises(ValueError, match="outside bounds"):
            grid.add_location(location, -3, 0)

        # X too high
        location2 = Location(name="Far Away 2", description="Too far.")
        with pytest.raises(ValueError, match="outside bounds"):
            grid.add_location(location2, 3, 0)

        # Y too low
        location3 = Location(name="Far Away 3", description="Too far.")
        with pytest.raises(ValueError, match="outside bounds"):
            grid.add_location(location3, 0, -3)

        # Y too high
        location4 = Location(name="Far Away 4", description="Too far.")
        with pytest.raises(ValueError, match="outside bounds"):
            grid.add_location(location4, 0, 3)

    def test_add_duplicate_name_raises(self):
        """Test adding location with duplicate name raises ValueError - spec: unique names."""
        grid = SubGrid(parent_name="Castle")
        loc1 = Location(name="Great Hall", description="A vast hall.")
        loc2 = Location(name="Great Hall", description="Another hall.")
        grid.add_location(loc1, 0, 0)

        with pytest.raises(ValueError, match="already exists"):
            grid.add_location(loc2, 1, 0)

    def test_get_by_coordinates(self):
        """Test retrieving location by coordinates - spec: get_by_coordinates method."""
        grid = SubGrid(parent_name="Castle")
        location = Location(name="Great Hall", description="A vast hall.")
        grid.add_location(location, 1, 1)

        result = grid.get_by_coordinates(1, 1)
        assert result is not None
        assert result.name == "Great Hall"

    def test_get_by_coordinates_not_found(self):
        """Test get_by_coordinates returns None for empty position."""
        grid = SubGrid(parent_name="Castle")
        assert grid.get_by_coordinates(99, 99) is None

    def test_get_by_name(self):
        """Test retrieving location by name - spec: get_by_name method."""
        grid = SubGrid(parent_name="Castle")
        location = Location(name="Great Hall", description="A vast hall.")
        grid.add_location(location, 0, 0)

        result = grid.get_by_name("Great Hall")
        assert result is not None
        assert result.name == "Great Hall"

    def test_get_by_name_not_found(self):
        """Test get_by_name returns None for unknown location."""
        grid = SubGrid(parent_name="Castle")
        assert grid.get_by_name("Unknown") is None

    def test_is_within_bounds_true(self):
        """Test is_within_bounds returns True for valid coordinates - spec: bounds check."""
        grid = SubGrid(bounds=(-2, 2, -2, 2))
        assert grid.is_within_bounds(0, 0) is True
        assert grid.is_within_bounds(-2, -2) is True
        assert grid.is_within_bounds(2, 2) is True
        assert grid.is_within_bounds(-2, 2) is True

    def test_is_within_bounds_false(self):
        """Test is_within_bounds returns False for invalid coordinates - spec: bounds check."""
        grid = SubGrid(bounds=(-2, 2, -2, 2))
        assert grid.is_within_bounds(-3, 0) is False
        assert grid.is_within_bounds(3, 0) is False
        assert grid.is_within_bounds(0, -3) is False
        assert grid.is_within_bounds(0, 3) is False


class TestSubGridCoordinateNavigation:
    """Test coordinate-based navigation in SubGrid.

    Navigation is now coordinate-based - adjacent locations are determined by
    their coordinates, not explicit connection dictionaries.
    """

    def test_adjacent_locations_by_coordinates(self):
        """Test adjacent locations are placed with correct coordinates - spec: coordinate adjacency."""
        grid = SubGrid(parent_name="Castle")
        hall = Location(name="Great Hall", description="A vast hall.")
        kitchen = Location(name="Kitchen", description="A kitchen.")
        grid.add_location(hall, 0, 0)
        grid.add_location(kitchen, 0, 1)  # north of hall

        # Verify coordinates set correctly
        assert hall.coordinates == (0, 0)
        assert kitchen.coordinates == (0, 1)
        # Verify Kitchen is north of Hall (dy=1)
        assert kitchen.coordinates[1] - hall.coordinates[1] == 1

    def test_non_adjacent_locations_by_coordinates(self):
        """Test non-adjacent locations have gap in coordinates."""
        grid = SubGrid(parent_name="Castle")
        hall = Location(name="Great Hall", description="A vast hall.")
        tower = Location(name="Tower", description="A tower.")
        grid.add_location(hall, 0, 0)
        grid.add_location(tower, 2, 2)  # not adjacent

        # Verify they're not adjacent (gap > 1 in both directions)
        dx = abs(tower.coordinates[0] - hall.coordinates[0])
        dy = abs(tower.coordinates[1] - hall.coordinates[1])
        assert dx > 1 or dy > 1  # Not cardinally adjacent

    def test_multi_direction_layout(self):
        """Test locations in all four directions work correctly."""
        grid = SubGrid(parent_name="Castle")
        center = Location(name="Center", description="Center room.")
        north = Location(name="North Room", description="North.")
        south = Location(name="South Room", description="South.")
        east = Location(name="East Room", description="East.")
        west = Location(name="West Room", description="West.")

        grid.add_location(center, 0, 0)
        grid.add_location(north, 0, 1)
        grid.add_location(south, 0, -1)
        grid.add_location(east, 1, 0)
        grid.add_location(west, -1, 0)

        # Center should have adjacent locations in all four directions via coordinates
        assert grid.get_by_coordinates(0, 1).name == "North Room"
        assert grid.get_by_coordinates(0, -1).name == "South Room"
        assert grid.get_by_coordinates(1, 0).name == "East Room"
        assert grid.get_by_coordinates(-1, 0).name == "West Room"


class TestSubGridSerialization:
    """Test serialization/deserialization."""

    def test_to_dict_structure(self):
        """Test to_dict returns correct structure - spec: serialization format."""
        grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Castle")
        hall = Location(name="Great Hall", description="A vast hall.")
        grid.add_location(hall, 0, 0)

        data = grid.to_dict()
        assert "locations" in data
        assert "bounds" in data
        assert "parent_name" in data
        assert data["bounds"] == [-2, 2, -2, 2]
        assert data["parent_name"] == "Castle"

    def test_from_dict_restores_locations(self):
        """Test from_dict restores locations - spec: deserialization."""
        data = {
            "locations": [
                {
                    "name": "Great Hall",
                    "description": "A vast hall.",
                    "coordinates": [0, 0],
                    "parent_location": "Castle",
                    "npcs": []
                }
            ],
            "bounds": [-2, 2, -2, 2],
            "parent_name": "Castle"
        }
        grid = SubGrid.from_dict(data)

        assert grid.get_by_name("Great Hall") is not None
        assert grid.get_by_coordinates(0, 0) is not None

    def test_from_dict_restores_bounds(self):
        """Test from_dict restores bounds - spec: bounds preservation."""
        data = {
            "locations": [],
            "bounds": [-5, 5, -3, 3],
            "parent_name": "Castle"
        }
        grid = SubGrid.from_dict(data)

        assert grid.bounds == (-5, 5, -3, 3)

    def test_from_dict_restores_parent_name(self):
        """Test from_dict restores parent_name - spec: parent_name preservation."""
        data = {
            "locations": [],
            "bounds": [-2, 2, -2, 2],
            "parent_name": "Castle"
        }
        grid = SubGrid.from_dict(data)

        assert grid.parent_name == "Castle"

    def test_round_trip_preserves_data(self):
        """Test to_dict -> from_dict preserves all data - spec: roundtrip."""
        grid = SubGrid(bounds=(-3, 3, -3, 3), parent_name="Castle")
        hall = Location(name="Great Hall", description="A vast hall.")
        kitchen = Location(name="Kitchen", description="A kitchen.")
        grid.add_location(hall, 0, 0)
        grid.add_location(kitchen, 0, 1)

        data = grid.to_dict()
        restored = SubGrid.from_dict(data)

        # Check bounds preserved
        assert restored.bounds == (-3, 3, -3, 3)
        # Check parent_name preserved
        assert restored.parent_name == "Castle"
        # Check locations preserved
        assert restored.get_by_name("Great Hall") is not None
        assert restored.get_by_name("Kitchen") is not None
        assert restored.get_by_coordinates(0, 0).name == "Great Hall"
        assert restored.get_by_coordinates(0, 1).name == "Kitchen"
        # Check coordinates preserved (navigation is coordinate-based)
        assert restored.get_by_name("Great Hall").coordinates == (0, 0)
        assert restored.get_by_name("Kitchen").coordinates == (0, 1)
        # Check parent_location preserved
        assert restored.get_by_name("Great Hall").parent_location == "Castle"
        assert restored.get_by_name("Kitchen").parent_location == "Castle"


class TestSubGridEntryPoint:
    """Test entry point behavior at (0, 0)."""

    def test_entry_point_at_origin(self):
        """Test entry point location at (0, 0) works - spec: entry at origin."""
        grid = SubGrid(parent_name="Castle")
        entry = Location(name="Entrance", description="The entrance.")
        grid.add_location(entry, 0, 0)

        assert grid.get_by_coordinates(0, 0) is not None
        assert grid.get_by_coordinates(0, 0).name == "Entrance"
