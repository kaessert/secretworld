# Implementation Summary: Fix Circular Map Wrapping

## What Was Implemented

### Problem Fixed
The world grid was allowing circular wrapping when players moved repeatedly in one direction. This happened because movement followed `Location.connections` without checking if the destination's coordinates matched the expected target coordinates.

### Solution
Changed movement from connection-based to coordinate-based logic:
- **Before**: Follow `location.connections[direction]` to find destination
- **After**: Calculate target coordinates, find/generate location at those coordinates

### Files Modified

1. **`src/cli_rpg/game_state.py`**
   - Added `_get_location_by_coordinates(coords)` helper method to find a location by its (x, y) coordinates
   - Rewrote `move()` method to use coordinate-based logic:
     - For locations with coordinates: calculate target coords and look up location at those coords
     - For legacy locations (no coordinates): fall back to connection-based movement
     - AI generation now passes `target_coords` to ensure correct placement

2. **`src/cli_rpg/ai_world.py`**
   - Updated `expand_world()` to accept optional `target_coords` parameter
   - When `target_coords` is provided, the new location is placed at those exact coordinates
   - Maintains backward compatibility when `target_coords` is not provided

### Tests Added

1. **`tests/test_world_grid.py`** - `TestWorldGridNoWrapping` class:
   - `test_repeated_direction_extends_world`: Verifies that going west repeatedly from a chain of locations returns `None` for unexplored coordinates (no wrap-around)
   - `test_coordinates_are_consistent_after_movement`: Verifies bidirectional movement returns to correct coordinates

2. **`tests/test_game_state.py`** - `TestGameStateCoordinateBasedMovement` class:
   - `test_move_uses_coordinates_not_just_connections`: Verifies movement ignores misleading connections that would cause circular wrapping
   - `test_move_with_coordinates_goes_to_correct_location`: Verifies proper coordinate-based navigation
   - `test_move_falls_back_to_connection_for_legacy_locations`: Verifies backward compatibility with saves that don't have coordinates

## Test Results

All 773 tests pass (1 skipped - unrelated).

```
tests/test_game_state.py::TestGameStateCoordinateBasedMovement::test_move_uses_coordinates_not_just_connections PASSED
tests/test_game_state.py::TestGameStateCoordinateBasedMovement::test_move_with_coordinates_goes_to_correct_location PASSED
tests/test_game_state.py::TestGameStateCoordinateBasedMovement::test_move_falls_back_to_connection_for_legacy_locations PASSED
tests/test_world_grid.py::TestWorldGridNoWrapping::test_repeated_direction_extends_world PASSED
tests/test_world_grid.py::TestWorldGridNoWrapping::test_coordinates_are_consistent_after_movement PASSED
```

## Design Decisions

1. **Backward Compatibility**: Legacy saves without coordinates continue to work using connection-based movement. This ensures existing save files don't break.

2. **Coordinate Priority**: When a location has coordinates, the system uses coordinate-based logic exclusively, ignoring any potentially incorrect connection values. This guarantees spatial consistency.

3. **AI Generation Integration**: The `expand_world()` function now accepts explicit `target_coords` so that newly generated locations are placed at the correct position in the grid, not based on potentially stale connection information.

## E2E Validation

To fully validate this fix in a real game scenario:
1. Start a new game with AI-generated world
2. Travel west multiple times (west -> west -> west -> west)
3. Verify that each movement goes to a new location with decreasing x-coordinates
4. Verify that traveling east returns through the same locations in reverse order
5. Confirm no circular wrapping occurs regardless of what connection values the AI generates
