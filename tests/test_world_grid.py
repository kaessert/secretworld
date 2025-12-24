"""Tests for the WorldGrid class (grid-based world representation)."""

import pytest
from cli_rpg.world_grid import WorldGrid
from cli_rpg.models.location import Location


class TestWorldGridBasics:
    """Test basic WorldGrid operations."""

    def test_create_empty_world_grid(self):
        """Test creating empty WorldGrid - spec: WorldGrid class exists."""
        grid = WorldGrid()
        assert grid.as_dict() == {}

    def test_add_location_with_coordinates(self):
        """Test adding location at specific coordinates - spec: coordinate-based storage."""
        grid = WorldGrid()
        location = Location(name="Town Square", description="A town square.")
        grid.add_location(location, 0, 0)
        assert grid.get_by_coordinates(0, 0) == location
        assert location.coordinates == (0, 0)

    def test_get_location_by_coordinates(self):
        """Test retrieving location by coordinates - spec: get_by_coordinates method."""
        grid = WorldGrid()
        location = Location(name="Town Square", description="A town square.")
        grid.add_location(location, 5, 10)
        result = grid.get_by_coordinates(5, 10)
        assert result is not None
        assert result.name == "Town Square"

    def test_get_location_by_coordinates_not_found(self):
        """Test get_by_coordinates returns None for empty position."""
        grid = WorldGrid()
        assert grid.get_by_coordinates(99, 99) is None

    def test_get_location_by_name(self):
        """Test backward compatible name-based lookup - spec: get_by_name method."""
        grid = WorldGrid()
        location = Location(name="Town Square", description="A town square.")
        grid.add_location(location, 0, 0)
        result = grid.get_by_name("Town Square")
        assert result is not None
        assert result.name == "Town Square"

    def test_get_location_by_name_not_found(self):
        """Test get_by_name returns None for unknown location."""
        grid = WorldGrid()
        assert grid.get_by_name("Unknown") is None


class TestWorldGridDirectionalConsistency:
    """Test directional movement consistency."""

    def test_moving_north_increases_y(self):
        """Test north direction increases y coordinate - spec: north = +y."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        forest = Location(name="Forest", description="A forest.")
        grid.add_location(town, 0, 0)
        grid.add_location(forest, 0, 1)  # north of town

        neighbor = grid.get_neighbor(0, 0, "north")
        assert neighbor is not None
        assert neighbor.name == "Forest"

    def test_moving_south_decreases_y(self):
        """Test south direction decreases y coordinate - spec: south = -y."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        beach = Location(name="Beach", description="A sandy beach.")
        grid.add_location(town, 0, 0)
        grid.add_location(beach, 0, -1)  # south of town

        neighbor = grid.get_neighbor(0, 0, "south")
        assert neighbor is not None
        assert neighbor.name == "Beach"

    def test_moving_east_increases_x(self):
        """Test east direction increases x coordinate - spec: east = +x."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        cave = Location(name="Cave", description="A dark cave.")
        grid.add_location(town, 0, 0)
        grid.add_location(cave, 1, 0)  # east of town

        neighbor = grid.get_neighbor(0, 0, "east")
        assert neighbor is not None
        assert neighbor.name == "Cave"

    def test_moving_west_decreases_x(self):
        """Test west direction decreases x coordinate - spec: west = -x."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        lake = Location(name="Lake", description="A serene lake.")
        grid.add_location(town, 0, 0)
        grid.add_location(lake, -1, 0)  # west of town

        neighbor = grid.get_neighbor(0, 0, "west")
        assert neighbor is not None
        assert neighbor.name == "Lake"


