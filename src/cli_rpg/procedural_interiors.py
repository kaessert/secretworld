"""Procedural interior generation for enterable locations.

This module provides foundational data structures for procedural layout generation
of interior locations (dungeons, caves, towns, etc.).

Architecture:
- RoomType: Classification of room purposes
- RoomTemplate: Blueprint for a single room in a layout
- BSPNode: Binary Space Partitioning tree node for dungeon generation
- BSPGenerator: Generator using BSP algorithm for dungeons, temples, ruins
- CATEGORY_GENERATORS: Maps location categories to generator types
- generate_interior_layout: Factory function for generating layouts
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol
import random


class RoomType(Enum):
    """Room classifications for procedural layouts.

    Each type affects content generation and gameplay:
    - ENTRY: Entry/exit points connecting to overworld
    - CORRIDOR: Connecting passages between rooms
    - CHAMBER: Standard rooms for exploration
    - BOSS_ROOM: Boss encounter locations (end-of-dungeon)
    - TREASURE: Treasure rooms with valuable loot
    - PUZZLE: Puzzle rooms with interactive challenges
    """

    ENTRY = "entry"
    CORRIDOR = "corridor"
    CHAMBER = "chamber"
    BOSS_ROOM = "boss_room"
    TREASURE = "treasure"
    PUZZLE = "puzzle"


@dataclass
class RoomTemplate:
    """Procedural room blueprint for layout generation.

    Attributes:
        coords: 3D position as (x, y, z). Dungeons extend downward (z < 0),
                towers extend upward (z > 0).
        room_type: Classification determining content generation.
        connections: List of connected directions (e.g., ["north", "down"]).
        is_entry: True if this room is an entry/exit point to overworld.
        suggested_hazards: Hints for hazard types to generate (e.g., ["poison_gas"]).
    """

    coords: tuple[int, int, int]
    room_type: RoomType
    connections: list[str]
    is_entry: bool = False
    suggested_hazards: list[str] = field(default_factory=list)


class GeneratorProtocol(Protocol):
    """Abstract interface for procedural layout generators."""

    def generate(self) -> list[RoomTemplate]:
        """Generate a layout.

        Returns:
            List of RoomTemplate blueprints for the layout.
        """
        ...


@dataclass
class BSPNode:
    """Node in BSP tree representing a rectangular partition.

    Used by BSPGenerator to recursively divide space for dungeon layouts.
    """

    x: int
    y: int
    width: int
    height: int
    left: Optional["BSPNode"] = None
    right: Optional["BSPNode"] = None
    room: Optional[tuple[int, int, int, int]] = None  # (x, y, w, h) if leaf with room

    @property
    def is_leaf(self) -> bool:
        """Check if this node is a leaf (no children)."""
        return self.left is None and self.right is None

    def split(
        self, rng: random.Random, horizontal: Optional[bool] = None, min_size: int = 4
    ) -> bool:
        """Split this node into two children.

        Args:
            rng: Random number generator for split position.
            horizontal: If True, split horizontally. If None, auto-determine.
            min_size: Minimum dimension for a partition.

        Returns:
            True if split was successful, False otherwise.
        """
        if self.left is not None or self.right is not None:
            return False  # Already split

        if self.width < min_size * 2 and self.height < min_size * 2:
            return False  # Too small to split

        # Determine split direction if not specified
        if horizontal is None:
            if self.width > self.height * 1.25:
                horizontal = False  # Split vertically (wide partition)
            elif self.height > self.width * 1.25:
                horizontal = True  # Split horizontally (tall partition)
            else:
                horizontal = rng.random() < 0.5

        # Check if we can split in chosen direction
        if horizontal and self.height < min_size * 2:
            horizontal = False
        elif not horizontal and self.width < min_size * 2:
            horizontal = True

        # Calculate split position (40-60% of dimension)
        if horizontal:
            max_dim = self.height
        else:
            max_dim = self.width

        if max_dim < min_size * 2:
            return False

        min_pos = max(min_size, int(max_dim * 0.4))
        max_pos = min(max_dim - min_size, int(max_dim * 0.6))

        if min_pos > max_pos:
            min_pos = max_pos = max_dim // 2

        split_pos = rng.randint(min_pos, max_pos)

        # Create children
        if horizontal:
            self.left = BSPNode(self.x, self.y, self.width, split_pos)
            self.right = BSPNode(
                self.x, self.y + split_pos, self.width, self.height - split_pos
            )
        else:
            self.left = BSPNode(self.x, self.y, split_pos, self.height)
            self.right = BSPNode(
                self.x + split_pos, self.y, self.width - split_pos, self.height
            )

        return True


# Direction offsets for 3D navigation
DIRECTION_OFFSETS: dict[str, tuple[int, int, int]] = {
    "north": (0, 1, 0),
    "south": (0, -1, 0),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
}

# Opposite directions for bidirectional connections
OPPOSITE_DIRECTION: dict[str, str] = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
    "up": "down",
    "down": "up",
}


class CellularAutomataGenerator:
    """Cellular automata generator for cave/mine layouts.

    Uses the 4-5 rule (cell becomes solid if ≥5 neighbors are solid)
    to generate organic, cave-like interior layouts.
    """

    INITIAL_FILL_PROBABILITY = 0.45  # 45% initial solid cells
    AUTOMATA_ITERATIONS = 4  # Number of smoothing passes
    BIRTH_THRESHOLD = 5  # Become solid if ≥5 neighbors solid
    DEATH_THRESHOLD = 4  # Stay solid if ≥4 neighbors solid

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        """Initialize with SubGrid bounds and random seed.

        Args:
            bounds: 6-tuple (min_x, max_x, min_y, max_y, min_z, max_z).
            seed: Random seed for deterministic generation.
        """
        self.bounds = bounds
        self.seed = seed
        self.rng = random.Random(seed)
        self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z = bounds
        self.width = self.max_x - self.min_x + 1
        self.height = self.max_y - self.min_y + 1

    def generate(self) -> list[RoomTemplate]:
        """Generate layout returning list of RoomTemplate blueprints."""
        all_rooms: list[RoomTemplate] = []
        coord_to_room: dict[tuple[int, int, int], RoomTemplate] = {}

        # Generate each z-level
        for z in range(self.max_z, self.min_z - 1, -1):
            level_rooms = self._generate_level(z)
            for room in level_rooms:
                all_rooms.append(room)
                coord_to_room[room.coords] = room

        # Handle case of no rooms generated - ensure at least entry room
        if not all_rooms:
            center_x = (self.min_x + self.max_x) // 2
            center_y = (self.min_y + self.max_y) // 2
            entry_room = RoomTemplate(
                coords=(center_x, center_y, self.max_z),
                room_type=RoomType.ENTRY,
                connections=[],
                is_entry=True,
            )
            all_rooms.append(entry_room)
            coord_to_room[entry_room.coords] = entry_room

        # Add connections based on adjacency
        self._add_connections(all_rooms, coord_to_room)

        # Connect levels with stairs
        if self.min_z < self.max_z:
            self._connect_levels(all_rooms, coord_to_room)

        # Assign room types
        self._assign_room_types(all_rooms)

        return all_rooms

    def _generate_level(self, z: int) -> list[RoomTemplate]:
        """Generate rooms for a single z-level using cellular automata."""
        # Initialize grid with random noise
        grid = self._initialize_grid()

        # Apply cellular automata rules
        grid = self._apply_automata(grid, self.AUTOMATA_ITERATIONS)

        # Find largest connected region
        center_x = self.width // 2
        center_y = self.height // 2

        # Find a starting open cell near center
        start = self._find_open_cell_near(grid, center_x, center_y)
        if start is None:
            # No open cells - create one at center
            grid[center_y][center_x] = False
            start = (center_x, center_y)

        # Flood fill to find connected region
        connected = self._flood_fill(grid, start[0], start[1])

        # Convert connected cells to rooms
        rooms: list[RoomTemplate] = []
        for gx, gy in connected:
            # Convert grid coords to world coords
            world_x = self.min_x + gx
            world_y = self.min_y + gy
            rooms.append(
                RoomTemplate(
                    coords=(world_x, world_y, z),
                    room_type=RoomType.CHAMBER,
                    connections=[],
                    is_entry=False,
                )
            )

        return rooms

    def _initialize_grid(self) -> list[list[bool]]:
        """Initialize grid with random noise. True = solid/wall."""
        grid: list[list[bool]] = []
        for y in range(self.height):
            row: list[bool] = []
            for x in range(self.width):
                # Border cells are always solid
                if x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1:
                    row.append(True)
                else:
                    row.append(self.rng.random() < self.INITIAL_FILL_PROBABILITY)
            grid.append(row)
        return grid

    def _apply_automata(
        self, grid: list[list[bool]], iterations: int
    ) -> list[list[bool]]:
        """Apply cellular automata rules to smooth the grid."""
        for _ in range(iterations):
            new_grid: list[list[bool]] = [
                [False] * self.width for _ in range(self.height)
            ]
            for y in range(self.height):
                for x in range(self.width):
                    neighbors = self._count_neighbors(grid, x, y)
                    if grid[y][x]:  # Currently solid
                        new_grid[y][x] = neighbors >= self.DEATH_THRESHOLD
                    else:  # Currently open
                        new_grid[y][x] = neighbors >= self.BIRTH_THRESHOLD
            grid = new_grid
        return grid

    def _count_neighbors(self, grid: list[list[bool]], x: int, y: int) -> int:
        """Count solid neighbors (8-directional including diagonals)."""
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if grid[ny][nx]:
                        count += 1
                else:
                    count += 1  # Out of bounds counts as solid
        return count

    def _find_open_cell_near(
        self, grid: list[list[bool]], cx: int, cy: int
    ) -> Optional[tuple[int, int]]:
        """Find an open cell near the given center coordinates."""
        # Spiral outward from center to find an open cell
        for radius in range(max(self.width, self.height)):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if not grid[ny][nx]:
                                return (nx, ny)
        return None

    def _flood_fill(
        self, grid: list[list[bool]], start_x: int, start_y: int
    ) -> set[tuple[int, int]]:
        """Find all connected open cells from start position."""
        if grid[start_y][start_x]:
            return set()  # Start is solid

        connected: set[tuple[int, int]] = set()
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            if (x, y) in connected:
                continue
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue
            if grid[y][x]:  # Solid cell
                continue

            connected.add((x, y))
            # Only cardinal directions for room connectivity
            stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

        return connected

    def _add_connections(
        self,
        rooms: list[RoomTemplate],
        coord_to_room: dict[tuple[int, int, int], RoomTemplate],
    ) -> None:
        """Add directional connections based on adjacency."""
        for room in rooms:
            x, y, z = room.coords
            # Check each cardinal direction (horizontal only - vertical done separately)
            for direction in ["north", "south", "east", "west"]:
                dx, dy, dz = DIRECTION_OFFSETS[direction]
                neighbor_coord = (x + dx, y + dy, z + dz)
                if neighbor_coord in coord_to_room:
                    if direction not in room.connections:
                        room.connections.append(direction)

    def _connect_levels(
        self,
        rooms: list[RoomTemplate],
        coord_to_room: dict[tuple[int, int, int], RoomTemplate],
    ) -> None:
        """Add up/down connections between adjacent z-levels."""
        # Group rooms by z-level
        by_level: dict[int, list[RoomTemplate]] = {}
        for room in rooms:
            z = room.coords[2]
            if z not in by_level:
                by_level[z] = []
            by_level[z].append(room)

        # For each pair of adjacent levels, add stair connections
        z_levels = sorted(by_level.keys(), reverse=True)
        for i in range(len(z_levels) - 1):
            upper_z = z_levels[i]
            lower_z = z_levels[i + 1]

            upper_rooms = by_level[upper_z]
            lower_rooms = by_level[lower_z]

            if not upper_rooms or not lower_rooms:
                continue

            # Find the best pair to connect (closest to each other)
            best_pair: Optional[tuple[RoomTemplate, RoomTemplate]] = None
            best_dist = float("inf")

            for ur in upper_rooms:
                for lr in lower_rooms:
                    dist = abs(ur.coords[0] - lr.coords[0]) + abs(
                        ur.coords[1] - lr.coords[1]
                    )
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (ur, lr)

            if best_pair:
                upper_room, lower_room = best_pair
                if "down" not in upper_room.connections:
                    upper_room.connections.append("down")
                if "up" not in lower_room.connections:
                    lower_room.connections.append("up")

    def _assign_room_types(self, rooms: list[RoomTemplate]) -> None:
        """Assign special room types (entry, boss, treasure, puzzle)."""
        if not rooms:
            return

        # Find entry room: at max_z level, closest to center
        center_x = (self.min_x + self.max_x) // 2
        center_y = (self.min_y + self.max_y) // 2

        top_level_rooms = [r for r in rooms if r.coords[2] == self.max_z]
        entry_room: Optional[RoomTemplate] = None

        if top_level_rooms:
            entry_room = min(
                top_level_rooms,
                key=lambda r: abs(r.coords[0] - center_x) + abs(r.coords[1] - center_y),
            )
            entry_room.room_type = RoomType.ENTRY
            entry_room.is_entry = True

        # Find boss room: at min_z level, furthest from entry
        bottom_level_rooms = [r for r in rooms if r.coords[2] == self.min_z]
        if bottom_level_rooms and self.min_z < self.max_z:
            entry_coords = (
                entry_room.coords if entry_room else (center_x, center_y, self.max_z)
            )
            boss_room = max(
                bottom_level_rooms,
                key=lambda r: abs(r.coords[0] - entry_coords[0])
                + abs(r.coords[1] - entry_coords[1]),
            )
            boss_room.room_type = RoomType.BOSS_ROOM
        elif bottom_level_rooms and self.min_z == self.max_z:
            # Single level: place boss furthest from entry
            if entry_room:
                entry_coords = entry_room.coords
                candidates = [r for r in rooms if r != entry_room]
                if candidates:
                    boss_room = max(
                        candidates,
                        key=lambda r: abs(r.coords[0] - entry_coords[0])
                        + abs(r.coords[1] - entry_coords[1]),
                    )
                    boss_room.room_type = RoomType.BOSS_ROOM

        # Assign treasure and puzzle rooms to dead ends (1 connection)
        for room in rooms:
            if room.room_type in (RoomType.ENTRY, RoomType.BOSS_ROOM):
                continue
            if len(room.connections) == 1:
                roll = self.rng.random()
                if roll < 0.3:
                    room.room_type = RoomType.TREASURE
                elif roll < 0.5:
                    room.room_type = RoomType.PUZZLE

        # Rooms with 3+ connections become corridors
        for room in rooms:
            if room.room_type == RoomType.CHAMBER and len(room.connections) >= 3:
                room.room_type = RoomType.CORRIDOR


class BSPGenerator:
    """Binary Space Partitioning generator for dungeon layouts.

    Generates procedural interior layouts for dungeons, temples, ruins,
    tombs, crypts, monasteries, and shrines using the BSP algorithm.
    """

    MIN_ROOM_SIZE = 3
    MIN_PARTITION_SIZE = 4
    MAX_SPLIT_DEPTH = 6

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        """Initialize with SubGrid bounds and random seed.

        Args:
            bounds: 6-tuple (min_x, max_x, min_y, max_y, min_z, max_z).
            seed: Random seed for deterministic generation.
        """
        self.bounds = bounds
        self.seed = seed
        self.rng = random.Random(seed)
        self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z = bounds

    def generate(self) -> list[RoomTemplate]:
        """Generate layout returning list of RoomTemplate blueprints."""
        rooms: list[RoomTemplate] = []

        # Generate for each z-level
        for z in range(self.max_z, self.min_z - 1, -1):
            level_rooms = self._generate_level(z)
            rooms.extend(level_rooms)

        # Ensure rooms are connected between levels
        self._add_vertical_connections(rooms)

        # Assign special room types
        self._assign_room_types(rooms)

        return rooms

    def _generate_level(self, z: int) -> list[RoomTemplate]:
        """Generate rooms for a single z-level."""
        width = self.max_x - self.min_x + 1
        height = self.max_y - self.min_y + 1

        # Create root node for this level
        root = BSPNode(x=self.min_x, y=self.min_y, width=width, height=height)

        # Build BSP tree
        self._split_recursively(root, 0)

        # Collect leaf nodes and create rooms
        leaves = self._collect_leaves(root)

        # Create rooms in leaves
        rooms: list[RoomTemplate] = []
        for leaf in leaves:
            room_coords = self._create_room_in_partition(leaf, z)
            if room_coords:
                rooms.append(room_coords)

        # Connect sibling rooms
        self._connect_siblings(root, rooms, z)

        return rooms

    def _split_recursively(self, node: BSPNode, depth: int) -> None:
        """Recursively split the BSP tree."""
        if depth >= self.MAX_SPLIT_DEPTH:
            return

        if node.split(self.rng, min_size=self.MIN_PARTITION_SIZE):
            if node.left:
                self._split_recursively(node.left, depth + 1)
            if node.right:
                self._split_recursively(node.right, depth + 1)

    def _collect_leaves(self, node: BSPNode) -> list[BSPNode]:
        """Collect all leaf nodes from the BSP tree."""
        if node.is_leaf:
            return [node]
        leaves = []
        if node.left:
            leaves.extend(self._collect_leaves(node.left))
        if node.right:
            leaves.extend(self._collect_leaves(node.right))
        return leaves

    def _create_room_in_partition(
        self, node: BSPNode, z: int
    ) -> Optional[RoomTemplate]:
        """Create a room within a leaf partition."""
        # For very small partitions (like 3x3), use the entire partition
        if node.width <= self.MIN_ROOM_SIZE + 1 or node.height <= self.MIN_ROOM_SIZE + 1:
            # Use the entire partition as a room
            room_width = node.width
            room_height = node.height
            offset_x = 0
            offset_y = 0
        else:
            # Room is smaller than partition with some margin
            margin = 1
            room_width = max(
                self.MIN_ROOM_SIZE, node.width - margin * 2 - self.rng.randint(0, 2)
            )
            room_height = max(
                self.MIN_ROOM_SIZE, node.height - margin * 2 - self.rng.randint(0, 2)
            )

            # Ensure room fits within partition
            room_width = min(room_width, node.width - margin)
            room_height = min(room_height, node.height - margin)

            if room_width < 1 or room_height < 1:
                return None

            # Position room within partition (center with some offset)
            max_offset_x = node.width - room_width - margin
            max_offset_y = node.height - room_height - margin
            offset_x = self.rng.randint(0, max(0, max_offset_x))
            offset_y = self.rng.randint(0, max(0, max_offset_y))

        room_x = node.x + offset_x
        room_y = node.y + offset_y

        # Store room info in node for connection generation
        node.room = (room_x, room_y, room_width, room_height)

        # Pick a point in the room for the RoomTemplate coords
        center_x = room_x + room_width // 2
        center_y = room_y + room_height // 2

        # Clamp to bounds
        center_x = max(self.min_x, min(self.max_x, center_x))
        center_y = max(self.min_y, min(self.max_y, center_y))

        return RoomTemplate(
            coords=(center_x, center_y, z),
            room_type=RoomType.CHAMBER,  # Will be reassigned later
            connections=[],
            is_entry=False,
        )

    def _connect_siblings(
        self, node: BSPNode, rooms: list[RoomTemplate], z: int
    ) -> None:
        """Connect rooms in sibling partitions."""
        if node.is_leaf:
            return

        # Recursively connect children first
        if node.left:
            self._connect_siblings(node.left, rooms, z)
        if node.right:
            self._connect_siblings(node.right, rooms, z)

        # Connect rooms between left and right subtrees
        if node.left and node.right:
            left_rooms = self._get_rooms_in_subtree(node.left, rooms, z)
            right_rooms = self._get_rooms_in_subtree(node.right, rooms, z)

            if left_rooms and right_rooms:
                # Find closest pair of rooms
                best_pair = None
                best_dist = float("inf")

                for lr in left_rooms:
                    for rr in right_rooms:
                        dist = abs(lr.coords[0] - rr.coords[0]) + abs(
                            lr.coords[1] - rr.coords[1]
                        )
                        if dist < best_dist:
                            best_dist = dist
                            best_pair = (lr, rr)

                if best_pair:
                    self._add_connection(best_pair[0], best_pair[1])

    def _get_rooms_in_subtree(
        self, node: BSPNode, rooms: list[RoomTemplate], z: int
    ) -> list[RoomTemplate]:
        """Get all rooms in a subtree."""
        result = []
        for room in rooms:
            x, y, rz = room.coords
            if rz == z and node.x <= x < node.x + node.width and node.y <= y < node.y + node.height:
                result.append(room)
        return result

    def _add_connection(self, room1: RoomTemplate, room2: RoomTemplate) -> None:
        """Add bidirectional connections between two rooms."""
        x1, y1, z1 = room1.coords
        x2, y2, z2 = room2.coords

        if z1 != z2:
            # Vertical connection
            if z1 < z2:
                if "up" not in room1.connections:
                    room1.connections.append("up")
                if "down" not in room2.connections:
                    room2.connections.append("down")
            else:
                if "down" not in room1.connections:
                    room1.connections.append("down")
                if "up" not in room2.connections:
                    room2.connections.append("up")
        else:
            # Horizontal connection - determine direction
            dx = x2 - x1
            dy = y2 - y1

            if abs(dx) >= abs(dy):
                # Primarily east-west
                if dx > 0:
                    if "east" not in room1.connections:
                        room1.connections.append("east")
                    if "west" not in room2.connections:
                        room2.connections.append("west")
                else:
                    if "west" not in room1.connections:
                        room1.connections.append("west")
                    if "east" not in room2.connections:
                        room2.connections.append("east")
            else:
                # Primarily north-south
                if dy > 0:
                    if "north" not in room1.connections:
                        room1.connections.append("north")
                    if "south" not in room2.connections:
                        room2.connections.append("south")
                else:
                    if "south" not in room1.connections:
                        room1.connections.append("south")
                    if "north" not in room2.connections:
                        room2.connections.append("north")

    def _add_vertical_connections(self, rooms: list[RoomTemplate]) -> None:
        """Add up/down connections between adjacent z-levels."""
        # Group rooms by z-level
        by_level: dict[int, list[RoomTemplate]] = {}
        for room in rooms:
            z = room.coords[2]
            if z not in by_level:
                by_level[z] = []
            by_level[z].append(room)

        # For each pair of adjacent levels, add stair connections
        z_levels = sorted(by_level.keys(), reverse=True)
        for i in range(len(z_levels) - 1):
            upper_z = z_levels[i]
            lower_z = z_levels[i + 1]

            upper_rooms = by_level[upper_z]
            lower_rooms = by_level[lower_z]

            if upper_rooms and lower_rooms:
                # Find closest pair between levels
                best_pair = None
                best_dist = float("inf")

                for ur in upper_rooms:
                    for lr in lower_rooms:
                        dist = abs(ur.coords[0] - lr.coords[0]) + abs(
                            ur.coords[1] - lr.coords[1]
                        )
                        if dist < best_dist:
                            best_dist = dist
                            best_pair = (ur, lr)

                if best_pair:
                    self._add_connection(best_pair[0], best_pair[1])

    def _assign_room_types(self, rooms: list[RoomTemplate]) -> None:
        """Assign special room types (entry, boss, treasure, puzzle)."""
        if not rooms:
            return

        # Find entry room: at max_z level, closest to center
        center_x = (self.min_x + self.max_x) // 2
        center_y = (self.min_y + self.max_y) // 2

        top_level_rooms = [r for r in rooms if r.coords[2] == self.max_z]
        if top_level_rooms:
            entry_room = min(
                top_level_rooms,
                key=lambda r: abs(r.coords[0] - center_x) + abs(r.coords[1] - center_y),
            )
            entry_room.room_type = RoomType.ENTRY
            entry_room.is_entry = True

        # Find boss room: at min_z level, furthest from entry
        bottom_level_rooms = [r for r in rooms if r.coords[2] == self.min_z]
        if bottom_level_rooms and self.min_z < self.max_z:
            entry_coords = (
                entry_room.coords if top_level_rooms else (center_x, center_y, self.max_z)
            )
            boss_room = max(
                bottom_level_rooms,
                key=lambda r: abs(r.coords[0] - entry_coords[0])
                + abs(r.coords[1] - entry_coords[1]),
            )
            boss_room.room_type = RoomType.BOSS_ROOM
        elif bottom_level_rooms and self.min_z == self.max_z:
            # Single level: place boss furthest from entry
            if top_level_rooms:
                entry_coords = entry_room.coords
                candidates = [r for r in rooms if r != entry_room]
                if candidates:
                    boss_room = max(
                        candidates,
                        key=lambda r: abs(r.coords[0] - entry_coords[0])
                        + abs(r.coords[1] - entry_coords[1]),
                    )
                    boss_room.room_type = RoomType.BOSS_ROOM

        # Assign treasure and puzzle rooms to dead ends (1 connection)
        for room in rooms:
            if room.room_type in (RoomType.ENTRY, RoomType.BOSS_ROOM):
                continue
            if len(room.connections) == 1:
                roll = self.rng.random()
                if roll < 0.3:
                    room.room_type = RoomType.TREASURE
                elif roll < 0.5:
                    room.room_type = RoomType.PUZZLE

        # Rooms with 3+ connections become corridors
        for room in rooms:
            if room.room_type == RoomType.CHAMBER and len(room.connections) >= 3:
                room.room_type = RoomType.CORRIDOR


class GridSettlementGenerator:
    """Grid-based generator for settlement layouts (towns, cities, villages).

    Creates orthogonal street grids with building locations. Streets form
    a grid pattern (CORRIDOR rooms), with buildings placed along streets
    (CHAMBER rooms). Entry point is placed at the center of the settlement.
    """

    # Street spacing (every N tiles in each direction)
    STREET_SPACING = 3

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        """Initialize with SubGrid bounds and random seed.

        Args:
            bounds: 6-tuple (min_x, max_x, min_y, max_y, min_z, max_z).
            seed: Random seed for deterministic generation.
        """
        self.bounds = bounds
        self.seed = seed
        self.rng = random.Random(seed)
        self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z = bounds
        self.width = self.max_x - self.min_x + 1
        self.height = self.max_y - self.min_y + 1

    def generate(self) -> list[RoomTemplate]:
        """Generate layout returning list of RoomTemplate blueprints."""
        rooms: list[RoomTemplate] = []
        coord_to_room: dict[tuple[int, int, int], RoomTemplate] = {}

        # Generate street grid
        street_coords = self._generate_street_grid()

        # Create rooms for streets
        for x, y in street_coords:
            room = RoomTemplate(
                coords=(x, y, 0),
                room_type=RoomType.CORRIDOR,
                connections=[],
                is_entry=False,
            )
            rooms.append(room)
            coord_to_room[(x, y, 0)] = room

        # Add building locations along streets
        building_coords = self._generate_buildings(street_coords)
        for x, y in building_coords:
            if (x, y, 0) not in coord_to_room:
                room = RoomTemplate(
                    coords=(x, y, 0),
                    room_type=RoomType.CHAMBER,
                    connections=[],
                    is_entry=False,
                )
                rooms.append(room)
                coord_to_room[(x, y, 0)] = room

        # Ensure we have at least an entry room
        if not rooms:
            center_x = (self.min_x + self.max_x) // 2
            center_y = (self.min_y + self.max_y) // 2
            entry_room = RoomTemplate(
                coords=(center_x, center_y, 0),
                room_type=RoomType.ENTRY,
                connections=[],
                is_entry=True,
            )
            rooms.append(entry_room)
            coord_to_room[(center_x, center_y, 0)] = entry_room

        # Add connections based on adjacency
        self._add_connections(rooms, coord_to_room)

        # Assign entry room (center of settlement)
        self._assign_entry(rooms)

        return rooms

    def _generate_street_grid(self) -> set[tuple[int, int]]:
        """Generate street coordinates as a grid pattern."""
        streets: set[tuple[int, int]] = set()
        center_x = (self.min_x + self.max_x) // 2
        center_y = (self.min_y + self.max_y) // 2

        # Main streets through center
        for x in range(self.min_x, self.max_x + 1):
            streets.add((x, center_y))
        for y in range(self.min_y, self.max_y + 1):
            streets.add((center_x, y))

        # Additional cross-streets at intervals
        spacing = max(2, self.STREET_SPACING)

        # Horizontal streets
        for offset in range(spacing, max(self.height // 2, 1) + 1, spacing):
            if center_y + offset <= self.max_y:
                for x in range(self.min_x, self.max_x + 1):
                    streets.add((x, center_y + offset))
            if center_y - offset >= self.min_y:
                for x in range(self.min_x, self.max_x + 1):
                    streets.add((x, center_y - offset))

        # Vertical streets
        for offset in range(spacing, max(self.width // 2, 1) + 1, spacing):
            if center_x + offset <= self.max_x:
                for y in range(self.min_y, self.max_y + 1):
                    streets.add((center_x + offset, y))
            if center_x - offset >= self.min_x:
                for y in range(self.min_y, self.max_y + 1):
                    streets.add((center_x - offset, y))

        return streets

    def _generate_buildings(
        self, street_coords: set[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """Generate building locations adjacent to streets."""
        buildings: list[tuple[int, int]] = []
        potential: set[tuple[int, int]] = set()

        # Find all non-street tiles adjacent to streets
        for sx, sy in street_coords:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = sx + dx, sy + dy
                if (nx, ny) not in street_coords:
                    if self.min_x <= nx <= self.max_x and self.min_y <= ny <= self.max_y:
                        potential.add((nx, ny))

        # Randomly select ~50% of potential building spots
        for coord in potential:
            if self.rng.random() < 0.5:
                buildings.append(coord)

        return buildings

    def _add_connections(
        self,
        rooms: list[RoomTemplate],
        coord_to_room: dict[tuple[int, int, int], RoomTemplate],
    ) -> None:
        """Add directional connections based on adjacency."""
        for room in rooms:
            x, y, z = room.coords
            for direction in ["north", "south", "east", "west"]:
                dx, dy, dz = DIRECTION_OFFSETS[direction]
                neighbor_coord = (x + dx, y + dy, z + dz)
                if neighbor_coord in coord_to_room:
                    if direction not in room.connections:
                        room.connections.append(direction)

    def _assign_entry(self, rooms: list[RoomTemplate]) -> None:
        """Assign entry room at center of settlement."""
        if not rooms:
            return

        center_x = (self.min_x + self.max_x) // 2
        center_y = (self.min_y + self.max_y) // 2

        # Find room closest to center
        entry_room = min(
            rooms,
            key=lambda r: abs(r.coords[0] - center_x) + abs(r.coords[1] - center_y),
        )
        entry_room.room_type = RoomType.ENTRY
        entry_room.is_entry = True


# Maps location categories to generator types.
# All categories from ENTERABLE_CATEGORIES in world_tiles.py must be mapped.
CATEGORY_GENERATORS: dict[str, str] = {
    # Adventure locations
    "dungeon": "BSPGenerator",
    "cave": "CellularAutomataGenerator",
    "ruins": "BSPGenerator",
    "temple": "BSPGenerator",
    "tomb": "BSPGenerator",
    "mine": "CellularAutomataGenerator",
    "crypt": "BSPGenerator",
    "tower": "TowerGenerator",
    "monastery": "BSPGenerator",
    "shrine": "BSPGenerator",
    # Settlements
    "town": "GridSettlementGenerator",
    "village": "GridSettlementGenerator",
    "city": "GridSettlementGenerator",
    "settlement": "GridSettlementGenerator",
    "outpost": "GridSettlementGenerator",
    "camp": "GridSettlementGenerator",
    # Commercial buildings
    "tavern": "SingleRoomGenerator",
    "shop": "SingleRoomGenerator",
    "inn": "SingleRoomGenerator",
}


def generate_interior_layout(
    category: str, bounds: tuple, seed: int
) -> list[RoomTemplate]:
    """Generate a procedural interior layout for a location category.

    This is the entry point for procedural generation. Uses the appropriate
    generator based on the category.

    Args:
        category: Location category (e.g., "dungeon", "cave", "town").
        bounds: 6-tuple (min_x, max_x, min_y, max_y, min_z, max_z) defining
                the SubGrid bounds for the interior.
        seed: Random seed for deterministic generation.

    Returns:
        List of RoomTemplate blueprints for the layout.
    """
    generator_type = CATEGORY_GENERATORS.get(category, "BSPGenerator")

    # Use BSPGenerator for dungeon-type locations
    if generator_type == "BSPGenerator":
        generator = BSPGenerator(bounds=bounds, seed=seed)
        return generator.generate()

    # Use CellularAutomataGenerator for cave-type locations
    if generator_type == "CellularAutomataGenerator":
        generator = CellularAutomataGenerator(bounds=bounds, seed=seed)
        return generator.generate()

    # Use GridSettlementGenerator for settlement-type locations
    if generator_type == "GridSettlementGenerator":
        generator = GridSettlementGenerator(bounds=bounds, seed=seed)
        return generator.generate()

    # Fallback for other generator types (not yet implemented)
    return _generate_fallback_layout(bounds, seed)


def _generate_fallback_layout(bounds: tuple, seed: int) -> list[RoomTemplate]:
    """Generate a simple fallback layout for unimplemented generators."""
    rng = random.Random(seed)
    min_x, max_x, min_y, max_y, min_z, max_z = bounds

    rooms: list[RoomTemplate] = []

    # Always create an entry room at the center of level 0
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    entry_room = RoomTemplate(
        coords=(center_x, center_y, max_z),  # Entry at top level
        room_type=RoomType.ENTRY,
        connections=_get_fallback_connections(rng),
        is_entry=True,
    )
    rooms.append(entry_room)

    # Add a few random chambers based on bounds size
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    num_chambers = min(rng.randint(2, 5), width * height - 1)

    used_coords = {entry_room.coords}
    for _ in range(num_chambers):
        # Generate random coordinates within bounds
        x = rng.randint(min_x, max_x)
        y = rng.randint(min_y, max_y)
        z = rng.randint(min_z, max_z)
        coord = (x, y, z)

        if coord not in used_coords:
            used_coords.add(coord)
            room_type = rng.choice([RoomType.CHAMBER, RoomType.CORRIDOR])
            rooms.append(
                RoomTemplate(
                    coords=coord,
                    room_type=room_type,
                    connections=_get_fallback_connections(rng),
                )
            )

    return rooms


def _get_fallback_connections(rng: random.Random) -> list[str]:
    """Generate random connections for fallback layout."""
    directions = ["north", "south", "east", "west"]
    num_connections = rng.randint(1, 3)
    return rng.sample(directions, num_connections)
