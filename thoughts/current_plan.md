# Implementation Plan: Buff/Debuff Status Effects

## Spec

Add buff and debuff status effects to combat:

**Buff Effects** (applied to player or enemies to enhance stats):
- **Strength Buff**: Increases attack power by a percentage for X turns
- **Defense Buff**: Increases defense by a percentage for X turns

**Debuff Effects** (applied to weaken targets):
- **Weakness**: Reduces attack power by 25% for X turns
- **Vulnerability**: Reduces defense by 25% for X turns

**Mechanics**:
- Buffs/debuffs modify `get_attack_power()` and `get_defense()` calculations
- Effect types: "buff_attack", "buff_defense", "debuff_attack", "debuff_defense"
- New field on StatusEffect: `stat_modifier` (percentage as decimal, e.g., 0.25 = 25%)
- Stacking: Multiple effects of same type stack additively
- Duration-based (decrement each turn like existing DOT effects)

## Tests (TDD)

Add to `tests/test_status_effects.py`:

### 1. StatusEffect model tests for buff/debuff
- `test_buff_effect_creation`: Create buff with stat_modifier field
- `test_debuff_effect_creation`: Create debuff with stat_modifier field
- `test_buff_debuff_tick_no_damage`: Buffs/debuffs don't deal damage on tick
- `test_buff_debuff_serialization`: to_dict/from_dict includes stat_modifier

### 2. Character buff/debuff tests
- `test_attack_buff_increases_attack_power`: +25% attack buff
- `test_defense_buff_increases_defense`: +25% defense buff
- `test_attack_debuff_decreases_attack_power`: -25% attack debuff
- `test_defense_debuff_decreases_defense`: -25% defense debuff
- `test_multiple_buffs_stack_additively`: Two +25% buffs = +50%
- `test_buff_expires_restores_normal_stats`: Stats return to normal

### 3. Enemy buff/debuff tests
- `test_enemy_attack_power_affected_by_debuff`: Enemy with weakness deals less damage
- `test_enemy_defense_affected_by_debuff`: Enemy with vulnerability takes more damage

### 4. Combat integration tests
- `test_buff_displayed_in_combat_status`: Shows active buffs
- `test_debuff_displayed_in_combat_status`: Shows active debuffs
- `test_buffs_cleared_on_combat_end`: Clean slate after combat

## Implementation Steps

### Step 1: Update StatusEffect model
**File**: `src/cli_rpg/models/status_effect.py`

- Add `stat_modifier: float = 0.0` field to StatusEffect dataclass
- Update `to_dict()` to include stat_modifier
- Update `from_dict()` to restore stat_modifier

### Step 2: Update Character model
**File**: `src/cli_rpg/models/character.py`

- Modify `get_attack_power()` to apply buff_attack/debuff_attack modifiers
- Modify `get_defense()` to apply buff_defense/debuff_defense modifiers
- Add helper method `_get_stat_modifier(effect_types: List[str]) -> float`

### Step 3: Update Enemy model
**File**: `src/cli_rpg/models/enemy.py`

- Modify `calculate_damage()` to apply buff_attack/debuff_attack modifiers
- Add `get_defense()` method (currently just returns self.defense)
- Apply buff_defense/debuff_defense to defense calculations

### Step 4: Update combat.py for damage calculations
**File**: `src/cli_rpg/combat.py`

- Ensure `enemy_turn()` uses enemy's modified defense when calculating damage taken
- Ensure player attack uses enemy's `get_defense()` if debuffed

### Step 5: Write tests
**File**: `tests/test_status_effects.py`

- Add all test classes and methods as specified above

## Verification
Run: `pytest tests/test_status_effects.py -v`
Run: `pytest --cov=src/cli_rpg tests/test_status_effects.py`
