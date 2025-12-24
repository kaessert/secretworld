# Quest Model Implementation Plan

## Spec

Add a `Quest` dataclass model with:
- `name`: str (2-30 chars, validated)
- `description`: str (1-200 chars, validated)
- `status`: `QuestStatus` enum (`AVAILABLE`, `ACTIVE`, `COMPLETED`, `FAILED`)
- `objective_type`: `ObjectiveType` enum (`KILL`, `COLLECT`, `EXPLORE`, `TALK`)
- `target`: str (the target name - enemy type, item name, location, or NPC)
- `target_count`: int (how many, default 1)
- `current_count`: int (progress, default 0)
- Serialization: `to_dict()` / `from_dict()` methods

## Tests First

Create `tests/test_quest.py` with tests for:
1. Quest creation with all valid attributes
2. Name validation (2-30 chars, reject outside range)
3. Description validation (1-200 chars, reject outside range)
4. All QuestStatus values work
5. All ObjectiveType values work
6. target_count must be >= 1
7. current_count must be >= 0
8. Serialization roundtrip (to_dict → from_dict)
9. Status defaults to AVAILABLE
10. `is_complete` property returns `current_count >= target_count`
11. `progress()` method increments current_count and returns True when complete

## Implementation

1. **Create `src/cli_rpg/models/quest.py`**:
   - `QuestStatus` enum with AVAILABLE, ACTIVE, COMPLETED, FAILED
   - `ObjectiveType` enum with KILL, COLLECT, EXPLORE, TALK
   - `Quest` dataclass with validation in `__post_init__`
   - `to_dict()` and `from_dict()` for serialization
   - `is_complete` property
   - `progress()` method

2. **Update `src/cli_rpg/models/__init__.py`**:
   - Add Quest to exports

## File Locations

- New model: `src/cli_rpg/models/quest.py`
- New test: `tests/test_quest.py`
- Update: `src/cli_rpg/models/__init__.py`
