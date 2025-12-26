# Implementation Summary: AI Area Generation Bounds Fix

## Problem Fixed
AI area generation was failing when AI-generated locations had coordinates outside the SubGrid bounds (-3, 3, -3, 3). The error was:
```
AI area generation failed: Coordinates (0, 4) outside bounds (-3, 3, -3, 3)
```

## Changes Made

### 1. `src/cli_rpg/ai_world.py` (lines 683-689)
Added bounds checking before adding sub-locations to SubGrid:
- Check `sub_grid.is_within_bounds(rel_x, rel_y)` before calling `add_location()`
- Skip out-of-bounds locations with a warning log message
- Prevents entire area generation from crashing due to one bad coordinate

### 2. `src/cli_rpg/ai_service.py` (line 705)
Updated the area generation prompt to inform the AI about coordinate bounds:
- Added requirement #6: "Relative coordinates must be within bounds: x from -3 to 3, y from -3 to 3 (7x7 grid max)"
- This proactively guides the AI to stay within bounds, reducing the need for the fallback skip logic

### 3. `tests/test_ai_world_subgrid.py` (lines 461-514)
Added new test `test_expand_area_skips_out_of_bounds_locations`:
- Verifies out-of-bounds locations are skipped without exception
- Verifies in-bounds locations still work correctly
- Tests the specific scenario from the bug report (y=4 outside bounds)

## Test Results
- All 12 SubGrid tests pass
- All 125 AI world + world grid tests pass
- All 57 AI service tests pass

## Design Decisions
- **Graceful degradation**: Skip invalid locations rather than crashing. This ensures partial area generation succeeds even if AI occasionally generates bad coordinates.
- **Defense in depth**: Both prompt guidance (prevention) and runtime bounds checking (fallback) are implemented.
- **Logging**: Out-of-bounds skips are logged as warnings for debugging/monitoring.

## E2E Validation
The fix should be validated by:
1. Playing the game and entering AI-generated areas
2. Verifying no "Coordinates outside bounds" errors occur
3. Confirming that areas with many sub-locations still generate correctly
