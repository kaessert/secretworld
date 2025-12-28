# Implementation Plan: BSPGenerator for Dungeons, Temples, and Ruins

## Spec

Implement `BSPGenerator` class in `procedural_interiors.py` using Binary Space Partitioning algorithm to generate procedural interior layouts for dungeons, temples, ruins, tombs, crypts, monasteries, and shrines (all categories mapped to `"BSPGenerator"` in `CATEGORY_GENERATORS`).

### Requirements
1. **BSP Tree Structure**: Recursively divide space into partitions until minimum room size reached
2. **Room Generation**: Create rooms within leaf partitions
3. **Connection Generation**: Connect sibling partitions with corridors
4. **3D Support**: Handle multi-level dungeons (z-axis from bounds)
5. **Room Type Assignment**: Place ENTRY, CORRIDOR, CHAMBER, BOSS_ROOM, TREASURE, PUZZLE appropriately
6. **Deterministic**: Same seed produces identical layouts
7. **Bounds-Aware**: Respect 6-tuple bounds `(min_x, max_x, min_y, max_y, min_z, max_z)`

### Public Interface
```python
class BSPNode:
    """Node in BSP tree representing a rectangular partition."""
    x: int
    y: int
    width: int
    height: int
    left: Optional["BSPNode"]
    right: Optional["BSPNode"]
    room: Optional[tuple[int, int, int, int]]  # (x, y, w, h) if leaf with room

class BSPGenerator:
    """Binary Space Partitioning generator for dungeon layouts."""

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        """Initialize with SubGrid bounds and random seed."""

    def generate(self) -> list[RoomTemplate]:
        """Generate layout returning list of RoomTemplate blueprints."""
```

### Algorithm Steps
1. Create root node spanning (min_x to max_x, min_y to max_y) for z=max_z (entry level)
2. Recursively split nodes (horizontal/vertical) until min_size reached
3. Generate rooms in leaf nodes (smaller than partition, with margin)
4. Connect sibling rooms with corridors
5. For multi-level (min_z < max_z): repeat for each z-level, add stairs connecting levels
6. Assign room types: entry at (0,0,max_z), boss at lowest z furthest from entry, treasure/puzzle at dead ends

---

## Tests First (TDD)

Create `tests/test_bsp_generator.py`:

### BSPNode Tests
1. `test_bsp_node_creation` - Node stores x, y, width, height correctly
2. `test_bsp_node_split_horizontal` - Horizontal split creates two children
3. `test_bsp_node_split_vertical` - Vertical split creates two children
4. `test_bsp_node_is_leaf` - Leaf detection (no children)

### BSPGenerator Tests
5. `test_generator_returns_room_templates` - generate() returns list[RoomTemplate]
6. `test_generator_has_entry_room` - Layout has exactly one ENTRY room with is_entry=True
7. `test_entry_room_at_top_level` - Entry room z-coord equals max_z from bounds
8. `test_generator_deterministic` - Same seed produces identical output
9. `test_generator_different_seeds_differ` - Different seeds produce different layouts
10. `test_rooms_within_bounds` - All room coords within specified bounds
11. `test_multi_level_generates_stairs` - Multi-level bounds produce "up"/"down" connections
12. `test_boss_room_at_lowest_level` - BOSS_ROOM placed at min_z
13. `test_connections_are_valid_directions` - All connections are valid (north/south/east/west/up/down)
14. `test_rooms_are_connected` - All rooms reachable from entry via connections

### Integration Tests
15. `test_generate_interior_layout_uses_bsp` - Factory function uses BSPGenerator for "dungeon"
16. `test_category_dungeon_produces_valid_layout` - Dungeon category works end-to-end
17. `test_category_temple_produces_valid_layout` - Temple category works end-to-end

---

## Implementation Steps

### Step 1: Create test file
- File: `tests/test_bsp_generator.py`
- Import from `cli_rpg.procedural_interiors`
- Write all 17 tests (expect failures initially)

### Step 2: Implement BSPNode dataclass
- File: `src/cli_rpg/procedural_interiors.py`
- Add `BSPNode` dataclass with x, y, width, height, left, right, room
- Add `split()` method for horizontal/vertical partitioning
- Add `is_leaf` property
- Run tests 1-4, verify passing

### Step 3: Implement BSPGenerator class
- File: `src/cli_rpg/procedural_interiors.py`
- Add `BSPGenerator` class implementing `GeneratorProtocol`
- Implement `_build_tree()` - recursive BSP partitioning
- Implement `_generate_rooms()` - place rooms in leaf nodes
- Implement `_connect_rooms()` - corridor generation between siblings
- Run tests 5-14, verify passing

### Step 4: Integrate with generate_interior_layout
- File: `src/cli_rpg/procedural_interiors.py`
- Update `generate_interior_layout()` to instantiate and call `BSPGenerator` when `CATEGORY_GENERATORS[category] == "BSPGenerator"`
- Run tests 15-17, verify passing

### Step 5: Run full test suite
- `pytest tests/test_bsp_generator.py -v`
- `pytest` (ensure no regressions in 5064+ tests)

---

## Key Implementation Details

### BSP Split Logic
```python
def split(self, rng: random.Random, min_size: int = 4) -> bool:
    if self.left or self.right:
        return False  # Already split
    if self.width < min_size * 2 and self.height < min_size * 2:
        return False  # Too small to split

    # Choose split direction
    if self.width > self.height * 1.25:
        horizontal = False  # Split vertically
    elif self.height > self.width * 1.25:
        horizontal = True   # Split horizontally
    else:
        horizontal = rng.random() < 0.5

    # Calculate split position (40-60% of dimension)
    max_dim = self.height if horizontal else self.width
    split_pos = rng.randint(int(max_dim * 0.4), int(max_dim * 0.6))

    # Create children
    if horizontal:
        self.left = BSPNode(self.x, self.y, self.width, split_pos)
        self.right = BSPNode(self.x, self.y + split_pos, self.width, self.height - split_pos)
    else:
        self.left = BSPNode(self.x, self.y, split_pos, self.height)
        self.right = BSPNode(self.x + split_pos, self.y, self.width - split_pos, self.height)

    return True
```

### Room Type Assignment
- ENTRY: (0, 0, max_z) - entry point
- BOSS_ROOM: Furthest from entry at min_z level
- TREASURE: Dead-end rooms (1 connection) with 30% probability
- PUZZLE: Dead-end rooms with 20% probability
- CORRIDOR: Rooms connecting two or more other rooms
- CHAMBER: All other rooms (default)
