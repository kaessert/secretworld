# Implementation Plan: Fix Flaky Poison Test

**Issue**: `test_enemy_with_poison_can_apply_poison` in `tests/test_status_effects.py` is flaky - passes individually but sometimes fails in full test suite.

## Root Cause

The test creates a character with `dexterity=10`, giving ~10% dodge chance. When the enemy attacks:
1. Combat checks `random.random() < dodge_chance` (line 1676 in combat.py)
2. If dodge succeeds, the attack is skipped via `continue` (line 1687)
3. Poison application code (lines 1792-1804) is never reached
4. Test assertion fails because no poison was applied

The test doesn't mock `random.random()`, so ~10% of runs will fail due to dodge.

## Fix

Add `unittest.mock.patch` to prevent dodge, matching the pattern already used in:
- `test_burn_applies_in_combat` (line 530)
- `test_stun_applies_in_combat` (line 682)
- `test_bleed_applies_in_combat` (line 1266)

## Implementation

**File**: `tests/test_status_effects.py`, lines 278-289

Change from:
```python
def test_enemy_with_poison_can_apply_poison(self, character, poison_enemy):
    """Spec: Enemies can apply poison to the player (20% chance on attack)."""
    combat = CombatEncounter(player=character, enemy=poison_enemy)
    combat.start()

    # Enemy attacks - with 100% poison chance, should always apply
    initial_effects = len(character.status_effects)
    combat.enemy_turn()

    # Character should now have poison
    assert len(character.status_effects) == initial_effects + 1
    assert character.status_effects[0].name == "Poison"
```

To:
```python
def test_enemy_with_poison_can_apply_poison(self, character, poison_enemy):
    """Spec: Enemies can apply poison to the player (20% chance on attack)."""
    from unittest.mock import patch

    combat = CombatEncounter(player=character, enemy=poison_enemy)
    combat.start()

    initial_effects = len(character.status_effects)

    # Mock random to prevent dodge and ensure poison applies
    with patch('cli_rpg.combat.random.random', return_value=0.50):
        combat.enemy_turn()

    # Character should now have poison
    assert len(character.status_effects) == initial_effects + 1
    assert character.status_effects[0].name == "Poison"
```

## Verification

```bash
# Run test multiple times to confirm no flakiness
for i in {1..10}; do pytest tests/test_status_effects.py::TestCombatStatusEffects::test_enemy_with_poison_can_apply_poison -v; done

# Full test suite
pytest
```
