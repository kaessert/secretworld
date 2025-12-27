# Implementation Summary: Multi-Stage Quest Objectives

## What Was Implemented

### New QuestStage Dataclass (`src/cli_rpg/models/quest.py`)
Added a new `QuestStage` dataclass that represents a single stage within a multi-stage quest:

- **Fields:**
  - `name: str` - Stage title (e.g., "Find the Witness")
  - `description: str` - Stage-specific flavor text
  - `objective_type: ObjectiveType` - Type of objective (KILL, TALK, EXPLORE, etc.)
  - `target: str` - Target name
  - `target_count: int = 1` - How many to complete
  - `current_count: int = 0` - Progress tracking

- **Methods:**
  - `is_complete` property - Returns True when current_count >= target_count
  - `progress()` - Increments count and returns whether stage is complete
  - `to_dict()` / `from_dict()` - Serialization support

- **Validation:**
  - Name and target cannot be empty (ValueError raised)
  - target_count must be >= 1
  - current_count must be >= 0
  - Names/targets are trimmed of whitespace

### Quest Class Extensions (`src/cli_rpg/models/quest.py`)
Added new fields and methods to the existing Quest dataclass:

- **New Fields:**
  - `stages: List[QuestStage] = []` - Ordered list of stages
  - `current_stage: int = 0` - Index of active stage (0-based)

- **New Methods:**
  - `get_active_stage()` - Returns current stage or None if no stages/past all stages
  - `advance_stage()` - Moves to next stage, returns True if quest is complete
  - `get_active_objective()` - Returns (objective_type, target, target_count, current_count) for the active objective (uses stage if exists, otherwise root quest fields)

- **Updated Serialization:**
  - `to_dict()` now includes `stages` and `current_stage`
  - `from_dict()` now deserializes stages with backward compatibility

### Character Progress Recording (`src/cli_rpg/models/character.py`)
Updated all record_* methods to support staged quests:

- **New Helper Method:**
  - `_check_stage_progress()` - Checks if an action progresses/completes a stage

- **Updated Methods:**
  - `record_kill()` - Checks stages before branches/main objective
  - `record_talk()` - Same pattern
  - `record_explore()` - Same pattern
  - `record_collection()` - Same pattern
  - `record_use()` - Same pattern

- **Behavior:**
  - Staged quests are checked first
  - Stage completion triggers advancement to next stage
  - Final stage completion marks quest as READY_TO_TURN_IN
  - Progress messages include quest name and stage counts
  - Completion messages include "Stage complete" and "Next:" hints

## Files Modified

1. `src/cli_rpg/models/quest.py` - Added QuestStage class, extended Quest with stages support
2. `src/cli_rpg/models/character.py` - Added stage progress checking to record_* methods
3. `tests/test_quest_stages.py` - New test file with 50 comprehensive tests
4. `tests/test_quest.py` - Updated serialization test to include new fields

## Test Results

- All 50 new quest stage tests pass
- All 4006 tests in the full test suite pass
- Backward compatibility maintained (quests without stages work exactly as before)

## Key Design Decisions

1. **Empty stages = legacy behavior**: When `stages` is empty, the quest uses root fields (objective_type, target, etc.) exactly as before, maintaining full backward compatibility.

2. **Stages checked first**: In all record_* methods, staged quest logic runs before branch/main objective logic and uses `continue` to skip further processing.

3. **Stage-level progress tracking**: Each stage has its own current_count/target_count, independent of the quest's root fields.

4. **Clear progress messages**: Stage completions generate separate messages for stage completion and next stage hints.

## E2E Tests Should Validate

1. Creating a multi-stage quest and accepting it
2. Completing each stage in order
3. Verifying stage progress messages appear correctly
4. Confirming quest becomes READY_TO_TURN_IN after final stage
5. Save/load with staged quests preserves stage progress
6. Quest journal display with stage information
