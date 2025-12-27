# Monster Migration for Issue 25 (Dynamic Interior Events)

## Overview
Add monster migration events to SubGrid dungeons. When triggered, enemies shift spawn locations within the dungeon, creating dynamic encounter distributions. This builds on the existing `interior_events.py` infrastructure.

## Spec
- Monster migration is a new `InteriorEvent` type: `"monster_migration"`
- Triggers with 3% chance per SubGrid move (lower than cave-in's 5% since less disruptive)
- Same category restrictions as cave-ins: dungeon, cave, ruins, temple
- Effect: Modifies encounter rates for rooms within SubGrid temporarily
- Duration: 2-6 hours (shorter than cave-ins since less impactful)
- Player notification: Warning message when migration triggers

### Migration Mechanic
Rather than tracking individual enemy positions (enemies spawn on encounter), monster migration modifies **encounter rate multipliers** for SubGrid rooms:
- Some rooms get increased encounter rate (monsters gathered there)
- Some rooms get decreased encounter rate (monsters fled)
- Effect stored in `InteriorEvent` with `affected_rooms` field

## Implementation

### 1. Extend InteriorEvent dataclass
Add optional `affected_rooms` field for room-specific modifiers:
```python
@dataclass
class InteriorEvent:
    # ... existing fields ...
    affected_rooms: Optional[dict] = None  # {(x,y,z): modifier} for migration
```

### 2. Add migration constants and functions
Add to `interior_events.py`:
```python
MONSTER_MIGRATION_SPAWN_CHANCE = 0.03
MONSTER_MIGRATION_DURATION_RANGE = (2, 6)
MONSTER_MIGRATION_CATEGORIES = CAVE_IN_CATEGORIES  # Same: dungeon, cave, ruins, temple

def check_for_monster_migration(game_state, sub_grid) -> Optional[str]:
    """Check for monster migration event after SubGrid movement."""

def get_encounter_modifier_at_location(sub_grid, coords) -> float:
    """Get cumulative encounter rate modifier from active migrations."""
```

### 3. Integrate with random encounter system
Modify `random_encounters.py` to check for migration modifiers when inside SubGrid:
```python
def check_for_random_encounter(game_state):
    # ... existing code ...
    # Add: Check for migration modifier in SubGrid
    if game_state.active_sub_grid:
        modifier = get_encounter_modifier_at_location(sub_grid, coords)
        encounter_rate *= modifier
```

### 4. Clear expired migrations
Extend `progress_interior_events()` to handle migration expiry.

## Test Plan
File: `tests/test_interior_events.py` (extend existing)

1. **test_monster_migration_event_creation** - Event with type "monster_migration" and affected_rooms
2. **test_monster_migration_spawn_chance** - 3% spawn rate
3. **test_monster_migration_valid_categories** - Only dungeon/cave/ruins/temple
4. **test_monster_migration_duration_range** - 2-6 hours
5. **test_monster_migration_affected_rooms** - affected_rooms dict populated
6. **test_get_encounter_modifier_default** - Returns 1.0 when no migrations
7. **test_get_encounter_modifier_with_migration** - Returns modified value
8. **test_monster_migration_expiry** - Migration clears after duration
9. **test_monster_migration_serialization** - affected_rooms serializes correctly
10. **test_multiple_migrations_stack** - Multiple active migrations combine

## Files to Modify
- `src/cli_rpg/interior_events.py` - Add migration event logic
- `src/cli_rpg/random_encounters.py` - Apply migration modifiers
- `tests/test_interior_events.py` - Add migration tests

## Acceptance Criteria
- [ ] Monster migration event type added to InteriorEvent
- [ ] 3% spawn chance per SubGrid move in valid categories
- [ ] Affected rooms get encounter rate modifiers (0.5x to 2.0x)
- [ ] Duration 2-6 hours with auto-expiry
- [ ] Integration with random encounter system
- [ ] Serialization preserves affected_rooms
- [ ] 10 new tests pass
