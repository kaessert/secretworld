# Implementation Plan: Quest Full Flow Validation Scenario

## Task
Add `scripts/scenarios/quests/basic_quest.yaml` covering accept, track, and complete quest flow using the demo world's "Scout the Ruins" quest.

## Spec
The scenario validates the complete quest lifecycle:
1. Accept quest from NPC
2. Track quest progress via `quests` command
3. Complete quest objective (explore location)
4. Return to quest giver and turn in quest
5. Verify rewards received

Uses existing demo world with Elder Theron offering "Scout the Ruins" (EXPLORE type, target: Abandoned Ruins).

## Implementation Steps

### 1. Create quests directory
- Path: `scripts/scenarios/quests/__init__.py` (empty package)

### 2. Create basic_quest.yaml scenario
- Path: `scripts/scenarios/quests/basic_quest.yaml`
- Config: `demo_mode: true`, unique seed (42050)
- Steps:
  1. `look` - verify starting at Peaceful Village
  2. `talk Elder Theron` - initiate dialogue with quest giver
  3. `accept Scout the Ruins` - accept the exploration quest
  4. `dump_state` - verify quest added to character.quests with status ACTIVE
  5. `quests` - verify quest appears in journal
  6. `go west` - move to Abandoned Ruins (at coordinates [-1,0])
  7. `look` - verify at Abandoned Ruins (triggers EXPLORE objective)
  8. `dump_state` - verify quest status changed to READY_TO_TURN_IN
  9. `go east` - return to Peaceful Village
  10. `talk Elder Theron` - talk to quest giver again
  11. `complete Scout the Ruins` - turn in the quest
  12. `dump_state` - verify quest status is COMPLETED and gold reward received

### 3. Assertions to include
- NARRATIVE_MATCH for location names and quest text
- STATE_CONTAINS for quest in character.quests
- COMMAND_VALID for all commands
- Check gold increases after turn-in (gold_reward: 30 from fixture)

### 4. Update ISSUES.md
- Check off "Quests (accept, track, complete, world effects, quest chains)" in the Scripted Playthrough feature list

## Files to Create/Modify
1. `scripts/scenarios/quests/__init__.py` - new (empty)
2. `scripts/scenarios/quests/basic_quest.yaml` - new (main scenario)
3. `ISSUES.md` - update checkbox

## Verification
- Run: `pytest tests/test_scenario_files.py -v -k quests`
- Run: `python -m scripts.run_simulation --scenario scripts/scenarios/quests/basic_quest.yaml`
