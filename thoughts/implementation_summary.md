# Implementation Summary: Fix Confusing `enter` Command Error Message

## What Was Implemented

Fixed a confusing UX issue where typing `enter Dark Cave` at the "Dark Cave" location would show an error listing internal SubGrid room names instead of entering the location.

### Solution
When `enter <name>` fails to match a SubGrid room, the code now checks if `<name>` matches the current overworld location's name (exact or partial match). If so, it automatically redirects to the entry_point.

### Files Modified

1. **`src/cli_rpg/game_state.py`** (~lines 1435-1444)
   - Added logic to detect when user types the parent location name
   - Redirects to entry_point when there's a SubGrid with an entry_point defined
   - Both exact match (`Dark Cave`) and partial match (`dark`) are supported

2. **`tests/test_game_state.py`** (~lines 1216-1305)
   - Added `test_enter_accepts_parent_location_name_with_subgrid` - Tests exact match redirection
   - Added `test_enter_accepts_partial_parent_location_name` - Tests partial match redirection

## Test Results

All tests pass:
- 15/15 tests in `TestEnterExitCommands` class pass
- 21/21 tests in `test_subgrid_navigation.py` pass

## Acceptance Criteria Verified

- `enter Dark Cave` at Dark Cave enters through Cave Entrance
- `enter dark` at Dark Cave enters through Cave Entrance (partial match)
- Original error preserved for genuinely invalid names (existing test `test_enter_invalid_location_shows_available` still passes)
- All existing enter/exit tests continue to pass

## Technical Notes

- The fix is placed AFTER the SubGrid room lookup and traditional sub_locations lookup, so existing behavior takes priority
- Only triggers when `matched_location is None` (i.e., no room was found)
- Uses same case-insensitive matching logic as the rest of the enter command
