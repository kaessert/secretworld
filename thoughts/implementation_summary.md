# Implementation Summary: Buff/Debuff Status Effects

## What Was Implemented

Added buff and debuff status effects to the combat system that modify attack power and defense.

### Features

**Buff Effects** (enhance stats):
- **buff_attack**: Increases attack power by percentage (e.g., +25%)
- **buff_defense**: Increases defense by percentage (e.g., +25%)

**Debuff Effects** (weaken targets):
- **debuff_attack**: Reduces attack power by percentage (e.g., -25% for Weakness)
- **debuff_defense**: Reduces defense by percentage (e.g., -25% for Vulnerability)

**Mechanics**:
- Effects use `stat_modifier` field (percentage as decimal, e.g., 0.25 = 25%)
- Multiple effects of the same type stack additively (two +25% buffs = +50%)
- Duration-based (decrements each turn like existing DOT effects)
- Buffs/debuffs are cleared at combat end
- Fully serializable for save/load functionality

### Files Modified

1. **`src/cli_rpg/models/status_effect.py`**
   - Added `stat_modifier: float = 0.0` field to StatusEffect dataclass
   - Updated docstring with new effect types
   - Updated `to_dict()` to include stat_modifier
   - Updated `from_dict()` to restore stat_modifier (with backward compatibility)

2. **`src/cli_rpg/models/character.py`**
   - Added `_get_stat_modifier(buff_type, debuff_type)` helper method
   - Modified `get_attack_power()` to apply buff_attack/debuff_attack modifiers
   - Modified `get_defense()` to apply buff_defense/debuff_defense modifiers

3. **`src/cli_rpg/models/enemy.py`**
   - Added `_get_stat_modifier(buff_type, debuff_type)` helper method
   - Modified `calculate_damage()` to apply buff_attack/debuff_attack modifiers
   - Added `get_defense()` method to apply buff_defense/debuff_defense modifiers

4. **`tests/test_status_effects.py`**
   - Added 17 new tests for buff/debuff functionality:
     - `TestBuffDebuffStatusEffect`: 5 tests for StatusEffect model
     - `TestCharacterBuffDebuff`: 6 tests for Character buff/debuff
     - `TestEnemyBuffDebuff`: 3 tests for Enemy buff/debuff
     - `TestCombatBuffDebuff`: 3 tests for combat integration
   - Updated existing serialization test to include stat_modifier

## Test Results

```
pytest tests/test_status_effects.py -v
============================== 75 passed ==============================

pytest
============================== 1807 passed ==============================
```

All 17 new buff/debuff tests pass, and the full test suite (1807 tests) passes without regressions.

## E2E Validation Suggestions

To manually verify in-game:
1. Create a game and enter combat
2. Apply a strength buff to the player (would need a consumable or spell that applies it)
3. Verify attack damage increases by the expected percentage
4. Apply a weakness debuff to an enemy
5. Verify enemy deals reduced damage

Note: Currently there are no in-game sources that apply these effects. Future work could add:
- Consumable items that grant buffs (e.g., "Strength Potion")
- Enemy abilities that apply debuffs to the player
- Spell effects that apply debuffs to enemies

## Design Decisions

1. **Additive Stacking**: Multiple buffs/debuffs stack additively rather than multiplicatively. Two +25% buffs result in +50%, not +56.25%. This is simpler to understand and balance.

2. **Stat Modifier as Percentage**: The `stat_modifier` field represents the percentage change (0.25 = 25%). Buffs add this value, debuffs subtract it. This allows flexible modifier amounts.

3. **Backward Compatibility**: The `stat_modifier` field defaults to 0.0, and `from_dict()` uses `.get()` with a default, ensuring old save files without this field still load correctly.
