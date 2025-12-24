# Quest Model Implementation Summary

## What Was Implemented

### New Files

1. **`src/cli_rpg/models/quest.py`** - Quest dataclass model with:
   - `QuestStatus` enum: AVAILABLE, ACTIVE, COMPLETED, FAILED
   - `ObjectiveType` enum: KILL, COLLECT, EXPLORE, TALK
   - `Quest` dataclass with:
     - `name`: str (2-30 chars, validated, stripped)
     - `description`: str (1-200 chars, validated, stripped)
     - `status`: QuestStatus (defaults to AVAILABLE)
     - `objective_type`: ObjectiveType
     - `target`: str (target name)
     - `target_count`: int (>= 1, default 1)
     - `current_count`: int (>= 0, default 0)
     - `is_complete` property: returns `current_count >= target_count`
     - `progress()` method: increments current_count, returns True when complete
     - `to_dict()` / `from_dict()` serialization methods

2. **`tests/test_quest.py`** - Comprehensive test suite with 37 tests covering:
   - Quest creation with valid attributes
   - Name validation (length, empty, whitespace)
   - Description validation (length, empty, whitespace)
   - All QuestStatus enum values
   - All ObjectiveType enum values
   - Count validation (target_count >= 1, current_count >= 0)
   - is_complete property
   - progress() method behavior
   - Serialization roundtrip (to_dict → from_dict)

### Modified Files

- **`src/cli_rpg/models/__init__.py`** - Added exports for Quest, QuestStatus, ObjectiveType

## Test Results

```
tests/test_quest.py: 37 passed
Full suite: 690 passed, 1 skipped
```

## Design Decisions

- Followed existing patterns from Location model (ClassVar constants, validation in __post_init__, to_dict/from_dict methods)
- Used field(default=...) for mutable defaults
- Enum values use lowercase strings for serialization consistency
- Whitespace is stripped from name and description (consistent with Location model)

## E2E Validation

The Quest model should be validated with:
- Creating quests via NPC dialogue or game events
- Tracking progress through KILL/COLLECT/EXPLORE/TALK objectives
- Save/load persistence of quest state
- Quest completion and status transitions
