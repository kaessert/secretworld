# Implementation Summary: Quest Prerequisites Based on NPC Arc Stage

## Date: 2025-12-28

## What Was Implemented

This feature adds the ability to gate quest availability based on the player's relationship (arc stage) with an NPC. Quests can now require a minimum trust level before they become available.

### Files Modified/Created

1. **`src/cli_rpg/models/quest.py`**
   - Added `required_arc_stage: Optional[str] = field(default=None)` field to Quest dataclass (line 282)
   - Updated `to_dict()` to serialize the new field (line 474)
   - Updated `from_dict()` to deserialize with None default for backward compatibility (line 533)

2. **`src/cli_rpg/npc_arc_quests.py`** (new file)
   - `ARC_STAGE_ORDER`: List defining stage hierarchy (enemy → hostile → wary → stranger → acquaintance → trusted → devoted)
   - `get_arc_stage_index(stage_name: str) -> int`: Gets numerical index for stage comparison (case-insensitive, defaults to stranger for unknown)
   - `check_arc_stage_requirement(arc, required) -> Tuple[bool, Optional[str]]`: Validates if NPC's arc meets quest requirement

3. **`src/cli_rpg/main.py`** (lines 1838-1849)
   - Added arc stage validation check in accept command handler
   - Placed after faction reputation check and before prerequisite quests check
   - Returns rejection message if insufficient: "{npc.name} doesn't trust you enough to offer this quest. ({reason})"

4. **`tests/test_quest_arc_requirements.py`** (new file)
   - 19 comprehensive tests covering:
     - Helper function tests (stage order, index lookup, case insensitivity)
     - Requirement checking tests (no requirement, exact match, higher/lower stages)
     - Quest model serialization tests (to_dict, from_dict, default values)
     - Integration tests for accept command (rejection, acceptance, no requirement, NPC without arc)

## Test Results

All 19 tests pass:
- TestNpcArcQuestsHelper: 4 tests
- TestCheckArcStageRequirement: 7 tests
- TestQuestModelArcRequirement: 4 tests
- TestAcceptCommandArcRequirement: 4 tests

Additionally, 84 related tests in test_quest.py and test_npc_arc.py continue to pass, confirming no regressions.

## Technical Design Decisions

1. **Stage ordering**: Used list index for comparison rather than enum values to allow flexible comparison (e.g., trusted >= acquaintance)
2. **NPCs without arc**: Treated as STRANGER (index 3) to maintain backward compatibility
3. **Unknown stages**: Default to STRANGER level as safe fallback
4. **Case insensitivity**: Stage names compared case-insensitively for user convenience

## Backward Compatibility

- `required_arc_stage` defaults to `None` (no requirement)
- NPCs without arc initialized are treated as STRANGER stage
- Existing quests and saves unaffected (`from_dict` handles missing field with None default)

## E2E Test Validation

E2E tests should validate:
1. Creating a quest with `required_arc_stage` set
2. Attempting to accept that quest with insufficient NPC relationship
3. Building relationship through interactions and accepting the quest once threshold is met
