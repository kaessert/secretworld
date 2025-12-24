# Implementation Plan: Quest Progress Tracking from Combat

## Spec

When defeating an enemy in combat, increment `current_count` on any active KILL quests where the enemy's name matches the quest's target. When a quest reaches `target_count`, mark it as COMPLETED and notify the player.

**Matching rules:**
- Compare enemy name to quest target (case-insensitive)
- Only consider quests with `status == ACTIVE` and `objective_type == KILL`
- Use `Quest.progress()` which increments count and returns True when complete

## Tests First (`tests/test_quest_progress.py`)

```python
# Test: Defeating enemy increments matching quest progress
# Test: Quest completion detected and status updated to COMPLETED
# Test: Player receives notification on quest progress
# Test: Player receives special notification on quest completion
# Test: Non-matching enemy names don't increment progress
# Test: Only ACTIVE quests get progress (not COMPLETED, AVAILABLE, FAILED)
# Test: Only KILL objective type quests get progress
# Test: Multiple quests can progress from same kill
```

## Implementation Steps

### 1. Add Character method for quest progress (`src/cli_rpg/models/character.py`)

Add method after `has_quest()` (~line 211):
```python
def record_kill(self, enemy_name: str) -> List[str]:
    """Record an enemy kill for quest progress.

    Args:
        enemy_name: Name of the defeated enemy

    Returns:
        List of notification messages for quest progress/completion
    """
    from cli_rpg.models.quest import QuestStatus, ObjectiveType

    messages = []
    for quest in self.quests:
        if (quest.status == QuestStatus.ACTIVE and
            quest.objective_type == ObjectiveType.KILL and
            quest.target.lower() == enemy_name.lower()):

            completed = quest.progress()
            if completed:
                quest.status = QuestStatus.COMPLETED
                messages.append(f"Quest Complete: {quest.name}!")
            else:
                messages.append(f"Quest progress: {quest.name} [{quest.current_count}/{quest.target_count}]")
    return messages
```

### 2. Call record_kill after combat victory (`src/cli_rpg/main.py`)

In `handle_combat_command`, after `combat.end_combat(victory=True)` (~lines 178, 251):
```python
# Track quest progress for kill objectives
enemy_name = combat.enemy.name
quest_messages = game_state.current_character.record_kill(enemy_name)
for msg in quest_messages:
    output += f"\n{msg}"
```

Update both locations: `attack` command (~line 178) and `cast` command (~line 251).

### 3. Write tests (`tests/test_quest_progress.py`)

New test file with fixtures and comprehensive coverage of the spec.

## File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/models/character.py` | Add `record_kill()` method |
| `src/cli_rpg/main.py` | Call `record_kill()` after combat victories (~lines 178, 251) |
| `tests/test_quest_progress.py` | New test file for quest progress tracking |
