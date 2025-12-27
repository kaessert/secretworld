# Implementation Summary: Map Visibility Radius Integration

## What Was Implemented

Fixed the wiring between the visibility system and the map renderer. The `seen_tiles` set was already being populated during movement, but was not being passed to the map rendering functions.

## Files Modified

### src/cli_rpg/main.py
- **Line 1815**: Added `game_state.seen_tiles` parameter to `render_map()` call in the `map` command
- **Line 1825**: Added `game_state.seen_tiles` parameter to `render_worldmap()` call in the `worldmap` command

### src/cli_rpg/map_renderer.py
- **Lines 439-443**: Added `seen_tiles: Optional[set[tuple[int, int]]] = None` parameter to `render_worldmap()` function signature
- **Line 484**: Passed `seen_tiles=seen_tiles` to the `render_map()` call inside `render_worldmap()`

## Test Results

All 63 tests in the visibility and map renderer test suites pass:
- `tests/test_visibility_radius.py` - 24 tests passed
- `tests/test_map_renderer.py` - 39 tests passed

## How It Works

1. When the player moves, `GameState.update_visibility()` calculates visible tiles based on terrain type and adds them to `seen_tiles`
2. The `map` command now passes `seen_tiles` to `render_map()`, which displays terrain symbols for seen-but-not-visited tiles
3. The `worldmap` command passes `seen_tiles` through `render_worldmap()` to `render_map()` for the same effect on the world map

## E2E Validation

The fix enables the map to show terrain symbols (T for forest, ~ for water, etc.) for tiles the player has seen but not visited. This allows players to:
- See nearby terrain before moving to it
- Plan routes by seeing what terrain types are around them
- Distinguish between unexplored areas (blank) and areas within their visibility radius (terrain symbols)