class TestWorldGridBidirectionalConnections:
    """Test bidirectional connection creation."""

    def test_add_location_creates_bidirectional_connections(self):
        """Test adding adjacent location creates both connections - spec: bidirectional guarantee."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        forest = Location(name="Forest", description="A forest.")
        grid.add_location(town, 0, 0)
        grid.add_location(forest, 0, 1)  # north of town

        # Town should have north connection to Forest
        assert town.get_connection("north") == "Forest"
        # Forest should have south connection to Town Square
        assert forest.get_connection("south") == "Town Square"

    def test_north_south_roundtrip_returns_to_same_location(self):
        """Test going north then south returns to same location - spec: bidirectional consistency."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        forest = Location(name="Forest", description="A forest.")
        grid.add_location(town, 0, 0)
        grid.add_location(forest, 0, 1)

        # Start at town, go north to forest
        north_location = grid.get_neighbor(0, 0, "north")
        assert north_location.name == "Forest"

        # From forest, go south back to town
        south_location = grid.get_neighbor(0, 1, "south")
        assert south_location.name == "Town Square"

    def test_east_west_roundtrip_returns_to_same_location(self):
        """Test going east then west returns to same location - spec: bidirectional consistency."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        cave = Location(name="Cave", description="A dark cave.")
        grid.add_location(town, 0, 0)
        grid.add_location(cave, 1, 0)

        # Start at town, go east to cave
        east_location = grid.get_neighbor(0, 0, "east")
        assert east_location.name == "Cave"

        # From cave, go west back to town
        west_location = grid.get_neighbor(1, 0, "west")
        assert west_location.name == "Town Square"


class TestWorldGridValidation:
    """Test spatial validation and constraints."""

    def test_cannot_add_location_at_occupied_coordinates(self):
        """Test adding location at occupied coordinates raises error - spec: unique coordinates."""
        grid = WorldGrid()
        loc1 = Location(name="Town Square", description="A town square.")
        loc2 = Location(name="Market", description="A busy market.")
        grid.add_location(loc1, 0, 0)

        with pytest.raises(ValueError, match="already occupied"):
            grid.add_location(loc2, 0, 0)

    def test_cannot_add_duplicate_name(self):
        """Test adding location with duplicate name raises error - spec: unique names."""
        grid = WorldGrid()
        loc1 = Location(name="Town Square", description="A town square.")
        loc2 = Location(name="Town Square", description="Another square.")
        grid.add_location(loc1, 0, 0)

        with pytest.raises(ValueError, match="already exists"):
            grid.add_location(loc2, 1, 0)


class TestWorldGridBackwardCompatibility:
    """Test backward compatibility with dict[str, Location] interface."""

    def test_world_grid_as_dict_returns_location_dict(self):
        """Test as_dict returns dict[str, Location] - spec: backward compat."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        forest = Location(name="Forest", description="A forest.")
        grid.add_location(town, 0, 0)
        grid.add_location(forest, 0, 1)

        world_dict = grid.as_dict()
        assert isinstance(world_dict, dict)
        assert "Town Square" in world_dict
        assert "Forest" in world_dict
        assert world_dict["Town Square"] == town
        assert world_dict["Forest"] == forest


class TestWorldGridSerialization:
    """Test serialization/deserialization."""

    def test_to_dict_includes_coordinates(self):
        """Test to_dict includes grid coordinates - spec: serialization."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        grid.add_location(town, 0, 0)

        data = grid.to_dict()
        assert "locations" in data
        assert len(data["locations"]) == 1
        assert data["locations"][0]["coordinates"] == [0, 0]

    def test_from_dict_restores_coordinates(self):
        """Test from_dict restores grid structure - spec: deserialization."""
        data = {
            "locations": [
                {
                    "name": "Town Square",
                    "description": "A town square.",
                    "connections": {"north": "Forest"},
                    "coordinates": [0, 0],
                    "npcs": []
                },
                {
                    "name": "Forest",
                    "description": "A forest.",
                    "connections": {"south": "Town Square"},
                    "coordinates": [0, 1],
                    "npcs": []
                }
            ]
        }
        grid = WorldGrid.from_dict(data)

        assert grid.get_by_coordinates(0, 0) is not None
        assert grid.get_by_coordinates(0, 1) is not None
        assert grid.get_by_name("Town Square") is not None
        assert grid.get_by_name("Forest") is not None

    def test_serialization_roundtrip(self):
        """Test to_dict -> from_dict preserves data - spec: roundtrip."""
        grid = WorldGrid()
        town = Location(name="Town Square", description="A town square.")
        forest = Location(name="Forest", description="A forest.")
        grid.add_location(town, 0, 0)
        grid.add_location(forest, 0, 1)

        data = grid.to_dict()
        restored = WorldGrid.from_dict(data)

        assert restored.get_by_name("Town Square") is not None
        assert restored.get_by_name("Forest") is not None
        assert restored.get_by_coordinates(0, 0).name == "Town Square"
        assert restored.get_by_coordinates(0, 1).name == "Forest"
        # Check connections preserved
        assert restored.get_by_name("Town Square").get_connection("north") == "Forest"
        assert restored.get_by_name("Forest").get_connection("south") == "Town Square"

    def test_from_dict_backward_compat_no_coordinates(self):
        """Test from_dict handles legacy data without coordinates - spec: backward compat."""
        # Legacy format: just dict of location names to location data
        legacy_data = {
            "Town Square": {
                "name": "Town Square",
                "description": "A town square.",
                "connections": {"north": "Forest"},
                "npcs": []
            },
            "Forest": {
                "name": "Forest",
                "description": "A forest.",
                "connections": {"south": "Town Square"},
                "npcs": []
            }
        }
        grid = WorldGrid.from_legacy_dict(legacy_data)

        assert grid.get_by_name("Town Square") is not None
        assert grid.get_by_name("Forest") is not None
        # Legacy locations should still be accessible by name
