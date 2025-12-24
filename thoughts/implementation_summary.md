# Implementation Summary: COLLECT Objective Type for Quests

## What Was Implemented

Added the `record_collection()` method to the Character class, mirroring the existing `record_kill()` pattern. This enables quest progress tracking when players collect items from:
1. Combat loot drops
2. Shop purchases

### Files Modified

1. **`src/cli_rpg/models/character.py`** (lines 243-271)
   - Added `record_collection(item_name: str) -> List[str]` method
   - Matches item names case-insensitively against active COLLECT quest targets
   - Increments quest progress and returns notification messages
   - Marks quests COMPLETED and grants rewards when target_count reached

2. **`src/cli_rpg/combat.py`** (lines 170-172)
   - Integrated `record_collection()` call after adding loot to inventory in `end_combat()`
   - Quest progress messages are appended to combat victory messages

3. **`src/cli_rpg/main.py`** (lines 477-482)
   - Integrated `record_collection()` call after shop purchase in buy command handler
   - Quest progress messages are appended to purchase confirmation

4. **`tests/test_quest_progress.py`** (lines 219-418)
   - Added `collect_quest` fixture
   - Added `TestRecordCollection` class with 10 test cases covering:
     - Progress increment on matching item collection
     - Progress notification messages
     - Quest completion and status update
     - Completion notification messages
     - Case-insensitive item name matching
     - Non-matching items ignored
     - Only ACTIVE status quests affected
     - Only COLLECT objective type quests affected
     - Multiple quests can match same item
     - Empty list returned when no matching quests

## Test Results

All 906 tests pass (including 10 new tests for record_collection).

## Design Decisions

- Followed exact same pattern as `record_kill()` for consistency
- Quest rewards are automatically claimed on completion (gold, XP, items)
- Item name matching is case-insensitive for better UX
- Integration points chosen to capture all item acquisition paths

## E2E Validation

The following scenarios should work:
1. Player with COLLECT quest for "Health Potion" wins combat, gets Health Potion loot → quest progress updates
2. Player with COLLECT quest for "Iron Sword" buys Iron Sword from shop → quest progress updates
3. Player completes final item collection → quest marked COMPLETED and rewards granted
