# Plan: Extend AgentState with Environmental Fields

## Spec

Add environmental awareness fields to `AgentState` in `scripts/state_parser.py`:
- `time_of_day: str` - "day" or "night" (from GameTime.get_period())
- `hour: int` - Current hour 0-23 (from GameTime.hour)
- `season: str` - "spring", "summer", "autumn", "winter"
- `weather: str` - "clear", "rain", "storm", "fog"
- `tiredness: int` - Current tiredness level 0-100

The `dread` field already exists (line 85). Parse these from `dump_state` JSON which includes:
- `game_time.hour`, `game_time.total_hours` (derive period/season)
- `weather.condition`
- `character.tiredness.current`

Helper methods to add:
- `is_night() -> bool` - Check if night time (agent should be cautious of undead +50%)
- `is_tired() -> bool` - Check if tiredness >= 60 (should consider rest)
- `is_exhausted() -> bool` - Check if tiredness >= 80 (attack/perception penalty)
- `is_bad_weather() -> bool` - Check for storm/fog (extra dread, visibility issues)
- `should_rest() -> bool` - Composite check: tired AND (not in combat) AND (rest available)

## Tests

Add to `tests/test_ai_agent.py` in new `TestEnvironmentalAwareness` class:

1. **Field parsing from dump_state**:
   - `test_update_state_parses_game_time` - hour, time_of_day, season
   - `test_update_state_parses_weather` - weather condition
   - `test_update_state_parses_tiredness` - tiredness from character

2. **Helper method tests**:
   - `test_is_night_true_at_night_hours` - hour 18-23, 0-5
   - `test_is_night_false_at_day_hours` - hour 6-17
   - `test_is_tired_threshold` - tiredness >= 60
   - `test_is_exhausted_threshold` - tiredness >= 80
   - `test_is_bad_weather_storm_fog` - storm and fog return True
   - `test_is_bad_weather_clear_rain` - clear and rain return False
   - `test_should_rest_composite` - combines tiredness + not in combat + rest command

3. **Season derivation**:
   - `test_season_from_total_hours` - spring days 1-30, summer 31-60, etc.

## Implementation Steps

1. **Add new fields to AgentState** (`scripts/state_parser.py:85-86`):
   ```python
   # After existing dread field (line 85)
   time_of_day: str = "day"
   hour: int = 6
   season: str = "spring"
   weather: str = "clear"
   tiredness: int = 0
   ```

2. **Add helper methods to AgentState** (after `has_unexplored_exits`, ~line 170):
   - `is_night()` - return `self.hour >= 18 or self.hour < 6`
   - `is_tired()` - return `self.tiredness >= 60`
   - `is_exhausted()` - return `self.tiredness >= 80`
   - `is_bad_weather()` - return `self.weather in ("storm", "fog")`
   - `should_rest()` - return `self.is_tired() and not self.in_combat and "rest" in self.commands`

3. **Update `update_state()` for dump_state** (~line 252):
   - Parse `game_time` dict: extract `hour`, derive `time_of_day` and `season` from `total_hours`
   - Parse `weather` dict: extract `condition`
   - Parse `character.tiredness.current`

4. **Write tests** in `tests/test_ai_agent.py`:
   - Add `TestEnvironmentalAwareness` class with all tests listed above
