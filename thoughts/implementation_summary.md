# Map Visibility Radius Implementation Summary

## What Was Implemented

The map visibility radius feature transforms the map from "visited tiles only" mode to "visibility radius" mode. Players now see nearby terrain within a configurable radius based on terrain type and Perception stat.

### Features Implemented

1. **Visibility Radius by Terrain Type** (`world_tiles.py`)
   - Plains: 3 tiles (open terrain, far view)
   - Hills/Beach/Desert/Water: 2 tiles (moderate obstacles)
   - Forest/Swamp/Foothills: 1 tile (blocked view)
   - Mountain: 0 tiles (only current tile visible - peaks block everything)

2. **Mountain Standing Bonus**
   - Standing ON a mountain grants +2 visibility bonus
   - Allows players to scout from high ground (0 base + 2 bonus = 2 total)

3. **Perception Stat Bonus**
   - +1 visibility radius per 5 PER above 10
   - Example: PER 15 = +1, PER 20 = +2

4. **Tile Visibility Tracking** (`game_state.py`)
   - `seen_tiles: set[tuple[int, int]]` - Tracks all tiles within visibility radius
   - `calculate_visibility_radius()` - Calculates total radius from terrain + bonuses
   - `update_visibility()` - Called after movement to update seen tiles
   - Visibility accumulates as player moves around

5. **Map Rendering Update** (`map_renderer.py`)
   - Added `seen_tiles` parameter to `render_map()`
   - Seen-but-not-visited tiles show terrain symbol (T, ., n, etc.)
   - Visited tiles show full location details
   - Unseen tiles remain empty

6. **Persistence** (`game_state.py`)
   - `seen_tiles` serialized in `to_dict()` as list of coordinate tuples
   - Restored in `from_dict()` with backward compatibility (empty set for old saves)

### Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Added `VISIBILITY_RADIUS` dict, `MOUNTAIN_VISIBILITY_BONUS`, `get_visibility_radius()` |
| `src/cli_rpg/world_grid.py` | Added `get_tiles_in_radius()` helper function |
| `src/cli_rpg/game_state.py` | Added `seen_tiles`, `calculate_visibility_radius()`, `update_visibility()`, persistence |
| `src/cli_rpg/map_renderer.py` | Added `seen_tiles` parameter, display terrain for seen-not-visited tiles |
| `tests/test_visibility_radius.py` | NEW - 24 comprehensive tests |

## Test Results

All 24 visibility radius tests pass:
- 3 tests for `get_tiles_in_radius()` (radius 0, 1, 2)
- 10 tests for visibility radius by terrain type
- 1 test for mountain standing bonus constant
- 1 test for mountain visibility calculation
- 4 tests for Perception stat bonus
- 2 tests for `update_visibility()` (marking tiles, accumulation)
- 1 test for save/load persistence
- 2 tests for map display (seen terrain shown, unseen hidden)

Full test suite: 4242 passed, 2 unrelated failures in `test_ai_agent.py` (pre-existing bug in state_parser.py)

## E2E Validation

To validate the feature:
1. Start the game and note the map shows only the current location
2. Move in any direction - nearby tiles within visibility radius should appear
3. Test from different terrains (plains vs forest vs mountain)
4. Test with high PER character to see extended visibility
5. Climb to a mountain tile - should have enhanced visibility
6. Save and load - seen tiles should persist
