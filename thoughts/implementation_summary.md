# Implementation Summary: Weather Penetration Sounds

## What Was Implemented

Added weather-aware ambient sounds near SubGrid entrance rooms. When it's raining or storming outside, players hear muffled weather sounds near the entrance at z=0 level.

### Files Modified

1. **`src/cli_rpg/world_grid.py`**
   - Added `SubGrid.get_distance_to_nearest_exit(coords)` method
   - Calculates Manhattan distance from any (x, y, z) coordinate to the nearest `is_exit_point=True` location
   - Returns -1 if no exit points exist

2. **`src/cli_rpg/ambient_sounds.py`**
   - Added `WEATHER_PENETRATION_SOUNDS` dict with rain and storm sound pools (5-6 sounds each)
   - Added `get_weather_penetration_sound(weather_condition, distance_from_exit)` function
   - Updated `AmbientSoundService.get_ambient_sound()` to accept optional `weather_condition` and `distance_from_exit` parameters
   - Weather penetration bypasses normal ambient sound roll but respects cooldown

3. **`src/cli_rpg/game_state.py`**
   - Updated `_move_in_sub_grid()` to calculate distance from nearest exit
   - Only calculates distance at z=0 level (ground floor)
   - Passes weather condition and exit distance to ambient sound service

### Feature Behavior

- **At exit room (distance=0):** 30% chance of weather penetration sound
- **1 room away (distance=1):** 15% chance of weather penetration sound
- **2+ rooms away:** No weather sounds
- **Underground (z < 0):** No weather sounds (too deep)
- **Clear/Fog weather:** No penetration sounds (rain/storm only)

### New Tests

Created `tests/test_weather_penetration.py` with 16 tests:
- `TestWeatherPenetrationSounds`: 7 tests for sound pools and probability mechanics
- `TestSubGridExitDistance`: 6 tests for distance calculation
- `TestAmbientSoundServiceWeatherIntegration`: 3 tests for service integration

## Test Results

All tests pass:
- 16 new weather penetration tests
- 5592 total tests in the test suite (all passing)

## E2E Validation

The feature should be validated by:
1. Entering a dungeon/cave with rain/storm weather
2. Moving around rooms at z=0 level
3. Verifying weather sounds appear near the exit and fade as you go deeper
4. Verifying no weather sounds appear underground (z < 0)
