# Implementation Summary: Exits Disappear When Revisiting Locations Bug Fix

## What Was Implemented

Fixed a bug where available exits would change inconsistently when revisiting overworld locations. For example, a location might show "east, north, west" initially, but later show only "east, west" after exploration.

### Root Cause
`get_filtered_directions()` relied on `get_available_directions()` which only returns directions where **Location objects already exist** in the world dict. Since locations are generated on-demand when the player moves, unexplored but passable directions were hidden.

### Solution
Modified `get_filtered_directions()` in `src/cli_rpg/models/location.py` to:

1. **For overworld with WFC**: Use `get_valid_moves()` directly to determine exits based on terrain passability, not location existence
2. **For interior (SubGrid) navigation**: Continue using location-based logic since interiors have predefined bounded layouts

### Files Modified

| File | Change |
|------|--------|
| `src/cli_rpg/models/location.py` | Rewrote `get_filtered_directions()` to use terrain-based exits for overworld |
| `tests/test_wfc_exit_display.py` | Added 3 new test cases in `TestExitStability` class |

### New Test Cases

1. `test_exits_shown_for_unexplored_passable_directions` - Verifies exits are shown for all passable terrain directions even when no Location objects exist there yet

2. `test_exits_stable_across_revisits` - Verifies exits remain consistent when revisiting a location (adding new locations to the world doesn't change displayed exits)

3. `test_subgrid_uses_location_based_exits` - Verifies SubGrid interiors still use location-based logic (only rooms that exist are shown as exits)

## Test Results

- All 11 tests in `test_wfc_exit_display.py` pass
- All 58 WFC-related tests pass
- All 44 location model tests pass
- Full test suite: **3638 tests passed**

## E2E Validation

To validate this fix in E2E testing:
1. Start a new game with WFC enabled (default)
2. Note the exits shown at the starting location
3. Explore in one direction, then return to the starting location
4. Verify the exits shown are identical to the initial observation
5. The exits should be determined by terrain passability (e.g., no exits to water tiles)
