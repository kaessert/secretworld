# Implementation Plan: TALK Quest Objective Tracking

## Spec
When a player talks to an NPC, check if they have any active quests with `ObjectiveType.TALK` where the target matches the NPC name. If so, increment the quest's `current_count` and mark as `READY_TO_TURN_IN` when complete.

## 1. Write Tests (`tests/test_quest_progress.py`)

Add `TestRecordTalk` class following the existing pattern for `TestRecordExplore`:
- `test_record_talk_increments_matching_quest_progress` - talking to NPC increments matching quest
- `test_record_talk_returns_progress_message` - returns progress notification
- `test_record_talk_marks_quest_ready_to_turn_in_when_target_reached` - status updates correctly
- `test_record_talk_returns_ready_to_turn_in_message` - returns notification with quest giver name
- `test_record_talk_matches_case_insensitive` - NPC name matching is case-insensitive
- `test_record_talk_does_not_increment_non_matching_quest` - non-matching NPCs don't increment
- `test_record_talk_only_affects_active_quests` - only ACTIVE quests get progress
- `test_record_talk_only_affects_talk_objective_quests` - only TALK objective type quests get progress
- `test_record_talk_progresses_multiple_matching_quests` - multiple matching quests all progress
- `test_record_talk_returns_empty_list_when_no_matching_quests` - returns empty list when no matches

## 2. Implement `record_talk()` (`src/cli_rpg/models/character.py`)

Add `record_talk(npc_name: str) -> List[str]` method after `record_explore()` (line ~361):
- Pattern matches existing `record_explore()` implementation exactly
- Check for `ObjectiveType.TALK` instead of `EXPLORE`
- Use case-insensitive comparison: `quest.target.lower() == npc_name.lower()`
- Return list of progress/completion messages

## 3. Call from Talk Handler (`src/cli_rpg/main.py`)

In the `talk` command handler (around line 436, after `output = f"\n{npc.name}: ..."`):
- Call `game_state.current_character.record_talk(npc.name)`
- Append any returned messages to the output
