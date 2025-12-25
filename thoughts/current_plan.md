# Plan: Add test for unequip armor with full inventory

## Task
Add test coverage for `unequip("armor")` when inventory is full (line 145-146 in `inventory.py`).

## Analysis
The existing test `test_unequip_when_inventory_full` only covers the **weapon** slot. The parallel armor slot path (lines 145-146) is untested.

## Implementation

### Add test to `tests/test_inventory.py`

Add to `TestInventoryUnequip` class (after line 292):

```python
def test_unequip_armor_when_inventory_full(self):
    """Test: Cannot unequip armor when inventory is full"""
    inventory = Inventory(capacity=1)
    armor = Item(name="Chainmail", description="Protective", item_type=ItemType.ARMOR)
    other = Item(name="Other", description="Item", item_type=ItemType.MISC)
    inventory.add_item(armor)
    inventory.equip(armor)
    inventory.add_item(other)  # Fill the only slot

    result = inventory.unequip("armor")

    assert result is False
    assert inventory.equipped_armor == armor  # Still equipped
```

### Verify
Run: `pytest tests/test_inventory.py::TestInventoryUnequip::test_unequip_armor_when_inventory_full -v`
