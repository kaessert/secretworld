# Implementation Summary: Connect Terrain to Location Generation

## What Was Implemented

This implementation connects WFC terrain types to AI location generation prompts, ensuring generated locations match their terrain (e.g., a "Desert Oasis" only spawns on desert tiles).

### Files Modified

1. **`src/cli_rpg/ai_config.py`**
   - Updated `DEFAULT_LOCATION_PROMPT_MINIMAL` template (lines 306-335)
   - Added `{terrain_type}` placeholder in Region Context section
   - Added terrain-aware requirements for location generation

2. **`src/cli_rpg/ai_service.py`**
   - Added `terrain_type: Optional[str] = None` parameter to `generate_location_with_context()` (line 2412)
   - Updated `_build_location_with_context_prompt()` to accept and use terrain_type (lines 2473, 2490, 2500)
   - Defaults to "wilderness" when terrain_type is None

3. **`src/cli_rpg/ai_world.py`**
   - Added `terrain_type: Optional[str] = None` parameter to `expand_world()` (line 361)
   - Added `terrain_type: Optional[str] = None` parameter to `expand_area()` (line 509)
   - Updated both fallback calls in `expand_area()` to pass terrain_type through

4. **`src/cli_rpg/game_state.py`**
   - Updated `expand_area()` call in `move()` to pass `terrain_type=terrain` (line 530)

5. **`tests/test_terrain_location_coherence.py`** (new file)
   - Tests for terrain inclusion in prompts
   - Tests for backward compatibility when terrain_type is None
   - Tests for function signature validation
   - Tests for terrain passthrough in expand_world

6. **`tests/test_game_state_ai_integration.py`**
   - Fixed `mock_expand_area` to accept `**kwargs` for new parameters

## Test Results

All 3434 tests pass, including:
- 6 new tests in `test_terrain_location_coherence.py`
- All existing layered generation tests
- All game state context tests

## Design Decisions

1. **Backward Compatibility**: `terrain_type` defaults to `None`, and prompts use "wilderness" as a fallback
2. **Passthrough Pattern**: terrain_type is passed from `game_state.move()` → `expand_area()` → `expand_world()` → `generate_location_with_context()` → prompt template
3. **Prompt Enhancement**: The prompt now includes terrain in the Region Context section and adds a requirement ensuring locations make sense for the terrain

## E2E Validation

To manually verify:
1. Start the game with WFC enabled
2. Move to a desert tile
3. Verify the generated location has a desert-appropriate name/description
4. Repeat for other terrain types (forest, mountain, etc.)
