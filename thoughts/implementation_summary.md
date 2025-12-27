# Implementation Summary: SubGrid Exit Point Visual Indicator

## Status: COMPLETE

All related tests pass (92 total tests across 3 test files).

## What Was Implemented

Added a visual indicator "Exit to: <overworld_location>" when viewing a location inside a SubGrid that has `is_exit_point=True`. This helps players understand where the exit command will take them when they're exploring dungeons, caves, or other interior locations.

### Files Modified

1. **`src/cli_rpg/models/location.py`** (lines 279-281)
   - Added 3 lines to `get_layered_description()` method after the exits display
   - Shows "Exit to: {parent_name}" with cyan color formatting when:
     - `is_exit_point` is True
     - `sub_grid` is not None (player is inside a SubGrid)
     - `sub_grid.parent_name` exists

2. **`tests/test_exit_points.py`** (lines 241-291)
   - Added new test class `TestExitPointDisplay` with 3 test methods:
     - `test_exit_point_shows_exit_to_in_description` - verifies the indicator appears
     - `test_non_exit_point_does_not_show_exit_to` - verifies indicator doesn't appear for non-exit locations
     - `test_exit_to_uses_color_formatting` - verifies cyan ANSI color is applied

## Test Results

```
tests/test_exit_points.py - 19 passed
tests/test_location.py - 44 passed
tests/test_world_grid.py - 29 passed
```

All related tests pass, confirming no regressions.

## Design Decisions

1. **Placement**: The "Exit to:" line is placed after the "Exits:" line (cardinal directions) but before the "Enter:" line, maintaining logical grouping of navigation information.

2. **Color formatting**: Uses the existing `colors.location()` function for consistent cyan coloring of location names throughout the UI.

3. **Conditional display**: Only shows when all conditions are met (exit point + inside SubGrid + parent name exists), ensuring it doesn't appear in inappropriate contexts.

## E2E Test Validation

To manually verify:
1. Run `cli-rpg --demo --skip-character-creation`
2. Navigate to a location with an enterable SubGrid (e.g., a mine or dungeon)
3. Enter the SubGrid with `enter <name>`
4. Run `look` command at the entrance/exit point
5. Verify "Exit to: <parent location name>" appears in the description
