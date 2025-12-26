# Implementation Plan: Fix Flaky Fighting Stance Test

## Problem
The test `test_aggressive_stance_increases_attack_damage` in `tests/test_fighting_stances.py` is flaky because it seeds `random` **after** the balanced stance attack (line 247), allowing balanced to get a random crit while aggressive gets a deterministic non-crit.

## Root Cause
- Line 237: Balanced stance attack (no seed) → can crit randomly
- Line 247: `random.seed(42)` set only before aggressive attack
- Line 248: Aggressive stance attack → deterministic, no crit with seed 42
- If balanced crits (1.5x damage) and aggressive doesn't, aggressive may deal less damage

## Fix
Seed `random` **before both attacks** with the same seed value so both get identical crit rolls (either both crit or neither crits), ensuring aggressive always deals 20% more damage.

## Implementation

### File: `tests/test_fighting_stances.py`

**Current code (lines 225-253)**:
```python
def test_aggressive_stance_increases_attack_damage(self):
    """Test that AGGRESSIVE stance increases damage dealt by 20%."""
    from cli_rpg.combat import CombatEncounter
    from cli_rpg.models.enemy import Enemy

    char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
    enemy = Enemy(name="Dummy", health=1000, max_health=1000, attack_power=1, defense=0, xp_reward=10, level=1)

    # Baseline damage with BALANCED stance
    char.stance = FightingStance.BALANCED
    combat = CombatEncounter(char, enemy)
    combat.start()
    victory, _ = combat.player_attack()
    balanced_damage = 1000 - enemy.health

    # Reset enemy
    enemy.health = 1000
    char.stance = FightingStance.AGGRESSIVE
    combat2 = CombatEncounter(char, enemy)
    combat2.start()
    # Seed random for consistent results in crit chance
    import random
    random.seed(42)
    victory, _ = combat2.player_attack()
    aggressive_damage = 1000 - enemy.health

    # Aggressive should deal more damage (about 1.2x)
    # Allow some variance due to crit chance
    assert aggressive_damage >= balanced_damage
```

**Fixed code**:
```python
def test_aggressive_stance_increases_attack_damage(self):
    """Test that AGGRESSIVE stance increases damage dealt by 20%."""
    import random
    from cli_rpg.combat import CombatEncounter
    from cli_rpg.models.enemy import Enemy

    char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
    enemy = Enemy(name="Dummy", health=1000, max_health=1000, attack_power=1, defense=0, xp_reward=10, level=1)

    # Seed random BEFORE both attacks for consistent crit behavior
    random.seed(42)

    # Baseline damage with BALANCED stance
    char.stance = FightingStance.BALANCED
    combat = CombatEncounter(char, enemy)
    combat.start()
    victory, _ = combat.player_attack()
    balanced_damage = 1000 - enemy.health

    # Reset enemy and reseed for identical crit roll
    enemy.health = 1000
    random.seed(42)
    char.stance = FightingStance.AGGRESSIVE
    combat2 = CombatEncounter(char, enemy)
    combat2.start()
    victory, _ = combat2.player_attack()
    aggressive_damage = 1000 - enemy.health

    # Aggressive should deal more damage (about 1.2x)
    # With same seed, both get same crit roll, so aggressive is strictly greater
    assert aggressive_damage > balanced_damage
```

**Key changes**:
1. Move `import random` to top of function
2. Add `random.seed(42)` **before** balanced stance attack
3. Add `random.seed(42)` again before aggressive attack (to reset RNG to same state)
4. Change assertion from `>=` to `>` since with identical crit behavior, aggressive is always strictly greater

## Verification
Run the test multiple times to confirm it passes consistently:
```bash
pytest tests/test_fighting_stances.py::TestCombatWithStance::test_aggressive_stance_increases_attack_damage -v --count=10
```
