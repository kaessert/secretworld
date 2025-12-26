# Implementation Summary: Parry Command

## What Was Implemented

Added a new `parry` combat command as a timing-based defensive option with high risk/reward mechanics.

### Parry Mechanics
- **Cost**: 8 stamina
- **Success chance**: 40% base + DEX * 2%, capped at 70%
- **On success**: Negate incoming damage AND counter-attack for 50% of player attack power
- **On failure**: Take full damage (no reduction)
- **Alias**: `pa`

## Files Modified

### 1. `src/cli_rpg/combat.py`
- Added `self.parrying = False` state in `CombatEncounter.__init__`
- Added `player_parry()` method (after `player_block()`)
- Added parry logic in `enemy_turn()` (checks parrying state, calculates success chance, handles success/failure outcomes)
- Added `self.parrying = False` reset after enemy turn

### 2. `src/cli_rpg/game_state.py`
- Added `"parry"` to `KNOWN_COMMANDS` set
- Added `"pa": "parry"` alias

### 3. `src/cli_rpg/main.py`
- Added parry to help text: `"parry (pa) - Parry attacks for counter (8 stamina, DEX-based)"`
- Added `elif command == "parry":` handler after block handler
- Added "parry" to combat command sets for error messages and autocomplete
- Updated exploration command "Not in combat" list

### 4. `tests/test_combat.py`
Added `TestPlayerParry` class with 10 tests:
1. `test_player_parry_sets_parrying_stance` - parry() sets `parrying=True`
2. `test_player_parry_costs_8_stamina` - deducts 8 stamina
3. `test_player_parry_fails_without_stamina` - fails if < 8 stamina
4. `test_parry_success_negates_damage` - player takes 0 damage on success
5. `test_parry_success_deals_counter_damage` - enemy takes 50% of player attack power
6. `test_parry_failure_takes_full_damage` - player takes full damage on failure
7. `test_parry_success_chance_scales_with_dex` - verifies 40% + DEX*2% formula (capped at 70%)
8. `test_parry_resets_after_enemy_turn` - parrying stance resets
9. `test_player_parry_fails_when_stunned` - parry fails if stunned
10. `test_parry_records_action_for_combo` - action recorded as "parry"

## Test Results

All 3062 tests pass (including 59 combat tests, 10 new parry tests).

## Design Decisions

1. **Parry before Defend in damage reduction checks**: Parry is checked after Block but before Defend since it has higher stakes (full damage on failure vs guaranteed reduction)

2. **DEX scaling with cap**: The 40-70% success range makes parry viable for all builds while rewarding high-DEX characters

3. **Counter-attack uses STR**: Counter damage is 50% of player strength, making parry useful for STR/DEX hybrid builds

4. **Messages use color helpers**: Success shows "PARRIED!" in heal color, failure shows damage in enemy color for clear feedback
