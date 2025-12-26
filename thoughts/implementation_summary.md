# Implementation Summary: Mana Resource System

## What Was Implemented

### Character Model (`src/cli_rpg/models/character.py`)
1. **Added mana fields**:
   - `mana: int` and `max_mana: int` as `field(init=False)`

2. **Mana calculation in `__post_init__`**:
   - Mages: `50 + intelligence * 5`
   - Other classes: `20 + intelligence * 2`
   - Mana starts at max_mana

3. **New methods**:
   - `use_mana(amount: int) -> bool`: Attempts to use mana, returns False if insufficient
   - `restore_mana(amount: int)`: Restores mana, capped at max_mana

4. **Updated `level_up()`**:
   - Recalculates max_mana based on new INT
   - Restores mana to new maximum on level up

5. **Serialization**:
   - `to_dict()`: Includes `mana` and `max_mana`
   - `from_dict()`: Backward compatible - calculates defaults for old saves

6. **Display**:
   - `__str__()`: Shows mana bar with color coding (like health)

7. **Item usage**:
   - `use_item()`: Now handles `mana_restore` items

### Item Model (`src/cli_rpg/models/item.py`)
1. Added `mana_restore: int = 0` field
2. Added validation in `__post_init__`
3. Updated `to_dict()` and `from_dict()` for serialization
4. Updated `__str__()` to show "restores X mana" when applicable

### Combat System (`src/cli_rpg/combat.py`)
1. **Updated `player_cast()`**:
   - Normal cast costs 10 mana
   - Arcane Burst combo costs 25 mana (not 3×10)
   - Returns failure message with current/max mana if insufficient

### Test File (`tests/test_mana.py`)
Created comprehensive test suite with 16 tests covering:
- Mage vs non-mage max_mana calculations
- `use_mana()` and `restore_mana()` methods
- Mana costs in combat (cast and Arcane Burst)
- Mana potion usage
- Serialization and backward compatibility
- Status display

### Updated Existing Tests (`tests/test_combo_combat.py`)
Fixed Arcane Burst tests to ensure player has sufficient mana for the combo.

## Test Results
- All 16 new mana tests pass
- All 2793 total tests pass
- No regressions

## Design Decisions
1. **Mana costs are checked before damage is dealt** - If you can't afford the spell, no action happens
2. **Arcane Burst costs 25 mana** - This is a special combo cost, not 3×10 (30)
3. **Backward compatibility** - Old saves without mana fields get calculated defaults based on class/INT
4. **Mana potions** - Work similarly to health potions with `mana_restore` field

## What E2E Tests Should Validate
1. A Mage character has higher max_mana than other classes
2. Cast command consumes mana and fails when mana is depleted
3. Mana potions restore mana when used
4. Rest command restores 25% of max_mana (already tested in rest functionality)
5. Status display shows mana bar
6. Saving and loading preserves mana state
