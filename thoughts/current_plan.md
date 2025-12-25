# Plan: Cover Remaining Lines in `models/inventory.py`

## Uncovered Lines Analysis

Coverage report shows `inventory.py` at 88% with missing lines:
- **Line 143**: `return False` when `unequip("armor")` called with no armor equipped
- **Line 151**: `return False` when `unequip()` called with invalid slot name
- **Lines 241-255**: `__str__` method (string representation)

## Tests to Add

### 1. Test `unequip("armor")` with no armor equipped
```python
def test_unequip_armor_empty_slot(self):
    """Test: Unequip armor returns False when no armor equipped"""
    inventory = Inventory()
    result = inventory.unequip("armor")
    assert result is False
```

### 2. Test `unequip()` with invalid slot name
```python
def test_unequip_invalid_slot(self):
    """Test: Unequip invalid slot returns False"""
    inventory = Inventory()
    result = inventory.unequip("invalid_slot")
    assert result is False
```

### 3. Test `__str__` method - Add new test class

```python
class TestInventoryStr:
    """Test inventory string representation."""

    def test_str_empty_inventory(self):
        """Test: String representation of empty inventory"""
        inventory = Inventory()
        result = str(inventory)
        assert "Inventory" in result
        assert "(0/20)" in result
        assert "No items" in result

    def test_str_with_items(self):
        """Test: String representation with items"""
        inventory = Inventory()
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)
        result = str(inventory)
        assert "Inventory" in result
        assert "(1/20)" in result
        assert "Iron Sword" in result

    def test_str_with_equipped_weapon(self):
        """Test: String representation with equipped weapon"""
        inventory = Inventory()
        sword = Item(name="Iron Sword", description="Sharp", item_type=ItemType.WEAPON)
        inventory.add_item(sword)
        inventory.equip(sword)
        result = str(inventory)
        assert "Weapon" in result
        assert "Iron Sword" in result

    def test_str_with_equipped_armor(self):
        """Test: String representation with equipped armor"""
        inventory = Inventory()
        armor = Item(name="Chainmail", description="Protective", item_type=ItemType.ARMOR)
        inventory.add_item(armor)
        inventory.equip(armor)
        result = str(inventory)
        assert "Armor" in result
        assert "Chainmail" in result
```

## Implementation Steps

1. Add `test_unequip_armor_empty_slot` to `TestInventoryUnequip` class (after line 278)
2. Add `test_unequip_invalid_slot` to `TestInventoryUnequip` class
3. Add new `TestInventoryStr` class at end of file with 4 test methods
4. Run `pytest tests/test_inventory.py -v` to verify tests pass
5. Run `pytest --cov=src/cli_rpg/models/inventory --cov-report=term-missing tests/test_inventory.py` to confirm 100% coverage
