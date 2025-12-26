"""Tests for Location is_exit_point and sub_grid fields.

These tests verify the new fields added to support the SubGrid-based sub-location system:
- is_exit_point: Marks locations where 'exit' command is allowed
- sub_grid: Contains the bounded interior grid for overworld landmarks
"""

import pytest
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid


class TestIsExitPointField:
    """Tests for the is_exit_point field on Location."""

    def test_location_is_exit_point_default_false(self):
        """Test is_exit_point defaults to False - spec: default value."""
        location = Location(name="Test Room", description="A test room.")
        assert location.is_exit_point is False

    def test_location_is_exit_point_can_be_true(self):
        """Test is_exit_point can be set to True - spec: setting to True."""
        location = Location(
            name="Entrance Hall",
            description="The main entrance.",
            is_exit_point=True
        )
        assert location.is_exit_point is True

    def test_location_to_dict_includes_is_exit_point_when_true(self):
        """Test to_dict includes is_exit_point when True - spec: serialization."""
        location = Location(
            name="Entrance Hall",
            description="The main entrance.",
            is_exit_point=True
        )
        data = location.to_dict()
        assert "is_exit_point" in data
        assert data["is_exit_point"] is True

    def test_location_to_dict_excludes_is_exit_point_when_false(self):
        """Test to_dict omits is_exit_point when False - spec: minimal serialization."""
        location = Location(name="Test Room", description="A test room.")
        data = location.to_dict()
        # Should not include is_exit_point when False (default)
        assert "is_exit_point" not in data

    def test_location_from_dict_restores_is_exit_point_true(self):
        """Test from_dict restores is_exit_point=True - spec: deserialization."""
        data = {
            "name": "Entrance Hall",
            "description": "The main entrance.",
            "is_exit_point": True
        }
        location = Location.from_dict(data)
        assert location.is_exit_point is True

    def test_location_from_dict_restores_is_exit_point_false(self):
        """Test from_dict restores is_exit_point=False - spec: deserialization."""
        data = {
            "name": "Deep Cave",
            "description": "A deep cave.",
            "is_exit_point": False
        }
        location = Location.from_dict(data)
        assert location.is_exit_point is False


class TestSubGridField:
    """Tests for the sub_grid field on Location."""

    def test_location_sub_grid_default_none(self):
        """Test sub_grid defaults to None - spec: default value."""
        location = Location(name="Test Room", description="A test room.")
        assert location.sub_grid is None

    def test_location_sub_grid_can_be_set(self):
        """Test sub_grid can be set to a SubGrid instance - spec: setting SubGrid."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Castle")
        location = Location(
            name="Castle",
            description="A grand castle.",
            is_overworld=True,
            sub_grid=sub_grid
        )
        assert location.sub_grid is sub_grid
        assert location.sub_grid.parent_name == "Castle"

    def test_location_to_dict_includes_sub_grid(self):
        """Test to_dict includes sub_grid when present - spec: serialization."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Castle")
        hall = Location(name="Great Hall", description="A vast hall.")
        sub_grid.add_location(hall, 0, 0)

        location = Location(
            name="Castle",
            description="A grand castle.",
            is_overworld=True,
            sub_grid=sub_grid
        )
        data = location.to_dict()

        assert "sub_grid" in data
        assert "locations" in data["sub_grid"]
        assert "bounds" in data["sub_grid"]
        assert "parent_name" in data["sub_grid"]
        assert data["sub_grid"]["parent_name"] == "Castle"

    def test_location_to_dict_excludes_sub_grid_when_none(self):
        """Test to_dict omits sub_grid when None - spec: minimal serialization."""
        location = Location(name="Test Room", description="A test room.")
        data = location.to_dict()
        assert "sub_grid" not in data

    def test_location_from_dict_restores_sub_grid(self):
        """Test from_dict restores sub_grid with locations - spec: deserialization."""
        data = {
            "name": "Castle",
            "description": "A grand castle.",
            "is_overworld": True,
            "sub_grid": {
                "locations": [
                    {
                        "name": "Great Hall",
                        "description": "A vast hall.",
                        "connections": {},
                        "coordinates": [0, 0],
                        "parent_location": "Castle",
                        "npcs": []
                    }
                ],
                "bounds": [-2, 2, -2, 2],
                "parent_name": "Castle"
            }
        }
        location = Location.from_dict(data)

        assert location.sub_grid is not None
        assert location.sub_grid.parent_name == "Castle"
        assert location.sub_grid.bounds == (-2, 2, -2, 2)
        assert location.sub_grid.get_by_name("Great Hall") is not None
        assert location.sub_grid.get_by_coordinates(0, 0).name == "Great Hall"


class TestBackwardCompatibility:
    """Tests for backward compatibility with old saves."""

    def test_location_from_dict_without_is_exit_point(self):
        """Test old saves without is_exit_point still load - spec: backward compat."""
        data = {
            "name": "Test Room",
            "description": "A test room.",
            "connections": {},
            "npcs": []
        }
        location = Location.from_dict(data)
        assert location.is_exit_point is False  # defaults to False

    def test_location_from_dict_without_sub_grid(self):
        """Test old saves without sub_grid still load - spec: backward compat."""
        data = {
            "name": "Test Room",
            "description": "A test room.",
            "connections": {},
            "npcs": []
        }
        location = Location.from_dict(data)
        assert location.sub_grid is None  # defaults to None


class TestRoundTrip:
    """Test full serialization/deserialization cycle."""

    def test_roundtrip_with_is_exit_point_true(self):
        """Test roundtrip preserves is_exit_point=True - spec: roundtrip."""
        original = Location(
            name="Entrance Hall",
            description="The main entrance.",
            is_exit_point=True
        )
        data = original.to_dict()
        restored = Location.from_dict(data)
        assert restored.is_exit_point is True

    def test_roundtrip_with_sub_grid(self):
        """Test roundtrip preserves sub_grid - spec: roundtrip."""
        sub_grid = SubGrid(bounds=(-3, 3, -2, 2), parent_name="Castle")
        hall = Location(name="Great Hall", description="A vast hall.")
        kitchen = Location(name="Kitchen", description="A kitchen.")
        sub_grid.add_location(hall, 0, 0)
        sub_grid.add_location(kitchen, 0, 1)

        original = Location(
            name="Castle",
            description="A grand castle.",
            is_overworld=True,
            sub_grid=sub_grid
        )
        data = original.to_dict()
        restored = Location.from_dict(data)

        assert restored.sub_grid is not None
        assert restored.sub_grid.bounds == (-3, 3, -2, 2)
        assert restored.sub_grid.parent_name == "Castle"
        assert restored.sub_grid.get_by_name("Great Hall") is not None
        assert restored.sub_grid.get_by_name("Kitchen") is not None
        assert restored.sub_grid.get_by_coordinates(0, 0).name == "Great Hall"
        assert restored.sub_grid.get_by_coordinates(0, 1).name == "Kitchen"

    def test_roundtrip_with_both_fields(self):
        """Test roundtrip preserves both new fields - spec: roundtrip."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Castle")
        entrance = Location(
            name="Entrance",
            description="The entrance.",
            is_exit_point=True
        )
        sub_grid.add_location(entrance, 0, 0)

        original = Location(
            name="Castle",
            description="A grand castle.",
            is_overworld=True,
            sub_grid=sub_grid
        )
        data = original.to_dict()
        restored = Location.from_dict(data)

        assert restored.sub_grid is not None
        entrance_restored = restored.sub_grid.get_by_name("Entrance")
        assert entrance_restored is not None
        assert entrance_restored.is_exit_point is True
