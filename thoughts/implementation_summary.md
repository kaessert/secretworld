# Implementation Summary: Fix Flaky Companion Combat Tests

## What was fixed
Fixed 4 additional flaky tests in `tests/test_companion_combat.py` that were failing intermittently due to random critical hits affecting damage calculations.

## Changes made
**File:** `tests/test_companion_combat.py`

Wrapped attack/cast calls with `random.random` mock to prevent critical hits in 4 tests:

1. `test_cast_damage_increased_by_companion_bonus` - wrapped `player_cast()`
2. `test_multiple_companions_stack_bonuses` - wrapped `player_attack()`
3. `test_no_companions_means_no_bonus` - wrapped `player_attack()`
4. `test_empty_companions_list_handled_correctly` - wrapped `player_attack()`

Pattern used (same as previous fix in commit a4ecd9b):
```python
with patch('cli_rpg.combat.random.random', return_value=0.50):
    combat.player_attack()  # or player_cast()
```

## Root cause
Tests expected deterministic damage but sometimes got critical hit damage due to:
- `combat.py` calculates `crit_chance` based on player dexterity
- With 10 DEX, there's ~10% chance to crit (1.5x damage multiplier)
- Mocking `random.random` to return 0.50 prevents crits from triggering

## Test results
- All 11 tests in `test_companion_combat.py` pass
- Verified 5 consecutive runs with 0 failures
