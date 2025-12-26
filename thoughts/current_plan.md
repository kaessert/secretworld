# BLOCKER #2: Fix `trigger_encounter()` Safe Zone Bypass

## Spec
`trigger_encounter()` must return `None` immediately when the location has `is_safe_zone=True`, preventing combat in safe zones like Town Square's Market District.

## Test (add to `tests/test_game_state_combat.py`)

```python
def test_trigger_encounter_respects_safe_zone(self):
    """Spec: trigger_encounter() returns None for safe zone locations."""
    character = Character(
        name="Hero",
        strength=10,
        dexterity=10,
        intelligence=10
    )
    world = {
        "Market District": Location(
            name="Market District",
            description="A busy market",
            connections={},
            is_safe_zone=True
        )
    }
    game_state = GameState(character, world, starting_location="Market District")

    # Even with forced random (mocked to always trigger), should return None
    from unittest.mock import patch
    with patch("cli_rpg.game_state.random.random", return_value=0.1):  # < 0.3 would trigger
        result = game_state.trigger_encounter("Market District")

    assert result is None
    assert game_state.current_combat is None
```

## Implementation (`src/cli_rpg/game_state.py`, line ~308)

Add safe zone check at start of `trigger_encounter()`:

```python
def trigger_encounter(self, location_name: str) -> Optional[str]:
    # Check if location is a safe zone
    location = self.world.get(location_name)
    if location and location.is_safe_zone:
        return None

    # 30% chance of encounter (existing code continues...)
```

## Files to Modify
1. `tests/test_game_state_combat.py` - Add `test_trigger_encounter_respects_safe_zone` to `TestTriggerEncounter` class
2. `src/cli_rpg/game_state.py` - Add safe zone check at line ~308 (before random check)
