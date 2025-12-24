# Plan: Add "use item" support during combat

## Summary
Add `use` command to `handle_combat_command()` to allow players to use consumable items (like health potions) during combat.

## Implementation

### 1. Add tests for combat `use` command
**File**: `tests/test_main_combat_integration.py`

Add new test class `TestUseItemDuringCombat`:
- `test_use_health_potion_during_combat_heals_player` - Use potion when damaged, verify healing
- `test_use_item_during_combat_triggers_enemy_turn` - After using item, enemy attacks
- `test_use_item_not_found_during_combat` - Error when item doesn't exist
- `test_use_no_args_during_combat` - Error when no item specified
- `test_use_non_consumable_during_combat` - Can't use weapons/armor
- `test_use_potion_at_full_health_during_combat` - Reject when at full health

### 2. Add `use` command handler to `handle_combat_command()`
**File**: `src/cli_rpg/main.py` (lines 152-289)

Add new `elif` block after `status` handler (~line 270):
```python
elif command == "use":
    if not args:
        return (True, "\nUse what? Specify an item name.")
    item_name = " ".join(args)
    item = game_state.current_character.inventory.find_item_by_name(item_name)
    if item is None:
        return (True, f"\nYou don't have '{item_name}' in your inventory.")
    success, message = game_state.current_character.use_item(item)
    output = f"\n{message}"

    if success:
        # Using item counts as a turn, enemy attacks
        enemy_message = combat.enemy_turn()
        output += f"\n{enemy_message}"

        # Check if player died
        if not game_state.current_character.is_alive():
            death_message = combat.end_combat(victory=False)
            output += f"\n{death_message}"
            output += "\n\n=== GAME OVER ==="
            game_state.current_combat = None

    return (True, output)
```

### 3. Update help text to list `use` as combat command
**File**: `src/cli_rpg/main.py` (lines 39-45)

Add to Combat Commands section:
```
"  use <item>    - Use a consumable item",
```

### 4. Update error message for unknown commands in combat
**File**: `src/cli_rpg/main.py` (line 289)

Update to include `use`:
```python
return (True, "\n✗ Can't do that during combat! Use: attack, defend, cast, flee, use, status, help, or quit")
```

### 5. Run tests
```bash
pytest tests/test_main_combat_integration.py -v
pytest tests/test_main_inventory_commands.py -v
pytest --cov=src/cli_rpg -q
```
