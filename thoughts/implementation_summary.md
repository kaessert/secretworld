# NPC Echo Consequences MVP - Implementation Summary

## What Was Implemented

### Feature: NPCs Reference Tracked Player Choices

NPCs now vary their greetings based on player reputation (combat flee history). If a player has fled from enemies 3+ times, NPCs may comment on their "cautious reputation."

### Files Modified

1. **`src/cli_rpg/models/npc.py`**
   - Updated `get_greeting()` signature to accept optional `choices: Optional[List[dict]] = None` parameter
   - Added `_get_reputation_greeting(reputation_type: str)` helper method
   - Added 3 "cautious" reputation greeting variants

2. **`src/cli_rpg/main.py`** (line 603)
   - Updated talk command to pass `game_state.choices` to `npc.get_greeting()`

### New Test File

**`tests/test_npc_consequences.py`** - 6 tests covering:
- `test_get_greeting_acknowledges_flee_reputation` - Verifies reputation greeting when 3+ flee choices
- `test_get_greeting_normal_when_few_flees` - Normal greeting with <3 flee choices
- `test_get_greeting_normal_when_no_choices` - Backward compatibility when no choices passed
- `test_get_greeting_normal_when_empty_choices` - Normal greeting with empty choices list
- `test_reputation_greeting_serializes_correctly` - Serialization regression test
- `test_get_greeting_with_dialogue_fallback_and_reputation` - Reputation works without greetings list

## Test Results

- All 6 new tests pass
- All 1891 total tests pass (no regressions)

## Technical Details

### Method Signature Change

```python
# Before
def get_greeting(self) -> str:

# After
def get_greeting(self, choices: Optional[List[dict]] = None) -> str:
```

### Reputation Logic

- Checks if `choices` list has 3+ entries with `choice_type == "combat_flee"`
- If threshold met, returns random reputation-aware greeting
- Falls back to normal greeting behavior otherwise

### Reputation Greeting Templates

```python
"cautious": [
    "Ah, I've heard of you... one who knows when to run. Smart.",
    "Word travels fast. They say you're... careful. I respect that.",
    "A survivor, they call you. Some might say coward, but you're alive.",
]
```

## E2E Test Scenarios

To validate in-game:
1. Start new game
2. Encounter and flee from 3+ different enemies
3. Talk to any NPC
4. NPC greeting should reference player's "cautious" reputation

## Design Notes

- Used optional parameter with None default for backward compatibility
- Python 3.9 compatible type hints (`Optional[List[dict]]` instead of `list[dict] | None`)
- Reputation check happens before normal greeting logic (early return pattern)
- No changes to NPC serialization - only runtime behavior affected
