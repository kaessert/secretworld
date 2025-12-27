# Monster Migration Implementation Summary

## Status: COMPLETE

All 30 interior events tests pass, all 36 random encounters tests pass, and full test suite (4919 tests) passes.

## What Was Implemented

Added monster migration events for SubGrid dungeons (Issue 25 - Dynamic Interior Events). When triggered, migrations modify encounter rate multipliers for rooms within the SubGrid, creating dynamic encounter distributions.

## Files Modified

### 1. `src/cli_rpg/interior_events.py`

**Extended `InteriorEvent` dataclass:**
- Added optional `affected_rooms: Optional[dict]` field
- Stores `{(x,y,z): modifier}` for migration-affected rooms

**Added migration constants:**
- `MONSTER_MIGRATION_SPAWN_CHANCE = 0.03` (3% per SubGrid move)
- `MONSTER_MIGRATION_DURATION_RANGE = (2, 6)` (2-6 hours)
- `MONSTER_MIGRATION_CATEGORIES` (same as cave-ins: dungeon, cave, ruins, temple)
- `MONSTER_MIGRATION_MODIFIER_RANGE = (0.5, 2.0)` (encounter rate multipliers)

**Added new functions:**
- `check_for_monster_migration(game_state, sub_grid)` - Spawns migration events with affected rooms
- `get_encounter_modifier_at_location(sub_grid, coords)` - Returns cumulative encounter modifier
- `get_active_migrations(sub_grid)` - Returns list of active migration events

**Updated existing functionality:**
- `progress_interior_events()` - Now handles migration expiry with appropriate message
- `to_dict()` and `from_dict()` - Updated to serialize/deserialize `affected_rooms` field
  - Dict with tuple keys serialized as list of `[coords, modifier]` pairs

### 2. `src/cli_rpg/random_encounters.py`

**Added migration modifier integration** in `check_for_random_encounter()`:
- When inside SubGrid, applies encounter rate modifier from active migrations
- Multiple migrations stack multiplicatively

### 3. `tests/test_interior_events.py`

**Added 10 new tests** in `TestMonsterMigration` class:
1. `test_monster_migration_event_creation` - Event with type "monster_migration" and affected_rooms
2. `test_monster_migration_spawn_chance` - 3% spawn rate
3. `test_monster_migration_valid_categories` - Only dungeon/cave/ruins/temple
4. `test_monster_migration_duration_range` - 2-6 hours
5. `test_monster_migration_affected_rooms` - affected_rooms dict populated
6. `test_get_encounter_modifier_default` - Returns 1.0 when no migrations
7. `test_get_encounter_modifier_with_migration` - Returns modified value
8. `test_monster_migration_expiry` - Migration clears after duration
9. `test_monster_migration_serialization` - affected_rooms serializes correctly
10. `test_multiple_migrations_stack` - Multiple active migrations combine multiplicatively

## Test Results

```
tests/test_interior_events.py - 30 passed
tests/test_random_encounters.py - 36 passed
Full test suite: 4919 passed
```

## Design Decisions

1. **Encounter rate modifiers instead of enemy position tracking** - Simpler design that integrates with existing encounter system
2. **Multiplicative stacking** - Multiple migrations combine multiplicatively (e.g., 1.5 * 1.2 = 1.8)
3. **Affected rooms range 0.5x to 2.0x** - Balanced to not be too disruptive
4. **Lower spawn chance than cave-ins** - 3% vs 5% since less disruptive
5. **Shorter duration than cave-ins** - 2-6 hours vs 4-12 hours since less impactful

## E2E Test Validation

To manually verify:
1. Run `cli-rpg --demo`
2. Enter a dungeon or cave location with `enter <name>`
3. Move around within the SubGrid
4. Observe for "You hear creatures stirring..." migration message (3% chance per move)
5. If triggered, encounter rates in affected rooms should be modified
6. Wait or rest for migration to expire and observe "migration has subsided" message
7. Save and load game to verify migration events persist correctly
