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

# 3D direction offsets for SubGrid navigation (includes z-axis)
SUBGRID_DIRECTION_OFFSETS: Dict[str, Tuple[int, int, int]] = {
    "north": (0, 1, 0),
    "south": (0, -1, 0),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
}


def get_tiles_in_radius(center_x: int, center_y: int, radius: int) -> set[tuple[int, int]]:
    """Return all (x, y) coordinates within Manhattan distance radius.

    Args:
        center_x: X coordinate of center tile
        center_y: Y coordinate of center tile
        radius: Maximum Manhattan distance from center (0 = center only)

    Returns:
        Set of (x, y) coordinate tuples within the radius
    """
    tiles = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if abs(dx) + abs(dy) <= radius:
                tiles.add((center_x + dx, center_y + dy))
    return tiles

# SubGrid size configuration by location category
# Format: (min_x, max_x, min_y, max_y, min_z, max_z)
SUBGRID_BOUNDS: Dict[str, Tuple[int, int, int, int, int, int]] = {
    # Tiny (3x3) - Small structures
    "house": (-1, 1, -1, 1, 0, 0),        # single level
    "shop": (-1, 1, -1, 1, 0, 0),         # single level
    "cave": (-1, 1, -1, 1, -1, 0),        # goes down one level
    # Small (5x5) - Medium structures
    "tavern": (-2, 2, -2, 2, 0, 1),       # main floor + upstairs
    "ruins": (-2, 2, -2, 2, -1, 0),       # basement
    "settlement": (-2, 2, -2, 2, 0, 0),   # single level
    # Medium (7x7) - Standard interiors
    "dungeon": (-3, 3, -3, 3, -2, 0),     # multi-level down
    "forest": (-3, 3, -3, 3, 0, 0),       # single level
    "temple": (-3, 3, -3, 3, -1, 1),      # basement + main + upper
    "tower": (-1, 1, -1, 1, 0, 3),        # multi-level up
    "wilderness": (-3, 3, -3, 3, 0, 0),   # single level
    # Large (11x11) - Towns
    "town": (-5, 5, -5, 5, 0, 0),         # single level
    "village": (-5, 5, -5, 5, 0, 0),      # single level
    # Huge (17x17) - Cities
    "city": (-8, 8, -8, 8, 0, 0),         # single level
    # Default fallback
    "default": (-2, 2, -2, 2, 0, 0),      # single level
}


def get_subgrid_bounds(category: Optional[str]) -> Tuple[int, int, int, int, int, int]:
    """Get SubGrid bounds for a location category.

    Args:
        category: Location category (town, dungeon, etc.) or None

    Returns:
        Tuple of (min_x, max_x, min_y, max_y, min_z, max_z)
    """
    if category is None:
        return SUBGRID_BOUNDS["default"]
    return SUBGRID_BOUNDS.get(category.lower(), SUBGRID_BOUNDS["default"])


