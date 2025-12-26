# Implementation Summary: Fix Flaky Combat Tests

## What Was Implemented

Fixed two flaky combat tests that were failing intermittently due to unmocked `random.random()` calls causing unexpected 1.5x critical hit damage.

### Files Modified

1. **tests/test_combat.py**
   - Added `from unittest.mock import patch` import at the top
   - Wrapped `combat.player_cast()` call in `test_player_cast_damages_enemy_based_on_intelligence` with `patch('cli_rpg.combat.random.random', return_value=0.50)` to prevent critical hits

2. **tests/test_combat_equipment.py**
   - Wrapped `combat.player_attack()` call in `test_attack_damage_without_weapon` with `patch('cli_rpg.combat.random.random', return_value=0.50)` to prevent critical hits

## Test Results

Both tests were run 20 times each (40 total runs) and all passed:
- `test_combat.py::TestPlayerCast::test_player_cast_damages_enemy_based_on_intelligence` - 20/20 passed
- `test_combat_equipment.py::TestWeaponAffectsCombatDamage::test_attack_damage_without_weapon` - 20/20 passed

## Technical Details

The fix follows the same pattern established in previous commits (a4ecd9b and e88e8b4) for other combat tests. The `return_value=0.50` ensures the random roll is above the critical hit threshold, producing consistent non-critical damage calculations.
