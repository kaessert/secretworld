# Fix Invalid Direction Error Message (Issue #1)

## Spec
Distinguish between two error cases in `GameState.move()`:
1. **Invalid direction**: User enters non-supported direction (e.g., `up`, `northwest`) → "Invalid direction. Use: north, south, east, or west."
2. **No exit**: User enters valid direction with no connection (e.g., `south` when no southern exit) → "You can't go that way."

## Implementation

### 1. Add test for invalid direction message
**File**: `tests/test_game_state.py`

Add new test after `test_move_nonexistent_direction_failure`:
```python
def test_move_unsupported_direction_shows_invalid_message(self):
    """Test that unsupported directions show a different error than blocked exits.

    Spec: 'up', 'northwest', etc. should say "Invalid direction" not "You can't go that way."
    """
    character = Character("Hero", strength=10, dexterity=10, intelligence=10)
    world = {
        "Start": Location("Start", "Start location", {"north": "End"}),
        "End": Location("End", "End location")
    }

    game_state = GameState(character, world, "Start")

    # Test unsupported directions
    for invalid_dir in ["up", "northwest", "left", "forward", "xyz"]:
        success, message = game_state.move(invalid_dir)
        assert success is False
        assert "Invalid direction" in message, f"Expected 'Invalid direction' for '{invalid_dir}', got: {message}"

    # Verify blocked exit still shows original message
    success, message = game_state.move("south")  # valid direction, no exit
    assert success is False
    assert "can't go that way" in message.lower()
```

### 2. Update `GameState.move()` method
**File**: `src/cli_rpg/game_state.py`, line ~178-182

Add validation check before `has_connection`:
```python
def move(self, direction: str) -> tuple[bool, str]:
    ...
    current = self.get_current_location()

    # Check if direction is valid (north, south, east, west)
    valid_game_directions = {"north", "south", "east", "west"}
    if direction not in valid_game_directions:
        return (False, "Invalid direction. Use: north, south, east, or west.")

    # Check if direction exists (valid direction but no exit)
    if not current.has_connection(direction):
        return (False, "You can't go that way.")
    ...
```

### 3. Run tests
```bash
pytest tests/test_game_state.py -v -k "move"
pytest  # Full suite to ensure no regressions
```

## Notes
- `Location.VALID_DIRECTIONS` includes `up` and `down` for model flexibility, but the game's movement system only supports cardinal directions (north, south, east, west)
- The new validation goes before `has_connection()` to catch invalid directions first