@dataclass
class SubGrid:
    """Bounded grid for sub-location interiors.

    Unlike WorldGrid which is infinite, SubGrid has defined bounds.
    Entry is always at (0, 0, 0). Used for interior spaces like castles,
    dungeons, or buildings that have their own coordinate system
    separate from the overworld.

    Supports 3D coordinates with z-axis for multi-level structures:
    - z=0 is ground level
    - z>0 is upper floors (towers, etc.)
    - z<0 is below ground (dungeons, basements, etc.)

    Attributes:
        _grid: Internal storage mapping (x, y, z) coordinates to locations
        _by_name: Name-based lookup for convenience
        bounds: Tuple of (min_x, max_x, min_y, max_y, min_z, max_z) defining grid limits
        parent_name: Name of the parent location for exit navigation
    """

    _grid: Dict[Tuple[int, int, int], Location] = field(default_factory=dict)
    _by_name: Dict[str, Location] = field(default_factory=dict)
    bounds: Tuple[int, int, int, int, int, int] = (-2, 2, -2, 2, 0, 0)  # min_x, max_x, min_y, max_y, min_z, max_z
    parent_name: str = ""

    def add_location(self, location: Location, x: int, y: int, z: int = 0) -> None:
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
            z: Z coordinate (vertical axis, default 0 = ground level)

        Raises:
            ValueError: If coordinates outside bounds or name already exists
        """
        if not self.is_within_bounds(x, y, z):
            raise ValueError(f"Coordinates ({x}, {y}, {z}) outside bounds {self.bounds}")

        if location.name in self._by_name:
            raise ValueError(f"Location '{location.name}' already exists in sub-grid")

        # Set 3D coordinates and parent on the location
        location.coordinates = (x, y, z)
        location.parent_location = self.parent_name

        # Add to both indices
        self._grid[(x, y, z)] = location
        self._by_name[location.name] = location

    def get_by_coordinates(self, x: int, y: int, z: int = 0) -> Optional[Location]:
        """Get location at specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate (default 0)

        Returns:
            Location at coordinates, or None if empty
        """
        return self._grid.get((x, y, z))

    def get_by_name(self, name: str) -> Optional[Location]:
        """Get location by name.

        Args:
            name: Location name

        Returns:
            Location with given name, or None if not found
        """
        return self._by_name.get(name)

    def is_within_bounds(self, x: int, y: int, z: int = 0) -> bool:
        """Check if coordinates are within grid bounds.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate (default 0)

        Returns:
            True if within bounds, False otherwise
        """
        # Handle both 6-tuple and legacy 4-tuple bounds
        if len(self.bounds) == 6:
            min_x, max_x, min_y, max_y, min_z, max_z = self.bounds
        else:
            min_x, max_x, min_y, max_y = self.bounds
            min_z, max_z = 0, 0
        return min_x <= x <= max_x and min_y <= y <= max_y and min_z <= z <= max_z

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
        # Handle both legacy 4-tuple and new 6-tuple bounds
        raw_bounds = data.get("bounds", [-2, 2, -2, 2, 0, 0])
        if len(raw_bounds) == 4:
            # Upgrade legacy 4-tuple to 6-tuple with z=0
            raw_bounds = list(raw_bounds) + [0, 0]
        grid.bounds = tuple(raw_bounds)
        grid.parent_name = data.get("parent_name", "")

        for loc_data in data.get("locations", []):
            location = Location.from_dict(loc_data)
            if location.coordinates is not None:
                # Handle both 2D and 3D coordinates
                if len(location.coordinates) == 2:
                    x, y = location.coordinates
                    z = 0
                else:
                    x, y, z = location.coordinates
                # Bypass add_location to preserve existing connections
                grid._grid[(x, y, z)] = location
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

    def get_prioritized_frontier_exits(
        self,
        explored_regions: Optional[set[tuple[int, int]]] = None
    ) -> List[Tuple[str, str, Tuple[int, int]]]:
        """Find frontier exits prioritized by unexplored regions.

        Similar to find_frontier_exits() but orders results to prefer
        directions leading to unexplored regions. This guides players
        toward new content and creates a sense of world expansion.

        Args:
            explored_regions: Optional set of visited region coordinates.
                             If None, calculates from current locations.

        Returns:
            List of (location_name, direction, target_coords) prioritized
            with unexplored region directions first.
        """
        from cli_rpg.world_tiles import (
            get_region_coords,
            get_unexplored_region_directions,
        )

        # Get all frontier exits
        all_exits = self.find_frontier_exits()

        if not all_exits:
            return []

        # If no explored regions provided, calculate from grid locations
        if explored_regions is None:
            explored_regions = set()
            for location in self._by_name.values():
                if location.coordinates is not None:
                    explored_regions.add(get_region_coords(*location.coordinates))

        # Partition exits into unexplored-region and explored-region groups
        unexplored_exits = []
        explored_exits = []

        for exit_info in all_exits:
            location_name, direction, target_coords = exit_info
            location = self._by_name.get(location_name)

            if location is None or location.coordinates is None:
                # Can't determine priority, add to explored (lower priority)
                explored_exits.append(exit_info)
                continue

            # Get unexplored directions from this location
            unexplored_dirs = get_unexplored_region_directions(
                location.coordinates[0],
                location.coordinates[1],
                explored_regions
            )

            if direction in unexplored_dirs:
                unexplored_exits.append(exit_info)
            else:
                explored_exits.append(exit_info)

        # Return unexplored exits first, then explored exits
        return unexplored_exits + explored_exits
