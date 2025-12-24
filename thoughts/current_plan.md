# Implement COLLECT Objective Type for Quests

## Spec
When a player picks up an item (from combat loot or shop purchase) that matches an active quest's target, the quest progress should increment. When `current_count >= target_count`, mark quest as COMPLETED and grant rewards.

This mirrors the existing `record_kill()` pattern for KILL quests.

## Tests (`tests/test_quest_progress.py`)

Add `TestRecordCollection` class with tests:
1. `test_record_collection_increments_matching_quest_progress` - collecting item increments quest
2. `test_record_collection_returns_progress_message` - returns progress notification
3. `test_record_collection_marks_quest_completed_when_target_reached` - completes quest at target
4. `test_record_collection_returns_completion_message` - returns completion notification
5. `test_record_collection_matches_case_insensitive` - item name matching is case-insensitive
6. `test_record_collection_does_not_increment_non_matching_quest` - non-matching items ignored
7. `test_record_collection_only_affects_active_quests` - only ACTIVE status quests progress
8. `test_record_collection_only_affects_collect_objective_quests` - only COLLECT type quests
9. `test_record_collection_progresses_multiple_matching_quests` - multiple quests can match
10. `test_record_collection_returns_empty_list_when_no_matching_quests` - empty list for no match

## Implementation

### 1. Add `record_collection()` to Character (`src/cli_rpg/models/character.py`)

Add method after `record_kill()` (~line 241):

```python
def record_collection(self, item_name: str) -> List[str]:
    """Record an item collection for quest progress.

    Args:
        item_name: Name of the collected item

    Returns:
        List of notification messages for quest progress/completion
    """
    from cli_rpg.models.quest import QuestStatus, ObjectiveType

    messages = []
    for quest in self.quests:
        if (
            quest.status == QuestStatus.ACTIVE
            and quest.objective_type == ObjectiveType.COLLECT
            and quest.target.lower() == item_name.lower()
        ):
            completed = quest.progress()
            if completed:
                quest.status = QuestStatus.COMPLETED
                messages.append(f"Quest Complete: {quest.name}!")
                reward_messages = self.claim_quest_rewards(quest)
                messages.extend(reward_messages)
            else:
                messages.append(
                    f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]"
                )
    return messages
```

### 2. Call `record_collection()` from combat loot (`src/cli_rpg/combat.py`)

Modify `end_combat()` (~line 168) to track collection after adding loot:

```python
if self.player.inventory.add_item(loot):
    messages.append(f"You found: {colors.item(loot.name)}!")
    # Track quest progress for collect objectives
    quest_messages = self.player.record_collection(loot.name)
    messages.extend(quest_messages)
```

### 3. Call `record_collection()` from shop purchase (`src/cli_rpg/main.py`)

Modify buy command handler (~line 476) after adding item:

```python
game_state.current_character.inventory.add_item(new_item)
# Track quest progress for collect objectives
quest_messages = game_state.current_character.record_collection(new_item.name)
for msg in quest_messages:
    # Prepend newline for formatting
    pass  # Messages will be included in output
autosave(game_state)
output = f"\nYou bought {new_item.name} for {shop_item.buy_price} gold."
if quest_messages:
    output += "\n" + "\n".join(quest_messages)
return (True, output)
```

## Execution Order
1. Write tests in `tests/test_quest_progress.py`
2. Run tests to verify they fail: `pytest tests/test_quest_progress.py::TestRecordCollection -v`
3. Add `record_collection()` to `character.py`
4. Run tests to verify they pass
5. Integrate into `combat.py` and `main.py`
6. Run full test suite: `pytest`
