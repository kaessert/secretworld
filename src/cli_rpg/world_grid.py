"""Grid-based world representation with spatial consistency."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List
from cli_rpg.models.location import Location


# Direction offsets: (dx, dy)
DIRECTION_OFFSETS: Dict[str, Tuple[int, int]] = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0),
}

# Opposite directions for bidirectional connections
OPPOSITE_DIRECTIONS: Dict[str, str] = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


@dataclass
class SubGrid:
    """Bounded grid for sub-location interiors.

    Unlike WorldGrid which is infinite, SubGrid has defined bounds.
    Entry is always at (0, 0). Used for interior spaces like castles,
    dungeons, or buildings that have their own coordinate system
    separate from the overworld.

    Attributes:
        _grid: Internal storage mapping (x, y) coordinates to locations
        _by_name: Name-based lookup for convenience
        bounds: Tuple of (min_x, max_x, min_y, max_y) defining grid limits
        parent_name: Name of the parent location for exit navigation
    """

    _grid: Dict[Tuple[int, int], Location] = field(default_factory=dict)
    _by_name: Dict[str, Location] = field(default_factory=dict)
    bounds: Tuple[int, int, int, int] = (-2, 2, -2, 2)  # min_x, max_x, min_y, max_y
    parent_name: str = ""

    def add_location(self, location: Location, x: int, y: int) -> None:
        """Add a location within bounds.

        This method:
        1. Validates coordinates are within bounds
        2. Places the location at the given coordinates
        3. Sets the location's coordinates and parent_location fields

        Navigation between locations is determined by coordinate adjacency,
        not explicit connections.

        Args:
            location: The Location instance to add
            x: X coordinate (east/west axis)
            y: Y coordinate (north/south axis)

        Raises:
            ValueError: If coordinates outside bounds or name already exists
        """
        if not self.is_within_bounds(x, y):
            raise ValueError(f"Coordinates ({x}, {y}) outside bounds {self.bounds}")

        if location.name in self._by_name:
            raise ValueError(f"Location '{location.name}' already exists in sub-grid")

        # Set coordinates and parent on the location
        location.coordinates = (x, y)
        location.parent_location = self.parent_name

        # Add to both indices
        self._grid[(x, y)] = location
        self._by_name[location.name] = location

    def get_by_coordinates(self, x: int, y: int) -> Optional[Location]:
        """Get location at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Location at coordinates, or None if empty
        """
        return self._grid.get((x, y))

    def get_by_name(self, name: str) -> Optional[Location]:
        """Get location by name.

        Args:
            name: Location name

        Returns:
            Location with given name, or None if not found
        """
        return self._by_name.get(name)

    def is_within_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within grid bounds.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if within bounds, False otherwise
        """
        min_x, max_x, min_y, max_y = self.bounds
        return min_x <= x <= max_x and min_y <= y <= max_y

    def to_dict(self) -> dict:
        """Serialize the sub-grid to a dictionary.

        Returns:
            Dictionary representation with locations, bounds, and parent_name
        """
        locations = []
        for location in self._by_name.values():
            locations.append(location.to_dict())

        return {
            "locations": locations,
            "bounds": list(self.bounds),
            "parent_name": self.parent_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SubGrid":
        """Create a SubGrid from a serialized dictionary.

        Args:
            data: Dictionary containing serialized sub-grid data

        Returns:
            SubGrid instance with restored locations
        """
        grid = cls()
        grid.bounds = tuple(data.get("bounds", [-2, 2, -2, 2]))
        grid.parent_name = data.get("parent_name", "")

        for loc_data in data.get("locations", []):
            location = Location.from_dict(loc_data)
            if location.coordinates is not None:
                x, y = location.coordinates
                # Bypass add_location to preserve existing connections
                grid._grid[(x, y)] = location
                grid._by_name[location.name] = location

        return grid


@dataclass
class WorldGrid:
    """Grid-based world representation with spatial consistency.

    This class provides a coordinate-based world structure that ensures
    geographic consistency (going north then south returns to the same place).

    Attributes:
        _grid: Internal storage mapping (x, y) coordinates to locations
        _by_name: Name-based lookup for backward compatibility
    """

    _grid: Dict[Tuple[int, int], Location] = field(default_factory=dict)
    _by_name: Dict[str, Location] = field(default_factory=dict)

    def add_location(self, location: Location, x: int, y: int) -> None:
        """Add a location at specific coordinates.

        This method:
        1. Places the location at the given coordinates
        2. Sets the location's coordinates field

        Navigation between locations is determined by coordinate adjacency,
        not explicit connections.

        Args:
            location: The Location instance to add
            x: X coordinate (east/west axis)
            y: Y coordinate (north/south axis)

        Raises:
            ValueError: If coordinates are already occupied or name already exists
        """
        coords = (x, y)

        # Check for occupied coordinates
        if coords in self._grid:
            raise ValueError(
                f"Coordinates ({x}, {y}) already occupied by '{self._grid[coords].name}'"
            )

        # Check for duplicate name
        if location.name in self._by_name:
            raise ValueError(f"Location '{location.name}' already exists in world")

        # Set coordinates on the location
        location.coordinates = coords

        # Add to both indices
        self._grid[coords] = location
        self._by_name[location.name] = location

    def get_by_coordinates(self, x: int, y: int) -> Optional[Location]:
        """Get location at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Location at coordinates, or None if empty
        """
        return self._grid.get((x, y))

    def get_by_name(self, name: str) -> Optional[Location]:
        """Get location by name (backward compatible lookup).

        Args:
            name: Location name

        Returns:
            Location with given name, or None if not found
        """
        return self._by_name.get(name)

    def get_neighbor(
        self, x: int, y: int, direction: str
    ) -> Optional[Location]:
        """Get the neighbor location in a given direction.

        Args:
            x: X coordinate of current position
            y: Y coordinate of current position
            direction: Direction to look (north, south, east, west)

        Returns:
            Neighbor location, or None if no location in that direction
        """
        if direction not in DIRECTION_OFFSETS:
            return None

        dx, dy = DIRECTION_OFFSETS[direction]
        neighbor_coords = (x + dx, y + dy)
        return self._grid.get(neighbor_coords)

    def as_dict(self) -> Dict[str, Location]:
        """Get world as dictionary for backward compatibility.

        Returns:
            Dictionary mapping location names to Location instances
        """
        return self._by_name.copy()

    def to_dict(self) -> dict:
        """Serialize the world grid to a dictionary.

        Returns:
            Dictionary representation with location list including coordinates
        """
        locations = []
        for location in self._by_name.values():
            loc_data = location.to_dict()
            locations.append(loc_data)

        return {"locations": locations}

    @classmethod
    def from_dict(cls, data: dict) -> "WorldGrid":
        """Create a WorldGrid from a serialized dictionary.

        Args:
            data: Dictionary containing serialized world data

        Returns:
            WorldGrid instance with restored locations
        """
        grid = cls()

        for loc_data in data.get("locations", []):
            location = Location.from_dict(loc_data)
            if location.coordinates is not None:
                x, y = location.coordinates
                # Bypass add_location to preserve existing connections
                grid._grid[(x, y)] = location
                grid._by_name[location.name] = location

        return grid

    @classmethod
    def from_legacy_dict(cls, data: Dict[str, dict]) -> "WorldGrid":
        """Create a WorldGrid from legacy dict[str, Location] format.

        This handles saves that don't have coordinate information.
        Locations are added without coordinates (coordinate = None).

        Args:
            data: Dictionary mapping location names to location data

        Returns:
            WorldGrid with locations (no coordinate-based features)
        """
        grid = cls()

        for name, loc_data in data.items():
            location = Location.from_dict(loc_data)
            # Add to name index only (no coordinates)
            grid._by_name[location.name] = location

        return grid

    def __len__(self) -> int:
        """Return the number of locations in the grid."""
        return len(self._by_name)

    def __contains__(self, name: str) -> bool:
        """Check if a location name exists in the grid."""
        return name in self._by_name

    def __iter__(self):
        """Iterate over location names."""
        return iter(self._by_name)

    def items(self):
        """Return items view for dict-like iteration."""
        return self._by_name.items()

    def values(self):
        """Return values view for dict-like iteration."""
        return self._by_name.values()

    def keys(self):
        """Return keys view for dict-like iteration."""
        return self._by_name.keys()

    def find_frontier_exits(self) -> List[Tuple[str, str, Tuple[int, int]]]:
        """Find directions pointing to unexplored coordinates (frontier exits).

        These exits enable world expansion - when a player travels through them,
        new areas can be generated. Frontier exits are found by checking all
        cardinal directions from each location for empty coordinates.

        Returns:
            List of tuples (location_name, direction, target_coords) for each
            direction pointing to unexplored coordinates.
        """
        frontier = []

        for location in self._by_name.values():
            if location.coordinates is None:
                continue

            x, y = location.coordinates
            for direction, (dx, dy) in DIRECTION_OFFSETS.items():
                target_coords = (x + dx, y + dy)

                # Check if target coordinates are empty (unexplored)
                if target_coords not in self._grid:
                    frontier.append((location.name, direction, target_coords))

        return frontier

    # Backward compatibility alias
    def find_unreachable_exits(self) -> List[Tuple[str, str, Tuple[int, int]]]:
        """Alias for find_frontier_exits (backward compatibility)."""
        return self.find_frontier_exits()

    def has_expansion_exits(self) -> bool:
        """Check if the world has at least one exit to unexplored territory.

        Returns True if there's at least one frontier exit that can trigger
        area generation. This is the desired state - the world should always
        be expandable.

        Returns:
            True if at least one frontier exit exists, False if world is closed.
        """
        return len(self.find_frontier_exits()) > 0

    def validate_border_closure(self) -> bool:
        """Check if all exits point to existing locations (backward compatibility).

        Returns True if there are no "dangling" exits pointing to empty
        coordinates. This means the world border is "closed".

        Note: A closed border is generally NOT desired - the world should
        always have at least one frontier exit for expansion. Use
        has_expansion_exits() to check for the desired state.

        Returns:
            True if all cardinal exits point to existing locations,
            False if any exits point to empty coordinates.
        """
        return not self.has_expansion_exits()

    def ensure_expansion_possible(self) -> bool:
        """Ensure the world has at least one frontier exit.

        With coordinate-based navigation, expansion is always possible if any
        location exists with coordinates, since players can move in any cardinal
        direction to unexplored coordinates. This method exists for backward
        compatibility but now returns False (no modifications needed) as long as
        any location with coordinates exists.

        Returns:
            True if the world was modified, False if already had frontier exits.
        """
        # With coordinate-based movement, any location with coordinates
        # always allows expansion in any direction without explicit connections.
        # So if we have frontier exits, we're good.
        return not self.has_expansion_exits()

    def get_frontier_locations(self) -> List[Location]:
        """Get locations at the world border with exits to empty coordinates.

        These are locations where the player could potentially trigger
        area generation by moving in a direction that leads to an empty
        coordinate.

        Returns:
            List of Location objects that have at least one exit pointing
            to empty coordinates.
        """
        frontier = []
        seen_names = set()

        for location_name, direction, target_coords in self.find_frontier_exits():
            if location_name not in seen_names:
                seen_names.add(location_name)
                frontier.append(self._by_name[location_name])

        return frontier
