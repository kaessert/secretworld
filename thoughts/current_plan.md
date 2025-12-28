# Implementation Plan: Stealth Kills Bonus XP

## Spec
Award bonus XP when player kills an enemy with a backstab (attack from stealth). Bonus: 25% of enemy's base XP reward per stealth kill.

## Files to Modify
- `src/cli_rpg/combat.py` - Track stealth kills, apply bonus in `end_combat()`
- `tests/test_sneak.py` - Add test for stealth kill XP bonus

## Implementation Steps

### 1. Add test for stealth kill XP bonus
**File:** `tests/test_sneak.py`

Add new test class after existing tests:
```python
class TestSneakKillBonusXP:
    """Spec: Killing enemy with backstab grants 25% bonus XP."""

    def test_stealth_kill_grants_bonus_xp(self):
        """Spec: Backstab kill grants 25% bonus XP on combat end."""
        # Create Rogue with high STR to one-shot enemy
        # Use enemy with xp_reward=100 for easy math
        # Sneak -> attack -> verify combat.stealth_kills == 1
        # Call end_combat(victory=True)
        # Assert "Stealth bonus" in message
        # Assert player got 125 XP (100 base + 25 bonus)

    def test_no_bonus_for_normal_kills(self):
        """Spec: Normal kills don't grant stealth bonus XP."""
        # Kill without stealth
        # Assert combat.stealth_kills == 0
        # Assert no "Stealth bonus" message
        # Assert player got exactly 100 XP
```

### 2. Add stealth_kills counter to CombatEncounter.__init__()
**File:** `src/cli_rpg/combat.py`, line ~403 (after combo system state)

```python
# Stealth kill tracking for bonus XP
self.stealth_kills = 0
```

### 3. Track stealth kills in player_attack()
**File:** `src/cli_rpg/combat.py`, lines 749-750

Modify enemy death check to increment counter:
```python
if not enemy.is_alive():
    if is_backstab:
        self.stealth_kills += 1
    message += f"\n{colors.enemy(enemy.name)} has been defeated!"
```

### 4. Apply stealth kill bonus XP in end_combat()
**File:** `src/cli_rpg/combat.py`, lines 1958-1961

After calculating total_xp, add bonus before calling gain_xp:
```python
# Sum XP from all enemies
total_xp = sum(e.xp_reward for e in self.enemies)

# Add stealth kill bonus (25% per stealth kill)
stealth_bonus = 0
if self.stealth_kills > 0:
    stealth_bonus = int(total_xp * 0.25 * self.stealth_kills / len(self.enemies))
    messages.append(f"Stealth bonus: +{stealth_bonus} XP!")

xp_messages = self.player.gain_xp(total_xp + stealth_bonus)
```

## Verification
```bash
pytest tests/test_sneak.py::TestSneakKillBonusXP -v
pytest tests/test_sneak.py -v
```
