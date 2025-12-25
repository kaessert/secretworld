# Implementation Plan: USE Objective Type for Quests

## Spec
Add `USE` objective type allowing quests to require players to use specific items (e.g., "Use a Health Potion to heal yourself"). Follows the established pattern of other objective types (KILL, COLLECT, TALK, EXPLORE, DROP).

## Implementation Steps

### 1. Add USE to ObjectiveType enum
**File:** `src/cli_rpg/models/quest.py` (line ~24)
- Add `USE = "use"` to the ObjectiveType enum

### 2. Add `record_use()` method to Character
**File:** `src/cli_rpg/models/character.py` (after `record_talk`, around line 398)
- Add `record_use(self, item_name: str) -> List[str]` method
- Pattern: identical to `record_talk` but matches ObjectiveType.USE and item names
- Case-insensitive matching on target vs item_name

### 3. Call `record_use()` from `use_item()`
**File:** `src/cli_rpg/models/character.py` (in `use_item` method, around line 197)
- After successful item use, call `self.record_use(item.name)`
- Append quest progress messages to return message

### 4. Write tests (TDD)
**File:** `tests/test_quest_use.py` (new file)
- Test `ObjectiveType.USE` enum exists and has value `"use"`
- Test `record_use()` increments progress for matching ACTIVE USE quests
- Test case-insensitive matching
- Test non-matching items don't progress
- Test only ACTIVE quests progress
- Test only USE objective type quests progress
- Test status changes to READY_TO_TURN_IN on completion
- Test multiple USE quests can progress from single item use
- Test quest serialization round-trips with USE type

## Test-First Order
1. Create `tests/test_quest_use.py` with all tests (they will fail)
2. Add `USE = "use"` to ObjectiveType enum (some tests pass)
3. Add `record_use()` method (more tests pass)
4. Integrate into `use_item()` (all tests pass)
5. Run full test suite to ensure no regressions
