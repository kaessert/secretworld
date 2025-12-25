# Implementation Plan: Boss Fights

## Spec

Boss fights are special combat encounters with enhanced enemies that serve as progression milestones. Bosses:
- Have `is_boss=True` flag on the Enemy model
- Have 2-3x base stats (health, attack, defense) and 3-5x XP reward
- Spawn deterministically in dungeon/ruins locations (not random 30% chance)
- Drop guaranteed loot with enhanced quality
- Are tracked separately in the bestiary

## Implementation Steps

### 1. Extend Enemy Model

**File:** `src/cli_rpg/models/enemy.py`

Add optional boss flag to Enemy dataclass:
```python
is_boss: bool = False
```

Update `to_dict()` and `from_dict()` to serialize/deserialize the new field (with backward compatibility default of `False`).

### 2. Add Boss Spawn Function

**File:** `src/cli_rpg/combat.py`

Add `spawn_boss()` function after `spawn_enemy()`:
```python
def spawn_boss(
    location_name: str,
    level: int,
    location_category: Optional[str] = None
) -> Enemy:
```

Boss templates by location type:
- `dungeon`: ["Lich Lord", "Dark Champion", "Demon Lord"]
- `ruins`: ["Ancient Guardian", "Cursed Pharaoh", "Shadow King"]
- `cave`: ["Cave Troll King", "Elder Wyrm", "Crystal Golem"]
- `default`: ["Archdemon", "Overlord", "Chaos Beast"]

Stats scaling:
- `base_health = (40 + level * 25) * 2` (2x normal)
- `base_attack = (5 + level * 3) * 2` (2x normal)
- `base_defense = (2 + level * 2) * 2` (2x normal)
- `xp_reward = (30 + level * 20) * 4` (4x normal)

Add ASCII art templates for bosses (larger, more detailed).

### 3. Add Boss Loot Generation

**File:** `src/cli_rpg/combat.py`

Add `generate_boss_loot()` function:
```python
def generate_boss_loot(boss: Enemy, level: int) -> Item:
```

Boss loot characteristics:
- 100% drop rate (guaranteed)
- Enhanced stats: `damage_bonus = level + random(5, 10)` for weapons
- Unique prefixes: ["Legendary", "Ancient", "Cursed", "Divine", "Epic"]
- Higher tier item names: ["Greatsword", "Platemail", "Grand Elixir"]

### 4. Integrate Boss Encounters into GameState

**File:** `src/cli_rpg/game_state.py`

Add `trigger_boss_encounter()` method:
```python
def trigger_boss_encounter(self, location: Location) -> Optional[str]:
```

Modify `trigger_encounter()` logic:
- Check if location category is `dungeon` or `ruins`
- For boss-eligible locations: 10% chance of boss instead of normal enemies
- Boss encounters are single-enemy (no multi-boss fights)

### 5. Enhance Combat UI for Bosses

**File:** `src/cli_rpg/combat.py`

In `CombatEncounter.start()`:
- Check if any enemy has `is_boss=True`
- Display enhanced intro: "A BOSS appears: {name}!"
- Show boss ASCII art prominently

In `CombatEncounter.end_combat()`:
- Check if any defeated enemy was a boss
- Use `generate_boss_loot()` for boss enemies
- Display enhanced victory message for boss kills

### 6. Track Boss Kills in Bestiary

**File:** `src/cli_rpg/models/character.py`

In `record_enemy_defeat()`:
- Store `is_boss` flag in bestiary entry
- Allow bestiary display to highlight bosses

## Tests

**File:** `tests/test_boss_combat.py`

### Test Enemy Model
- `test_enemy_is_boss_default_false`: Verify default `is_boss=False`
- `test_enemy_is_boss_serialization`: Verify to_dict/from_dict preserves flag

### Test Boss Spawn
- `test_spawn_boss_stats_scaled`: Verify 2x stats, 4x XP
- `test_spawn_boss_is_boss_flag`: Verify `is_boss=True`
- `test_spawn_boss_location_category_templates`: Verify category-based templates

### Test Boss Loot
- `test_generate_boss_loot_guaranteed`: Verify 100% drop rate
- `test_generate_boss_loot_enhanced_stats`: Verify higher damage/defense bonuses
- `test_generate_boss_loot_unique_prefixes`: Verify legendary-tier prefixes

### Test Boss Combat Flow
- `test_boss_combat_intro_message`: Verify "BOSS appears" messaging
- `test_boss_combat_end_uses_boss_loot`: Verify boss loot generation on victory
- `test_boss_combat_quest_tracking`: Verify boss kills trigger KILL quests

### Test Boss Encounters
- `test_trigger_boss_encounter_dungeon_chance`: Verify 10% in dungeons
- `test_trigger_boss_encounter_town_no_boss`: Verify 0% in towns
- `test_boss_encounter_single_enemy`: Verify boss fights are solo (no adds)

## File Summary

| File | Action |
|------|--------|
| `src/cli_rpg/models/enemy.py` | Add `is_boss` field |
| `src/cli_rpg/combat.py` | Add `spawn_boss()`, `generate_boss_loot()`, enhance UI |
| `src/cli_rpg/game_state.py` | Add `trigger_boss_encounter()` |
| `src/cli_rpg/models/character.py` | Track boss flag in bestiary |
| `tests/test_boss_combat.py` | New test file |
