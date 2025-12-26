# Implementation Plan: Mana Resource System

## Overview
Add a mana resource system for magic users. This is a prerequisite for Mage-specific spells and creates the foundation for class-specific resource management.

## Spec

### Mana Stat
- Add `mana: int` and `max_mana: int` fields to Character model
- Mages get higher max_mana (50 + INT × 5); other classes get base 20 + INT × 2
- Mana regenerates on `rest` command (+25% of max_mana)
- Mana displayed in status command for characters with mana > 0

### Mana Costs
- `cast` command now costs 10 mana per use
- Casting without sufficient mana fails with message: "Not enough mana! (X/Y)"
- Arcane Burst combo costs 25 mana (not 3 × 10)

### Mana Potions
- Add `mana_restore: int` field to Item model (similar to `heal_amount`)
- Add Mana Potion consumable (restores 25 mana)
- Mana potions can drop from loot (10% of consumable drops)
- Shop sells Mana Potions for 35 gold

### Persistence
- Save/load mana and max_mana with backward compatibility (default to calculated values)

---

## Tests (TDD)

### File: `tests/test_mana.py`

1. **test_mage_has_higher_max_mana** - Mage with INT 15 gets 50 + 15×5 = 125 max_mana
2. **test_warrior_has_lower_max_mana** - Warrior with INT 10 gets 20 + 10×2 = 40 max_mana
3. **test_cast_deducts_mana** - Casting reduces mana by 10
4. **test_cast_fails_without_mana** - Cast with 0 mana returns failure message
5. **test_rest_regenerates_mana** - Rest restores 25% of max_mana
6. **test_mana_capped_at_max** - Mana cannot exceed max_mana
7. **test_mana_potion_restores_mana** - Using Mana Potion adds mana_restore amount
8. **test_arcane_burst_costs_25_mana** - Combo costs 25, not 30
9. **test_mana_serialization** - to_dict/from_dict preserve mana
10. **test_mana_backward_compat** - Old saves without mana load with defaults
11. **test_status_shows_mana** - Status display includes mana bar
12. **test_item_mana_restore_field** - Item with mana_restore serializes correctly

---

## Implementation Steps

### Step 1: Character Model (`src/cli_rpg/models/character.py`)
1. Add `mana: int` and `max_mana: int` fields with `field(init=False)`
2. Calculate max_mana in `__post_init__`:
   - Mage: `50 + intelligence * 5`
   - Others: `20 + intelligence * 2`
3. Initialize `mana = max_mana`
4. Add `use_mana(amount: int) -> bool` method (returns False if insufficient)
5. Add `restore_mana(amount: int)` method (capped at max_mana)
6. Update `level_up()` to recalculate max_mana and restore mana
7. Update `to_dict()` to include mana/max_mana
8. Update `from_dict()` with backward-compatible defaults
9. Update `__str__()` to show mana in status

### Step 2: Item Model (`src/cli_rpg/models/item.py`)
1. Add `mana_restore: int = 0` field
2. Update `to_dict()` and `from_dict()` for mana_restore
3. Update `__str__()` to show "restores X mana" when mana_restore > 0

### Step 3: Character use_item (`src/cli_rpg/models/character.py`)
1. Update `use_item()` to handle mana_restore items
2. Add mana restoration logic similar to heal_amount

### Step 4: Combat cast (`src/cli_rpg/combat.py`)
1. Update `player_cast()` to check and deduct mana
2. Return failure message if mana insufficient
3. Update Arcane Burst combo to cost 25 mana

### Step 5: Rest command (`src/cli_rpg/game_state.py`)
1. Update rest handler to restore 25% max_mana

### Step 6: Loot & Shop (`src/cli_rpg/combat.py`, `src/cli_rpg/world.py`)
1. Add 10% chance for Mana Potion in consumable loot
2. Add Mana Potion to shop inventory (35 gold)

### Step 7: Tests
1. Create `tests/test_mana.py` with all test cases above
2. Run full test suite to ensure no regressions
