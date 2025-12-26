# Implementation Plan: Luck (LCK) Stat Affecting Outcomes

## Spec

**New Stat**: Luck (LCK) - subtle influence on RNG outcomes

**Mechanics**:
- **Base value**: 10 (same as CHA/PER baseline)
- **Class bonuses**: Rogue +2, Ranger +1, others 0
- **Level-up**: +1 LCK per level (like other stats)
- **Effects** (all relative to LCK 10 baseline):
  - **Crit chance**: ±0.5% per LCK point (LCK 15 = +2.5% crit bonus)
  - **Loot quality**: LCK affects weapon/armor bonus rolls (+1 per 5 LCK above 10)
  - **Gold drops**: ±5% per LCK point from baseline
  - **Loot drop rate**: ±2% per LCK point (base 50%, LCK 15 = 60%)

**Persistence**: Save/load with backward compatibility (default 10)

## Tests (TDD)

**File**: `tests/test_luck_stat.py`

1. `test_character_has_luck_stat` - Character has `luck` attribute defaulting to 10
2. `test_luck_stat_validation` - LCK validates 1-20 like other stats
3. `test_class_bonuses_include_luck` - Rogue +2, Ranger +1 LCK
4. `test_level_up_increases_luck` - LCK +1 on level up
5. `test_luck_serialization` - to_dict/from_dict include luck
6. `test_luck_backward_compat` - from_dict defaults to 10 if missing
7. `test_character_str_includes_luck` - __str__ displays LCK

**File**: `tests/test_luck_combat.py`

8. `test_crit_chance_with_luck_bonus` - High LCK increases crit chance
9. `test_crit_chance_with_luck_penalty` - Low LCK decreases crit chance
10. `test_crit_chance_formula` - ±0.5% per LCK from 10

**File**: `tests/test_luck_loot.py`

11. `test_loot_drop_rate_with_high_luck` - LCK 15 = 60% drop rate
12. `test_loot_drop_rate_with_low_luck` - LCK 5 = 40% drop rate
13. `test_gold_reward_with_high_luck` - LCK 15 = +25% gold
14. `test_gold_reward_with_low_luck` - LCK 5 = -25% gold
15. `test_weapon_bonus_with_high_luck` - LCK 15 = +1 to damage bonus roll
16. `test_armor_bonus_with_high_luck` - LCK 15 = +1 to defense bonus roll

## Implementation Steps

### 1. Update Character model (`src/cli_rpg/models/character.py`)

**Add luck field** (after `perception: int = 10`, line 81):
```python
luck: int = 10  # Default luck for backward compatibility
```

**Add to CLASS_BONUSES** (lines 25-41):
- Rogue: add `"luck": 2`
- Ranger: add `"luck": 1`
- Others: add `"luck": 0`

**Update validation loop** (line 109-122):
- Add `("luck", self.luck)` to stats list

**Update __post_init__ class bonus application** (line 131):
```python
self.luck += bonuses.get("luck", 0)
```

**Update level_up()** (line 816):
```python
self.luck += 1
```
Update message (line 831):
```python
f"Stats increased: STR +1, DEX +1, INT +1, CHA +1, PER +1, LCK +1\n"
```

**Update to_dict()** (line 846):
```python
"luck": self.luck,
```

**Update from_dict()** (line 882, 914):
```python
capped_luck = min(data.get("luck", 10), cls.MAX_STAT)
```
And restore actual luck (line 914):
```python
character.luck = data.get("luck", 10)
```

**Update __str__()** (line 987):
```python
f"{colors.stat_header('Luck')}: {self.luck}"
```

### 2. Update combat crit calculation (`src/cli_rpg/combat.py`)

**Modify calculate_crit_chance()** (line 101-112):
```python
def calculate_crit_chance(stat: int, luck: int = 10) -> float:
    """Calculate critical hit chance based on a stat and luck.

    Formula: 5% base + 1% per stat point + 0.5% per luck above/below 10, capped at 25%.
    """
    base_chance = 5 + stat
    luck_bonus = (luck - 10) * 0.5
    return min(base_chance + luck_bonus, 25) / 100.0
```

**Update player_attack() crit roll** (line 645):
```python
crit_chance = calculate_crit_chance(self.player.dexterity, self.player.luck)
```

**Update player_cast() crit roll** (line 797):
```python
crit_chance = calculate_crit_chance(self.player.intelligence, self.player.luck)
```

### 3. Update loot generation (`src/cli_rpg/combat.py`)

**Modify generate_loot()** (line 1165):
```python
def generate_loot(enemy: Enemy, level: int, luck: int = 10) -> Optional[Item]:
```

**Update drop rate** (line 1176):
```python
# Base 50% + 2% per luck above/below 10
drop_chance = 0.50 + (luck - 10) * 0.02
if random.random() > drop_chance:
    return None
```

**Update weapon damage bonus** (line 1202):
```python
luck_bonus = max(0, (luck - 10) // 5)
damage_bonus = max(1, level + random.randint(1, 3) + luck_bonus)
```

**Update armor defense bonus** (line 1215):
```python
luck_bonus = max(0, (luck - 10) // 5)
defense_bonus = max(1, level + random.randint(0, 2) + luck_bonus)
```

### 4. Update gold reward calculation (`src/cli_rpg/combat.py`)

**Modify end_combat()** (line 1086):
```python
# Apply luck modifier to gold: ±5% per luck from 10
luck_modifier = 1.0 + (self.player.luck - 10) * 0.05
gold_reward = int(random.randint(5, 15) * total_level * luck_modifier)
```

### 5. Update character creation (`src/cli_rpg/character_creation.py`)

**Update get_manual_stats()** (line 109):
```python
stat_names = ["strength", "dexterity", "intelligence", "charisma", "perception", "luck"]
```

**Update generate_random_stats()** (line 150):
```python
"luck": random.randint(8, 15),
```

**Update display outputs** (lines 268-272, 397-403):
```python
print(f"Luck: {stats['luck']}")
```

### 6. Update character creation non-interactive (line 375):
Add luck to the stat_names list for manual stats.

### 7. Call site updates

**In CombatEncounter.end_combat()** - pass luck to generate_loot:
```python
loot = generate_loot(enemy, self.player.level, self.player.luck)
```

### 8. Update help/stats display
- Verify `stats` command displays luck (uses Character.__str__)
