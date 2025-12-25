# Implementation Plan: Weather Visibility Effects

## Feature Spec
Weather affects what players can see when looking at locations:
- **Fog**: Hides some exits (50% chance each exit hidden), obscures NPC names with "???"
- **Storm**: Reduces description detail (truncates to first sentence), hides secrets/details layers entirely
- **Rain/Clear**: No visibility effects

Visibility effects apply to `look` command output only. Cave locations (underground) are unaffected by weather.

## Files to Modify
1. `src/cli_rpg/models/weather.py` - Add `VISIBILITY_LEVELS` constant and `get_visibility_level()` method
2. `src/cli_rpg/models/location.py` - Update `get_layered_description()` to accept weather/visibility parameter
3. `src/cli_rpg/game_state.py` - Pass weather to `get_layered_description()` in `look()` method
4. `tests/test_weather.py` - Add visibility effect tests

## Implementation Steps

### 1. Add visibility levels to Weather model (`models/weather.py`)
```python
VISIBILITY_LEVELS = {
    "clear": "full",    # No visibility reduction
    "rain": "full",     # No visibility reduction
    "storm": "reduced", # Truncated descriptions, no details/secrets
    "fog": "obscured",  # Some exits hidden, NPC names obscured
}
```
Add method `get_visibility_level(location_category: Optional[str] = None) -> str` that:
- Returns "full" for caves (underground, unaffected)
- Returns visibility level for effective weather condition

### 2. Update Location.get_layered_description() (`models/location.py`)
Add optional `visibility: str = "full"` parameter:
- `"full"`: Current behavior (no change)
- `"reduced"`: Truncate description to first sentence, skip details/secrets layers
- `"obscured"`: Hide ~50% of exits (seeded by location name for consistency), show NPC names as "???"

### 3. Update GameState.look() (`game_state.py`)
Get visibility level from weather and pass to `get_layered_description()`:
```python
visibility = self.weather.get_visibility_level(location.category)
return location.get_layered_description(look_count, visibility=visibility)
```

### 4. Add tests (`tests/test_weather.py`)

**Test visibility level method:**
- `test_weather_visibility_level_clear` - returns "full"
- `test_weather_visibility_level_rain` - returns "full"
- `test_weather_visibility_level_storm` - returns "reduced"
- `test_weather_visibility_level_fog` - returns "obscured"
- `test_weather_visibility_level_cave_always_full` - caves return "full" regardless of weather

**Test location description effects:**
- `test_location_reduced_visibility_truncates_description` - storm cuts to first sentence
- `test_location_reduced_visibility_hides_details_secrets` - storm hides layers
- `test_location_obscured_visibility_hides_some_exits` - fog hides some exits
- `test_location_obscured_visibility_obscures_npc_names` - fog shows "???" for NPCs
- `test_location_full_visibility_unchanged` - clear/rain show everything

**Test GameState integration:**
- `test_look_in_storm_reduces_visibility` - storm affects look output
- `test_look_in_fog_obscures_visibility` - fog affects look output
- `test_look_in_cave_unaffected_by_weather` - caves always full visibility
