# Fix Flaky Companion Combat Tests

## Problem
Four tests in `tests/test_companion_combat.py` are flaky because they don't mock `random.random`, allowing random critical hits to alter expected damage values.

## Fix
Add `with patch('cli_rpg.combat.random.random', return_value=0.50)` around attack/cast calls (same fix applied to `test_attack_damage_increased_by_companion_bonus` in commit a4ecd9b).

## Changes to `tests/test_companion_combat.py`

1. **Line 157** - `test_cast_damage_increased_by_companion_bonus`: Wrap `combat.player_cast()` with the random patch

2. **Line 186** - `test_multiple_companions_stack_bonuses`: Wrap `combat.player_attack()` with the random patch

3. **Line 195** - `test_no_companions_means_no_bonus`: Wrap `combat.player_attack()` with the random patch

4. **Line 242** - `test_empty_companions_list_handled_correctly`: Wrap `combat.player_attack()` with the random patch

## Verification
Run: `pytest tests/test_companion_combat.py -v`
