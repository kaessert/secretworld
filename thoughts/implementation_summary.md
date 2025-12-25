# Implementation Summary: DROP Quest Objective Type

## What Was Implemented

### New Feature: DROP Objective Type
Added a new quest objective type that requires **both** a specific enemy kill AND a specific item drop to progress the quest. This enables quests like "Collect 3 Wolf Pelts from Wolves" where progress only increments when a Wolf is killed AND drops a Wolf Pelt.

### Files Modified

1. **`src/cli_rpg/models/quest.py`**
   - Added `DROP = "drop"` to the `ObjectiveType` enum
   - Added `drop_item: Optional[str] = field(default=None)` field to the `Quest` dataclass
   - Updated `to_dict()` to include `"drop_item"` in serialization
   - Updated `from_dict()` to parse `drop_item` with backward compatibility (defaults to `None`)

2. **`src/cli_rpg/models/character.py`**
   - Added `record_drop(enemy_name: str, item_name: str) -> List[str]` method
   - Only progresses quests where:
     - Status is `ACTIVE`
     - Objective type is `DROP`
     - Target (enemy) matches (case-insensitive)
     - `drop_item` matches (case-insensitive)
   - Sets quest status to `READY_TO_TURN_IN` upon completion
   - Returns appropriate progress/completion messages

3. **`src/cli_rpg/combat.py`**
   - Updated `end_combat()` to call `record_drop()` when loot drops
   - Added after existing `record_collection()` call to support both COLLECT and DROP quest types simultaneously

4. **`tests/test_quest.py`**
   - Updated `test_to_dict` to include `drop_item` in expected serialization output

### New Test File

**`tests/test_quest_drop.py`** - 19 tests covering:
- `ObjectiveType.DROP` enum existence
- `drop_item` field on Quest dataclass
- Serialization/deserialization with `drop_item`
- `record_drop()` functionality:
  - Progress increments when both enemy AND item match
  - No progress when enemy doesn't match
  - No progress when item doesn't match
  - Case-insensitive matching
  - Only ACTIVE quests get progress
  - Completion sets READY_TO_TURN_IN status
  - Proper notification messages
  - Multiple DROP quests can progress together
  - Does not affect KILL or COLLECT quests

## Test Results

- **New tests:** 19 passed
- **All quest tests:** 129 passed
- **Full test suite:** 939 passed, 1 skipped

## Design Decisions

1. **Backward Compatibility**: The `drop_item` field defaults to `None` and `from_dict()` uses `.get()` to handle old save files that don't have this field.

2. **Case Insensitivity**: Both enemy name and item name matching are case-insensitive, consistent with existing `record_kill()` and `record_collection()` methods.

3. **Integration Point**: `record_drop()` is called from `combat.py` after `record_collection()`, allowing both COLLECT and DROP quests to potentially progress from the same loot drop.

4. **Separation of Concerns**: DROP quests don't affect KILL quests (even for same enemy) and don't affect COLLECT quests (even for same item), maintaining clear semantics for each objective type.

## E2E Validation Scenarios

1. Create a DROP quest with specific enemy/item targets
2. Kill the target enemy and receive the target item drop
3. Verify quest progress message appears
4. Complete the quest and turn it in to the quest giver
5. Verify save/load preserves `drop_item` field correctly
