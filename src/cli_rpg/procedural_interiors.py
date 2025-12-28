"""Procedural interior generation for enterable locations.

This module provides foundational data structures for procedural layout generation
of interior locations (dungeons, caves, towns, etc.). The actual generators
(BSP, cellular automata, etc.) will be implemented in Phase 1 Step 2.

Architecture:
- RoomType: Classification of room purposes
- RoomTemplate: Blueprint for a single room in a layout
- CATEGORY_GENERATORS: Maps location categories to generator types
- generate_interior_layout: Factory function for generating layouts
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
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
    """Abstract interface for procedural layout generators.

    Implementations (BSPGenerator, CellularAutomataGenerator, etc.)
    will be added in Phase 1 Step 2.
    """

    def generate(self, seed: int) -> list[RoomTemplate]:
        """Generate a layout from the given seed.

        Args:
            seed: Random seed for deterministic generation.

        Returns:
            List of RoomTemplate blueprints for the layout.
        """
        ...


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

    This is the entry point for procedural generation. Currently returns
    a fallback layout; actual generator implementations come in Phase 1 Step 2.

    Args:
        category: Location category (e.g., "dungeon", "cave", "town").
        bounds: 6-tuple (min_x, max_x, min_y, max_y, min_z, max_z) defining
                the SubGrid bounds for the interior.
        seed: Random seed for deterministic generation.

    Returns:
        List of RoomTemplate blueprints for the layout.
    """
    # Use deterministic random for reproducibility
    rng = random.Random(seed)

    # Extract bounds
    min_x, max_x, min_y, max_y, min_z, max_z = bounds

    # Fallback: Generate a simple layout
    # This will be replaced by actual generator implementations in Step 2
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
