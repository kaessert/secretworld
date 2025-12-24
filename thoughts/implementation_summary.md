# Implementation Summary: Fix `talk` command error message

## What was implemented

Fixed the misleading error message when using `talk` without arguments in a location with no NPCs.

### Changes:

1. **`src/cli_rpg/main.py`** (lines 389-394):
   - Modified the `talk` command handler to check if the current location has NPCs before showing the generic "Talk to whom?" message
   - When location has no NPCs: Shows "There are no NPCs here to talk to."
   - When location has NPCs: Shows "Talk to whom? Specify an NPC name."

2. **`tests/test_shop_commands.py`**:
   - Added `test_talk_no_args_no_npcs_in_location()` test to verify the new behavior
   - Added spec comment to the existing `test_talk_no_args()` test

## Test results

All 23 shop command tests pass:
- 4 talk command tests (including the new one)
- 8 buy command tests
- 5 sell command tests
- 2 shop command tests
- 4 parse command tests

## Technical details

The fix adds a location lookup before the existing NPC name check to determine which error message to show. This provides better UX by telling users when there are simply no NPCs to talk to, rather than asking them to specify an NPC name when none exist.
