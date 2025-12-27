# Implementation Summary: Fix "bye" command error message

## What was implemented

Fixed the error message displayed when typing "bye" outside of NPC conversation mode. Previously, it would suggest "buy" (which is also contextual), now it provides a helpful contextual message explaining that "bye" is for ending conversations.

### Files Modified

1. **src/cli_rpg/main.py** (line 2316-2318):
   - Added special case handling for "bye" in the unknown command handler
   - Returns contextual message: "The 'bye' command ends conversations. Use it while talking to an NPC."

2. **tests/test_main.py**:
   - Added test `test_bye_command_outside_talk_mode` that verifies:
     - "buy" is NOT suggested when typing "bye"
     - The message mentions "bye" and explains it's for conversations/NPC interactions

## Test Results

- All 6 tests in test_main.py pass
- Full test suite: 3662 tests pass

## Technical Details

The fix intercepts the "bye" command in `handle_exploration_command()` before it reaches the generic `suggest_command()` function. This prevents the string similarity matching from incorrectly suggesting "buy".
