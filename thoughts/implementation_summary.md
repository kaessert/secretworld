# Implementation Summary: Validate EXPLORE Quest Targets

## What Was Implemented

Added validation for EXPLORE quest targets against known location names, following the same pattern as the existing KILL quest validation.

### Files Modified

1. **`src/cli_rpg/ai_service.py`**
   - Added `valid_locations: Optional[set[str]] = None` parameter to `generate_quest()` method
   - Added `valid_locations: Optional[set[str]] = None` parameter to `_parse_quest_response()` method
   - Added EXPLORE quest target validation logic after existing KILL validation:
     ```python
     if objective_type == "explore" and valid_locations is not None:
         if target.lower() not in valid_locations:
             raise AIGenerationError(
                 f"Invalid EXPLORE quest target '{target}'. Must be an existing location."
             )
     ```

2. **`src/cli_rpg/main.py`**
   - Updated talk command handler to pass `valid_locations` to `generate_quest()`
   - Builds set of lowercase location names from `game_state.world.keys()`

### Files Created

1. **`tests/test_explore_quest_validation.py`**
   - 7 tests covering all aspects of EXPLORE validation:
     - Valid explore target accepted
     - Invalid explore target rejected (raises AIGenerationError)
     - Case-insensitive matching
     - Backward compatibility when valid_locations=None
     - KILL quests still validate against VALID_ENEMY_TYPES
     - COLLECT quests not validated against locations
     - generate_quest accepts valid_locations parameter

## Test Results

All tests pass:
- `tests/test_explore_quest_validation.py`: 7 passed
- `tests/test_quest_validation.py`: 15 passed (existing tests unchanged)
- `tests/test_ai_service.py`: 94 passed
- `tests/test_main.py`: 5 passed

## Design Decisions

1. **Backward Compatibility**: When `valid_locations=None` (the default), EXPLORE validation is skipped entirely. This ensures existing code paths that don't pass this parameter continue to work.

2. **Case-Insensitive Matching**: Location names are compared lowercase, matching the pattern used for KILL quest validation against VALID_ENEMY_TYPES.

3. **Minimal Changes**: Only added the necessary validation logic without modifying existing behavior for other quest types (KILL, COLLECT, TALK, DROP).

## E2E Validation

To validate this feature works end-to-end:
1. Start a game and explore some locations
2. Talk to a quest-giving NPC
3. If they offer an EXPLORE quest, the target should be one of the discovered locations
4. If AI generates an invalid location target, it will trigger quest regeneration automatically
