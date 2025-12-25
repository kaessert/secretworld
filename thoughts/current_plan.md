# Implementation Plan: Improve Equip Command Error Message

**Task**: When a player tries to equip a non-equippable item (consumable/misc), provide a helpful error message explaining why and suggesting the `use` command for consumables.

## 1. Update Test (TDD)

**File**: `tests/test_main_coverage.py` - Update `TestEquipCannotEquip` class

Add test for consumable item with improved error message:
```python
def test_equip_consumable_suggests_use_command(self):
    """Spec: Equipping consumable explains why and suggests 'use' command."""
    from cli_rpg.main import handle_exploration_command

    character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    potion = Item(name="Health Potion", description="Heals", item_type=ItemType.CONSUMABLE, heal_amount=20)
    character.inventory.add_item(potion)
    world = {"Town": Location(name="Town", description="A town", connections={})}
    game_state = GameState(character, world, starting_location="Town")

    continue_game, message = handle_exploration_command(game_state, "equip", ["Health", "Potion"])

    assert continue_game is True
    assert "weapon" in message.lower() or "armor" in message.lower()
    assert "use" in message.lower()
```

Update existing `test_equip_misc_item_fails` to check for enhanced message:
```python
def test_equip_misc_item_fails(self):
    """Spec: Cannot equip misc items - explains only weapons/armor can be equipped."""
    # ... existing setup ...
    assert "weapon" in message.lower() or "armor" in message.lower()
```

## 2. Implement Error Message Improvement

**File**: `src/cli_rpg/main.py` - Line 434

**Current code**:
```python
return (True, f"\nYou can't equip {item.name}.")
```

**Replace with**:
```python
if item.item_type == ItemType.CONSUMABLE:
    return (True, f"\nYou can only equip weapons or armor. Use 'use {item.name}' for consumables.")
else:
    return (True, f"\nYou can only equip weapons or armor.")
```

**Note**: Will need to import `ItemType` at the top of main.py if not already imported.

## 3. Verify

Run tests:
```bash
pytest tests/test_main_coverage.py::TestEquipCannotEquip -v
pytest tests/test_main_inventory_commands.py -v
```
