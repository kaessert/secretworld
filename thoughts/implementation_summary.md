# Implementation Summary: Natural Terrain Transitions

## What Was Implemented

Added a "biome distance penalty" system to WFC generation that penalizes placing incompatible terrain types (like desert near forest) within 2 tiles of each other. This creates wider transition zones instead of single-tile buffers.

### Files Modified

1. **`src/cli_rpg/world_tiles.py`**
   - Added `BIOME_GROUPS` constant mapping terrain types to biome categories:
     - temperate: forest, swamp
     - arid: desert
     - aquatic: water, beach
     - alpine: mountain, foothills
     - neutral: plains, hills (bridge all biomes)
   - Added `INCOMPATIBLE_GROUPS` set defining which groups conflict (temperate ↔ arid)
   - Added `get_distance_penalty(terrain, nearby_terrains)` function that returns 0.01 (99% weight reduction) for incompatible biomes nearby, 1.0 otherwise

2. **`src/cli_rpg/wfc_chunks.py`**
   - Added `_get_nearby_collapsed_tiles(grid, x, y, radius=2)` helper method to find terrain types of collapsed cells within radius
   - Modified `_collapse_cell()` signature to accept optional `grid` parameter
   - Updated `_collapse_cell()` to apply distance penalties when grid is provided
   - Updated call site in `_try_generate_with_constraints()` to pass grid

3. **`src/cli_rpg/wfc.py`**
   - Added same `_get_nearby_collapsed_tiles()` helper method
   - Modified `_collapse_cell()` signature to accept optional `grid` parameter
   - Updated `_collapse_cell()` to apply distance penalties
   - Updated call site in `_try_generate_chunk()` to pass grid

4. **`tests/test_terrain_transitions.py`** (new file)
   - 10 tests covering:
     - BIOME_GROUPS definition completeness
     - INCOMPATIBLE_GROUPS symmetry
     - Distance penalty calculations for neutral, same-group, and incompatible terrain
     - `_get_nearby_collapsed_tiles()` helper behavior
     - Statistical tests for forest-desert and swamp-desert minimum separation

## Test Results

All 10 new tests pass, and the full test suite (4102 tests) passes.

## Technical Details

### Penalty Mechanism
- When collapsing a WFC cell, nearby collapsed tiles within radius 2 are collected
- For each tile option being considered, a weight multiplier is calculated:
  - 1.0 (no change) for neutral terrain or same biome group
  - 0.01 (99% reduction) for incompatible biome groups
- This makes incompatible terrain 100x less likely to be selected near conflicting biomes

### Limitations
- The penalty is applied during collapse, so tiles collapsed *before* their incompatible neighbors exist won't receive the penalty
- Statistical tests show ~30-35% of cases still have close transitions due to collapse order
- This is acceptable as the goal is to reduce jarring transitions, not eliminate all edge cases

## E2E Validation
- Generate a few worlds with different seeds and visually inspect terrain
- Look for smoother transitions between forest/swamp areas and desert areas
- Verify that neutral terrain (plains, hills) still bridges biomes naturally
