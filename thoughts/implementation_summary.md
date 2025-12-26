# Implementation Summary: Warrior Bash Command

## What Was Implemented

Added the **bash** combat command for Warriors, providing a stun-focused ability that mirrors the Rogue's sneak command.

### Features
- **Warrior-only ability**: Non-warriors receive "Only Warriors can bash!" error
- **15 stamina cost**: Higher than sneak (10) to balance the stun effect
- **0.75x damage multiplier**: Deals reduced STR-based damage (trade-off for stun)
- **1-turn stun**: Applies stun StatusEffect to target enemy
- **Target selection**: Supports targeting specific enemies by name (e.g., `bash orc`)
- **Combo tracking**: Records "bash" in action_history for combo system

### Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/combat.py` | Added `player_bash()` method (~70 lines) after `player_sneak()` |
| `src/cli_rpg/game_state.py` | Added "bash" to KNOWN_COMMANDS, added "ba" alias |
| `src/cli_rpg/main.py` | Added command handler (~65 lines), added help text |
| `tests/test_bash.py` | New test file with 13 tests |

## Test Results

All **13 bash tests pass**:
- `test_bash_only_available_to_warrior` - Non-warriors get error
- `test_mage_cannot_bash` - Mages cannot use bash
- `test_bash_costs_15_stamina` - Stamina decreases by 15
- `test_bash_fails_without_stamina` - Error with <15 stamina
- `test_bash_deals_reduced_damage` - Deals 0.75x damage
- `test_bash_minimum_damage_is_1` - Minimum 1 damage
- `test_bash_can_defeat_enemy` - Returns victory on enemy defeat
- `test_bash_applies_stun_to_enemy` - Enemy has stun effect
- `test_bash_stun_lasts_1_turn` - Duration is 1
- `test_bash_stun_message` - Message indicates stun
- `test_bash_fails_when_stunned` - Can't bash while stunned
- `test_bash_with_target` - Target selection works
- `test_bash_records_action_for_combo` - Action recorded

Full test suite: **2872 passed**

## Technical Notes

### Design Decisions
1. **Damage formula**: `max(1, int(max(1, STR - DEF) * 0.75))` ensures minimum 1 damage
2. **Stun implementation**: Uses existing StatusEffect with `effect_type="stun"`
3. **Command handler pattern**: Follows existing attack/cast pattern for victory handling, XP, quests, companion reactions, invasion checks, and autosave
4. **Error checking order**: Stun check > Warrior check > Stamina check > Target check

### Command Usage
```
bash              # Bash first living enemy
bash orc          # Bash enemy named "orc"
ba                # Shorthand alias
```

## E2E Test Validation
Should validate:
1. Warrior can use bash in combat and enemy is stunned
2. Non-warriors (Rogue, Mage, etc.) cannot use bash
3. Bash fails gracefully with insufficient stamina
4. Stunned enemies skip their turn (existing stun behavior)
