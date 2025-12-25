# Weather Interactions Implementation Plan

## Feature Spec
Weather affects status effects during combat:
- **Rain extinguishes fire**: When weather is "rain" or "storm", Burn status effects on all combatants have a 40% chance to be removed each turn (rain dampens flames)
- **Cold weather enhances freeze**: When weather is "storm" (cold/harsh), Freeze status effects on enemies have their duration extended by 1 turn when applied (cold prolongs freezing)

## Tests (TDD - write first)

### File: `tests/test_weather_interactions.py`

**Rain Extinguishes Burn tests:**
- `test_rain_can_remove_burn_from_player` - Rain has 40% chance to remove Burn each turn
- `test_storm_can_remove_burn_from_player` - Storm also has rain component
- `test_clear_weather_does_not_remove_burn` - Clear weather doesn't affect burn
- `test_rain_removes_burn_from_enemy` - Rain also removes burn from enemies
- `test_rain_extinguish_produces_message` - Extinguishing produces flavor message

**Cold Weather Enhances Freeze tests:**
- `test_storm_extends_freeze_on_enemy` - Storm adds +1 duration to freeze
- `test_clear_weather_no_freeze_extension` - Clear doesn't extend freeze
- `test_rain_no_freeze_extension` - Rain doesn't extend freeze (not cold enough)

## Implementation Steps

### 1. Add `weather` attribute to `CombatEncounter` (combat.py, line ~200)
- Add `weather: Optional[Weather] = None` parameter to `__init__`
- Store as `self.weather = weather`

### 2. Add `_check_rain_extinguish()` method to `CombatEncounter` (combat.py)
```python
def _check_rain_extinguish(self) -> list[str]:
    """Check if rain extinguishes burn effects (40% chance each)."""
    messages = []
    # Check player burns
    for effect in list(self.player.status_effects):
        if effect.name == "Burn" and random.random() < 0.4:
            self.player.status_effects.remove(effect)
            messages.append("The rain douses your flames!")
    # Check enemy burns
    for enemy in self.get_living_enemies():
        for effect in list(enemy.status_effects):
            if effect.name == "Burn" and random.random() < 0.4:
                enemy.status_effects.remove(effect)
                messages.append(f"The rain extinguishes {enemy.name}'s flames!")
    return messages
```

### 3. Call rain extinguish in `enemy_turn()` (combat.py, ~line 700)
After status effect ticks, before returning:
```python
# Weather interactions: rain/storm can extinguish burn
if self.weather and self.weather.condition in ("rain", "storm"):
    messages.extend(self._check_rain_extinguish())
```

### 4. Add `apply_status_effect_with_weather()` method (combat.py)
```python
def apply_status_effect_with_weather(
    self,
    target: Union[Character, Enemy],
    effect: StatusEffect
) -> None:
    """Apply status effect with weather modifications.
    Storm extends Freeze duration by 1 turn.
    """
    if self.weather and self.weather.condition == "storm" and effect.effect_type == "freeze":
        effect.duration += 1
    target.apply_status_effect(effect)
```

### 5. Pass weather to CombatEncounter in GameState (game_state.py, ~line 308)
In `trigger_encounter()`:
```python
self.current_combat = CombatEncounter(
    self.current_character,
    enemies=enemies,
    weather=self.weather
)
```

## File Changes Summary
1. `src/cli_rpg/combat.py`: Add weather param, `_check_rain_extinguish()`, `apply_status_effect_with_weather()`
2. `src/cli_rpg/game_state.py`: Pass weather to CombatEncounter
3. `tests/test_weather_interactions.py`: New test file

## Verification
```bash
pytest tests/test_weather_interactions.py -v
pytest tests/test_combat.py tests/test_status_effects.py tests/test_weather.py -v
pytest  # Full suite
```
