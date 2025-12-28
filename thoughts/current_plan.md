# Implementation Plan: CellularAutomataGenerator for Caves and Mines

## Spec

Implement `CellularAutomataGenerator` class in `procedural_interiors.py` using cellular automata algorithm to generate organic, cave-like interior layouts for caves and mines (categories mapped to `"CellularAutomataGenerator"` in `CATEGORY_GENERATORS`).

### Requirements
1. **Cellular Automata Algorithm**: Use 4-5 rule (cell becomes solid if ≥5 neighbors are solid) to generate organic cave shapes
2. **Initial Noise**: Start with random noise (45-55% fill) then apply automata rules 4-5 iterations
3. **Flood Fill Connectivity**: Ensure all traversable cells connect to entry point
4. **3D Support**: Handle multi-level caves (z-axis from bounds)
5. **Room Type Assignment**: ENTRY at top level, BOSS_ROOM at deepest dead-end, TREASURE/PUZZLE at isolated areas
6. **Deterministic**: Same seed produces identical layouts
7. **Bounds-Aware**: Respect 6-tuple bounds `(min_x, max_x, min_y, max_y, min_z, max_z)`
8. **Organic Connections**: Directions based on actual traversable neighbors (not BSP corridors)

### Public Interface
```python
class CellularAutomataGenerator:
    """Cellular automata generator for cave/mine layouts."""

    INITIAL_FILL_PROBABILITY = 0.45  # 45% initial solid cells
    AUTOMATA_ITERATIONS = 4          # Number of smoothing passes
    BIRTH_THRESHOLD = 5              # Become solid if ≥5 neighbors solid
    DEATH_THRESHOLD = 4              # Stay solid if ≥4 neighbors solid

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        """Initialize with SubGrid bounds and random seed."""

    def generate(self) -> list[RoomTemplate]:
        """Generate layout returning list of RoomTemplate blueprints."""
```

### Algorithm Steps
1. Create 2D grid for each z-level, initialize with random noise (45% solid)
2. Apply cellular automata rules 4 iterations:
   - Count 8 neighbors (including diagonals) for each cell
   - Cell becomes solid if ≥5 neighbors are solid
   - Cell becomes open if <4 neighbors are solid
3. Identify largest connected region via flood fill from center
4. Discard disconnected regions (fill them as solid)
5. Convert remaining open cells to RoomTemplates with coordinate-based connections
6. For multi-level: add stair connections between levels
7. Assign room types based on distance from entry and dead-end status

---

## Tests First (TDD)

Create `tests/test_cellular_automata_generator.py`:

### Core Algorithm Tests
1. `test_generator_returns_room_templates` - generate() returns list[RoomTemplate]
2. `test_generator_has_entry_room` - Layout has exactly one ENTRY room with is_entry=True
3. `test_entry_room_at_top_level` - Entry room z-coord equals max_z from bounds
4. `test_generator_deterministic` - Same seed produces identical output
5. `test_generator_different_seeds_differ` - Different seeds produce different layouts
6. `test_rooms_within_bounds` - All room coords within specified bounds

### Cave-Specific Tests
7. `test_all_rooms_connected` - All rooms reachable from entry (flood fill works)
8. `test_organic_layout_not_rectangular` - Layout has irregular shape (not grid-aligned)
9. `test_connections_based_on_adjacency` - Connections reflect actual adjacent rooms
10. `test_dead_ends_exist` - Caves have dead-end rooms (1 connection)

### Multi-Level Tests
11. `test_multi_level_generates_stairs` - Multi-level bounds produce "up"/"down" connections
12. `test_boss_room_at_deepest_level` - BOSS_ROOM placed at min_z

### Room Type Tests
13. `test_treasure_rooms_at_dead_ends` - TREASURE rooms have 1-2 connections
14. `test_connections_are_valid_directions` - All connections are valid (n/s/e/w/up/down)

