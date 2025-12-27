# Implementation Summary: Layered AI Integration for Area Generation

## What Was Implemented

Added `generate_area_with_context()` method to `AIService` that orchestrates layered AI generation (Layers 3-4) for named location clusters, completing Item 4 of the WFC World Generation Overhaul.

### Files Modified

1. **src/cli_rpg/ai_service.py** (+120 lines)
   - Added `generate_area_with_context()` method that:
     - Takes WorldContext (Layer 1) and RegionContext (Layer 2) as inputs
     - Generates area layout coordinates using `_generate_area_layout()`
     - Calls `generate_location_with_context()` for each location (Layer 3)
     - Calls `generate_npcs_for_location()` for each location (Layer 4)
     - Returns list of location dicts with `relative_coords`, `name`, `description`, `category`, `npcs`
   - Added `_generate_area_layout()` helper that creates a branching coordinate pattern from origin (0,0)

2. **src/cli_rpg/ai_world.py** (+10 lines)
   - Updated `expand_area()` to conditionally use layered generation:
     - Uses `generate_area_with_context()` when both `world_context` and `region_context` are provided
     - Falls back to monolithic `generate_area()` when contexts are None (backward compatibility)

3. **tests/test_generate_area_with_context.py** (new file, 9 tests)
   - Tests for `generate_area_with_context()`:
     - Returns list of locations
     - Includes entry at origin (0,0)
     - Each location has required fields
     - Uses world context theme in prompts
     - Uses region context in prompts
     - Generates NPCs for each location
     - Respects size parameter
   - Integration tests for `expand_area()`:
     - Uses layered generation when contexts provided
     - Falls back to monolithic without contexts

4. **tests/test_ai_failure_fallback.py** (1 line fix)
   - Added mock for `generate_area_with_context` to test error handling

## Test Results

All 3657 tests pass (9 new tests added).

## Architecture

```
Before (monolithic for areas):
  expand_area() → generate_area() [single prompt, ignores context]

After (layered for areas):
  expand_area() → generate_area_with_context() [orchestrates layers 3+4]
                → for each location:
                    → generate_location_with_context() [Layer 3]
                    → generate_npcs_for_location() [Layer 4]
```

## Design Decisions

1. **Size clamping**: Area size clamped to 4-7 locations (matching existing `generate_area()` behavior)

2. **Layout algorithm**: Simple branching pattern starting from origin:
   - First location at (0,0)
   - Expands in primary direction (opposite to entry)
   - Branches perpendicular for variety

3. **Backward compatibility**: When contexts are None, falls back to monolithic generation

4. **Cost tradeoff**: More AI calls (2 per location) but:
   - Smaller prompts (less likely to fail/truncate)
   - Better coherence with world/region themes
   - Reuses proven Layer 3/4 generation code

## E2E Validation

To validate in-game:
1. Start game with AI enabled
2. Move to trigger named location generation (after ~5-10 tiles)
3. Verify generated area locations reference region/world themes
4. Check NPCs are present and contextually appropriate
