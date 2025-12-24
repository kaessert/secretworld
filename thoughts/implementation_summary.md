# Implementation Summary: Fix Inconsistent Save Behavior During Combat

## What Was Implemented

Fixed the save exploit during combat where `quit + y` allowed saving and losing combat state, enabling players to escape losing fights.

### Changes Made

**1. Modified `src/cli_rpg/main.py` (lines 299-307)**
- Changed quit prompt during combat from "Save before quitting?" to "Quit without saving?"
- Removed the save functionality during combat quit (matching `save` command behavior)
- Added explicit warning that saving is disabled during combat
- Answering 'n' now cancels the quit and returns to combat

**2. Updated tests in `tests/test_main_combat_integration.py`**
- Updated `test_quit_command_during_combat_exits_game` to use 'y' as the quit confirmation
- Replaced old `test_quit_command_with_save_saves_game` with:
  - `test_quit_during_combat_does_not_offer_save` - verifies save is NOT called
  - `test_quit_during_combat_cancel_returns_to_combat` - verifies 'n' cancels quit

## Test Results

All 732 tests pass (1 skipped).

## Behavior Change

| Action | Before | After |
|--------|--------|-------|
| `save` during combat | Blocked with error | Blocked with error |
| `quit` during combat | Offers save option (exploit!) | No save option, warns about lost progress |
| `quit + y` during combat | Saves and quits | Quits without saving |
| `quit + n` during combat | Quits without saving | Cancels quit, returns to combat |

## E2E Validation

To manually test:
1. Start a new game and enter combat
2. Type `quit` during combat
3. Verify the message says "Saving is disabled during combat" and "combat progress will be lost"
4. Verify typing 'n' returns to combat
5. Verify typing 'y' exits without saving
