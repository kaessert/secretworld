# Implementation Plan: Parry Command

## Overview
Add a `parry` combat command as a timing-based defensive option alongside `block`. Parry has higher risk/reward: on success, negate damage + counter-attack; on failure, take full damage.

## Spec

**Parry mechanics:**
- **Cost**: 8 stamina (between defend's 0 and block's 5)
- **Success chance**: 40% base + DEX * 2% (capped at 70%)
- **On success**: Negate incoming damage AND counter-attack for 50% of player attack power
- **On failure**: Take full damage (no reduction)
- **Alias**: `pa` (consistent with `bl` for block, `ba` for bash)

**Why this design:**
- Higher skill floor than block (40-70% success vs block's guaranteed 75% reduction)
- Risk/reward tradeoff: potential full damage negation + counter vs possible full damage taken
- DEX-scaling rewards agile characters, fits thematically with parrying
- Stamina cost (8) is moderate - more than block (5) but doesn't cost as much as bash (15)

## Tests (tests/test_combat.py)

Add `TestPlayerParry` class with tests:

1. `test_player_parry_sets_parrying_stance` - parry() should set `parrying=True`
2. `test_player_parry_costs_8_stamina` - should deduct 8 stamina
3. `test_player_parry_fails_without_stamina` - fails if < 8 stamina, returns error message
4. `test_parry_success_negates_damage` - on success (mock random), player takes 0 damage
5. `test_parry_success_deals_counter_damage` - on success, enemy takes 50% of player attack power
6. `test_parry_failure_takes_full_damage` - on failure (mock random), player takes full damage
7. `test_parry_success_chance_scales_with_dex` - verify 40% + DEX*2% formula (capped at 70%)
8. `test_parry_resets_after_enemy_turn` - parrying stance resets after enemy turn
9. `test_player_parry_fails_when_stunned` - parry fails if player is stunned
10. `test_parry_records_action_for_combo` - verify action recorded as "parry"

## Implementation Steps

### 1. Add `parrying` state to CombatEncounter (src/cli_rpg/combat.py)
- Add `self.parrying = False` in `__init__` (line ~354, after `self.blocking = False`)

### 2. Add `player_parry()` method to CombatEncounter (src/cli_rpg/combat.py)
- Add after `player_block()` method (~line 765)
- Implement:
  - Check for stun (using `_check_and_consume_stun()`)
  - Check stamina cost (8 stamina via `use_stamina()`)
  - Record action for combo tracking
  - Set `self.parrying = True`
  - Return success message

### 3. Modify `enemy_turn()` to handle parry (src/cli_rpg/combat.py)
- After the blocking damage reduction check (~line 1523), add parry logic:
  - Calculate success chance: `min(40 + player.dexterity * 2, 70) / 100.0`
  - Roll for success
  - On success: negate damage, deal counter-attack (50% of player attack power)
  - On failure: take full damage
- Reset `self.parrying = False` after all attacks (~line 1661)

### 4. Add parry command handling (src/cli_rpg/main.py)
- Add to command reference (~line 83): `  parry (pa)   - Parry attacks for counter (8 stamina, DEX-based)`
- Add `elif command == "parry":` handler after block handler (~line 445)
- Add "parry" to combat command sets in suggest_command (~line 972) and error messages

### 5. Add parry alias to parse_command (src/cli_rpg/game_state.py)
- Add `"pa": "parry"` to aliases dict (~line 126)
- Add `"parry"` to KNOWN_COMMANDS set (~line 53)

### 6. Update ISSUES.md
- Mark "Defensive options: parry" as MVP IMPLEMENTED with mechanics summary
