# Implementation Summary: USE Objective Type for Quests

## What Was Implemented

Added a new `USE` objective type that allows quests to require players to use specific items (e.g., "Use a Health Potion to heal yourself").

### Changes Made

1. **`src/cli_rpg/models/quest.py`** (line 26)
   - Added `USE = "use"` to the `ObjectiveType` enum

2. **`src/cli_rpg/models/character.py`**
   - Added `record_use(item_name: str) -> List[str]` method (lines 400-435)
     - Follows the same pattern as `record_talk()` and other record methods
     - Case-insensitive matching of item names to quest targets
     - Only progresses ACTIVE quests with USE objective type
     - Returns quest progress/completion messages
   - Modified `use_item()` method (lines 186-209)
     - Calls `record_use(item.name)` after successful item consumption
     - Appends quest progress messages to the return message

3. **`tests/test_quest_use.py`** (new file - 17 tests)
   - `TestUseObjectiveType`: Enum existence and value tests
   - `TestRecordUse`: Direct record_use() method tests
   - `TestUseItemIntegration`: End-to-end use_item() integration tests
   - `TestQuestSerializationWithUse`: Serialization round-trip tests

## Test Results

- All 17 new tests pass
- Full test suite: 1205 passed, 1 skipped
- No regressions

## Design Decisions

- Follows existing pattern of other objective types (KILL, COLLECT, TALK, EXPLORE, DROP)
- Quest progress messages are appended to use_item() return message using newline separator
- Works with both healing consumables and generic consumables

## E2E Validation

To validate in the game:
1. Create/accept a quest with `objective_type: USE` and `target: "Health Potion"`
2. Use a Health Potion when health is below max
3. Quest should progress and show appropriate message
4. Save/load game - USE quest should persist correctly
