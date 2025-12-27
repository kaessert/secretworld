# Issue 25: Dynamic Interior Events - Cave-In Implementation

## Spec

Implement **cave-in events** that temporarily block passages in SubGrid locations (dungeons, caves, temples, ruins). Cave-ins:
- Spawn randomly during SubGrid movement (similar to overworld world events)
- Block a direction for a limited time (hours) until cleared
- Can be cleared by waiting or manually (future: digging tools)
- Use existing `blocked_directions` infrastructure from Issue 23
- Persist in save files via SubGrid serialization

## Files to Create

### `src/cli_rpg/interior_events.py`
New module for interior-specific events (cave-ins, future: monster migrations, spreading hazards)
- `InteriorEvent` dataclass: `event_id`, `event_type`, `location_coords`, `blocked_direction`, `start_hour`, `duration_hours`, `is_active`
- `CAVE_IN_SPAWN_CHANCE = 0.05` (5% per move, matches world event spawn rate)
- `CAVE_IN_DURATION_RANGE = (4, 12)` hours
- `CAVE_IN_CATEGORIES = {"dungeon", "cave", "ruins", "temple"}` - locations where cave-ins can occur
- `check_for_cave_in(game_state, sub_grid) -> Optional[str]` - spawn cave-in on movement
- `progress_interior_events(game_state, sub_grid, hours=1) -> list[str]` - clear expired cave-ins
- `clear_cave_in(sub_grid, coords, direction) -> bool` - remove cave-in from blocked_directions

### `tests/test_interior_events.py`
Test file with:
- `TestInteriorEventModel`: event creation, serialization
- `TestCaveInSpawning`: spawn chance, valid categories, blocked direction updates
- `TestCaveInClearing`: time-based expiry, manual clearing
- `TestCaveInIntegration`: movement blocked, cleared after time, message display

## Files to Modify

### `src/cli_rpg/world_grid.py`
Add to SubGrid:
- `interior_events: List[InteriorEvent] = field(default_factory=list)`
- Update `to_dict()` and `from_dict()` for serialization (backward compatible)

### `src/cli_rpg/game_state.py`
In `_move_in_sub_grid()`:
1. After movement succeeds, call `check_for_cave_in()` (5% chance)
2. Before time advance, call `progress_interior_events()` to clear expired cave-ins
3. Display cave-in messages if any

### `src/cli_rpg/models/location.py`
No changes needed - `blocked_directions` already exists and is serialized.

## Implementation Steps

1. **Create InteriorEvent model and core functions** in `interior_events.py`:
   - Define `InteriorEvent` dataclass with serialization
   - Implement `check_for_cave_in()` - picks random available direction from current location, adds to `blocked_directions`, creates event
   - Implement `progress_interior_events()` - checks each event, removes from `blocked_directions` when expired
   - Implement `clear_cave_in()` for manual clearing

2. **Write tests** in `test_interior_events.py`:
   - Test event model creation and serialization
   - Test spawn logic (correct categories, direction selection)
   - Test expiry logic (event clears after duration)
   - Test integration with Location.blocked_directions

3. **Extend SubGrid serialization** in `world_grid.py`:
   - Add `interior_events` field with backward-compatible deserialization

4. **Integrate with game loop** in `game_state.py`:
   - Hook `check_for_cave_in()` into `_move_in_sub_grid()` after successful move
   - Hook `progress_interior_events()` to clear expired events when time advances

5. **Run tests**: `pytest tests/test_interior_events.py -v && pytest`
