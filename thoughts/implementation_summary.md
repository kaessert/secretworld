# Implementation Summary: `dismiss <companion>` Command

## What Was Implemented

Added a `dismiss` command that allows players to remove companions from their party, completing the companion management lifecycle (recruit -> travel with -> dismiss).

### Files Modified

1. **`src/cli_rpg/game_state.py`** (line 55)
   - Added "dismiss" to `KNOWN_COMMANDS` set

2. **`src/cli_rpg/main.py`** (lines 51, 1100-1112)
   - Added help text: `"  dismiss <name>     - Dismiss a companion from your party"`
   - Added command handler with:
     - Error handling for missing name argument
     - Error handling for non-existent companion
     - Case-insensitive name matching
     - Removes companion from `game_state.companions` list

3. **`tests/test_companion_commands.py`** (lines 213-283)
   - Added `TestDismissCommand` class with 4 test cases
   - Added `test_dismiss_in_known_commands` test
   - Updated class docstring for `TestCompanionsInKnownCommands`

## Test Results

All 17 companion command tests pass:
- 3 companions command tests
- 7 recruit command tests
- 4 dismiss command tests (new)
- 3 KNOWN_COMMANDS tests

Full test suite: 2261 tests passed

## Behavior

- `dismiss` (no args): Returns "Dismiss whom? Specify a companion name."
- `dismiss NonExistent`: Returns "No companion named 'NonExistent' in your party."
- `dismiss Elara` (or `dismiss elara`): Removes companion and returns "{name} has left your party."
