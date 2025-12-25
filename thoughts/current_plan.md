# Implementation Plan: Quest Turn-In Mechanic

## Summary
Add a "turn in" quest mechanic requiring players to return to the quest-giver NPC to claim rewards, plus fix a critical bug where quest rewards are not copied when accepting quests.

## Bug Fix (Must be done first)
**File**: `src/cli_rpg/main.py` (lines 546-555)

The `accept` command clones quests WITHOUT copying reward fields:
```python
# Current (missing rewards):
new_quest = Quest(
    name=matching_quest.name,
    description=matching_quest.description,
    objective_type=matching_quest.objective_type,
    target=matching_quest.target,
    target_count=matching_quest.target_count,
    status=QuestStatus.ACTIVE,
    current_count=0
)
```

**Fix**: Add `gold_reward`, `xp_reward`, and `item_rewards` to the clone.

## Feature: Quest Turn-In Mechanic

### Spec
1. When quest objectives are met, set status to `READY_TO_TURN_IN` (new status) instead of `COMPLETED`
2. Rewards are NOT granted automatically - player must return to quest-giver NPC
3. New `complete <quest>` command when talking to the quest-giving NPC claims rewards and sets status to `COMPLETED`
4. Quest journal shows "Ready to turn in" for quests awaiting turn-in
5. NPCs with turn-in-ready quests show indicator in dialogue

### Changes

#### 1. Add READY_TO_TURN_IN status to Quest model
**File**: `src/cli_rpg/models/quest.py`
- Add `READY_TO_TURN_IN = "ready_to_turn_in"` to `QuestStatus` enum

#### 2. Track quest giver on Quest
**File**: `src/cli_rpg/models/quest.py`
- Add `quest_giver: Optional[str] = None` field to Quest dataclass
- Update `to_dict()` and `from_dict()` to serialize/deserialize this field

#### 3. Update record_kill and record_collection
**File**: `src/cli_rpg/models/character.py`
- Change: when quest is complete, set `status = QuestStatus.READY_TO_TURN_IN` instead of `COMPLETED`
- Remove automatic call to `claim_quest_rewards()`
- Change message from "Quest Complete" to "Quest objectives complete! Return to {quest_giver} to claim your reward."

#### 4. Store quest_giver when accepting quest
**File**: `src/cli_rpg/main.py`
- In `accept` command, set `quest_giver=npc.name` on the cloned quest

#### 5. Add `complete` command
**File**: `src/cli_rpg/main.py`
- Add "complete" to known_commands set
- Implement handler:
  - Check `game_state.current_npc` is set
  - Find matching quest in character's quests with `status == READY_TO_TURN_IN`
  - Verify `quest.quest_giver == current_npc.name`
  - Call `claim_quest_rewards()` and set `status = COMPLETED`
  - Return reward messages

#### 6. Update quest journal display
**File**: `src/cli_rpg/main.py`
- In `quests` command, add section for "Ready to Turn In" quests
- In `quest <name>` command, show quest_giver and status appropriately

#### 7. Show turn-in indicator in NPC dialogue
**File**: `src/cli_rpg/main.py`
- In `talk` command, check if NPC has any turn-in-ready quests from player
- Show "Quests ready to turn in: ..." if applicable

## Test Plan

### Tests for bug fix
**File**: `tests/test_quest_commands.py` (add tests)
- `test_accept_quest_copies_gold_reward`
- `test_accept_quest_copies_xp_reward`
- `test_accept_quest_copies_item_rewards`

### Tests for READY_TO_TURN_IN status
**File**: `tests/test_quest.py` (add tests)
- `test_ready_to_turn_in_status_exists`
- `test_quest_giver_field_serialization`

### Tests for turn-in behavior
**File**: `tests/test_quest_progress.py` (modify existing)
- Update `test_record_kill_grants_rewards_on_completion` → verify NO rewards granted, status is READY_TO_TURN_IN
- Update `test_record_collection_grants_rewards_on_completion` → same

### Tests for complete command
**File**: `tests/test_quest_commands.py` (add tests)
- `test_complete_command_requires_npc`
- `test_complete_command_requires_quest_name`
- `test_complete_command_requires_ready_to_turn_in_status`
- `test_complete_command_requires_matching_quest_giver`
- `test_complete_command_grants_rewards`
- `test_complete_command_sets_completed_status`
- `test_complete_command_shows_reward_messages`

### Tests for quest journal display
**File**: `tests/test_quest_commands.py` (add tests)
- `test_quests_command_shows_ready_to_turn_in_section`
- `test_quest_detail_shows_quest_giver`

## Implementation Order
1. Fix the bug in accept command (copy rewards)
2. Add READY_TO_TURN_IN status to QuestStatus enum
3. Add quest_giver field to Quest model with serialization
4. Write tests for new status and field
5. Update accept command to set quest_giver
6. Write tests for complete command
7. Implement complete command
8. Update record_kill/record_collection to use READY_TO_TURN_IN
9. Update tests for record_kill/record_collection behavior change
10. Update quest journal display
11. Add turn-in indicator to NPC dialogue
12. Run full test suite
