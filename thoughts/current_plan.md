# Region Planning System Implementation Plan

## Overview
Divide the world into ~16x16 tile regions and pre-generate `RegionContext` when approaching region boundaries. This provides cohesive regional theming and is the foundation for terrain-biased WFC.

## Spec

**Region Size**: 16x16 tiles (256 tiles per region)
**Boundary Trigger**: Pre-generate when player is within 2 tiles of unvisited region boundary
**Caching**: Region contexts cached by region coordinates `(region_x, region_y)`

### Key Functions

1. `get_region_coords(x, y) -> (region_x, region_y)`: Convert world coords to region coords
2. `get_region_context_for_coords(x, y) -> RegionContext`: Look up by world coords (uses region cache)
3. `check_region_boundary_proximity(x, y) -> list[(region_x, region_y)]`: Return adjacent regions within 2 tiles
4. `pregenerate_adjacent_regions(x, y)`: Trigger async pre-generation of nearby regions

### Integration Points

- `GameState.move()`: After successful move, check for nearby region boundaries and pre-generate
- `GameState.get_or_create_region_context()`: Refactor to use region-based lookup instead of per-coordinate

## Tests (TDD)

Create `tests/test_region_planning.py`:

1. `test_get_region_coords_returns_floor_division` - (0,0) -> (0,0), (15,15) -> (0,0), (16,0) -> (1,0)
2. `test_get_region_coords_handles_negative` - (-1,-1) -> (-1,-1), (-16,-16) -> (-1,-1)
3. `test_check_region_boundary_proximity_center` - (8,8) returns empty list (far from boundary)
4. `test_check_region_boundary_proximity_near_edge` - (14,8) returns [(1,0)] (2 tiles from east edge)
5. `test_check_region_boundary_proximity_corner` - (14,14) returns [(1,0), (0,1), (1,1)] (near 3 regions)
6. `test_pregenerate_adjacent_regions_caches_contexts` - After call, region_contexts populated
7. `test_move_triggers_pregeneration_near_boundary` - Moving to (14,8) triggers pregeneration
8. `test_region_context_lookup_by_world_coords` - Different world coords in same region return same context
9. `test_region_context_persists_across_save_load` - Region contexts serialized with region coords as keys

## Implementation Steps

### 1. Add region helper functions to `world_tiles.py`

```python
REGION_SIZE = 16  # 16x16 tiles per region
REGION_BOUNDARY_PROXIMITY = 2  # Pre-generate when within 2 tiles of boundary

def get_region_coords(world_x: int, world_y: int) -> tuple[int, int]:
    """Convert world coordinates to region coordinates."""
    return (world_x // REGION_SIZE, world_y // REGION_SIZE)

def check_region_boundary_proximity(
    world_x: int, world_y: int
) -> list[tuple[int, int]]:
    """Return adjacent region coords if player is within REGION_BOUNDARY_PROXIMITY of boundary."""
    # Implementation in step 3
```

### 2. Refactor `GameState.region_contexts` storage

Change from:
```python
region_contexts: dict[tuple[int, int], RegionContext] = {}  # keyed by world coords
```

To:
```python
region_contexts: dict[tuple[int, int], RegionContext] = {}  # keyed by REGION coords
```

### 3. Update `GameState.get_or_create_region_context()`

```python
def get_or_create_region_context(
    self, coords: tuple[int, int], terrain_hint: str = "wilderness"
) -> RegionContext:
    """Get cached region context for the region containing coords."""
    from cli_rpg.world_tiles import get_region_coords, REGION_SIZE

    # Convert to region coordinates
    region_x, region_y = get_region_coords(*coords)
    region_key = (region_x, region_y)

    # Return cached if available
    if region_key in self.region_contexts:
        return self.region_contexts[region_key]

    # Generate new context for this region
    # Use center of region as coordinates
    center_x = region_x * REGION_SIZE + REGION_SIZE // 2
    center_y = region_y * REGION_SIZE + REGION_SIZE // 2

    # ... AI generation or default fallback ...
    self.region_contexts[region_key] = region_context
    return region_context
```

### 4. Add pre-generation trigger to `GameState.move()`

After successful move, before returning:
```python
# Pre-generate adjacent region contexts if near boundary
from cli_rpg.world_tiles import check_region_boundary_proximity
adjacent_regions = check_region_boundary_proximity(*target_coords)
for region_coords in adjacent_regions:
    # Pre-generate (this will cache if not already present)
    self._pregenerate_region(region_coords)
```

### 5. Update serialization

Ensure `to_dict()` and `from_dict()` use region coords as keys (already compatible format).

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Add `REGION_SIZE`, `get_region_coords()`, `check_region_boundary_proximity()` |
| `src/cli_rpg/game_state.py` | Refactor `get_or_create_region_context()` to use region coords, add pre-generation in `move()` |
| `tests/test_region_planning.py` | NEW - 9 tests for region planning system |

## Verification

```bash
pytest tests/test_region_planning.py -v
pytest tests/test_game_state_context.py -v  # Ensure existing tests still pass
pytest --cov=src/cli_rpg/world_tiles --cov=src/cli_rpg/game_state
```
