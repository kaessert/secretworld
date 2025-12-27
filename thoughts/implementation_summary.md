# Implementation Summary: Issue 25 - Dynamic Interior Events (Cave-Ins)

## What Was Implemented

### New Module: `src/cli_rpg/interior_events.py`
Created a new module for interior-specific dynamic events with:

- **InteriorEvent dataclass**: Model with fields:
  - `event_id`: Unique identifier
  - `event_type`: Type of event (currently "cave_in")
  - `location_coords`: 3-tuple (x, y, z) where event occurred
  - `blocked_direction`: Direction blocked by this event
  - `start_hour`: Game hour when event started
  - `duration_hours`: How long the event lasts
  - `is_active`: Whether event is still in effect
  - Methods: `is_expired()`, `get_time_remaining()`, `to_dict()`, `from_dict()`

- **Cave-in spawn logic**:
  - `check_for_cave_in()`: 5% spawn chance per move (matches world events)
  - Only spawns in valid categories: dungeon, cave, ruins, temple
  - Blocks a random available direction (north/south/east/west)
  - Duration: 4-12 hours (random)

- **Cave-in clearing logic**:
  - `progress_interior_events()`: Clears expired cave-ins on time advance
  - `clear_cave_in()`: Manual clearing function for future digging tools
  - `get_active_cave_ins()`, `get_cave_in_at_location()`: Query functions

### Modified Files

1. **`src/cli_rpg/world_grid.py`**:
   - Added `interior_events: List[InteriorEvent]` field to SubGrid dataclass
   - Updated `to_dict()` to serialize interior_events
   - Updated `from_dict()` to deserialize with backward compatibility

2. **`src/cli_rpg/game_state.py`**:
   - Modified `_move_in_sub_grid()` to:
     - Check for blocked directions (now includes cave-ins, not just puzzles)
     - Call `progress_interior_events()` after time advance
     - Call `check_for_cave_in()` after successful movement (5% chance)
     - Display messages for cleared/new cave-ins

### New Test File: `tests/test_interior_events.py`
20 tests covering:
- InteriorEvent model creation and serialization
- Cave-in spawn logic (categories, chance, duration)
- Cave-in clearing (time-based expiry, manual clearing)
- Integration with SubGrid and movement blocking
- Backward-compatible deserialization

## Test Results
- All 20 new tests pass
- Full test suite: 4657 tests pass

## Design Decisions

1. **Reused existing infrastructure**: Cave-ins use the `blocked_directions` list from Issue 23's puzzle system, ensuring consistent movement blocking behavior.

2. **Matches world events pattern**: 5% spawn chance and time-based expiry mirror the overworld world_events system for consistency.

3. **Backward compatible serialization**: Old saves without `interior_events` field load correctly with an empty list.

4. **Generic blocked message**: Changed the blocked direction message from "blocked by a puzzle" to simply "blocked" since it can now be either puzzles or cave-ins.

## E2E Validation
To validate the feature works in-game:
1. Enter a dungeon/cave/ruins/temple location
2. Move around inside the SubGrid
3. With 5% chance, a cave-in message will appear blocking a direction
4. Attempting to move in that direction will show "The way X is blocked"
5. After 4-12 game hours, the cave-in clears automatically with a message
6. Save/load should preserve cave-in state correctly
