# Plan: Fix Class-Specific Ability Error Message Ordering

## Summary
Fix UX issue where class-specific combat abilities show "Not in combat" instead of class restriction errors when used outside combat by wrong class.

## Spec
- **Warrior-only**: `bash` → "Only Warriors can bash!"
- **Mage-only**: `fireball`, `ice_bolt`, `heal` → "Only Mages can cast X!"
- **Cleric-only**: `bless`, `smite` → "Only Clerics can X!"

When a non-matching class uses these commands outside combat, show class error first.
When the correct class uses these commands outside combat, show "Not in combat."

## Implementation

### 1. Modify `src/cli_rpg/main.py` (lines 2488-2490)

**Current code:**
```python
elif command in ["attack", "defend", "block", "parry", "flee", "rest", "cast",
                  "fireball", "ice_bolt", "heal", "bash", "bless", "smite", "hide"]:
    return (True, "\n✗ Not in combat.")
```

**New code:**
```python
# Class-specific abilities: check class BEFORE combat state
elif command == "bash":
    if game_state.current_character.character_class != CharacterClass.WARRIOR:
        return (True, "\n✗ Only Warriors can bash!")
    return (True, "\n✗ Not in combat.")

elif command == "fireball":
    if game_state.current_character.character_class != CharacterClass.MAGE:
        return (True, "\n✗ Only Mages can cast Fireball!")
    return (True, "\n✗ Not in combat.")

elif command == "ice_bolt":
    if game_state.current_character.character_class != CharacterClass.MAGE:
        return (True, "\n✗ Only Mages can cast Ice Bolt!")
    return (True, "\n✗ Not in combat.")

elif command == "heal":
    if game_state.current_character.character_class != CharacterClass.MAGE:
        return (True, "\n✗ Only Mages can cast Heal!")
    return (True, "\n✗ Not in combat.")

elif command == "bless":
    if game_state.current_character.character_class != CharacterClass.CLERIC:
        return (True, "\n✗ Only Clerics can bless!")
    return (True, "\n✗ Not in combat.")

elif command == "smite":
    if game_state.current_character.character_class != CharacterClass.CLERIC:
        return (True, "\n✗ Only Clerics can smite!")
    return (True, "\n✗ Not in combat.")

# Generic combat commands: just check combat state
elif command in ["attack", "defend", "block", "parry", "flee", "rest", "cast", "hide"]:
    return (True, "\n✗ Not in combat.")
```

### 2. Add CharacterClass import at top of function

Add near existing imports in `handle_exploration_command`:
```python
from cli_rpg.models.character import CharacterClass
```

### 3. Update tests in `tests/test_main_coverage.py`

Update 6 tests (lines 599-675) to test new behavior:

- `test_fireball_command_outside_combat`: Create Warrior, expect "Only Mages"
- `test_ice_bolt_command_outside_combat`: Create Warrior, expect "Only Mages"
- `test_heal_command_outside_combat`: Create Warrior, expect "Only Mages"
- `test_bash_command_outside_combat`: Create Mage, expect "Only Warriors"
- `test_bless_command_outside_combat`: Create Warrior, expect "Only Clerics"
- `test_smite_command_outside_combat`: Create Warrior, expect "Only Clerics"

Add 6 complementary tests for correct class + "Not in combat":
- `test_fireball_mage_outside_combat_shows_not_in_combat`
- `test_ice_bolt_mage_outside_combat_shows_not_in_combat`
- `test_heal_mage_outside_combat_shows_not_in_combat`
- `test_bash_warrior_outside_combat_shows_not_in_combat`
- `test_bless_cleric_outside_combat_shows_not_in_combat`
- `test_smite_cleric_outside_combat_shows_not_in_combat`

## Files to Modify
1. `src/cli_rpg/main.py` - Reorder checks (lines 2488-2490)
2. `tests/test_main_coverage.py` - Update and add tests (lines 599-675)

## Verification
```bash
pytest tests/test_main_coverage.py::TestExplorationCombatCommandsOutsideCombat -v
```
