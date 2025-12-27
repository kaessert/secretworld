# Implementation Summary: Time-Sensitive Quests

## What Was Implemented

### Quest Model (`src/cli_rpg/models/quest.py`)
Already implemented by previous work:
- `time_limit_hours: Optional[int]` - Hours until quest expires (None = no limit)
- `accepted_at: Optional[int]` - Game hour when quest was accepted
- `is_expired(current_game_hour: int) -> bool` - Check if quest has expired
- `get_time_remaining(current_game_hour: int) -> Optional[int]` - Get hours left
- Validation: `time_limit_hours` must be >= 1 if set
- Serialization: Both fields included in `to_dict()` and `from_dict()`

### Quest Acceptance (`src/cli_rpg/main.py`, `src/cli_rpg/companion_quests.py`)
Already implemented by previous work:
- NPC quest acceptance sets `accepted_at` to current game hour when quest has time limit
- Companion quest acceptance accepts `current_hour` parameter and sets `accepted_at`

### GameState (`src/cli_rpg/game_state.py`)
Already implemented by previous work:
- `check_expired_quests() -> list[str]` - Fails expired quests, returns messages

**Newly Added:**
- `check_expired_quests()` is now called after time advances in `move()` method (line 651)
- Expired quest messages are displayed with error styling (line 673-674)

### Journal Display (`src/cli_rpg/main.py`)
**Newly Added:**
- Active quests in journal show time remaining: `(Xh left)` or `(EXPIRED!)` (lines 1833-1841)
- Quest details show "Time Remaining: X hours" or "Time Remaining: EXPIRED!" (lines 1890-1897)

## Test Results

All 29 tests pass in `tests/test_quest_time_limit.py`:
- 2 model defaults tests
- 5 is_expired() tests
- 4 get_time_remaining() tests
- 3 validation tests
- 4 serialization tests
- 3 quest acceptance integration tests
- 3 check_expired_quests() tests
- 5 journal display tests (newly added)

Full test suite: 3956 tests passed.

## Files Modified

1. `src/cli_rpg/game_state.py` - Added call to `check_expired_quests()` in move() and display expired messages
2. `src/cli_rpg/main.py` - Added time remaining display in quests journal and quest details
3. `tests/test_quest_time_limit.py` - Added 5 new journal display tests

## E2E Validation

Should validate:
- Create a time-limited quest, travel until time expires, verify quest fails and message appears
- View journal to see "(Xh left)" countdown on active time-limited quests
- View quest details to see "Time Remaining: X hours" for time-limited quests
