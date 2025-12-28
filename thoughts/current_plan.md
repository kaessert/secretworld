# GridSettlementGenerator Implementation Plan

## Spec

Implement `GridSettlementGenerator` for town/city/village/settlement/outpost/camp interiors using a grid-based street layout pattern. This differs from BSP (dungeon corridors) and cellular automata (organic caves) by creating orthogonal street grids with buildings.

**Key Requirements:**
- Generate orthogonal street grid (intersections become CORRIDOR rooms)
- Place buildings/points of interest along streets (CHAMBER rooms)
- Entry point at center or edge of grid
- Single z-level (z=0) for all settlements
- Deterministic via seed
- Follow `GeneratorProtocol` interface

## Tests

Add to `tests/test_procedural_interiors.py`:

```python
class TestGridSettlementGenerator:
    """Tests for GridSettlementGenerator for town/city layouts."""

    def test_generator_exists(self):
        """GridSettlementGenerator class is importable."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        assert GridSettlementGenerator is not None

    def test_implements_protocol(self):
        """GridSettlementGenerator follows GeneratorProtocol."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        bounds = (-5, 5, -5, 5, 0, 0)  # town size
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert isinstance(result, list)

    def test_returns_room_templates(self):
        """generate() returns list of RoomTemplate."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator, RoomTemplate
        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

    def test_has_entry_room(self):
        """Generated layout includes at least one entry room."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator, RoomType
        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) >= 1

    def test_entry_at_top_z_level(self):
        """Entry room is at z=0 (top level for settlements)."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        entry_rooms = [r for r in result if r.is_entry]
        assert all(r.coords[2] == 0 for r in entry_rooms)

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical layout."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        bounds = (-5, 5, -5, 5, 0, 0)
        gen1 = GridSettlementGenerator(bounds=bounds, seed=12345)
        gen2 = GridSettlementGenerator(bounds=bounds, seed=12345)
        result1 = gen1.generate()
        result2 = gen2.generate()
        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.coords == r2.coords
            assert r1.room_type == r2.room_type

    def test_different_seed_different_layout(self):
        """Different seeds produce different layouts."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        bounds = (-5, 5, -5, 5, 0, 0)
        gen1 = GridSettlementGenerator(bounds=bounds, seed=111)
        gen2 = GridSettlementGenerator(bounds=bounds, seed=222)
        result1 = gen1.generate()
        result2 = gen2.generate()
        coords1 = [r.coords for r in result1]
        coords2 = [r.coords for r in result2]
        # Very unlikely to be identical with different seeds
        assert coords1 != coords2 or len(result1) != len(result2)

    def test_has_connected_rooms(self):
        """Rooms have connections to adjacent rooms."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        # At least some rooms should have connections
        rooms_with_connections = [r for r in result if len(r.connections) > 0]
        assert len(rooms_with_connections) > 0

    def test_grid_pattern_has_corridors(self):
        """Grid layout produces CORRIDOR rooms (streets/intersections)."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator, RoomType
        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        corridors = [r for r in result if r.room_type == RoomType.CORRIDOR]
        # Grid should have some corridor/street tiles
        assert len(corridors) > 0

    def test_small_bounds_still_works(self):
        """Generator handles small bounds (village-sized)."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator
        bounds = (-1, 1, -1, 1, 0, 0)  # 3x3
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert len(result) >= 1  # At least entry room
```

## Implementation

In `src/cli_rpg/procedural_interiors.py`:

1. Add `GridSettlementGenerator` class after `CellularAutomataGenerator` (around line 490):

```python
class GridSettlementGenerator:
    """Grid-based generator for settlement layouts (towns, cities, villages).

    Creates orthogonal street grids with building locations. Streets form
    a grid pattern (CORRIDOR rooms), with buildings placed along streets
    (CHAMBER rooms). Entry point is placed at the center of the settlement.
    """

    # Street spacing (every N tiles in each direction)
    STREET_SPACING = 3

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        """Initialize with SubGrid bounds and random seed."""
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
```

2. Update `generate_interior_layout()` to use GridSettlementGenerator (around line 870):

```python
def generate_interior_layout(
    category: str, bounds: tuple, seed: int
) -> list[RoomTemplate]:
    ...
    # Use GridSettlementGenerator for settlements
    if generator_type == "GridSettlementGenerator":
        generator = GridSettlementGenerator(bounds=bounds, seed=seed)
        return generator.generate()
    ...
```

## Files to Modify

1. `src/cli_rpg/procedural_interiors.py` - Add GridSettlementGenerator class + update factory
2. `tests/test_procedural_interiors.py` - Add TestGridSettlementGenerator test class
