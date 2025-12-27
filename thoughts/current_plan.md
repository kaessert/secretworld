# Implementation Plan: Terrain-Biased WFC

## Objective
Make WFC chunk generation respect region themes so terrain generates coherent mega-biomes (e.g., mountain regions bias toward mountain/foothills/hills) instead of "random terrain salad."

## Spec

**Current behavior**: WFC generates terrain using static weights from `TERRAIN_WEIGHTS` in `world_tiles.py` regardless of region context.

**Target behavior**: When generating a chunk, WFC should apply terrain biases based on the region's theme/terrain_hint. A "mountains" region should have 3-4x weight for mountain/foothills/hills tiles and reduced weights for incompatible terrain like beach/swamp.

**Terrain bias mapping** (region theme → terrain weight multipliers):
| Region Theme | Boosted Terrain (3x) | Normal (1x) | Reduced (0.3x) |
|-------------|---------------------|-------------|----------------|
| mountains | mountain, foothills, hills | plains, forest | beach, swamp, desert |
| forest | forest | plains, hills, swamp | mountain, desert, beach |
| swamp | swamp, forest, water | plains | mountain, desert, beach |
| desert | desert, plains | hills, beach | forest, swamp, mountain |
| coastal/beach | beach, water, plains | forest | mountain, swamp, desert |
| plains/wilderness | plains, forest, hills | (all others) | - |

## Tests (write first)

### File: `tests/test_terrain_biased_wfc.py`

1. **test_get_biased_weights_returns_modified_weights** - `get_biased_weights("mountains")` returns dict with mountain/foothills/hills at 3x base weight
2. **test_get_biased_weights_unknown_theme_returns_base** - Unknown theme returns unmodified base weights
3. **test_wfc_generator_accepts_tile_weight_overrides** - WFCGenerator can accept custom weights that override registry defaults
4. **test_chunk_manager_passes_bias_to_generator** - ChunkManager passes region bias when generating new chunks
5. **test_mountain_region_generates_more_mountains** - Statistical test: chunk in "mountains" region has >40% mountain-family tiles (vs ~15% baseline)
6. **test_forest_region_generates_more_forest** - Statistical test: chunk in "forest" region has >50% forest tiles (vs ~20% baseline)
7. **test_bias_respects_adjacency_rules** - Biased generation still produces valid terrain (all tiles have valid neighbors)

## Implementation Steps

### Step 1: Add terrain bias configuration to `world_tiles.py`
- Add `REGION_TERRAIN_BIASES: Dict[str, Dict[str, float]]` mapping region themes to terrain weight multipliers
- Add `get_biased_weights(region_theme: str) -> Dict[str, float]` function that applies multipliers to `TERRAIN_WEIGHTS`

### Step 2: Modify `WFCGenerator` to accept weight overrides
- Add optional `weight_overrides: Optional[Dict[str, float]] = None` parameter to `__init__`
- In `_collapse_cell()`, use overrides when available instead of registry weights

### Step 3: Modify `ChunkManager` to use region context
- Add optional `region_context: Optional[RegionContext] = None` field
- Add `set_region_context(region: RegionContext)` method
- In `_generate_chunk()`, compute biased weights from region context and pass to WFCGenerator

### Step 4: Wire up region context in `GameState.move()`
- After `get_or_create_region_context()`, call `chunk_manager.set_region_context(region_ctx)`
- This ensures new chunks generated during movement use the correct region's terrain bias

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Add `REGION_TERRAIN_BIASES`, `get_biased_weights()` |
| `src/cli_rpg/wfc.py` | Add `weight_overrides` param to `WFCGenerator.__init__()` and use in `_collapse_cell()` |
| `src/cli_rpg/wfc_chunks.py` | Add `region_context` field, `set_region_context()`, use biased weights in `_generate_chunk()` |
| `src/cli_rpg/game_state.py` | Call `set_region_context()` on chunk_manager when region context is obtained |
| `tests/test_terrain_biased_wfc.py` | NEW - 7 tests |
