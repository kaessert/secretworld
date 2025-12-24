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
    "up": "down",
    "down": "up",
}


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
        3. Creates bidirectional connections with adjacent locations

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

        # Create bidirectional connections with adjacent locations
        self._create_connections(location, x, y)

    def _create_connections(self, location: Location, x: int, y: int) -> None:
        """Create bidirectional connections with adjacent locations.

        Args:
            location: The newly added location
            x: X coordinate of the location
            y: Y coordinate of the location
        """
        for direction, (dx, dy) in DIRECTION_OFFSETS.items():
            neighbor_coords = (x + dx, y + dy)
            if neighbor_coords in self._grid:
                neighbor = self._grid[neighbor_coords]
                opposite = OPPOSITE_DIRECTIONS[direction]

                # Add connection from this location to neighbor
                location.add_connection(direction, neighbor.name)

                # Add reverse connection from neighbor to this location
                neighbor.add_connection(opposite, location.name)

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
