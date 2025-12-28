# Implementation Summary: AgentState Environmental Fields

## What Was Implemented

Added environmental awareness fields and helper methods to `AgentState` in `scripts/state_parser.py`:

### New Fields (lines 87-91)
- `time_of_day: str = "day"` - "day" or "night" derived from hour
- `hour: int = 6` - Current hour 0-23
- `season: str = "spring"` - "spring", "summer", "autumn", "winter"
- `weather: str = "clear"` - "clear", "rain", "storm", "fog"
- `tiredness: int = 0` - Current tiredness level 0-100

### New Helper Methods (lines 178-218)
- `is_night() -> bool` - True if hour 18-23 or 0-5 (night hours)
- `is_tired() -> bool` - True if tiredness >= 60 (should consider rest)
- `is_exhausted() -> bool` - True if tiredness >= 80 (attack/perception penalty)
- `is_bad_weather() -> bool` - True if weather is "storm" or "fog"
- `should_rest() -> bool` - Composite: is_tired() AND not in_combat AND "rest" in commands

### Parsing Logic in update_state() (lines 319-362)
- Parses `character.tiredness.current` for tiredness value
- Parses `game_time.hour` and `game_time.total_hours` to derive:
  - `hour` (direct from JSON)
  - `time_of_day` ("night" for 18-5, "day" for 6-17)
  - `season` (spring days 1-30, summer 31-60, autumn 61-90, winter 91-120)
- Parses `weather.condition` for weather value

## Files Modified
- `scripts/state_parser.py` - Added fields, methods, and parsing logic
- `tests/test_ai_agent.py` - Added `TestEnvironmentalAwareness` class with 12 tests

## Test Results
All 43 tests in test_ai_agent.py pass, including:
- 12 new environmental awareness tests covering:
  - Field parsing from dump_state (game_time, weather, tiredness)
  - Helper method thresholds (is_night, is_tired, is_exhausted)
  - Weather condition checks (is_bad_weather)
  - Composite rest check (should_rest)
  - Season derivation from total_hours

## Design Decisions
1. Season derivation mirrors `GameTime.get_season()` logic exactly (120-day year, 30 days per season)
2. Night hours match `GameTime.is_night()` (18-5 inclusive)
3. Tiredness thresholds (60/80) align with game's Tiredness model penalties
4. Weather check focuses on storm/fog as "bad" since these affect visibility and dread

## E2E Validation
The agent can now use these fields to make smarter decisions:
- `is_night()` - Be cautious of undead (+50% spawn rate at night)
- `is_tired()` / `is_exhausted()` - Prioritize rest to avoid penalties
- `is_bad_weather()` - Account for visibility issues and extra dread
- `should_rest()` - Composite check for safe rest opportunities
