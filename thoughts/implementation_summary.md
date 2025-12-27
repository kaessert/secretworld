# Implementation Summary: Add Neighboring Locations to Location Prompts

## What Was Implemented

Added `{neighboring_locations}` context to the minimal location generation prompt (Phase 1, item 4 of World Generation Immersion). This provides the AI with context about nearby locations for spatial coherence when generating new locations.

### Files Modified

1. **`src/cli_rpg/ai_config.py`** (line 308)
   - Added `- Nearby: {neighboring_locations}` placeholder to `DEFAULT_LOCATION_PROMPT_MINIMAL` under Region Context

2. **`src/cli_rpg/ai_service.py`** (lines 2571, 2585, 2602, 2637, 2647, 2655-2661, 2670)
   - Added `neighboring_locations: Optional[list[dict]] = None` parameter to `generate_location_with_context()`
   - Added `neighboring_locations: Optional[list[dict]] = None` parameter to `_build_location_with_context_prompt()`
   - Added formatting logic: neighbors displayed as comma-separated "Name (direction)" or "none yet" if empty
   - Pass `neighboring_locations` through to template format call

3. **`src/cli_rpg/ai_world.py`** (lines 437-448, 457)
   - Added neighbor gathering logic in `expand_world()` before calling `generate_location_with_context()`
   - Iterates through `DIRECTION_OFFSETS` to find existing locations at neighboring coordinates
   - Builds list of `{name, direction}` dicts for each neighbor found

4. **`tests/test_ai_config.py`** (lines 407-415)
   - Added `test_ai_config_location_prompt_minimal_has_neighboring()` test verifying the placeholder exists

5. **`ISSUES.md`** (lines 1311-1315)
   - Updated Phase 1 task status to "Complete"
   - Marked `region_theme` as done (was already implemented)
   - Marked `neighboring_locations` as done

## Test Results

- All 3680 tests pass
- New test `test_ai_config_location_prompt_minimal_has_neighboring` passes
- All 123 ai_config and ai_service tests pass

## Design Decisions

1. **Format**: Neighbors formatted as "Name (direction)" for readability, e.g., "Dark Forest (north), Ancient Tower (east)"
2. **Empty state**: "none yet" when no neighbors exist (first location or edge of explored area)
3. **Optional parameter**: Default to `None` for backward compatibility
4. **Coordinate-based lookup**: Uses `target_coords` to find neighbors at adjacent coordinates, consistent with existing grid-based navigation

## E2E Validation

When playing the game and exploring, the AI should now generate locations that:
- Reference nearby locations in their descriptions
- Have names/themes that fit with adjacent areas
- Create more spatially coherent world-building
