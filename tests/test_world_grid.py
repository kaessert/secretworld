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


class TestWorldGridNoWrapping:
    """Test that world grid does not wrap circularly.

    Spec: Coordinate-based movement should never wrap back to previously visited
    locations via connections that would violate coordinate consistency.
    """

    def test_repeated_direction_extends_world(self):
        """Going west repeatedly should not return to start.

        Spec: Moving in one direction repeatedly should reach unexplored coordinates,
        not wrap back to existing locations.
        """
        grid = WorldGrid()
        loc0 = Location(name="Start", description="Origin")
        loc1 = Location(name="West1", description="First west")
        loc2 = Location(name="West2", description="Second west")
        grid.add_location(loc0, 0, 0)
        grid.add_location(loc1, -1, 0)
        grid.add_location(loc2, -2, 0)

        # Going west from West2 should find no neighbor (needs generation)
        neighbor = grid.get_neighbor(-2, 0, "west")
        assert neighbor is None  # No wrap-around

    def test_coordinates_are_consistent_after_movement(self):
        """Moving west then east should return to same coordinates.

        Spec: Bidirectional movement returns to the original position.
        """
        grid = WorldGrid()
        start = Location(name="Start", description="Origin")
        west = Location(name="West", description="West")
        grid.add_location(start, 0, 0)
        grid.add_location(west, -1, 0)

        # West of (0,0) is (-1,0)
        assert grid.get_neighbor(0, 0, "west").coordinates == (-1, 0)
        # East of (-1,0) is (0,0)
        assert grid.get_neighbor(-1, 0, "east").coordinates == (0, 0)


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


class TestWorldGridBorderValidation:
    """Test border validation methods for area generation.

    Spec: find_unreachable_exits and validate_border_closure methods ensure
    that the world border is "closed" - all exits either point to existing
    locations or are reachable via frontier movement.
    """

    def test_find_unreachable_exits_empty_world(self):
        """Single-location world with no exits has no unreachable exits.

        Spec: A world with just one location and no connections should
        return an empty list from find_unreachable_exits.
        """
        grid = WorldGrid()
        loc = Location(name="Start", description="Starting location")
        grid.add_location(loc, 0, 0)

        unreachable = grid.find_unreachable_exits()
        assert unreachable == []

    def test_find_unreachable_exits_detects_orphan(self):
        """Detects exit pointing to coordinates that can't be reached.

        Spec: If a location has an exit to coordinates where no location
        exists, and that exit cannot be reached from the player (frontier),
        it should be detected as unreachable.
        """
        grid = WorldGrid()
        loc = Location(
            name="Start",
            description="Starting location",
            connections={"north": "Unreachable Place"}  # Points to (0, 1) but nothing there
        )
        grid.add_location(loc, 0, 0)

        # Add another location to the east that also points north to empty space
        loc2 = Location(
            name="East",
            description="East location",
            connections={"north": "Another Unreachable"}  # Points to (1, 1) but nothing there
        )
        grid.add_location(loc2, 1, 0)

        unreachable = grid.find_unreachable_exits()
        # Both dangling exits should be detected
        assert len(unreachable) == 2
        # Each entry is (location_name, direction, target_coords)
        exit_info = [(name, direction) for name, direction, coords in unreachable]
        assert ("Start", "north") in exit_info
        assert ("East", "north") in exit_info

    def test_find_unreachable_exits_ignores_valid_connections(self):
        """Does not report exits that point to existing locations.

        Spec: Exits pointing to coordinates with existing locations are
        not unreachable.
        """
        grid = WorldGrid()
        start = Location(name="Start", description="Starting location")
        north = Location(name="North", description="North location")
        grid.add_location(start, 0, 0)
        grid.add_location(north, 0, 1)

        # Both locations now have connections to each other (created by WorldGrid)
        unreachable = grid.find_unreachable_exits()
        assert unreachable == []

    def test_validate_border_closure_true_when_closed(self):
        """Returns True when all exits point to existing locations.

        Spec: validate_border_closure returns True if no orphaned exits.
        """
        grid = WorldGrid()
        start = Location(name="Start", description="Starting location")
        north = Location(name="North", description="North location")
        grid.add_location(start, 0, 0)
        grid.add_location(north, 0, 1)

        assert grid.validate_border_closure() is True

    def test_validate_border_closure_false_when_orphan(self):
        """Returns False when there are unreachable exits.

        Spec: validate_border_closure returns False if any orphaned exits.
        """
        grid = WorldGrid()
        loc = Location(
            name="Start",
            description="Starting location",
            connections={"north": "Nowhere"}  # Dangling exit
        )
        grid.add_location(loc, 0, 0)

        assert grid.validate_border_closure() is False

    def test_get_frontier_locations_returns_border_locations(self):
        """Returns locations with exits to empty coordinates.

        Spec: get_frontier_locations finds locations at world border with
        dangling exits that can trigger area generation.
        """
        grid = WorldGrid()
        center = Location(name="Center", description="Center location")
        grid.add_location(center, 0, 0)

        north = Location(
            name="North",
            description="North location",
            connections={"north": "Far North"}  # Dangling exit
        )
        grid.add_location(north, 0, 1)

        east = Location(name="East", description="East location")
        grid.add_location(east, 1, 0)

        frontier = grid.get_frontier_locations()
        frontier_names = [loc.name for loc in frontier]
        # North has a dangling exit
        assert "North" in frontier_names
        # East has no dangling exits (only connections to existing locations)
        # So East might or might not be in frontier depending on implementation

    def test_find_unreachable_exits_with_cardinal_directions_only(self):
        """Only considers cardinal directions (north, south, east, west).

        Spec: Exits to non-cardinal directions (up, down) don't affect
        coordinate-based border validation.
        """
        grid = WorldGrid()
        loc = Location(
            name="Start",
            description="Starting location",
            connections={"up": "Sky", "down": "Basement"}  # Non-cardinal
        )
        grid.add_location(loc, 0, 0)

        unreachable = grid.find_unreachable_exits()
        # up/down don't have coordinate offsets, so they shouldn't be in unreachable
        assert unreachable == []
