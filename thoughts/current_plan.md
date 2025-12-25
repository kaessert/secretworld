# Implementation Plan: EXPLORE Objective Type Tracking

## Spec
When a player enters a new location via `GameState.move()`, check if they have any active quests with `ObjectiveType.EXPLORE` where the target matches the location name. If so, increment the quest's `current_count` and mark as `READY_TO_TURN_IN` when complete.

## Tests First (TDD)

**File**: `tests/test_quest_progress.py`

Add new test class `TestRecordExplore` following existing `TestRecordKill`/`TestRecordCollection` patterns:

1. `test_record_explore_increments_matching_quest_progress` - entering location increments current_count
2. `test_record_explore_returns_progress_message` - returns "Quest progress: X [N/M]"
3. `test_record_explore_marks_quest_ready_to_turn_in_when_target_reached` - status changes to READY_TO_TURN_IN
4. `test_record_explore_returns_ready_to_turn_in_message` - returns message with quest giver name
5. `test_record_explore_matches_case_insensitive` - "Dark Forest" matches "dark forest"
6. `test_record_explore_does_not_increment_non_matching_quest` - wrong location doesn't progress
7. `test_record_explore_only_affects_active_quests` - AVAILABLE/COMPLETED/FAILED quests unchanged
8. `test_record_explore_only_affects_explore_objective_quests` - KILL/COLLECT/TALK unchanged
9. `test_record_explore_progresses_multiple_matching_quests` - multiple quests can match same location
10. `test_record_explore_returns_empty_list_when_no_matching_quests`

## Implementation

### Step 1: Add `record_explore()` to Character class

**File**: `src/cli_rpg/models/character.py`

Add method after `record_drop()` (around line 324):

```python
def record_explore(self, location_name: str) -> List[str]:
    """Record exploring a location for quest progress.

    Args:
        location_name: Name of the explored location

    Returns:
        List of notification messages for quest progress/completion
    """
    from cli_rpg.models.quest import QuestStatus, ObjectiveType

    messages = []
    for quest in self.quests:
        if (
            quest.status == QuestStatus.ACTIVE
            and quest.objective_type == ObjectiveType.EXPLORE
            and quest.target.lower() == location_name.lower()
        ):
            completed = quest.progress()
            if completed:
                quest.status = QuestStatus.READY_TO_TURN_IN
                if quest.quest_giver:
                    messages.append(
                        f"Quest objectives complete: {quest.name}! "
                        f"Return to {quest.quest_giver} to claim your reward."
                    )
                else:
                    messages.append(
                        f"Quest objectives complete: {quest.name}! "
                        "Return to the quest giver to claim your reward."
                    )
            else:
                messages.append(
                    f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                )
    return messages
```

### Step 2: Call `record_explore()` from `GameState.move()`

**File**: `src/cli_rpg/game_state.py`

After successful move (line ~301), before returning, add:

```python
# Check for exploration quest progress
explore_messages = self.current_character.record_explore(self.current_location)
for msg in explore_messages:
    message += f"\n{msg}"
```

## Verification

Run: `pytest tests/test_quest_progress.py -v -k "explore"`
