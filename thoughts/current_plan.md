# Day/Night Cycle Implementation Plan

## Overview
Implement a basic day/night cycle that tracks game time and changes location descriptions, NPC availability, and whispers based on time of day.

## Spec

**Time System:**
- Game time tracked in `GameState` as `game_time: int` (hour 0-23)
- Time advances on player actions: movement (+1 hour), rest (+4 hours), combat completion (+1 hour)
- Two periods: Day (6:00-17:59) and Night (18:00-5:59)
- `get_time_period() -> str` returns "day" or "night"
- `get_time_display() -> str` returns formatted time like "14:00 (Day)"

**Time Effects:**
1. Location descriptions append time-specific flavor text at night
2. WhisperService uses time-aware whisper templates (eerie at night)
3. NPCs may be unavailable at night (shops close)
4. `status` command displays current time

**Persistence:**
- `game_time` serialized in `GameState.to_dict()` and restored in `from_dict()`

---

## Implementation Steps

### 1. Create time model (`src/cli_rpg/models/game_time.py`)
```python
@dataclass
class GameTime:
    hour: int = 6  # Start at 6:00 AM

    def advance(self, hours: int) -> None
    def get_period(self) -> str  # "day" or "night"
    def get_display(self) -> str  # "14:00 (Day)"
    def is_night(self) -> bool
    def to_dict() / from_dict()
```

### 2. Add `GameTime` to `GameState` (`src/cli_rpg/game_state.py`)
- Add `game_time: GameTime` attribute in `__init__`
- Advance time on: `move()` (+1), rest command (+4), combat end (+1)
- Serialize/deserialize in `to_dict()`/`from_dict()`

### 3. Update `status` command (`src/cli_rpg/main.py`)
- Add time display to character status output: `"Time: 14:00 (Day)"`

### 4. Add night whispers (`src/cli_rpg/whisper.py`)
- Add `NIGHT_WHISPERS` templates
- `get_whisper()` takes `is_night: bool` parameter
- At night, blend night-specific whispers into pool

### 5. Add night flavor to locations (`src/cli_rpg/models/location.py`)
- Add `night_description: Optional[str]` field
- `get_layered_description()` appends night flavor when `is_night=True`

### 6. NPC night availability (`src/cli_rpg/models/npc.py`, `src/cli_rpg/main.py`)
- Add `available_at_night: bool = True` field to NPC
- `talk` command checks availability: "The merchant has gone home for the night."
- `shop` command blocked at night for closed shops

---

## Test Plan (`tests/test_day_night.py`)

### GameTime Tests
- `test_game_time_defaults_to_morning` - starts at 6:00
- `test_game_time_advance_wraps_at_24` - 23 + 2 = 1
- `test_game_time_is_night_returns_true_at_night` - 18-5 is night
- `test_game_time_is_night_returns_false_during_day` - 6-17 is day
- `test_game_time_get_period_day` - returns "day"
- `test_game_time_get_period_night` - returns "night"
- `test_game_time_serialization` - to_dict/from_dict roundtrip

### GameState Time Integration
- `test_move_advances_time` - moving increments hour by 1
- `test_rest_advances_time_by_4` - resting increments by 4
- `test_game_time_persists_in_save` - saved/loaded correctly
- `test_game_time_backward_compatibility` - old saves default to 6:00

### Whisper Night Integration
- `test_whisper_uses_night_templates_at_night` - night-specific whispers appear

### NPC Night Availability
- `test_npc_unavailable_at_night` - merchant not available at night
- `test_talk_to_npc_at_night_blocked` - returns unavailable message
- `test_shop_closed_at_night` - shop command returns closed message

### Status Display
- `test_status_shows_time` - character status includes time display

---

## Files to Create
- `src/cli_rpg/models/game_time.py` - new

## Files to Modify
- `src/cli_rpg/game_state.py` - add game_time, advance on actions
- `src/cli_rpg/main.py` - status display, NPC availability checks
- `src/cli_rpg/whisper.py` - night whispers
- `src/cli_rpg/models/npc.py` - available_at_night field
- `tests/test_day_night.py` - new test file
