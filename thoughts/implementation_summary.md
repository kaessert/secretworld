# Weather Interactions Implementation Summary

## What Was Implemented

### Feature: Weather affects combat status effects

Two new weather-combat interactions were implemented:

1. **Rain extinguishes fire**: When weather is "rain" or "storm", Burn status effects on all combatants have a 40% chance to be removed each turn (rain dampens flames).

2. **Cold weather enhances freeze**: When weather is "storm" (cold/harsh), Freeze status effects have their duration extended by 1 turn when applied (cold prolongs freezing).

## Files Modified

### 1. `src/cli_rpg/combat.py`
- Added `Weather` import from `cli_rpg.models.weather`
- Added `weather: Optional[Weather] = None` parameter to `CombatEncounter.__init__`
- Added `_check_rain_extinguish()` method - checks all combatants for Burn effects, 40% chance to remove each in rain/storm
- Added `apply_status_effect_with_weather()` method - applies status effects with weather modifications (storm extends freeze by 1 turn)
- Modified `enemy_turn()` to call `_check_rain_extinguish()` when weather is rain/storm

### 2. `src/cli_rpg/game_state.py`
- Modified `trigger_encounter()` to pass `weather=self.weather` to `CombatEncounter`

### 3. `tests/test_weather_interactions.py` (NEW)
- 15 comprehensive tests covering:
  - Rain can remove burn from player (40% chance)
  - Storm can remove burn from player
  - Clear weather does not remove burn
  - Rain removes burn from enemies
  - Rain extinguish produces flavor messages
  - Rain has exactly 40% threshold (fails at 0.4)
  - Fog does not remove burn
  - Storm extends freeze on enemy (+1 duration)
  - Clear/rain/fog do not extend freeze
  - Storm extends freeze on player too
  - Storm only extends freeze, not other effects
  - Integration tests for enemy turn and backward compatibility

## Test Results

All tests pass:
- `tests/test_weather_interactions.py`: 15 passed
- Related module tests: 151 passed (combat, status_effects, weather, weather_interactions)
- Full test suite: 2083 passed

## Design Decisions

1. **Weather is optional**: `CombatEncounter` accepts `weather=None` for backward compatibility. Combat works normally without weather.

2. **Rain extinguish timing**: Happens at end of enemy turn, after status effect ticks. This means burn still deals damage for the turn before potentially being extinguished.

3. **Freeze extension on apply**: The `apply_status_effect_with_weather()` method modifies freeze duration when applied, not after. This is consistent with the spec "when applied".

4. **40% threshold**: Uses `random.random() < 0.4` so values 0.0-0.39999... succeed, 0.4-1.0 fail.

## E2E Validation

The implementation can be validated by:
1. Starting combat during rain/storm weather
2. Getting a Burn effect applied (e.g., from a fire-type enemy)
3. Observing that burn may be extinguished with "The rain douses your flames!" message
4. Starting combat during storm weather
5. Applying a freeze effect (e.g., via abilities or ice enemy)
6. Observing the freeze has +1 duration compared to normal
