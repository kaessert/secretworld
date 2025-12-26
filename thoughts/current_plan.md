# Implementation Plan: Stamina Resource System

## Spec

Add a **Stamina** resource for physical classes (Warrior, Rogue, Ranger) that powers physical abilities. Mirrors the existing mana system implementation.

### Formula
- **Warriors/Rangers**: `50 + STR * 5` (physical focus)
- **Mages/Clerics/Rogues**: `20 + STR * 2` (lower base)

### Costs
- **Sneak** (Rogue): 10 stamina
- **Future abilities**: Power Strike (15 stamina), Bash (20 stamina)

### Regeneration
- Regenerates 1 stamina per combat turn (slow regen)
- Rest restores 25% of max stamina (matches mana)
- Stamina Potions for instant recovery

---

## Tests (`tests/test_stamina.py`)

### TestStaminaStat
1. `test_warrior_has_higher_max_stamina` - Warrior with STR 15 gets 50 + 15×5 = 125
2. `test_mage_has_lower_max_stamina` - Mage with STR 10 gets 20 + 10×2 = 40
3. `test_rogue_has_lower_max_stamina` - Non-warrior classes use 20 + STR×2
4. `test_stamina_use_method` - use_stamina(amount) returns False if insufficient
5. `test_stamina_restore_method` - restore_stamina capped at max_stamina
6. `test_stamina_capped_at_max` - Cannot exceed max_stamina

### TestStaminaInCombat
7. `test_sneak_deducts_stamina` - Sneak costs 10 stamina
8. `test_sneak_fails_without_stamina` - Sneak with <10 stamina returns failure
9. `test_stamina_regen_on_turn` - Stamina regenerates 1 per enemy turn

### TestStaminaRest
10. `test_rest_regenerates_stamina` - Rest restores 25% of max_stamina

### TestStaminaPotion
11. `test_stamina_potion_restores_stamina` - Using Stamina Potion adds stamina_restore
12. `test_item_stamina_restore_field` - Item with stamina_restore serializes correctly
13. `test_item_str_shows_stamina_restore` - Item __str__() shows stamina

### TestStaminaSerialization
14. `test_stamina_serialization` - to_dict/from_dict preserve stamina
15. `test_stamina_backward_compat` - Old saves without stamina load with defaults

### TestStaminaStatus
16. `test_status_shows_stamina` - Status display includes stamina bar

---

## Implementation Steps

### 1. Item Model (`src/cli_rpg/models/item.py`)
- Add `stamina_restore: int = 0` field
- Add validation in `__post_init__`
- Update `to_dict()` and `from_dict()` with backward compat
- Update `__str__()` to show stamina restore

### 2. Character Model (`src/cli_rpg/models/character.py`)
- Add `stamina: int` and `max_stamina: int` fields
- Add stamina calculation in `__post_init__`:
  - Warrior/Ranger: 50 + STR×5
  - Others: 20 + STR×2
- Add `use_stamina(amount: int) -> bool` method (mirrors use_mana)
- Add `restore_stamina(amount: int)` method (mirrors restore_mana)
- Add `regen_stamina(amount: int = 1)` for combat turn regen
- Update `use_item()` to handle stamina_restore items
- Update `level_up()` to recalculate max_stamina and restore full
- Update `to_dict()` and `from_dict()` with backward compat
- Update `__str__()` to display stamina bar

### 3. Combat (`src/cli_rpg/combat.py`)
- Update `player_sneak()` to cost 10 stamina
- Add stamina regen call in `enemy_turn()` (regen 1 per turn)

### 4. Main Commands (`src/cli_rpg/main.py`)
- Update `rest` command to restore 25% stamina
- Update `status` command display (if needed)

### 5. Shop Items (`src/cli_rpg/world.py`)
- Add "Stamina Potion" to Market District shop (30 gold, 25 stamina restore)

---

## File Modifications Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/models/item.py` | Add stamina_restore field |
| `src/cli_rpg/models/character.py` | Add stamina stat, methods, serialization |
| `src/cli_rpg/combat.py` | Add stamina cost to sneak, regen on turn |
| `src/cli_rpg/main.py` | Update rest to restore stamina |
| `src/cli_rpg/world.py` | Add Stamina Potion to shop |
| `tests/test_stamina.py` | New test file (16 tests) |
