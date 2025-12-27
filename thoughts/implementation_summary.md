# Implementation Summary: Quest Chains & Prerequisites

## What Was Implemented

### 1. New Fields Added to Quest Model (`src/cli_rpg/models/quest.py`)
- `chain_id: Optional[str]` - Groups related quests (e.g., "goblin_war")
- `chain_position: int` - Order in chain (0 = standalone, 1 = first, etc.)
- `prerequisite_quests: List[str]` - Quest names that must be COMPLETED first
- `unlocks_quests: List[str]` - Quest names unlocked on completion

### 2. New Method: `prerequisites_met()`
```python
def prerequisites_met(self, completed_quests: List[str]) -> bool
```
- Checks if all prerequisite quests have been completed
- Case-insensitive matching
- Returns True if no prerequisites or all are in completed list

### 3. Serialization Support
- `to_dict()` now includes all four chain fields
- `from_dict()` handles chain fields with safe defaults for backward compatibility

### 4. Quest Acceptance Prerequisite Check (`src/cli_rpg/main.py`)
- Added check after faction reputation check in the `accept` command handler
- Blocks acceptance if prerequisites not met, with message listing missing prereqs
- Quest cloning now copies chain fields to accepted quests

### 5. Quest Display Enhancement (`src/cli_rpg/main.py`)
- The `quest` command now shows chain info when present:
  - "Chain: {chain_id} (Part {position})" or "(Prologue)" for position 0
  - "Prerequisites: {comma-separated list}" if any exist

## Files Modified
1. `src/cli_rpg/models/quest.py` - Added fields, method, serialization
2. `src/cli_rpg/main.py` - Added prerequisite check in accept command, chain display in quest command
3. `tests/test_quest.py` - Added new test classes and updated existing serialization test

## Test Results
- All 3795 tests pass
- New tests added:
  - `TestQuestChainFields` (5 tests) - Field defaults, assignment, serialization
  - `TestPrerequisiteValidation` (5 tests) - prerequisites_met() behavior

## E2E Tests Should Validate
1. Create NPC with quest chain (part 1 and part 2 with prerequisite)
2. Attempt to accept part 2 before completing part 1 - should fail with message
3. Complete part 1, then accept part 2 - should succeed
4. View quest details - should show chain info and prerequisites
