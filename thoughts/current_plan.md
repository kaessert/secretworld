# Fighting Styles System Implementation Plan

## Feature Spec

Add a `stance` command that lets players choose between 4 combat stances, each providing stat modifiers during combat:

| Stance | Damage Modifier | Defense Modifier | Other |
|--------|----------------|------------------|-------|
| Aggressive | +20% | -10% | - |
| Defensive | -10% | +20% | - |
| Balanced | 0% | 0% | +5% crit chance |
| Berserker | +X% (scales with missing HP) | 0% | - |

**Berserker Formula**: Damage bonus = `(1 - current_hp/max_hp) * 50%` (e.g., at 50% HP: +25% damage; at 10% HP: +45% damage)

## Implementation Steps

### 1. Add FightingStance Enum and stance field to Character model

**File**: `src/cli_rpg/models/character.py`

- Add `FightingStance` enum with values: BALANCED, AGGRESSIVE, DEFENSIVE, BERSERKER
- Add `stance: FightingStance = FightingStance.BALANCED` field to Character dataclass
- Update `to_dict()` to serialize stance
- Update `from_dict()` to deserialize stance (default BALANCED for backward compat)

### 2. Add stance modifier methods to Character

**File**: `src/cli_rpg/models/character.py`

- Add `get_stance_damage_modifier() -> float` method:
  - AGGRESSIVE: 1.20
  - DEFENSIVE: 0.90
  - BALANCED: 1.0
  - BERSERKER: 1.0 + (1 - health/max_health) * 0.5
- Add `get_stance_defense_modifier() -> float` method:
  - AGGRESSIVE: 0.90
  - DEFENSIVE: 1.20
  - BALANCED: 1.0
  - BERSERKER: 1.0
- Add `get_stance_crit_modifier() -> float` method:
  - BALANCED: 0.05 (5% bonus crit chance)
  - Others: 0.0

### 3. Apply stance modifiers in combat calculations

**File**: `src/cli_rpg/combat.py`

- In `player_attack()`: Multiply damage by `player.get_stance_damage_modifier()`
- In `player_cast()`: Multiply damage by `player.get_stance_damage_modifier()`
- In `player_fireball()`, `player_ice_bolt()`: Same damage modifier
- In `player_bash()`: Same damage modifier
- In `player_smite()`: Same damage modifier
- In `enemy_turn()` damage calculation: Multiply defense by `player.get_stance_defense_modifier()`
- In `calculate_crit_chance()`: Add `player.get_stance_crit_modifier()` to crit chance

### 4. Add `stance` command to game

**File**: `src/cli_rpg/game_state.py`

- Add "stance" to `KNOWN_COMMANDS` set
- Add alias "st" -> "stance" in `parse_command()`

**File**: `src/cli_rpg/main.py`

- Add `stance` command handler that:
  - With no args: Shows current stance and available options
  - With arg: Changes stance to specified option (case-insensitive partial match)
  - Works in and out of combat
- Add to help text

### 5. Write tests

**File**: `tests/test_fighting_stances.py` (new file)

Test coverage:
- FightingStance enum values exist
- Character defaults to BALANCED stance
- Stance serialization/deserialization (to_dict/from_dict)
- Backward compatibility (old saves without stance field)
- Stance damage modifier calculations for each stance
- Stance defense modifier calculations for each stance
- Berserker modifier scales with missing HP
- Balanced crit bonus applies
- Stance command changes stance
- Stance affects combat damage dealt
- Stance affects combat damage received
- Stance persists through save/load

## Verification

```bash
# Run new tests
pytest tests/test_fighting_stances.py -v

# Run full test suite to ensure no regressions
pytest
```
