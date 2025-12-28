# Weather Penetration: Rain Sounds Near Cave Entrance

## Summary
Add weather-aware ambient sounds near SubGrid entrance rooms (exit_points). When it's raining or storming outside, players hear muffled weather sounds near the entrance.

## Spec
- When inside a SubGrid at z=0 and at or adjacent to an `is_exit_point` room, check overworld weather
- If weather is `rain` or `storm`, trigger weather penetration sounds instead of/in addition to normal ambient sounds
- Sound intensity decreases with distance from exit (exit room = 30% chance, 1 room away = 15%, 2+ rooms = 0%)
- Does not apply to deep underground (z < 0)

## Files to Modify

### 1. `src/cli_rpg/ambient_sounds.py`
- Add `WEATHER_PENETRATION_SOUNDS` dict with rain/storm sound pools
- Add `get_weather_penetration_sound(weather_condition: str, distance_from_exit: int) -> Optional[str]`
- Modify `AmbientSoundService.get_ambient_sound()` to accept optional `weather_condition` and `distance_from_exit` params

### 2. `src/cli_rpg/world_grid.py`
- Add `get_distance_to_nearest_exit(coords: tuple) -> int` method to SubGrid using BFS

### 3. `src/cli_rpg/game_state.py`
- In `_move_in_sub_grid()`, calculate distance from nearest exit_point
- Pass weather condition and exit distance to `ambient_sound_service.get_ambient_sound()`

## Tests (`tests/test_weather_penetration.py`)
1. `test_rain_sound_at_exit_point` - Rain sounds trigger at exit rooms
2. `test_storm_sound_at_exit_point` - Storm sounds trigger at exit rooms
3. `test_muffled_sound_one_room_away` - Lower chance 1 room from exit
4. `test_no_weather_sound_deep_inside` - No weather sounds 2+ rooms from exit
5. `test_no_weather_sound_underground` - No weather sounds at z < 0
6. `test_no_weather_sound_clear_weather` - No penetration in clear weather
7. `test_distance_calculation` - SubGrid exit distance calculation works

## Implementation Order
1. Add `get_distance_to_nearest_exit()` to SubGrid
2. Add weather penetration sounds to `ambient_sounds.py`
3. Integrate in `game_state.py` movement
4. Write tests
5. Update ISSUES.md to mark acceptance criteria complete
