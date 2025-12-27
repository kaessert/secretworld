# Issue 20: Procedural Dungeon Layouts

## Spec

Add category-specific layout algorithms to `_generate_area_layout()` and `_generate_area_layout_3d()` so AI-generated interiors feel structurally distinct. Currently all areas use a simple branching pattern regardless of category.

**Layout Types by Category:**
| Layout | Categories | Structure |
|--------|------------|-----------|
| Linear | cave, mine | Corridor progression: entry -> room -> corridor -> room (size rooms in a line) |
| Branching | forest, ruins, wilderness | Current default - entry point with perpendicular branches |
| Hub | temple, monastery, shrine | Central hub at (0,0) with 4 spokes (N/S/E/W) radiating outward |
| Maze | dungeon | Grid-based with multiple paths, dead ends, loops |

**Secret Passages:**
- 10-20% chance per layout to add 1 secret passage
- Connects non-adjacent rooms (Manhattan distance >= 2)
- Marked with `is_secret_passage=True` on Location exit

## Tests (tests/test_procedural_layouts.py)

### Unit Tests - Layout Generators

1. `test_linear_layout_produces_corridor_shape` - Linear layout for cave produces coords in a line (all same x OR all same y)
2. `test_linear_layout_entry_at_origin` - Entry point is (0,0)
3. `test_linear_layout_respects_size` - Returns requested number of coords

4. `test_hub_layout_has_central_room` - Hub layout has entry at (0,0)
5. `test_hub_layout_four_spokes` - Hub layout creates rooms extending in cardinal directions
6. `test_hub_layout_respects_size` - Returns requested number of coords

7. `test_maze_layout_has_multiple_branches` - Maze layout has coords with multiple neighbors
8. `test_maze_layout_has_dead_ends` - Maze layout includes dead-end coords (1 neighbor only)
9. `test_maze_layout_respects_size` - Returns requested number of coords

10. `test_branching_layout_unchanged` - Existing branching behavior preserved for forest/ruins

### Unit Tests - Category Selection

11. `test_layout_selection_cave_uses_linear` - "cave" category triggers linear layout
12. `test_layout_selection_temple_uses_hub` - "temple" category triggers hub layout
13. `test_layout_selection_dungeon_uses_maze` - "dungeon" category triggers maze layout
14. `test_layout_selection_forest_uses_branching` - "forest" category uses branching (default)
15. `test_layout_selection_unknown_uses_branching` - Unknown category falls back to branching

### Unit Tests - Secret Passages

16. `test_secret_passage_connects_non_adjacent` - Secret passage connects rooms >= 2 Manhattan distance apart
17. `test_secret_passage_returns_valid_structure` - Secret passage has from_coord, to_coord, is_secret_passage fields

### Integration Tests

18. `test_generate_subgrid_uses_category_layout` - `generate_subgrid_for_location()` selects layout by category
19. `test_3d_layout_applies_category_patterns` - `_generate_area_layout_3d()` respects category on each z-level

## Implementation Steps

### 1. Add layout type constants and category mapping (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

Add at module level (near other constants):
```python
from enum import Enum, auto

class LayoutType(Enum):
    LINEAR = auto()      # Corridor-style progression
    BRANCHING = auto()   # Current default behavior
    HUB = auto()         # Central room with spokes
    MAZE = auto()        # Multiple paths with dead ends

CATEGORY_LAYOUTS: dict[str, LayoutType] = {
    # Linear (progression-focused)
    "cave": LayoutType.LINEAR,
    "mine": LayoutType.LINEAR,
    # Hub (central with spokes)
    "temple": LayoutType.HUB,
    "monastery": LayoutType.HUB,
    "shrine": LayoutType.HUB,
    # Maze (exploration-focused)
    "dungeon": LayoutType.MAZE,
    # Everything else uses BRANCHING (forest, ruins, wilderness, etc.)
}
```

### 2. Rename existing layout logic to `_generate_branching_layout()` (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

Extract the current `_generate_area_layout()` body into `_generate_branching_layout()`:
```python
def _generate_branching_layout(self, size: int, entry_direction: str) -> list[tuple[int, int]]:
    """Generate branching layout - perpendicular branches from primary direction.

    This is the original/default layout algorithm.
    """
    # ... existing implementation (lines 2940-2993)
```

### 3. Add `_generate_linear_layout()` method (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

```python
def _generate_linear_layout(self, size: int, entry_direction: str) -> list[tuple[int, int]]:
    """Generate linear corridor layout for caves/mines.

    Creates a straight line of rooms extending away from entry.
    Entry at (0,0), extending in opposite direction from entry.

    Example (entering from south, size=5):
    (0,0) -> (0,1) -> (0,2) -> (0,3) -> (0,4)
    """
    opposite_map = {
        "north": (0, 1), "south": (0, -1),
        "east": (1, 0), "west": (-1, 0),
    }
    direction = opposite_map.get(entry_direction, (0, 1))

    coords = [(0, 0)]
    for i in range(1, size):
        coords.append((direction[0] * i, direction[1] * i))
    return coords
```

### 4. Add `_generate_hub_layout()` method (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