### Integration Tests
15. `test_generate_interior_layout_uses_cellular` - Factory uses CellularAutomataGenerator for "cave"
16. `test_category_cave_produces_valid_layout` - Cave category works end-to-end
17. `test_category_mine_produces_valid_layout` - Mine category works end-to-end

---

## Implementation Steps

### Step 1: Create test file
- File: `tests/test_cellular_automata_generator.py`
- Import from `cli_rpg.procedural_interiors`
- Write all 17 tests (expect failures initially)

### Step 2: Implement CellularAutomataGenerator class
- File: `src/cli_rpg/procedural_interiors.py`
- Add `CellularAutomataGenerator` class implementing `GeneratorProtocol`
- Implement `_initialize_grid()` - random noise generation
- Implement `_apply_automata()` - cellular automata smoothing
- Implement `_flood_fill()` - connectivity check and region isolation
- Implement `_grid_to_rooms()` - convert grid cells to RoomTemplates
- Implement `_add_connections()` - direction-based connections from adjacency

### Step 3: Handle multi-level caves
- Implement `_generate_level()` - single z-level generation
- Implement `_connect_levels()` - stair placement between z-levels
- Handle z-axis iteration (max_z down to min_z)

### Step 4: Room type assignment
- Implement `_assign_room_types()`:
  - ENTRY at center of max_z level
  - BOSS_ROOM at min_z, furthest from entry
  - TREASURE/PUZZLE at dead ends (30%/20% probability)
  - CORRIDOR for 3+ connections
  - CHAMBER for rest

### Step 5: Integrate with generate_interior_layout
- File: `src/cli_rpg/procedural_interiors.py`
- Update `generate_interior_layout()` to instantiate `CellularAutomataGenerator` when `CATEGORY_GENERATORS[category] == "CellularAutomataGenerator"`

### Step 6: Run full test suite
- `pytest tests/test_cellular_automata_generator.py -v`
- `pytest` (ensure no regressions in 5081+ tests)

---

## Key Implementation Details

### Cellular Automata Core
```python
def _apply_automata(self, grid: list[list[bool]], iterations: int) -> list[list[bool]]:
    """Apply cellular automata rules to smooth the grid."""
    for _ in range(iterations):
        new_grid = [[False] * len(grid[0]) for _ in range(len(grid))]
        for y in range(len(grid)):
            for x in range(len(grid[0])):
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
            if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid):
                if grid[ny][nx]:
                    count += 1
            else:
                count += 1  # Out of bounds counts as solid
    return count
```

### Flood Fill for Connectivity
```python
def _flood_fill(self, grid: list[list[bool]], start_x: int, start_y: int) -> set[tuple[int, int]]:
    """Find all connected open cells from start position."""
    if grid[start_y][start_x]:
        return set()  # Start is solid

    connected = set()
    stack = [(start_x, start_y)]

    while stack:
        x, y = stack.pop()
        if (x, y) in connected:
            continue
        if x < 0 or x >= len(grid[0]) or y < 0 or y >= len(grid):
            continue
        if grid[y][x]:  # Solid cell
            continue

        connected.add((x, y))
        stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])

    return connected
```

### Connection Directions
```python
def _add_connections(self, rooms: list[RoomTemplate]) -> None:
    """Add directional connections based on adjacency."""
    coord_to_room = {r.coords: r for r in rooms}

    for room in rooms:
        x, y, z = room.coords
        # Check each cardinal direction
        for direction, (dx, dy, dz) in DIRECTION_OFFSETS.items():
            neighbor_coord = (x + dx, y + dy, z + dz)
            if neighbor_coord in coord_to_room:
                if direction not in room.connections:
                    room.connections.append(direction)
```

### Room Type Assignment
- ENTRY: Center of max_z level (closest to (0, 0, max_z))
- BOSS_ROOM: Furthest from entry at min_z level
- TREASURE: 30% of dead ends (1 connection)
- PUZZLE: 20% of dead ends
- CORRIDOR: 3+ connections
- CHAMBER: Default
