# Implementation Summary: Connection System Bug Fix

## Task
Fix the connection system bug where movement in coordinate-based mode was ignoring the `connections` dict, allowing players to move in any direction even without an exit.

## Changes Made

### Already Implemented
The fix was already in place in `src/cli_rpg/game_state.py` at lines 297-299:

```python
# Block movement if no connection exists in that direction
if not current.has_connection(direction):
    return (False, "You can't go that way.")
```

This check occurs immediately after validating the direction (north/south/east/west) and BEFORE any coordinate-based movement or new location generation. This ensures:
1. Players cannot move in directions without exits
2. New locations are NOT generated when no exit exists
3. The check works for both coordinate-based and legacy connection-based movement

### Test Added
A test `test_move_blocked_when_no_connection_coordinate_mode` already exists in `tests/test_game_state.py` under `TestGameStateCoordinateBasedMovement` class (lines 648-669) that verifies:
- Moving in a direction without a connection fails
- Error message contains "can't go that way"
- Player location remains unchanged
- No new locations are generated in the world

## Verification

### Test Results
- Specific test: PASSED
- Full test suite: 1709 tests passed in 32.77s

### Expected Behavior
From a location with only `{"north": "Forest"}`:
- `go north` → Success, moves to Forest
- `go south` → Failure, "You can't go that way."
- `go east` → Failure, "You can't go that way."
- `go west` → Failure, "You can't go that way."

## Technical Notes
The fix is strategically placed to handle both:
1. **Coordinate-based movement**: Prevents generation of new locations at target coordinates when no exit exists
2. **Legacy movement**: The existing check at line 364 becomes redundant but harmless (defense in depth)
