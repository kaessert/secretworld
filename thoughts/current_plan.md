# Plan: Player-Centered Map Display (5x5 Grid)

## Spec
Modify `render_map()` to display a 5x5 grid centered on the player's current location (2 tiles in each direction), rather than calculating bounds from all explored locations.

**Current behavior:** Map shows all locations based on min/max coordinates of explored world
**New behavior:** Map shows a fixed 5x5 area centered on player, with player always at center (offset 0,0 in viewport)

## Tests to Add (`tests/test_map_renderer.py` - new file)

1. **test_map_centered_on_player** - Verify player position is always at grid center regardless of absolute coordinates
2. **test_map_shows_5x5_viewport** - Verify exactly 5 columns (-2 to +2) and 5 rows (-2 to +2) are displayed
3. **test_map_clips_locations_outside_viewport** - Verify locations >2 tiles away are not shown on map (but may appear in legend if explored)
4. **test_map_handles_player_at_origin** - Player at (0,0) shows grid from (-2,-2) to (2,2)
5. **test_map_handles_player_at_large_coordinates** - Player at (100,50) shows grid from (98,48) to (102,52)

## Implementation Steps

### 1. Create test file `tests/test_map_renderer.py`
Add the 5 tests above using existing `Location` model pattern from `test_map_command.py`.

### 2. Modify `src/cli_rpg/map_renderer.py`

**Changes to `render_map()` function:**

1. Get current location's coordinates (handle None case - return early message)
2. Replace bounds calculation (lines 28-31) with fixed viewport:
   ```python
   player_x, player_y = current_loc.coordinates
   min_x, max_x = player_x - 2, player_x + 2
   min_y, max_y = player_y - 2, player_y + 2
   ```
3. Keep rest of rendering logic unchanged - it already iterates over the bounds correctly
4. Legend should only show locations visible in viewport (filter `locations_with_coords` to viewport bounds)

### 3. Run tests
```bash
pytest tests/test_map_renderer.py -v
pytest tests/test_map_command.py -v
```

Verify all new tests pass and existing map command tests still pass.
