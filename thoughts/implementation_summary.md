# Implementation Summary: Improve Equip Command Error Message

## What Was Implemented

Enhanced the error message when players try to equip non-equippable items (consumables/misc) to provide helpful guidance.

### Changes Made

**File: `src/cli_rpg/main.py`**
1. Added `ItemType` to the import statement (line 6)
2. Updated the equip command error handling (lines 433-437):
   - For consumable items: Returns message explaining only weapons/armor can be equipped AND suggests using the `use` command
   - For other non-equippable items (misc): Returns message explaining only weapons/armor can be equipped

**File: `tests/test_main_coverage.py`**
1. Updated `test_equip_misc_item_fails` to verify the new error message mentions "weapon" or "armor"
2. Added new test `test_equip_consumable_suggests_use_command` to verify consumables get a special message suggesting the `use` command

## Test Results

All tests passed:
- `tests/test_main_coverage.py::TestEquipCannotEquip::test_equip_misc_item_fails` - PASSED
- `tests/test_main_coverage.py::TestEquipCannotEquip::test_equip_consumable_suggests_use_command` - PASSED

Full test suite verification: 88 tests passed (test_main_inventory_commands.py + test_main_coverage.py)

## E2E Validation

The following scenarios should work correctly:
1. Player with a Health Potion in inventory types `equip Health Potion` → Gets message: "You can only equip weapons or armor. Use 'use Health Potion' for consumables."
2. Player with a Key (misc item) in inventory types `equip Key` → Gets message: "You can only equip weapons or armor."
