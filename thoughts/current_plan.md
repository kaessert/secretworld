# Implementation Plan: Critical Hits and Miss Chances

## Spec

Add critical hit and miss mechanics to combat based on player/enemy stats:

**Critical Hits (Player)**:
- Base crit chance: 5%
- DEX bonus: +1% per point (capped at +15% from DEX)
- On crit: 1.5x damage with special message
- Formula: `crit_chance = min(5 + player.dexterity, 20)`

**Miss Chance (Enemy attacks player)**:
- Base miss chance: 5%
- Player DEX bonus: +0.5% per point (capped at +10% from DEX)
- On miss: 0 damage with dodge message
- Formula: `dodge_chance = min(5 + player.dexterity // 2, 15)`

**Critical Hits (Enemy)**:
- Flat 5% crit chance for enemies
- On crit: 1.5x damage with special message

## Tests First (TDD)

Add to `tests/test_combat.py`:

1. `TestCriticalHits` class:
   - `test_player_attack_can_crit_with_high_dex` - DEX 20 player crits more often (statistical)
   - `test_player_crit_deals_1_5x_damage` - Verify damage formula on crit
   - `test_player_crit_message_includes_critical` - "critical" in message
   - `test_player_cast_can_crit` - Magic attacks can also crit (INT-based crit for cast)

2. `TestMissChance` class:
   - `test_enemy_attack_can_miss_high_dex_player` - High DEX player dodges sometimes
   - `test_enemy_miss_deals_zero_damage` - Verify no damage on miss
   - `test_enemy_miss_message_includes_dodge_or_miss` - Appropriate message

3. `TestEnemyCriticalHits` class:
   - `test_enemy_attack_can_crit` - Enemy can deal critical damage
   - `test_enemy_crit_deals_1_5x_damage` - Verify 1.5x multiplier

## Implementation

### File: `src/cli_rpg/combat.py`

1. Add helper functions after line ~100 (after `strip_leading_name`):

```python
def calculate_crit_chance(dexterity: int) -> float:
    """Calculate critical hit chance based on dexterity.

    Formula: 5% base + 1% per DEX point, capped at 20%.
    """
    return min(5 + dexterity, 20) / 100.0

def calculate_dodge_chance(dexterity: int) -> float:
    """Calculate dodge chance based on dexterity.

    Formula: 5% base + 0.5% per DEX point, capped at 15%.
    """
    return min(5 + dexterity // 2, 15) / 100.0

ENEMY_CRIT_CHANCE = 0.05  # Flat 5% crit chance for enemies
CRIT_MULTIPLIER = 1.5
```

2. Modify `player_attack()` (~line 479):
   - After calculating `dmg`, check for crit
   - Roll random, if <= crit_chance, multiply damage by 1.5
   - Modify message to include "CRITICAL HIT!"

3. Modify `player_cast()` (~line 610):
   - Add crit check using INT instead of DEX
   - Same crit multiplier and messaging

4. Modify `enemy_turn()` (~line 706):
   - Before applying damage, check for player dodge (based on player DEX)
   - If dodge, set damage to 0 and show dodge message
   - If not dodge, check for enemy crit (flat 5%)
   - If crit, multiply damage by 1.5 and show crit message

## Files to Modify

1. `tests/test_combat.py` - Add test classes for crit/miss mechanics
2. `src/cli_rpg/combat.py` - Add crit/dodge logic to attack methods
