# Implementation Summary: Fix ai_world.py expand_area() to Use SubGrid (Phase 1, Step 5)

## What Was Implemented

Fixed the `expand_area()` function in `src/cli_rpg/ai_world.py` to properly use SubGrid for sub-locations instead of adding all generated locations to the overworld.

### Changes Made

#### 1. Import SubGrid (line 10)
```python
from cli_rpg.world_grid import WorldGrid, SubGrid, DIRECTION_OFFSETS
```

#### 2. Store Relative Coordinates (line 611)
Added `relative_coords` to `placed_locations` dict for later use in SubGrid placement:
```python
"relative_coords": (rel_x, rel_y),
```

#### 3. Replace World Dict Logic with SubGrid Logic (lines 667-701)
Replaced the old code that added ALL locations to world dict with new logic that:
- Creates a SubGrid for sub-locations when there are multiple locations
- Adds only the entry location to the world dict
- Places sub-locations in the entry's SubGrid
- Sets `is_exit_point=True` on entry and first sub-location
- Uses SubGrid bounds of `(-3, 3, -3, 3)` for 7x7 areas

### Behavior Change

**Before (broken):**
- Entry location + all sub-locations added to overworld `world` dict with coordinates
- All locations show on worldmap
- Players move between rooms with `go north/south/east/west`

**After (fixed):**
- Entry location added to overworld `world` dict with coordinates
- Sub-locations added to entry's `sub_grid` (no overworld coordinates)
- Only entry shows on worldmap
- Players use `enter <name>` to go inside, `exit` to leave
- Cardinal movement works inside the SubGrid

## Files Modified

| File | Change |
|------|--------|
| `src/cli_rpg/ai_world.py` | Modified expand_area() to use SubGrid for sub-locations |
| `tests/test_ai_world_subgrid.py` | NEW: 11 tests for SubGrid integration |
| `tests/test_ai_world_hierarchy.py` | Updated 4 tests to access sub-locations via SubGrid |
| `tests/test_ai_world_generation.py` | Updated 4 tests for new SubGrid behavior |
| `tests/test_area_generation.py` | Updated 2 tests for new SubGrid behavior |
| `tests/test_ai_location_category.py` | Updated 1 test for new SubGrid behavior |

## Test Results

All 3253 tests pass, including:
- 11 new tests in `tests/test_ai_world_subgrid.py`
- 26 tests in `tests/test_ai_world_hierarchy.py`
- 21 tests in `tests/test_subgrid_navigation.py`
- Full test suite runs in ~65 seconds

## E2E Tests Should Validate

1. **Area expansion creates entry with SubGrid**: When `expand_area()` is called, verify entry location has `sub_grid` attached
2. **Sub-locations not in world dict**: Verify sub-locations are NOT accessible via `world["SubLocationName"]`
3. **Sub-locations accessible via SubGrid**: Verify sub-locations can be found via `entry.sub_grid.get_by_name("SubLocationName")`
4. **Entry marked as exit point**: Verify `entry.is_exit_point == True`
5. **First sub-location marked as exit point**: Verify first sub-location has `is_exit_point == True`
6. **Navigation works**: Player can enter via `enter`, move around with cardinal directions, and exit via `exit`
