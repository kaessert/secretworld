# Implementation Summary: Stamina Resource System

## What Was Implemented

The stamina resource system for physical classes (Warrior, Rogue, Ranger) has been fully implemented, mirroring the existing mana system.

### Key Features

1. **Stamina Calculation Formula**
   - Warriors/Rangers: `50 + STR * 5` (physical focus)
   - Mages/Clerics/Rogues: `20 + STR * 2` (lower base)

2. **Stamina Costs**
   - Sneak (Rogue): 10 stamina

3. **Stamina Regeneration**
   - 1 stamina per combat turn (in `enemy_turn()`)
   - Rest restores 25% of max stamina
   - Stamina Potions for instant recovery

### Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/models/item.py` | Added `stamina_restore: int = 0` field with validation, serialization, and `__str__()` display |
| `src/cli_rpg/models/character.py` | Added `stamina`, `max_stamina` fields, `use_stamina()`, `restore_stamina()`, `regen_stamina()` methods, serialization with backward compat, `__str__()` display |
| `src/cli_rpg/combat.py` | Added stamina cost (10) to `player_sneak()`, stamina regen (1) in `enemy_turn()` |
| `src/cli_rpg/main.py` | Updated `rest` command to restore 25% stamina |
| `src/cli_rpg/world.py` | Added "Stamina Potion" to Market District shop (30 gold, 25 stamina restore) |
| `tests/test_stamina.py` | New test file with 16 tests covering all features |

### Test Results

All 16 stamina-specific tests pass:
- `TestStaminaStat`: 6 tests (formula, use, restore, capping)
- `TestStaminaInCombat`: 3 tests (sneak cost, sneak fail, regen)
- `TestStaminaRest`: 1 test (rest restores 25%)
- `TestStaminaPotion`: 3 tests (potion use, item field, item display)
- `TestStaminaSerialization`: 2 tests (save/load, backward compat)
- `TestStaminaStatus`: 1 test (status display includes stamina)

Full test suite: **2853 tests passed** (no regressions)

## What E2E Tests Should Validate

1. **Create a Warrior** and verify stamina is `50 + STR * 5`
2. **Create a Mage** and verify stamina is `20 + STR * 2`
3. **As a Rogue, use `sneak` in combat** and verify 10 stamina is deducted
4. **With low stamina, try `sneak`** and verify it fails with appropriate message
5. **During combat, let enemy take turns** and verify stamina regenerates by 1 each turn
6. **Use `rest` command** and verify 25% of max stamina is restored
7. **Buy and use a Stamina Potion** and verify stamina is restored
8. **Save and load game** and verify stamina values persist correctly
9. **Load an old save without stamina** and verify it loads with default values
