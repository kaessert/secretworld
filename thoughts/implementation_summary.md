# Implementation Summary: Enter/Exit Commands for Hierarchical World Navigation

## What Was Implemented

### New Commands
- **`enter <location>`** - Navigate from an overworld location to a sub-location (e.g., entering a tavern within a city)
- **`exit` / `leave`** - Exit from a sub-location back to its parent overworld landmark

### Files Modified

#### 1. `src/cli_rpg/game_state.py`
- Added `enter`, `exit`, `leave` to `KNOWN_COMMANDS` set (line 56)
- Implemented `enter()` method (lines 582-628):
  - Validates player is at an overworld location (`is_overworld=True`)
  - Supports partial, case-insensitive name matching for sub-locations
  - Uses `entry_point` as default when no argument provided
  - Blocks during NPC conversation
  - Returns location description via `look()` on success

- Implemented `exit_location()` method (lines 630-657):
  - Validates current location has a `parent_location` set
  - Moves player to parent overworld location
  - Blocks during NPC conversation
  - Returns location description via `look()` on success

#### 2. `src/cli_rpg/main.py`
- Added help text for new commands (lines 31-32)
- Added command handlers in `handle_exploration_command()` (lines 524-531):
  - `enter` command handler that joins args for multi-word location names
  - Combined handler for `exit` and `leave` aliases

#### 3. `tests/test_game_state.py`
- Added `TestEnterExitCommands` test class with 11 tests (lines 835-1143):
  1. `test_enter_sublocation_from_overworld` - Basic enter functionality
  2. `test_enter_uses_entry_point_default` - Using entry_point when no arg given
  3. `test_enter_partial_match` - Case-insensitive partial matching
  4. `test_enter_fails_when_not_overworld` - Error when not at overworld
  5. `test_enter_fails_sublocation_not_found` - Error for nonexistent locations
  6. `test_enter_fails_no_arg_no_entrypoint` - Error when no arg and no entry_point
  7. `test_enter_blocked_during_conversation` - Blocked during NPC talk
  8. `test_exit_from_sublocation` - Basic exit functionality
  9. `test_exit_fails_when_no_parent` - Error when no parent location
  10. `test_exit_blocked_during_conversation` - Blocked during NPC talk
  11. `test_leave_alias_works` - Verify `leave` works same as `exit`

## Test Results
- All 11 new tests pass
- All 60 tests in `test_game_state.py` pass
- Full test suite (2421 tests) passes with no regressions

## Design Decisions

1. **Partial Matching**: The `enter` command supports partial, case-insensitive matching (e.g., `enter tav` matches "Tavern") for user convenience.

2. **Entry Point Default**: When `enter` is called without arguments and the overworld has an `entry_point` set, it automatically enters that default location.

3. **Conversation Blocking**: Both `enter` and `exit` are blocked when in conversation with an NPC, consistent with the existing `move()` behavior.

4. **Look Integration**: Both commands return the `look()` output for the destination, providing immediate location context.

## E2E Test Validation
The following scenarios should be validated:
- Player at overworld can `enter <sub-location>` and move inside
- Player inside can `exit` or `leave` to return to overworld
- Both commands show appropriate error messages for invalid operations
- Help text displays the new commands correctly
