# Fix: Misleading Error Message When Equipping Already-Equipped Item

## Spec
When `equip <item>` is called on an item that's already equipped, show "{Item Name} is already equipped." instead of "You don't have '{item}' in your inventory."

## Test (add to `tests/test_main_inventory_commands.py`)
Add new test class `TestEquipAlreadyEquipped`:
- `test_equip_already_equipped_weapon`: Equip sword, run `equip Iron Sword` again, assert message contains "already equipped" and NOT "don't have"
- `test_equip_already_equipped_armor`: Same pattern for armor

## Implementation (`src/cli_rpg/main.py`, lines 435-449)
Add check after `if item is None:` block (before calling `equip(item)`):

```python
elif command == "equip":
    if not args:
        return (True, "\nEquip what? Specify an item name.")
    item_name = " ".join(args)
    item = game_state.current_character.inventory.find_item_by_name(item_name)
    if item is None:
        # Check if item is already equipped (following pattern from 'use' command fix)
        inv = game_state.current_character.inventory
        item_name_lower = item_name.lower()
        if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
            return (True, f"\n{inv.equipped_weapon.name} is already equipped.")
        if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
            return (True, f"\n{inv.equipped_armor.name} is already equipped.")
        return (True, f"\nYou don't have '{item_name}' in your inventory.")
    # ... rest of equip logic unchanged
```

## Verification
```bash
pytest tests/test_main_inventory_commands.py -v -k "equip"
pytest tests/test_main_inventory_commands.py -v
```
