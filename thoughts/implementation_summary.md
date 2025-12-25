# Implementation Summary: Fix Misleading 'use' Error for Equipped Items

## What Was Implemented

Fixed the `use` command to show an appropriate "equipped" message when a player tries to use an item that is currently equipped as a weapon or armor, instead of the misleading "You don't have '<item>' in your inventory" message.

### Files Modified

1. **src/cli_rpg/main.py** - Two locations updated:
   - `handle_exploration_command()` (lines 461-468): Added equipped item check before "not found" error
   - `handle_combat_command()` (lines 351-358): Same fix applied for combat context

2. **tests/test_main_inventory_commands.py** - Added new test class:
   - `TestUseEquippedItem` with 2 tests verifying the spec

### Implementation Details

Both exploration and combat `use` command handlers now check if the item being used is currently equipped before returning the "not found" error. The new message format is:
- `"{Item Name} is currently equipped as your weapon and cannot be used."`
- `"{Item Name} is currently equipped as your armor and cannot be used."`

This matches the pattern already used by `sell` and `drop` commands in the codebase.

## Test Results

- 2 new tests added for the spec (weapon and armor cases)
- All 24 inventory command tests pass
- Full test suite: 1327 passed, 1 skipped

## E2E Validation

To manually verify:
1. Start game, equip a weapon (e.g., `equip iron sword`)
2. Try `use iron sword` - should see "Iron Sword is currently equipped as your weapon and cannot be used."
3. Equip armor and try to use it - should see similar message mentioning "armor"
