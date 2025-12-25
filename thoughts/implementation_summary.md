# Implementation Summary: Armor Unequip Test Coverage

## What was implemented

Added test case `test_unequip_armor_when_inventory_full` to `tests/test_inventory.py` in the `TestInventoryUnequip` class.

This test covers the armor slot path (lines 145-146 in `inventory.py`) for the `unequip()` method when inventory is full - previously only the weapon slot had this test coverage.

## Files modified

- `tests/test_inventory.py`: Added new test method at lines 294-306

## Test results

```
tests/test_inventory.py::TestInventoryUnequip::test_unequip_armor_when_inventory_full PASSED
```

## Technical details

The test verifies that:
1. When armor is equipped and inventory is at capacity
2. Calling `unequip("armor")` returns `False`
3. The armor remains equipped (not lost)

This mirrors the existing `test_unequip_when_inventory_full` test which covers the weapon slot.
