# Plan: Integration Tests for Coordinate-Based AI World Expansion

## Summary
Add tests for uncovered lines in `GameState.move()`:
- **Lines 254-275**: Coordinate-based AI expansion via `expand_area()`
- **Lines 311-312**: Autosave `IOError` silent failure
- **Line 319**: Quest exploration message appending

## Test File
`tests/test_game_state_ai_integration.py` (extend existing)

## Tests to Add

### 1. `test_move_triggers_coordinate_based_ai_expansion`
Create world with coordinates, mock `expand_area` to add location at target coords, verify move succeeds.

### 2. `test_move_coordinate_expansion_returns_failure_on_error`
Mock `expand_area` to raise `AIServiceError`, verify returns `(False, "Failed to generate destination: ...")`.

### 3. `test_move_coordinate_expansion_fails_when_location_not_created`
Mock `expand_area` to not place location, verify returns `(False, "Failed to generate destination.")`.

### 4. `test_move_autosave_ioerror_silent_failure`
Patch `autosave` to raise `IOError`, verify move still succeeds.

### 5. `test_move_appends_exploration_quest_messages`
Create character with active exploration quest, move to location, verify quest message in output.

## Implementation

```python
# New fixture for coordinate-based world
@pytest.fixture
def coord_world():
    """World with coordinates for testing coordinate-based movement."""
    town = Location(name="Town", description="A town.", coordinates=(0, 0))
    town.connections = {"north": "Placeholder"}  # Exit but no destination
    return {"Town": town}

# Test 1: Coordinate expansion success
@patch("cli_rpg.game_state.expand_area")
def test_move_triggers_coordinate_based_ai_expansion(mock_expand, test_character, coord_world, mock_ai_service):
    def add_location(world, ai_service, from_location, direction, theme, target_coords):
        new_loc = Location(name="Northern Area", description="desc", coordinates=target_coords)
        new_loc.connections = {"south": "Town"}
        world["Northern Area"] = new_loc
    mock_expand.side_effect = add_location

    game = GameState(character=test_character, world=coord_world, starting_location="Town", ai_service=mock_ai_service)
    success, msg = game.move("north")

    assert success is True
    assert game.current_location == "Northern Area"
    mock_expand.assert_called_once()

# Test 2: Expansion failure
@patch("cli_rpg.game_state.expand_area")
def test_move_coordinate_expansion_returns_failure_on_error(mock_expand, ...):
    mock_expand.side_effect = AIServiceError("API failed")
    success, msg = game.move("north")
    assert success is False
    assert "Failed to generate destination" in msg

# Test 3: Expansion succeeds but no location created
@patch("cli_rpg.game_state.expand_area")
def test_move_coordinate_expansion_fails_when_location_not_created(mock_expand, ...):
    mock_expand.return_value = None  # Does nothing
    success, msg = game.move("north")
    assert success is False
    assert msg == "Failed to generate destination."

# Test 4: Autosave IOError
@patch("cli_rpg.game_state.autosave")
def test_move_autosave_ioerror_silent_failure(mock_autosave, ...):
    mock_autosave.side_effect = IOError("Disk full")
    # Create world with existing destination
    success, msg = game.move("north")
    assert success is True  # Move succeeds despite autosave failure

# Test 5: Quest exploration messages
def test_move_appends_exploration_quest_messages(...):
    # Add exploration quest to character
    character.quests.append(quest_with_explore_objective)
    success, msg = game.move("north")
    assert "quest progress" in msg.lower() or objective tracked
```

## Steps
1. Add `coord_world` fixture with coordinates
2. Add 5 tests with appropriate mocking
3. Run `pytest tests/test_game_state_ai_integration.py -v`
4. Verify coverage on lines 254-275, 311-312, 319
