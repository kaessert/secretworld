# Implementation Summary: Map Command SubGrid Integration

## What Was Fixed

Fixed the `map` command in `main.py` to properly pass the `current_sub_grid` parameter to `render_map()`. Previously, the map command ignored the player's SubGrid context, causing it to show "No map available" when inside dungeons/interiors.

## Changes Made

### 1. `src/cli_rpg/main.py` (line 1639)

**Before:**
```python
map_output = render_map(game_state.world, game_state.current_location)
```

**After:**
```python
map_output = render_map(game_state.world, game_state.current_location, game_state.current_sub_grid)
```

### 2. `tests/test_map_command.py`

Added new test `test_map_command_inside_subgrid_shows_interior_map` in `TestMapExplorationCommand` class that:
- Creates a player inside a SubGrid (dungeon interior)
- Calls `handle_exploration_command(game_state, "map", [])`
- Verifies the output contains "INTERIOR MAP" header and the parent location name

## Test Results

All 48 map-related tests pass:
- `tests/test_map_command.py` - 9 tests
- `tests/test_map_renderer.py` - 39 tests

## Technical Details

- The `render_map()` function already had full SubGrid support via `_render_sub_grid_map()`
- The fix simply passes the existing `game_state.current_sub_grid` attribute
- When `current_sub_grid` is `None` (overworld), behavior is unchanged
- When inside a SubGrid, the interior map shows bounded grid, exit points, and parent context

## E2E Validation

To validate manually:
1. Start the game
2. Enter any dungeon/building interior (e.g., `enter <interior>`)
3. Type `map` command
4. Should see "INTERIOR MAP" header with bounded grid view
