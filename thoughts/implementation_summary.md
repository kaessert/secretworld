# Implementation Summary: Fix Confusing Error Message When Selling Equipped Items

## What Was Implemented

Added a helpful error message when a player tries to sell an equipped item, replacing the confusing "You don't have X in your inventory" message with clear guidance on how to unequip the item first.

### Files Modified

1. **`src/cli_rpg/main.py`** (lines 371-386)
   - Added check for equipped weapon/armor when item not found in inventory
   - Returns specific message explaining the item is equipped with unequip instructions

2. **`tests/test_shop_commands.py`** (lines 127-149)
   - Added `test_sell_equipped_weapon_shows_helpful_message`
   - Added `test_sell_equipped_armor_shows_helpful_message`

### Behavior Change

**Before**: `"You don't have 'battle axe' in your inventory."`

**After**: `"You can't sell Battle Axe because it's currently equipped. Unequip it first with 'unequip weapon'."`

(or `'unequip armor'` for armor items)

## Test Results

- All 5 sell command tests pass
- Full test suite: 692 passed, 1 skipped
- No regressions detected

## E2E Validation

To manually verify:
1. Start the game and create a character
2. Find/buy a weapon or armor
3. Equip the item
4. Visit a merchant (talk command)
5. Try to sell the equipped item
6. Verify the helpful message appears with unequip instructions
