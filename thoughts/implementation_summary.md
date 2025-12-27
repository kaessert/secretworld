# Implementation Summary: Branching Quest Objectives

## What Was Implemented

Added alternative completion paths to quests, enabling moral complexity and player choice. Example: "Stop the Bandit" can be completed by killing, convincing to leave, or helping him raid - each with different rewards and faction consequences.

## Files Modified

### `src/cli_rpg/models/quest.py`
- **Added `QuestBranch` dataclass** (lines 29-117):
  - Fields: `id`, `name`, `objective_type`, `target`, `target_count`, `current_count`, `description`, `faction_effects`, `gold_modifier`, `xp_modifier`
  - Includes `__post_init__` validation for required fields
  - `to_dict()` and `from_dict()` for serialization
  - `is_complete` property and `progress()` method

- **Extended `Quest` dataclass**:
  - Added `alternative_branches: List[QuestBranch]` field (line 165)
  - Added `completed_branch_id: Optional[str]` field (line 166)
  - Updated `to_dict()` to serialize branches (lines 274-275)
  - Updated `from_dict()` to deserialize branches (lines 292-294, 317-318)
  - Added `get_branches_display()` method for UI (lines 321-352)

### `src/cli_rpg/models/character.py`
- **Added `_check_branch_progress()` helper method** (lines 500-522):
  - Checks if any quest branch matches an action and progresses it
  - Returns the branch ID if a branch was completed

- **Updated `record_kill()`** (lines 524-594):
  - Checks alternative branches first for KILL objectives
  - Sets `completed_branch_id` when a branch completes
  - Falls back to main quest objective for quests without branches

- **Updated `record_talk()`** (lines 710-780):
  - Same branch-aware logic as `record_kill()` for TALK objectives

- **Updated `claim_quest_rewards()`** (lines 1046-1154):
  - Gets `gold_modifier` and `xp_modifier` from completed branch
  - Applies branch-specific `faction_effects`
  - Falls back to quest-level faction handling if no branch effects

### `tests/test_quest.py`
- Updated `test_to_dict` assertion to include new fields (lines 444-445)

## New Test Files

### `tests/test_quest_branching.py` (11 tests)
- `TestQuestBranchBasics`: Branch creation and field defaults
- `TestQuestBranchSerialization`: to_dict/from_dict round-trip
- `TestQuestWithBranches`: Backward compatibility, serialization, independent progress
- `TestBranchCompletion`: Quest ready when any branch complete, completed_branch_id tracking
- `TestBranchRewards`: Gold/XP modifiers, faction effects by branch
- `TestQuestDisplay`: `get_branches_display()` method

### `tests/test_quest_branch_validation.py` (6 tests)
- Validates required fields: id, name, target
- Validates target_count >= 1
- Validates current_count >= 0

## Test Results
- All 3812 tests pass (including 17 new branching tests)
- Backward compatibility maintained - existing quests work unchanged

## Design Decisions

1. **Branches are optional**: Quests without `alternative_branches` work exactly as before
2. **First branch to complete wins**: When any branch reaches its target_count, the quest becomes READY_TO_TURN_IN
3. **Branch-specific rewards override quest-level**: If a branch has faction_effects, they're used instead of quest's faction_affiliation/reward
4. **Progress is independent per branch**: Each branch tracks its own current_count

## E2E Tests Should Validate

1. Creating a quest with multiple branches
2. Completing different branches leads to different outcomes
3. Branch rewards (gold/XP modifiers) are applied correctly
4. Branch faction effects are applied correctly
5. Save/load preserves branch state and completed_branch_id
6. UI displays all available branches with progress
