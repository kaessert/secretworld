# Implementation Summary: Cover Item.__str__ heal_amount branch

## What Was Implemented

Added a single test case to `tests/test_item.py` in the `TestItemStringRepresentation` class:

- **New test**: `test_item_str_consumable_with_heal()`
  - Creates a consumable item with `heal_amount=25`
  - Verifies that `str(item)` contains "heals 25 HP"
  - Covers line 114 of `src/cli_rpg/models/item.py`

## Files Modified

- `tests/test_item.py`: Added new test method (lines 388-399)

## Test Results

- All 1322 tests pass (1 skipped)
- `cli_rpg.models.item` coverage increased to 98%
- Line 114 (the `heal_amount > 0` branch in `__str__`) is now covered

## Technical Details

The `Item.__str__()` method builds a stats string that includes heal amount for consumables. The new test exercises this branch by creating a Health Potion with `heal_amount=25` and asserting "heals 25 HP" appears in the string representation.
