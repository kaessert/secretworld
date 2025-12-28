# Implementation Summary: Reduce MAX_TILES_WITHOUT_ENTERABLE

## What was implemented

Reduced `MAX_TILES_WITHOUT_ENTERABLE` from 25 to 15 in `src/cli_rpg/world_tiles.py` to increase named location density in the game world. This ensures players encounter enterable locations (dungeons, caves, temples, etc.) more frequently during exploration.

## Files Modified

1. **`src/cli_rpg/world_tiles.py`** (line 924)
   - Changed `MAX_TILES_WITHOUT_ENTERABLE = 25` to `MAX_TILES_WITHOUT_ENTERABLE = 15`

2. **`tests/test_enterable_spawn.py`** (lines 26-28, 34)
   - Updated hardcoded test values from 25/24 to 15/14 to match new constant
   - Updated test comments to reflect new expected value

3. **`ISSUES.md`** (line 107)
   - Marked "Reduce Tiles Between Enterables" as DONE

## Test Results

All 31 tests in `test_named_locations_enterable.py` and `test_enterable_spawn.py` pass.

## Gameplay Impact

- Players will now encounter a forced enterable location after at most 15 tiles without one (previously 25)
- This increases dungeon/cave density by ~40%
- Improves exploration pacing by ensuring more frequent interesting locations
