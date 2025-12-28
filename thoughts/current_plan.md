# Issue 27 - Dungeon Ambiance: Day/Night Undead Effects

## Spec

**Feature**: Undead enemies are more active at night (more frequent, stronger)

**Behavior**:
- At night (18:00-5:59), undead encounter rates increase by 50%
- At night, undead enemy stats gain +20% attack and +10% health
- Affected enemies: Skeleton, Zombie, Ghost, Wraith, Phantom, Specter, Lich, Vampire (matches `cleric.py` UNDEAD_TERMS)
- Applies in dungeons, ruins, and caves where undead spawn

**Integration points**:
- `encounter_tables.py`: Add `get_undead_night_modifier()` for undead categories
- `combat.py`: Add `apply_undead_night_bonus()` in `spawn_enemy()`
- `random_encounters.py`: Apply night modifier to encounter rate

## Tests (TDD)

### File: `tests/test_undead_night_effects.py`

1. `test_undead_encounter_rate_increased_at_night` - Night undead encounter modifier is 1.5
2. `test_undead_encounter_rate_normal_during_day` - Day undead encounter modifier is 1.0
3. `test_undead_stats_boosted_at_night` - Undead attack +20%, health +10% at night
4. `test_undead_stats_normal_during_day` - No stat boost during day
5. `test_non_undead_no_night_bonus` - Non-undead enemies unaffected by night
6. `test_night_modifier_uses_game_time` - Modifier checks GameTime.is_night()
7. `test_spawn_enemy_applies_night_bonus` - spawn_enemy() applies bonus when is_night=True
8. `test_random_encounter_uses_night_modifier` - check_for_random_encounter() uses night modifier

## Implementation Steps

### Step 1: Add night encounter functions to `encounter_tables.py`

```python
# Night undead modifier (50% increase)
UNDEAD_NIGHT_ENCOUNTER_MODIFIER = 1.5

# Categories that have undead enemies
UNDEAD_CATEGORIES = {"dungeon", "ruins"}

def get_undead_night_modifier(category: str, is_night: bool) -> float:
    """Get encounter rate modifier for undead at night.

    Args:
        category: Location category
        is_night: Whether it's currently night

    Returns:
        1.5 if night and undead category, 1.0 otherwise
    """
    if is_night and category in UNDEAD_CATEGORIES:
        return UNDEAD_NIGHT_ENCOUNTER_MODIFIER
    return 1.0
```

### Step 2: Add night stat bonus to `combat.py`

In `spawn_enemy()`, after calculating base stats, check if enemy is undead and is_night:

```python
# Add parameter
def spawn_enemy(
    location_name: str,
    level: int,
    location_category: Optional[str] = None,
    terrain_type: Optional[str] = None,
    distance: int = 0,
    is_night: bool = False  # NEW PARAMETER
) -> Enemy:
    ...
    # After scaling by distance, apply night bonus for undead
    from cli_rpg.cleric import is_undead
    if is_night and is_undead(enemy_name):
        scaled_health = int(scaled_health * 1.1)   # +10% health
        scaled_attack = int(scaled_attack * 1.2)   # +20% attack
```

### Step 3: Pass is_night to spawn_enemy in `random_encounters.py`

In `_handle_hostile_encounter()`:

```python
enemy = spawn_enemy(
    location_name=location.name,
    level=level,
    location_category=location.category,
    terrain_type=location.terrain,
    is_night=game_state.game_time.is_night(),  # NEW
)
```

### Step 4: Apply night encounter modifier in `random_encounters.py`

In `check_for_random_encounter()`, after getting base encounter rate:

```python
from cli_rpg.encounter_tables import get_encounter_rate, get_undead_night_modifier

# Get base rate
encounter_rate = get_encounter_rate(location.category) if location.category else RANDOM_ENCOUNTER_CHANCE

# Apply night undead modifier
is_night = game_state.game_time.is_night()
encounter_rate *= get_undead_night_modifier(location.category or "", is_night)
```

## Files Modified

1. `src/cli_rpg/encounter_tables.py` - Add `UNDEAD_NIGHT_ENCOUNTER_MODIFIER`, `UNDEAD_CATEGORIES`, `get_undead_night_modifier()`
2. `src/cli_rpg/combat.py` - Add `is_night` parameter to `spawn_enemy()`, apply undead night stat bonus
3. `src/cli_rpg/random_encounters.py` - Pass `is_night` to spawn_enemy, apply night encounter modifier
4. `tests/test_undead_night_effects.py` - 8 new tests

## Files Created

1. `tests/test_undead_night_effects.py`
