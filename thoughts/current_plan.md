# Implementation Plan: Basic Weather System

## Overview
Add a weather system that affects gameplay, building on the existing day/night cycle infrastructure in `GameTime`. Weather states (clear, rain, storm, fog) will affect dread buildup, travel time, and provide atmospheric descriptions.

## Specification

### Weather States
- **clear**: Default weather, no modifiers
- **rain**: Atmospheric, +2 dread per move, reduces visibility slightly
- **storm**: Dangerous, +5 dread per move, travel takes +1 hour
- **fog**: Mysterious, +3 dread per move, 50% chance enemies get surprise attack

### Weather Transitions
- Weather changes randomly on each hour advance (10% chance per hour)
- Weather persists across saves (stored in GameTime or separate Weather model)
- Some location categories affect weather probability (caves always clear, mountains more storms)

### Display Integration
- `status` command shows weather: "Weather: Rainy ☔"
- Move descriptions include weather flavor: "You trudge through the rain..."
- Whispers can reference weather conditions

---

## Tests (TDD - write before implementation)

### File: `tests/test_weather.py`

1. **Weather model tests**
   - `test_weather_defaults_to_clear` - Default weather is "clear"
   - `test_weather_get_display_clear` - Display shows "Clear ☀"
   - `test_weather_get_display_rain` - Display shows "Rain ☔"
   - `test_weather_get_display_storm` - Display shows "Storm ⛈"
   - `test_weather_get_display_fog` - Display shows "Fog 🌫"
   - `test_weather_serialization` - to_dict/from_dict round-trips correctly
   - `test_weather_transition_changes_state` - transition() can change weather
   - `test_weather_stays_clear_in_caves` - Caves always report clear weather

2. **Weather integration tests**
   - `test_game_state_has_weather` - GameState includes weather attribute
   - `test_move_advances_weather` - Movement can trigger weather transitions
   - `test_weather_affects_dread_rain` - Rain adds +2 dread on move
   - `test_weather_affects_dread_storm` - Storm adds +5 dread on move
   - `test_storm_adds_travel_time` - Storm weather adds +1 hour to travel
   - `test_weather_persists_in_save` - Weather saved/loaded with game state
   - `test_weather_backward_compatibility` - Old saves without weather default to clear

3. **Display integration tests**
   - `test_status_shows_weather` - Status command includes weather display
   - `test_move_message_includes_weather_flavor` - Movement messages mention weather

---

## Implementation Steps

### Step 1: Create Weather Model
**File**: `src/cli_rpg/models/weather.py`

```python
@dataclass
class Weather:
    condition: str = "clear"  # clear, rain, storm, fog

    WEATHER_STATES = ["clear", "rain", "storm", "fog"]
    DREAD_MODIFIERS = {"clear": 0, "rain": 2, "storm": 5, "fog": 3}
    TRAVEL_MODIFIERS = {"clear": 0, "rain": 0, "storm": 1, "fog": 0}

    def get_display(self) -> str
    def get_dread_modifier(self) -> int
    def get_travel_modifier(self) -> int
    def transition(self) -> Optional[str]  # Returns new weather if changed
    def to_dict(self) -> dict
    @classmethod def from_dict(cls, data: dict) -> "Weather"
```

### Step 2: Add Weather Flavor Text
**File**: `src/cli_rpg/models/weather.py`

Add weather descriptions for movement messages:
```python
WEATHER_FLAVOR = {
    "clear": ["The sky is clear above you.", "Sunlight warms your path."],
    "rain": ["Rain patters against your gear.", "You trudge through the mud."],
    "storm": ["Thunder rumbles ominously.", "Lightning illuminates the path."],
    "fog": ["Mist swirls around you.", "Shapes move in the fog..."],
}
```

### Step 3: Integrate Weather into GameState
**File**: `src/cli_rpg/game_state.py`

- Add `weather: Weather` attribute in `__init__`
- Update `_update_dread_on_move()` to include weather modifier
- Update `move()` to:
  - Add weather flavor to movement message
  - Apply storm travel time modifier
  - Call `weather.transition()` after time advances
- Update `to_dict()` to include weather
- Update `from_dict()` to restore weather (with backward compat)

### Step 4: Update Status Display
**File**: `src/cli_rpg/main.py`

- Update status command handler to show weather:
  ```python
  weather_display = game_state.weather.get_display()
  return (True, f"\n{status_output}\nTime: {time_display}\nWeather: {weather_display}\n{dread_display}")
  ```

### Step 5: Cave Location Override
**File**: `src/cli_rpg/game_state.py`

- In `_update_dread_on_move()`, check if location category is "cave"
- If cave, skip weather dread modifier (you're underground)
- Add helper method `get_effective_weather(location)` that returns "clear" for caves
