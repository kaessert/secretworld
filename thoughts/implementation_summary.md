# Implementation Summary: Weather Visibility Effects

## What Was Implemented

Weather now affects what players can see when using the `look` command:

### Visibility Levels
- **Full** (clear/rain): No visibility reduction - everything shown normally
- **Reduced** (storm): Description truncated to first sentence, details/secrets layers hidden
- **Obscured** (fog): ~50% of exits hidden (deterministic based on location name), NPC names shown as "???"

### Cave Exception
Cave locations (underground) are unaffected by weather visibility effects - they always have full visibility.

## Files Modified

### 1. `src/cli_rpg/models/weather.py`
- Added `VISIBILITY_LEVELS` constant mapping weather conditions to visibility levels
- Added `get_visibility_level(location_category)` method that:
  - Returns "full" for caves (underground, unaffected)
  - Returns visibility level based on current weather condition

### 2. `src/cli_rpg/models/location.py`
- Added `hashlib` import for deterministic exit filtering
- Updated `get_layered_description(look_count, visibility)` to accept visibility parameter:
  - **Full**: Current behavior (no change)
  - **Reduced**: Truncates description to first sentence, skips details/secrets layers
  - **Obscured**: Filters exits (~50% hidden based on location name hash), shows NPC names as "???"
- Added `_filter_exits_for_fog(directions)` helper method:
  - Uses location name hash for deterministic, consistent results
  - Always keeps at least one exit visible

### 3. `src/cli_rpg/game_state.py`
- Updated `look()` method to:
  - Get visibility level from weather using `get_visibility_level(location.category)`
  - Pass visibility to `get_layered_description(look_count, visibility=visibility)`

### 4. `tests/test_weather.py`
Added 13 new tests in 3 test classes:

**TestWeatherVisibility** (5 tests):
- `test_weather_visibility_level_clear` - returns "full"
- `test_weather_visibility_level_rain` - returns "full"
- `test_weather_visibility_level_storm` - returns "reduced"
- `test_weather_visibility_level_fog` - returns "obscured"
- `test_weather_visibility_level_cave_always_full` - caves return "full" regardless of weather

**TestLocationVisibilityEffects** (5 tests):
- `test_location_reduced_visibility_truncates_description` - storm cuts to first sentence
- `test_location_reduced_visibility_hides_details_secrets` - storm hides layers
- `test_location_obscured_visibility_hides_some_exits` - fog hides some exits (deterministic)
- `test_location_obscured_visibility_obscures_npc_names` - fog shows "???" for NPCs
- `test_location_full_visibility_unchanged` - clear/rain show everything

**TestGameStateLookVisibility** (3 tests):
- `test_look_in_storm_reduces_visibility` - storm affects look output
- `test_look_in_fog_obscures_visibility` - fog affects look output
- `test_look_in_cave_unaffected_by_weather` - caves always full visibility

## Test Results
- All 39 weather tests pass
- All 2068 tests in the full test suite pass

## Technical Details

### Description Truncation (Storm)
Description is truncated to the first sentence by splitting on sentence-ending punctuation (". ", "! ", "? ") and keeping only the first part.

### Exit Filtering (Fog)
Uses MD5 hash of location name to generate a deterministic seed. Each exit has ~50% chance of being hidden based on `(seed + index) % 2`. At least one exit is always visible.

### NPC Obscuring (Fog)
NPC names are replaced with "???" in the NPCs list when visibility is "obscured".

## E2E Validation
To verify manually:
1. Start game and set weather to storm: observe truncated descriptions, no details/secrets on repeated looks
2. Set weather to fog: observe some exits hidden, NPCs shown as "???"
3. Enter a cave location: observe full descriptions regardless of weather
4. Set weather to clear/rain: observe normal behavior
