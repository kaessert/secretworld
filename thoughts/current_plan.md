# Living World Events - Implementation Plan

## Feature Summary
Add timed world events (plagues, caravans, invasions) that progress with in-game time, giving players urgency and making the world feel alive. Leverages existing GameTime infrastructure.

## Spec

### WorldEvent Model
- **Type**: `dataclass` in new file `src/cli_rpg/models/world_event.py`
- **Fields**:
  - `event_id`: str - unique identifier (e.g., "plague_millbrook_001")
  - `name`: str - display name (e.g., "The Crimson Plague")
  - `description`: str - what's happening (e.g., "A deadly plague spreads through Millbrook")
  - `event_type`: str - category ("plague", "caravan", "invasion", "festival")
  - `affected_locations`: list[str] - location names affected
  - `start_hour`: int - game hour when event started
  - `duration_hours`: int - how long event lasts before consequence
  - `is_active`: bool - whether event is still ongoing
  - `is_resolved`: bool - whether player addressed it
  - `consequence_applied`: bool - whether negative outcome happened
- **Serialization**: `to_dict()` / `from_dict()` for persistence

### WorldEventManager
- **Location**: New file `src/cli_rpg/world_events.py`
- **State**: `active_events: list[WorldEvent]` stored in GameState
- **Functions**:
  - `check_for_new_event(game_state, chance=0.05) -> Optional[WorldEvent]` - 5% chance per move to spawn
  - `progress_events(game_state) -> list[str]` - called on time advance, returns progress messages
  - `get_active_events() -> list[WorldEvent]` - for status display
  - `resolve_event(event_id) -> str` - mark event resolved
  - `apply_consequence(event: WorldEvent) -> str` - when event timer expires

### Event Types (MVP - 3 types)
1. **Caravan Arriving** (positive, timed)
   - "A merchant caravan arrives in {location}. They leave in {hours} hours."
   - Adds temporary merchant NPC with rare items
   - Consequence: Caravan leaves, merchant despawns

2. **Plague Spreading** (negative, timed)
   - "A plague spreads in {location}. Find a cure within {hours} hours!"
   - Affected location has "plague" marker
   - Consequence: NPCs become unavailable, shop prices double

3. **Monster Incursion** (negative, timed)
   - "Monsters overrun {location}! Clear them within {hours} hours."
   - Higher encounter rate in affected location
   - Consequence: Location becomes dangerous (instant combat on entry)

### Integration Points
- **Time progression**: Hook into `GameTime.advance()` to progress events
- **Move**: Show event warnings when entering affected locations
- **Status command**: Show active events and remaining time
- **New command**: `events` - list all active world events

### Output Format
```
╔════════════════════════════════════════════════════════╗
║  WORLD EVENT: Merchant Caravan Arriving               ║
║                                                       ║
║  A wealthy caravan has arrived at Millbrook Village.  ║
║  They will depart in 12 hours.                        ║
║                                                       ║
║  [Hint]: Visit Millbrook to trade for rare goods!     ║
╚════════════════════════════════════════════════════════╝
```

## Tests (TDD)

### File: `tests/test_world_events.py`

1. **test_world_event_model_creation** - WorldEvent dataclass with required fields
2. **test_world_event_serialization** - to_dict/from_dict roundtrip
3. **test_event_spawns_on_move** - With seeded RNG, event can trigger on move
4. **test_event_progresses_with_time** - Event duration decreases as GameTime advances
5. **test_event_consequence_when_expired** - Consequence applied when timer reaches 0
6. **test_event_resolved_before_expiry** - Resolving event prevents consequence
7. **test_caravan_adds_merchant_npc** - Caravan event adds temporary merchant to location
8. **test_plague_affects_location** - Plague marks location, affects NPCs
9. **test_events_command_lists_active** - `events` command shows active events
10. **test_status_shows_event_count** - Status command mentions active events
11. **test_events_persist_on_save_load** - Events survive save/load cycle
12. **test_enter_affected_location_shows_warning** - Moving to affected location shows event message

## Implementation Steps

1. **Create `src/cli_rpg/models/world_event.py`**
   - Define `WorldEvent` dataclass
   - Add `to_dict()` / `from_dict()` methods
   - Add `get_time_remaining(current_hour: int) -> int` method
   - Add `is_expired(current_hour: int) -> bool` method

2. **Create `src/cli_rpg/world_events.py`**
   - Constants: `EVENT_SPAWN_CHANCE = 0.05`, `EVENT_TEMPLATES`
   - `spawn_random_event(game_state) -> WorldEvent` - creates event from templates
   - `check_for_new_event(game_state) -> Optional[str]` - rolls for event spawn
   - `progress_events(game_state) -> list[str]` - advances all events, applies consequences
   - `format_event_notification(event) -> str` - formats event announcement box
   - `get_location_event_warning(location, events) -> Optional[str]` - warning for affected location

3. **Modify `src/cli_rpg/game_state.py`**
   - Add `world_events: list[WorldEvent] = []` attribute
   - In `move()`: Check for new event spawn (after random encounters)
   - In `move()`: Show warning if entering affected location
   - Modify `to_dict()` / `from_dict()` to include world_events

4. **Modify `src/cli_rpg/models/game_time.py`**
   - Add callback hook or modify `advance()` to trigger event progression
   - Or: Call event progression from GameState when time advances

5. **Add `events` command to game loop**
   - List all active world events with time remaining
   - Format: "1. The Crimson Plague - Millbrook (8 hours remaining)"

6. **Modify status command**
   - Add line: "Active Events: 2" (if any)

7. **Write tests in `tests/test_world_events.py`**
   - Follow existing test patterns from `test_random_encounters.py` and `test_dread.py`
   - Use `unittest.mock.patch` to control RNG

## Files to Create/Modify
- **Create**: `src/cli_rpg/models/world_event.py`
- **Create**: `src/cli_rpg/world_events.py`
- **Create**: `tests/test_world_events.py`
- **Modify**: `src/cli_rpg/game_state.py` (add world_events list, hooks in move())
- **Modify**: `src/cli_rpg/main.py` (add `events` command)
- **Modify**: Status command output (show event count)
