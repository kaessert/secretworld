# Implementation Plan: DROP Quest Objective Type

## Spec

Add a `DROP` objective type to the quest system that tracks specific item drops from specific enemy types. Unlike `COLLECT` (any item acquisition) or `KILL` (any enemy defeat), `DROP` requires **both conditions**: a specific item dropped from a specific enemy type.

**Example quest**: "Collect 3 Wolf Pelts from Wolves"
- Target enemy: "Wolf"
- Target item: "Wolf Pelt"
- Progress increments only when a Wolf is killed AND drops a Wolf Pelt

### Quest Model Changes
- New `ObjectiveType.DROP` enum value
- New optional field `drop_item: Optional[str]` on `Quest` for the item to track
- Serialization/deserialization support for `drop_item`

### Tracking Mechanism
- New `Character.record_drop(enemy_name: str, item_name: str)` method
- Called from `CombatEncounter.end_combat()` when loot drops
- Only progresses DROP quests where both enemy AND item match

---

## Tests (TDD)

### File: `tests/test_quest_drop.py`

```python
"""Tests for DROP quest objective type."""
```

1. **test_drop_objective_type_exists** - Verify `ObjectiveType.DROP` is valid
2. **test_quest_with_drop_item_field** - Create quest with `drop_item` set
3. **test_quest_drop_item_serialization** - `to_dict()`/`from_dict()` round-trip
4. **test_record_drop_increments_matching_quest** - Both enemy + item match → progress
5. **test_record_drop_enemy_mismatch_no_progress** - Wrong enemy, right item → no progress
6. **test_record_drop_item_mismatch_no_progress** - Right enemy, wrong item → no progress
7. **test_record_drop_case_insensitive** - Both matches are case-insensitive
8. **test_record_drop_only_active_quests** - Only ACTIVE status gets progress
9. **test_record_drop_marks_ready_to_turn_in** - Completion sets READY_TO_TURN_IN
10. **test_record_drop_returns_progress_messages** - Returns proper notifications
11. **test_record_drop_multiple_quests** - Multiple DROP quests can progress together

---

## Implementation Steps

### Step 1: Add DROP to ObjectiveType enum
**File**: `src/cli_rpg/models/quest.py` (line 18-25)

```python
class ObjectiveType(Enum):
    KILL = "kill"
    COLLECT = "collect"
    EXPLORE = "explore"
    TALK = "talk"
    DROP = "drop"  # NEW
```

### Step 2: Add drop_item field to Quest dataclass
**File**: `src/cli_rpg/models/quest.py` (after line 60)

```python
drop_item: Optional[str] = field(default=None)
```

### Step 3: Update Quest.to_dict()
**File**: `src/cli_rpg/models/quest.py` (line 128-146)

Add `"drop_item": self.drop_item` to the returned dict.

### Step 4: Update Quest.from_dict()
**File**: `src/cli_rpg/models/quest.py` (line 162-174)

Add `drop_item=data.get("drop_item")` to the constructor call.

### Step 5: Add record_drop method to Character
**File**: `src/cli_rpg/models/character.py` (after line 284)

```python
def record_drop(self, enemy_name: str, item_name: str) -> List[str]:
    """Record an item drop from an enemy for DROP quest progress.

    Args:
        enemy_name: Name of the defeated enemy
        item_name: Name of the dropped item

    Returns:
        List of notification messages for quest progress/completion
    """
    from cli_rpg.models.quest import QuestStatus, ObjectiveType

    messages = []
    for quest in self.quests:
        if (
            quest.status == QuestStatus.ACTIVE
            and quest.objective_type == ObjectiveType.DROP
            and quest.target.lower() == enemy_name.lower()
            and quest.drop_item
            and quest.drop_item.lower() == item_name.lower()
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

### Step 6: Call record_drop from combat loot
**File**: `src/cli_rpg/combat.py` (line 165-172)

After adding loot to inventory, call `record_drop`:

```python
if loot is not None:
    if self.player.inventory.add_item(loot):
        messages.append(f"You found: {colors.item(loot.name)}!")
        # Track quest progress for collect objectives
        quest_messages = self.player.record_collection(loot.name)
        messages.extend(quest_messages)
        # Track quest progress for drop objectives (enemy + item)
        drop_messages = self.player.record_drop(self.enemy.name, loot.name)
        messages.extend(drop_messages)
```

### Step 7: Update Character.to_dict() and from_dict()
No changes needed - quests already serialize via `Quest.to_dict()`.

---

## Verification

Run tests:
```bash
pytest tests/test_quest_drop.py -v
pytest tests/test_quest*.py -v  # Ensure no regressions
pytest --cov=src/cli_rpg  # Full coverage check
```
