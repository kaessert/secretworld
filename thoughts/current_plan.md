# Fix: User can access impossible locations

## Bug Analysis

**Root Cause**: In `game_state.py:move()`, when using coordinate-based movement (line 213-249), the code validates that the direction is a valid cardinal direction (`north`/`south`/`east`/`west`) but does NOT check if that direction exists as an exit in the current location's connections.

**Current behavior (buggy)**:
1. User at "Shattered Peaks" with exits: north, south, west
2. User types `go east`
3. Code validates "east" is a valid cardinal direction ✓
4. Code calculates target coordinates for east
5. If no location exists at those coords, AI generates one OR "You can't go that way."

**Expected behavior**:
1. User at "Shattered Peaks" with exits: north, south, west
2. User types `go east`
3. Code checks if "east" exists in `current.connections` → NO
4. Return (False, "You can't go that way.") immediately

## Fix Location

**File**: `src/cli_rpg/game_state.py`
**Method**: `move()` (lines 189-293)
**Line to add validation**: After line 212 (after coordinate check but before calculating target coords)

## Implementation

### Step 1: Write failing test

Add to `tests/test_game_state.py` in `TestGameStateCoordinateBasedMovement`:

```python
def test_move_direction_must_exist_in_exits(self, monkeypatch):
    """Movement should fail if direction doesn't exist in location exits.

    Spec: Even with coordinate-based movement, you can only move in directions
    that exist as exits in the current location.
    """
    monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

    character = Character("Hero", strength=10, dexterity=10, intelligence=10)

    # Location at (0,0) with only north, south, west exits - NO EAST
    loc_a = Location("Origin", "Location A", {"north": "North", "south": "South", "west": "West"}, coordinates=(0, 0))
    loc_north = Location("North", "North location", {"south": "Origin"}, coordinates=(0, 1))
    loc_south = Location("South", "South location", {"north": "Origin"}, coordinates=(0, -1))
    loc_west = Location("West", "West location", {"east": "Origin"}, coordinates=(-1, 0))

    world = {"Origin": loc_a, "North": loc_north, "South": loc_south, "West": loc_west}
    game_state = GameState(character, world, "Origin")

    # Moving east should fail - no east exit even though east is a valid direction
    success, message = game_state.move("east")
    assert success is False
    assert "can't go that way" in message.lower()
    assert game_state.current_location == "Origin"  # Should not have moved
```

### Step 2: Fix game_state.py

In `move()` method, add exit validation for coordinate-based movement. After line 212 (`if current.coordinates is not None:`), add:

```python
# Validate that the direction exists as an exit
if not current.has_connection(direction):
    return (False, "You can't go that way.")
```

This goes at approximately line 213, before the coordinate calculation on line 215.

## Verification

1. Run the new test: `pytest tests/test_game_state.py::TestGameStateCoordinateBasedMovement::test_move_direction_must_exist_in_exits -v`
2. Run all movement tests: `pytest tests/test_game_state.py::TestGameStateMove -v`
3. Run full test suite: `pytest`
