# Implementation Plan: Time-Sensitive Quests

## Spec

Add optional time limits to quests, creating urgency and gameplay tension. When a time-limited quest expires, it automatically fails.

**New Fields on Quest dataclass:**
- `time_limit_hours: Optional[int] = None` - Hours until quest expires (None = no limit)
- `accepted_at: Optional[int] = None` - Game hour when quest was accepted

**New Methods:**
```python
def is_expired(self, current_game_hour: int) -> bool:
    """Check if quest has expired based on time limit."""
    if self.time_limit_hours is None or self.accepted_at is None:
        return False
    return (current_game_hour - self.accepted_at) >= self.time_limit_hours

def get_time_remaining(self, current_game_hour: int) -> Optional[int]:
    """Return hours remaining, or None if no time limit."""
    if self.time_limit_hours is None or self.accepted_at is None:
        return None
    remaining = self.time_limit_hours - (current_game_hour - self.accepted_at)
    return max(0, remaining)
```

## Tests (TDD)

Create `tests/test_quest_time_limit.py`:

1. **Model Tests:**
   - `test_quest_time_limit_defaults_to_none` - new quests have no time limit
   - `test_quest_accepted_at_defaults_to_none` - new quests have no accepted_at
   - `test_is_expired_returns_false_when_no_time_limit` - no limit = never expires
   - `test_is_expired_returns_false_when_time_remaining` - still has time left
   - `test_is_expired_returns_true_when_time_exceeded` - past deadline
   - `test_is_expired_returns_true_when_exactly_at_limit` - edge case: exactly at limit
   - `test_get_time_remaining_returns_none_when_no_limit` - no limit = None
   - `test_get_time_remaining_returns_hours_left` - calculates correctly
   - `test_get_time_remaining_returns_zero_when_expired` - floor at 0
   - `test_time_limit_validation_rejects_zero` - time_limit_hours must be >= 1
   - `test_time_limit_validation_rejects_negative` - time_limit_hours must be >= 1

2. **Serialization Tests:**
   - `test_to_dict_includes_time_limit_fields` - serializes new fields
   - `test_from_dict_restores_time_limit_fields` - deserializes correctly
   - `test_from_dict_handles_missing_time_fields` - backward compat defaults

3. **Integration Tests:**
   - `test_accept_quest_sets_accepted_at` - main.py sets accepted_at on accept
   - `test_companion_quest_sets_accepted_at` - companion_quests.py sets accepted_at
   - `test_journal_shows_time_remaining` - quests command shows "(Xh left)"
   - `test_quest_details_shows_time_remaining` - quest command shows deadline
   - `test_expired_quest_auto_fails` - check_expired_quests fails expired quests

## Implementation Steps

### Step 1: Add fields to Quest model
**File:** `src/cli_rpg/models/quest.py`

Add after line 179 (after `recommended_level`):
```python
# Time limit fields for urgent quests
time_limit_hours: Optional[int] = field(default=None)
accepted_at: Optional[int] = field(default=None)
```

Add validation in `__post_init__` (after recommended_level validation):
```python
# Validate time limit fields
if self.time_limit_hours is not None and self.time_limit_hours < 1:
    raise ValueError("time_limit_hours must be at least 1")
```

Add methods after `prerequisites_met`:
```python
def is_expired(self, current_game_hour: int) -> bool:
    """Check if quest has expired based on time limit."""
    if self.time_limit_hours is None or self.accepted_at is None:
        return False
    return (current_game_hour - self.accepted_at) >= self.time_limit_hours

def get_time_remaining(self, current_game_hour: int) -> Optional[int]:
    """Return hours remaining, or None if no time limit."""
    if self.time_limit_hours is None or self.accepted_at is None:
        return None
    remaining = self.time_limit_hours - (current_game_hour - self.accepted_at)
    return max(0, remaining)
```

### Step 2: Update Quest serialization
**File:** `src/cli_rpg/models/quest.py`

In `to_dict()` add:
```python
"time_limit_hours": self.time_limit_hours,
"accepted_at": self.accepted_at,
```

In `from_dict()` add to constructor:
```python
time_limit_hours=data.get("time_limit_hours"),
accepted_at=data.get("accepted_at"),
```

### Step 3: Set accepted_at on quest acceptance
**File:** `src/cli_rpg/main.py` (around line 1699)

When creating new_quest, add:
```python
time_limit_hours=matching_quest.time_limit_hours,
accepted_at=game_state.game_time.total_hours if matching_quest.time_limit_hours else None,
```

**File:** `src/cli_rpg/companion_quests.py` (around line 73)

Update `accept_companion_quest()` signature to accept `current_hour: Optional[int] = None`:
```python
def accept_companion_quest(companion: Companion, current_hour: Optional[int] = None) -> Optional[Quest]:
```

Add to Quest constructor:
```python
time_limit_hours=quest.time_limit_hours,
accepted_at=current_hour if quest.time_limit_hours and current_hour else None,
```

Update caller in main.py (around line 2130) to pass current hour:
```python
new_quest = accept_companion_quest(companion, game_state.game_time.total_hours)
```

### Step 4: Display time remaining in journal
**File:** `src/cli_rpg/main.py`

In `quests` command (around line 1830), modify active quest display:
```python
time_info = ""
if quest.time_limit_hours:
    remaining = quest.get_time_remaining(game_state.game_time.total_hours)
    if remaining is not None and remaining > 0:
        time_info = f" ({remaining}h left)"
    elif remaining == 0:
        time_info = " (EXPIRED!)"
lines.append(f"  {diff_icon} {quest.name} [{quest.current_count}/{quest.target_count}]{time_info}")
```

In `quest` command details (around line 1878), add after Progress line:
```python
if quest.time_limit_hours:
    remaining = quest.get_time_remaining(game_state.game_time.total_hours)
    if remaining is not None:
        if remaining > 0:
            lines.append(f"Time Remaining: {remaining} hours")
        else:
            lines.append("Time Remaining: EXPIRED!")
```

### Step 5: Add expired quest check
**File:** `src/cli_rpg/game_state.py`

Add method to GameState:
```python
def check_expired_quests(self) -> list[str]:
    """Check for and fail any expired time-limited quests.

    Returns:
        List of messages about failed quests
    """
    from cli_rpg.models.quest import QuestStatus
    messages = []
    current_hour = self.game_time.total_hours
    for quest in self.current_character.quests:
        if quest.status == QuestStatus.ACTIVE and quest.is_expired(current_hour):
            quest.status = QuestStatus.FAILED
            messages.append(f"Quest '{quest.name}' has expired and failed!")
    return messages
```

Call this in `move()` method after advancing time, display any failure messages.

## Files to Modify

1. `src/cli_rpg/models/quest.py` - Add fields, validation, methods, serialization
2. `src/cli_rpg/main.py` - Set accepted_at on accept, display time in journal/details
3. `src/cli_rpg/companion_quests.py` - Update accept_companion_quest signature
4. `src/cli_rpg/game_state.py` - Add check_expired_quests method, call in move()
5. `tests/test_quest_time_limit.py` - New test file
