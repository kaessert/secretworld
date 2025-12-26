# Fix Flaky Combat Tests Due to Random Critical Hits

## Problem
Two tests fail intermittently because they don't mock `random.random()`, causing unexpected 1.5x damage when a crit occurs:
- `test_combat.py::TestPlayerCast::test_player_cast_damages_enemy_based_on_intelligence`
- `test_combat_equipment.py::TestWeaponAffectsCombatDamage::test_attack_damage_without_weapon`

## Fix Pattern
Wrap attack calls with `with patch('cli_rpg.combat.random.random', return_value=0.50):` (same pattern used in fixed tests from commits a4ecd9b and e88e8b4).

## Implementation Steps

### 1. Fix `tests/test_combat.py` (line 163)
- Add `from unittest.mock import patch` at top of `test_player_cast_damages_enemy_based_on_intelligence` method
- Wrap `combat.player_cast()` call with the random mock:
```python
with patch('cli_rpg.combat.random.random', return_value=0.50):
    victory, message = combat.player_cast()
```

### 2. Fix `tests/test_combat_equipment.py` (line 34)
- `from unittest.mock import patch` already imported at file top (line 8)
- Wrap `combat.player_attack()` call with the random mock:
```python
with patch('cli_rpg.combat.random.random', return_value=0.50):
    combat.player_attack()
```

## Verification
Run the specific tests multiple times to confirm they no longer flake:
```bash
pytest tests/test_combat.py::TestPlayerCast::test_player_cast_damages_enemy_based_on_intelligence tests/test_combat_equipment.py::TestWeaponAffectsCombatDamage::test_attack_damage_without_weapon -v --count=20
```
