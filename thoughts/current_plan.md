# Fix: AI Area Generation - Coordinates Outside SubGrid Bounds

## Problem
AI area generation fails when generated locations have coordinates outside SubGrid bounds:
```
AI area generation failed: Coordinates (0, 4) outside bounds (-3, 3, -3, 3)
```

The SubGrid has bounds of (-3, 3, -3, 3) = 7x7 grid, but AI generates locations at y=4 which is outside.

## Root Cause
1. `ai_service.py:_build_area_prompt()` doesn't tell the AI about coordinate bounds
2. `ai_world.py:expand_area()` calls `sub_grid.add_location()` which raises ValueError for out-of-bounds coords
3. One failed placement crashes the entire area generation

## Implementation

### 1. Update area generation prompt with coordinate bounds
**File**: `src/cli_rpg/ai_service.py`, `_build_area_prompt()` method (lines 657-742)

Add to the requirements section (around line 705):
```
6. Relative coordinates must be within bounds: x from -3 to 3, y from -3 to 3 (7x7 grid max)
```

### 2. Add bounds-checking in expand_area() before adding to SubGrid
**File**: `src/cli_rpg/ai_world.py`, in the sub-locations loop (around line 680-690)

Before calling `sub_grid.add_location()`, check if coordinates are within SubGrid bounds and skip with warning if out of bounds:

```python
# Check SubGrid bounds before adding
if not sub_grid.is_within_bounds(rel_x, rel_y):
    logger.warning(
        f"Skipping {name}: coords ({rel_x}, {rel_y}) outside SubGrid bounds {sub_grid.bounds}"
    )
    continue
```

### 3. Add test for out-of-bounds coordinate handling
**File**: `tests/test_ai_world_subgrid.py`

Add test `test_expand_area_skips_out_of_bounds_locations` that:
- Mock AI service returns a location with coords (0, 4) - outside bounds
- Verify the out-of-bounds location is NOT in SubGrid
- Verify in-bounds locations still work correctly
- Verify no exception is raised
