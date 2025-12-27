# Implementation Summary: Enter Command Entry Point Restriction

## What Was Implemented

The implementation restricts the `enter` command to only allow entering through designated entry points when a location has a `sub_grid` (interior grid system). This prevents players from teleporting directly into any interior room.

### Changes Made

1. **`src/cli_rpg/models/location.py`**:
   - `get_layered_description()` (lines 259-271): Now shows only the entry point in the "Enter:" line when `sub_grid` exists. Falls back to showing all `sub_locations` for legacy locations.
   - `__str__()` (lines 470-481): Same logic applied for consistency in string representation.

2. **`src/cli_rpg/game_state.py`**:
   - `enter()` method (lines 829-842): Validates that only entry point locations (those with `is_exit_point=True`) can be entered directly. Rejects attempts to enter non-entry-point rooms with a helpful error message directing the player to the entry point.

### Test Coverage

Created `tests/test_enter_entry_point.py` with 9 tests covering:
- `test_enter_shows_only_entry_point_with_sub_grid` - Description shows only entry point
- `test_enter_shows_entry_point_from_is_exit_point_fallback` - Falls back to `is_exit_point` when no explicit `entry_point`
- `test_enter_legacy_sub_locations_shows_all` - Legacy locations still show all sub_locations
- `test_str_shows_only_entry_point_with_sub_grid` - `__str__()` shows only entry point
- `test_str_legacy_shows_all_sub_locations` - Legacy behavior preserved in `__str__()`
- `test_enter_command_allows_entry_point` - Entry point access works
- `test_enter_command_rejects_non_entry_point` - Non-entry rooms blocked
- `test_enter_command_rejects_treasury_directly` - Additional room rejection test
- `test_enter_no_argument_uses_entry_point` - No-argument enter uses default entry point

## Test Results

All tests pass:
- `tests/test_enter_entry_point.py`: 9 passed
- `tests/test_location.py`: 44 passed
- `tests/test_game_state.py`: 44 passed
- `tests/test_world_grid.py`: 47 passed

Total: 135 tests passed in related test files.

## Design Decisions

1. **Entry point discovery**: When `entry_point` field is not set, the code searches the sub_grid for the first location with `is_exit_point=True`.

2. **Backward compatibility**: Legacy locations with only `sub_locations` list (no `sub_grid`) continue to show all sub-locations and allow direct entry to any of them.

3. **Error messages**: When attempting to enter a non-entry-point room, the error message explicitly names the correct entry point to help players.

## E2E Validation

To validate in-game:
1. Navigate to an overworld location with a sub_grid (e.g., Castle Ruins)
2. Verify "Enter:" shows only the entry point
3. Try `enter Council Chamber` - should fail with message mentioning Entry Hall
4. Try `enter Entry Hall` - should succeed
5. Navigate internally to reach other rooms