```python
def _generate_hub_layout(self, size: int, entry_direction: str) -> list[tuple[int, int]]:
    """Generate hub layout for temples/shrines.

    Central room at (0,0) with 4 spokes in cardinal directions.
    Distributes rooms evenly across spokes, extending outward.

    Example (size=9):
           (0,2)
             |
    (-2,0)-(-1,0)-(0,0)-(1,0)-(2,0)
             |
           (0,-1)
           (0,-2)
    """
    coords = [(0, 0)]  # Central hub

    # Four spokes: N, S, E, W
    spokes = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    rooms_per_spoke = (size - 1) // 4
    extra = (size - 1) % 4

    for i, (dx, dy) in enumerate(spokes):
        spoke_rooms = rooms_per_spoke + (1 if i < extra else 0)
        for dist in range(1, spoke_rooms + 1):
            coords.append((dx * dist, dy * dist))
            if len(coords) >= size:
                return coords

    return coords
```

### 5. Add `_generate_maze_layout()` method (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

```python
def _generate_maze_layout(self, size: int, entry_direction: str) -> list[tuple[int, int]]:
    """Generate maze layout for dungeons.

    Uses random walk with backtracking to create exploration-focused layout.
    Creates multiple branches, dead ends, and optional loops.
    """
    import random

    coords = [(0, 0)]
    coord_set = {(0, 0)}
    stack = [(0, 0)]  # For backtracking
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while len(coords) < size and stack:
        current = stack[-1]

        # Find unvisited neighbors
        neighbors = []
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor not in coord_set:
                neighbors.append(neighbor)

        if neighbors:
            # Random walk to a neighbor
            next_coord = random.choice(neighbors)
            coords.append(next_coord)
            coord_set.add(next_coord)
            stack.append(next_coord)
        else:
            # Dead end - backtrack
            stack.pop()

    return coords
```

### 6. Modify `_generate_area_layout()` to dispatch by category (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

Update signature and add dispatch:
```python
def _generate_area_layout(
    self,
    size: int,
    entry_direction: str,
    category: Optional[str] = None
) -> list[tuple[int, int]]:
    """Generate relative coordinates for area locations.

    Dispatches to category-specific layout generator.
    """
    layout_type = CATEGORY_LAYOUTS.get(category.lower(), LayoutType.BRANCHING) if category else LayoutType.BRANCHING

    if layout_type == LayoutType.LINEAR:
        return self._generate_linear_layout(size, entry_direction)
    elif layout_type == LayoutType.HUB:
        return self._generate_hub_layout(size, entry_direction)
    elif layout_type == LayoutType.MAZE:
        return self._generate_maze_layout(size, entry_direction)
    else:
        return self._generate_branching_layout(size, entry_direction)
```

### 7. Update `_generate_area_layout_3d()` to pass category to 2D fallback (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

At line ~3023, update single-level fallback:
```python
if min_z == max_z == 0:
    coords_2d = self._generate_area_layout(size, entry_direction, category)  # Pass category
    return [(x, y, 0) for x, y in coords_2d]
```

### 8. Add `_generate_secret_passage()` helper (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

```python
def _generate_secret_passage(
    self,
    coords: list[tuple[int, int]],
    probability: float = 0.15
) -> Optional[dict]:
    """Potentially generate a secret passage connecting non-adjacent rooms.

    Returns:
        Dict with from_coord, to_coord, is_secret_passage or None
    """
    import random

    if random.random() > probability or len(coords) < 4:
        return None

    # Find pairs of non-adjacent coords (Manhattan distance >= 2)
    valid_pairs = []
    for i, c1 in enumerate(coords):
        for c2 in coords[i+1:]:
            dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
            if dist >= 2:
                valid_pairs.append((c1, c2))

    if not valid_pairs:
        return None

    from_coord, to_coord = random.choice(valid_pairs)
    return {
        "from_coord": from_coord,
        "to_coord": to_coord,
        "is_secret_passage": True,
    }
```

### 9. Update callers to pass category (ai_world.py)

**File:** `src/cli_rpg/ai_world.py`

In `generate_area_with_context()` (~line 2860 in ai_service.py), pass category to layout:
```python
# Get category from context or first location hint
category = region_context.location_type_hint if region_context else None
coords = self._generate_area_layout(size, entry_direction, category)
```

### 10. Store secret passages on SubGrid (world_grid.py)

**File:** `src/cli_rpg/world_grid.py`

Add field to SubGrid:
```python
@dataclass
class SubGrid:
    ...
    secret_passages: list[dict] = field(default_factory=list)
```

Secret passages integrate with existing secrets system - when a "hidden door" secret is discovered via `search`, it can reveal a secret passage to a non-adjacent room.

## Summary of File Changes

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_service.py` | Add `LayoutType` enum, `CATEGORY_LAYOUTS` dict, `_generate_linear_layout()`, `_generate_hub_layout()`, `_generate_maze_layout()`, `_generate_secret_passage()`. Rename existing logic to `_generate_branching_layout()`. Update `_generate_area_layout()` signature and dispatch. |
| `src/cli_rpg/world_grid.py` | Add `secret_passages` field to SubGrid |
| `tests/test_procedural_layouts.py` | NEW - 19 tests covering layouts, category selection, and secret passages |
