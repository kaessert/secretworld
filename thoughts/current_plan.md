# Implementation Plan: Quest Prerequisites Based on NPC Arc Stage

## Summary
Add `required_arc_stage` field to Quest model allowing quests to require minimum NPC relationship levels before they can be accepted.

## Files to Modify

### 1. `src/cli_rpg/models/quest.py`
- Add `required_arc_stage: Optional[str] = None` field to Quest dataclass (after `required_reputation`)
- Update `to_dict()` to serialize new field
- Update `from_dict()` to deserialize new field with None default

### 2. `src/cli_rpg/npc_arc_quests.py` (new file)
- Create helper functions for arc stage requirements:
  - `ARC_STAGE_ORDER`: List defining stage hierarchy for comparison
  - `get_arc_stage_index(stage_name: str) -> int`: Get numerical index for stage
  - `check_arc_stage_requirement(arc: Optional[NPCArc], required: Optional[str]) -> Tuple[bool, Optional[str]]`: Check if arc meets requirement, return (allowed, rejection_reason)

### 3. `src/cli_rpg/main.py` (~line 1838)
- In accept command handler, after faction reputation check (line ~1836) and before prerequisite quests check (line ~1838):
- Import `check_arc_stage_requirement` from `npc_arc_quests`
- Add arc stage validation check
- Return rejection message if insufficient: `"{npc.name} doesn't trust you enough to offer this quest. (Requires: {stage})"`

## Stage Ordering (for comparison)
```
ENEMY < HOSTILE < WARY < STRANGER < ACQUAINTANCE < TRUSTED < DEVOTED
```
NPCs without arc initialized are treated as STRANGER (index 3).

## Tests: `tests/test_quest_arc_requirements.py`

1. `test_quest_no_arc_requirement_always_available` - None required_arc_stage passes
2. `test_quest_requires_stranger_accepts_stranger` - Stranger arc passes stranger requirement
3. `test_quest_requires_trusted_rejects_stranger` - Stranger arc fails trusted requirement
4. `test_quest_requires_trusted_accepts_trusted` - Trusted arc passes trusted requirement
5. `test_quest_requires_acquaintance_accepts_higher` - Trusted passes acquaintance requirement
6. `test_quest_requires_devoted_rejects_trusted` - Trusted arc fails devoted requirement
7. `test_npc_no_arc_treated_as_stranger` - None arc treated as STRANGER
8. `test_quest_serialization_with_required_arc_stage` - to_dict includes field
9. `test_quest_deserialization_with_required_arc_stage` - from_dict parses field
10. `test_quest_deserialization_without_required_arc_stage` - from_dict defaults None
11. `test_accept_command_rejects_insufficient_arc` - Integration test for main.py
12. `test_accept_command_accepts_sufficient_arc` - Integration test for main.py

## Implementation Order

1. Add `required_arc_stage` field to Quest model with serialization
2. Create `npc_arc_quests.py` with stage comparison helper
3. Write unit tests for Quest model changes and helper functions
4. Integrate arc check into main.py accept command handler
5. Write integration tests for accept command
6. Run full test suite
7. Update ISSUES.md Issue 13 to mark quest prerequisites complete

## Backward Compatibility

- `required_arc_stage` defaults to `None` (no requirement)
- NPCs without arc initialized are treated as STRANGER stage
- Existing quests and saves unaffected (from_dict handles missing field)
