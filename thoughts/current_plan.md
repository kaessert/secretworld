# Fix Misleading Error Message for 'use' on Equipped Items

## Spec
When a player tries to `use` an equipped item (weapon or armor), the error should explain the item is equipped, not say it's missing. Message format: "{Item Name} is currently equipped as your {weapon/armor} and cannot be used."

## Tests (add to tests/test_main_inventory_commands.py)

```python
def test_use_equipped_weapon_shows_equipped_message(self, game_state_with_items):
    """Spec: 'use' on equipped weapon shows equipped message, not 'not found'."""
    gs = game_state_with_items
    sword = gs.current_character.inventory.find_item_by_name("Iron Sword")
    gs.current_character.inventory.equip(sword)
    cont, msg = handle_exploration_command(gs, "use", ["iron", "sword"])
    assert cont is True
    assert "equipped" in msg.lower()
    assert "weapon" in msg.lower()
    assert "don't have" not in msg.lower()

def test_use_equipped_armor_shows_equipped_message(self, game_state_with_items):
    """Spec: 'use' on equipped armor shows equipped message, not 'not found'."""
    gs = game_state_with_items
    armor = gs.current_character.inventory.find_item_by_name("Leather Armor")
    gs.current_character.inventory.equip(armor)
    cont, msg = handle_exploration_command(gs, "use", ["leather", "armor"])
    assert cont is True
    assert "equipped" in msg.lower()
    assert "armor" in msg.lower()
    assert "don't have" not in msg.lower()
```

## Implementation

1. **src/cli_rpg/main.py** - `handle_exploration_command()` (line ~456-464):

   Replace the simple "not found" check with equipped item detection:
   ```python
   elif command == "use":
       if not args:
           return (True, "\nUse what? Specify an item name.")
       item_name = " ".join(args)
       item = game_state.current_character.inventory.find_item_by_name(item_name)
       if item is None:
           # Check if item is equipped
           inv = game_state.current_character.inventory
           item_name_lower = item_name.lower()
           if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
               return (True, f"\n{inv.equipped_weapon.name} is currently equipped as your weapon and cannot be used.")
           if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
               return (True, f"\n{inv.equipped_armor.name} is currently equipped as your armor and cannot be used.")
           return (True, f"\nYou don't have '{item_name}' in your inventory.")
       success, message = game_state.current_character.use_item(item)
       return (True, f"\n{message}")
   ```

2. **src/cli_rpg/main.py** - `handle_combat_command()` (line ~346-352):

   Apply same fix to combat `use` command:
   ```python
   elif command == "use":
       if not args:
           return (True, "\nUse what? Specify an item name.")
       item_name = " ".join(args)
       item = game_state.current_character.inventory.find_item_by_name(item_name)
       if item is None:
           inv = game_state.current_character.inventory
           item_name_lower = item_name.lower()
           if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
               return (True, f"\n{inv.equipped_weapon.name} is currently equipped as your weapon and cannot be used.")
           if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
               return (True, f"\n{inv.equipped_armor.name} is currently equipped as your armor and cannot be used.")
           return (True, f"\nYou don't have '{item_name}' in your inventory.")
       # ... rest of combat use logic
   ```

Note: This pattern matches the existing pattern used by `sell` and `drop` commands (lines ~629-638, ~658-667) which already check for equipped items before giving the "not found" error.
