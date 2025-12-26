# Implementation Summary: TALK Quest Target Validation

## What Was Implemented

Added validation for TALK quest targets to ensure they match existing NPC names in the game world, following the same pattern as EXPLORE quest validation.

### Files Modified

1. **`src/cli_rpg/ai_service.py`**
   - Added `valid_npcs: Optional[set[str]] = None` parameter to `generate_quest()` (line 1774)
   - Added `valid_npcs: Optional[set[str]] = None` parameter to `_parse_quest_response()` (line 1857)
   - Added TALK quest validation block (lines 1958-1963):
     ```python
     if objective_type == "talk" and valid_npcs is not None:
         if target.lower() not in valid_npcs:
             raise AIGenerationError(
                 f"Invalid TALK quest target '{target}'. Must be an existing NPC."
             )
     ```
   - Passed `valid_npcs` from `generate_quest()` to `_parse_quest_response()` (line 1818)

2. **`src/cli_rpg/main.py`**
   - Added collection of valid NPC names from all locations (lines 1265-1270):
     ```python
     valid_npcs = {
         npc_in_loc.name.lower()
         for location in game_state.world.values()
         for npc_in_loc in location.npcs
     }
     ```
   - Passed `valid_npcs` to `generate_quest()` (line 1277)

3. **`tests/test_talk_quest_validation.py`** (NEW)
   - Created 8 tests covering all spec requirements

### Test Results

All 8 new tests pass:
- `test_valid_talk_target_accepted` - TALK quest with existing NPC name parses successfully
- `test_invalid_talk_target_rejected` - TALK quest with non-existent NPC raises AIGenerationError
- `test_talk_target_case_insensitive` - "Village Elder" matches "village elder" in valid_npcs
- `test_talk_validation_skipped_when_no_npcs` - No validation when valid_npcs=None (backward compatibility)
- `test_kill_quest_unchanged` - KILL quests still validate against VALID_ENEMY_TYPES
- `test_explore_quest_unchanged` - EXPLORE quests still validate against valid_locations
- `test_collect_quest_unchanged` - COLLECT quests still validate against OBTAINABLE_ITEMS
- `test_generate_quest_accepts_valid_npcs_param` - generate_quest() accepts valid_npcs parameter

All 101 related tests (EXPLORE validation + ai_service tests) pass with no regressions.

### Design Decisions

- Case-insensitive matching: `target.lower() not in valid_npcs` (valid_npcs stored lowercase)
- Backward compatible: When `valid_npcs=None`, validation is skipped
- Used `npc_in_loc` variable name in main.py to avoid shadowing outer `npc` variable
- Follows existing validation pattern for EXPLORE quests (consistent code style)

### E2E Validation

To validate manually:
1. Start game with AI service enabled
2. Talk to a quest-giving NPC
3. Request a quest - TALK quests should only reference NPCs that exist in the world
4. Invalid TALK targets will trigger AIGenerationError, causing quest regeneration (up to max_retries)
