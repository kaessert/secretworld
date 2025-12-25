# Implementation Summary: Fix Equip Already-Equipped Error Message

## What Was Implemented

Fixed the misleading error message when running `equip <item>` on an already-equipped item. Previously showed "You don't have '{item}' in your inventory.", now correctly shows "{Item Name} is already equipped."

## Files Modified

1. **`src/cli_rpg/main.py`** (lines 440-448): Added check within the `equip` command handler to detect if the item being equipped is already equipped as weapon or armor, before returning the generic "not found" error.

2. **`tests/test_main_inventory_commands.py`**: Added `TestEquipAlreadyEquipped` test class with two tests:
   - `test_equip_already_equipped_weapon`: Verifies weapon case
   - `test_equip_already_equipped_armor`: Verifies armor case

## Implementation Details

The fix follows the same pattern as the existing `use` command fix for equipped items:
- When `find_item_by_name` returns `None` (item not in general inventory)
- Check if equipped_weapon or equipped_armor matches the item name (case-insensitive)
- Return appropriate "already equipped" message instead of "don't have" message

## Test Results

```
26 passed in 0.36s
```

All inventory command tests pass, including the 2 new tests for the fix.
