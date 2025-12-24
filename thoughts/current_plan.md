# Implementation Plan: Map Command

## Spec
Add a `map` command that displays an ASCII map of explored locations using the existing coordinate system. The map should:
- Show explored locations using their coordinates from `world.items()`
- Mark the player's current location distinctly
- Use simple ASCII characters for rendering
- Handle locations without coordinates gracefully (legacy saves)

## Tests (in `tests/test_map_command.py`)

1. **test_parse_command_map**: Verify `parse_command("map")` returns `("map", [])`
2. **test_map_command_returns_ascii_output**: Map command returns string with visual representation
3. **test_map_shows_current_location_marker**: Current location marked with `@` or `[X]`
4. **test_map_shows_explored_locations**: All locations in world appear on map
5. **test_map_command_during_combat_blocked**: Map not available during combat
6. **test_map_with_no_coordinates_shows_message**: Graceful handling of legacy saves

## Implementation Steps

1. **Add "map" to known commands** in `game_state.py`:
   - Add `"map"` to the `known_commands` set in `parse_command()` (line 48)

2. **Create map rendering function** in new file `src/cli_rpg/map_renderer.py`:
   ```python
   def render_map(world: dict[str, Location], current_location: str) -> str
   ```
   - Extract all locations with coordinates
   - Calculate bounds (min/max x,y)
   - Render grid with location markers and current position indicator
   - Return ASCII string

3. **Add map command handler** in `main.py`:
   - Add `elif command == "map":` case in `handle_exploration_command()` (after line ~408)
   - Call `render_map(game_state.world, game_state.current_location)`
   - Return the rendered map string

4. **Update help text** in `main.py`:
   - Add `"  map            - Display a map of explored areas"` to command lists (~lines 529 and 634)
   - Add `'map'` to unknown command error message (~lines 434 and 437)

## Map Display Format
```
=== MAP ===
   -1  0  1
 1     F
 0     @  C
-1
Legend: @ = You (Town Square), F = Forest, C = Cave
```
- Use first letter of location name as marker
- `@` or `[*]` indicates current position
- Show coordinate axes
