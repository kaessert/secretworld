# Implementation Summary: Fix "Can't go that way" despite map showing exits (Bug #5)

## What Was Implemented

Fixed a bug where exits were displayed to the player (in `look` command, map, etc.) but movement was blocked by WFC terrain passability checks, resulting in confusing "Can't go that way" messages.

### Root Cause

The bug occurred when:
1. Exit display was based on the `connections` dict in Location
2. Movement checked WFC terrain passability AFTER connection checks
3. Result: Exit shown (connection exists) → Movement fails (terrain impassable)

### Solution

Filter displayed exits by WFC terrain passability at display time, preventing the display of exits that cannot be traversed.

## Files Modified

### `src/cli_rpg/models/location.py`
- Added `ChunkManager` type hint import
- Added `get_filtered_directions(chunk_manager)` method that filters out directions where WFC terrain is impassable
- Updated `get_layered_description()` to accept optional `chunk_manager` parameter and use filtered directions

### `src/cli_rpg/game_state.py`
- Updated `look()` method to pass `self.chunk_manager` to `get_layered_description()`
- Updated `generate_fallback_location()` call in `move()` to pass `self.chunk_manager`

### `src/cli_rpg/map_renderer.py`
- Added `ChunkManager` type hint import
- Updated `render_map()` to accept optional `chunk_manager` parameter
- Changed exits display to use `get_filtered_directions(chunk_manager)` instead of `get_available_directions()`

### `src/cli_rpg/world.py`
- Added `ChunkManager` type hint import
- Updated `generate_fallback_location()` to accept optional `chunk_manager` parameter
- Added WFC terrain passability check before adding dangling exits to new locations

### `src/cli_rpg/main.py`
- Updated `map` command to pass `game_state.chunk_manager` to `render_map()`

### `tests/test_wfc_exit_display.py` (NEW)
- Added 8 new tests covering:
  - Location exit filtering by WFC terrain
  - Layered description filtering
  - Map renderer filtering
  - Fallback location generation
  - Integration test verifying displayed exits are traversable

## Test Results

- All 8 new tests pass
- All 3486 existing tests pass (no regressions)

## E2E Validation

To validate the fix works end-to-end:
1. Start game with WFC terrain enabled (default)
2. Navigate to a location adjacent to water
3. Run `look` command - exits should NOT include directions blocked by water
4. Run `map` command - exits list should match what `look` shows
5. Try `go <blocked_direction>` on a previously-shown exit - should succeed (not show "Can't go that way")

## Technical Details

- The filtering uses `TERRAIN_PASSABLE` dict from `world_tiles.py` to determine passability
- Direction offsets: north=(0,1), south=(0,-1), east=(1,0), west=(-1,0)
- Backward compatible: when `chunk_manager` is None, all directions are returned
- Legacy locations (no coordinates) skip filtering for compatibility
