# Implementation Summary: Talk Command SubGrid Fix

## What Was Implemented

Fixed a bug where the `talk` command couldn't find NPCs inside SubGrid sublocations (building interiors, dungeons, etc.).

### Root Cause
The `talk` command in `src/cli_rpg/main.py` line 1147 was using:
```python
location = game_state.world.get(game_state.current_location)
```
This only looked in the main world dictionary, not in SubGrid sublocations where interior locations are stored.

### Fix
Changed to use the existing `get_current_location()` method:
```python
location = game_state.get_current_location()
```
This method properly handles both overworld locations (from `game_state.world`) and SubGrid sublocations (from `game_state.current_sub_grid`).

## Files Modified
- `src/cli_rpg/main.py` - Line 1147: Changed world.get() to get_current_location()

## Files Created
- `tests/test_talk_subgrid.py` - 4 new tests verifying the fix:
  - `test_talk_finds_npc_in_subgrid` - Verifies talk finds NPCs in SubGrid
  - `test_talk_to_specific_npc_in_subgrid` - Verifies named NPC selection works
  - `test_talk_npc_not_found_in_subgrid` - Verifies proper error for missing NPC
  - `test_talk_to_merchant_in_subgrid_sets_shop` - Verifies merchant/shop context works

## Test Results
- All 4 new tests: PASSED
- All related talk command tests: PASSED (29 tests)
- Full test suite: 3407 PASSED

## E2E Validation
To manually verify:
1. Start game → Enter any building (e.g., Market, Inn)
2. Use `look` to see NPCs present
3. Use `talk` command - should now work correctly
4. Use `talk <NPC name>` - should find and interact with NPC
