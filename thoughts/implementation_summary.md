# Implementation Summary: Sub-locations Visitable from Overworld Fix

## What was Implemented

Fixed a critical bug where the `enter` command failed with "You're not at an overworld location" for AI-generated terrain tiles.

### Root Cause
Two location creation paths didn't set `is_overworld=True`:
1. **Unnamed locations** (game_state.py) - terrain filler tiles
2. **Fallback locations** (world.py) - named POIs when AI unavailable

The `enter()` method in GameState checks `if not current.is_overworld:` and rejected entry from these locations.

### Files Modified

1. **`src/cli_rpg/world.py`** (line 209)
   - Added `is_overworld=True` to the Location constructor in `generate_fallback_location()`

2. **`src/cli_rpg/game_state.py`** (line 574)
   - Added `is_overworld=True` to the Location constructor for unnamed terrain tiles

### Tests Added

Added `TestOverworldFlagOnDynamicLocations` class in `tests/test_enter_entry_point.py`:
- `test_fallback_location_has_is_overworld_true` - Verifies fallback locations have `is_overworld=True`
- `test_enter_command_works_from_dynamically_generated_tile` - Integration test verifying enter command works from dynamically generated terrain

## Test Results

- All 4140 tests pass
- Code coverage: 88.68% (exceeds 80% requirement)
- Related tests verified:
  - `tests/test_enter_entry_point.py` - 11 tests pass
  - `tests/test_game_state.py` - 62 tests pass

## E2E Test Validation

The fix should be validated by:
1. Walking to an unexplored tile that generates an unnamed location
2. Finding a sub-location/dungeon entrance at that tile
3. Using the `enter` command - it should now succeed where it previously failed
