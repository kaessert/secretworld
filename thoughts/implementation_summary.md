# Implementation Summary: Fix for accessing impossible locations

## Bug Fixed
Users could access locations in directions that didn't exist as exits in their current location when using coordinate-based movement.

## Root Cause
In `game_state.py:move()`, coordinate-based movement (lines 213-253) validated that the direction was a valid cardinal direction (north/south/east/west), but did NOT check if that direction existed as an exit in the current location's `connections`. This allowed players to reach any location at calculated coordinates, ignoring the game's intended exit restrictions.

## Changes Made

### 1. Test Added
**File:** `tests/test_game_state.py`
**Test:** `TestGameStateCoordinateBasedMovement::test_move_direction_must_exist_in_exits`

The test creates a scenario where:
- A location at (0,0) has exits: north, south, west (NO east)
- A location at (1,0) exists
- The bug allowed `go east` to succeed because coordinates (1,0) had a location
- The fix ensures the move fails because there's no east exit

### 2. Fix Applied
**File:** `src/cli_rpg/game_state.py`
**Method:** `move()`, lines 214-216

Added exit validation before coordinate calculation:
```python
# Validate that the direction exists as an exit
if not current.has_connection(direction):
    return (False, "You can't go that way.")
```

## Verification
- New test passes: `test_move_direction_must_exist_in_exits`
- All 11 movement tests pass
- Full test suite: 814 passed, 1 skipped

## E2E Validation
To validate in gameplay:
1. Start a new game or load an existing save
2. Find a location with limited exits (e.g., only north, south, west)
3. Try to `go east` - should fail with "You can't go that way."
4. Valid exits should still work normally
