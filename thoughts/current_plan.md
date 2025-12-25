# Fix Connection System Bug: Block Movement Without Exits

## Spec
Movement in coordinate-based mode should respect the `connections` dict - players can only move in directions where an exit exists. Currently, the code generates a new location in ANY direction, ignoring whether a connection exists.

**Expected behavior:** `go south` from a location with only `{"north": "Forest"}` should return "You can't go that way."

## Test Plan

Add test in `tests/test_game_state.py` under `TestGameStateCoordinateBasedMovement`:

```python
def test_move_blocked_when_no_connection_coordinate_mode(self, tmp_path, monkeypatch):
    """Movement fails when no connection exists in coordinate-based mode.

    Spec: Moving in a direction without a connection should fail with
    "You can't go that way" even when the location has coordinates.
    """
    monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

    character = Character("Hero", strength=10, dexterity=10, intelligence=10)
    # Location WITH coordinates but only north connection
    loc = Location("Town", "A town", connections={"north": "Forest"}, coordinates=(0, 0))
    world = {"Town": loc}
    game_state = GameState(character, world, "Town")

    # Try to go south - no connection exists
    success, msg = game_state.move("south")

    assert success is False
    assert "can't go that way" in msg.lower()
    assert game_state.current_location == "Town"
    # World should NOT have a new location generated
    assert len(game_state.world) == 1
```

## Implementation

**File:** `src/cli_rpg/game_state.py`

**Location:** Line ~297, immediately after line 295 (direction validation) and before line 298 (coordinate check)

**Change:** Add connection check before ANY coordinate-based movement or generation:

```python
        # Check if direction is valid (north, south, east, west)
        valid_game_directions = {"north", "south", "east", "west"}
        if direction not in valid_game_directions:
            return (False, "Invalid direction. Use: north, south, east, or west.")

        # NEW: Block movement if no connection exists in that direction
        if not current.has_connection(direction):
            return (False, "You can't go that way.")

        # Use coordinate-based movement if current location has coordinates
        if current.coordinates is not None:
            ...
```

This single check at line ~297 handles both:
1. Coordinate-based movement (blocks generation of new locations without exits)
2. Legacy movement (existing check at line 360 becomes redundant but harmless)

## Verification
1. Run new test: `pytest tests/test_game_state.py::TestGameStateCoordinateBasedMovement::test_move_blocked_when_no_connection_coordinate_mode -v`
2. Run full test suite: `pytest`
