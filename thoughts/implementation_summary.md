# Implementation Summary: Aggressive Reputation Type

## What Was Implemented

Added a new "aggressive" reputation type that NPCs recognize when players kill enemies frequently (10+ kills). This extends the existing reputation system that previously only tracked "cautious" (fleeing 3+ times).

### Files Modified

1. **`src/cli_rpg/models/npc.py`**
   - Added `"aggressive"` templates to `_get_reputation_greeting()` method (3 unique greetings)
   - Added aggressive check in `get_greeting()` method - triggers when `combat_kill` count >= 10
   - Priority: cautious (flee) is checked before aggressive (kill), so chronic fleers get coward reputation even if they also kill a lot

2. **`src/cli_rpg/main.py`**
   - Added `game_state.record_choice()` calls after `record_kill()` in two locations:
     - Line 258: After attack victory combat
     - Line 355: After cast victory combat
   - Records choice_type="combat_kill" with enemy name and time

3. **`tests/test_npc.py`**
   - Added 3 new tests:
     - `test_get_greeting_aggressive_reputation`: Verifies aggressive greeting at 10+ kills
     - `test_get_greeting_no_aggressive_below_threshold`: Verifies no trigger at 9 kills
     - `test_get_greeting_cautious_priority_over_aggressive`: Verifies cautious takes priority

### Aggressive Greeting Templates
- "I've heard tales of your... efficiency in combat. Many have fallen."
- "The blood of your enemies precedes you. What brings such a warrior here?"
- "A killer walks among us. I hope we remain on friendly terms."

## Test Results

- All 1894 tests pass
- Coverage: 92.32%
- NPC model coverage: 98%

## Technical Details

### Reputation Logic in `get_greeting()`
```python
# Check for reputation-based greetings first
if choices:
    flee_count = sum(1 for c in choices if c.get("choice_type") == "combat_flee")
    if flee_count >= 3:
        return self._get_reputation_greeting("cautious")

    # Check for aggressive reputation (10+ kills)
    kill_count = sum(1 for c in choices if c.get("choice_type") == "combat_kill")
    if kill_count >= 10:
        return self._get_reputation_greeting("aggressive")
```

### Kill Recording in `main.py`
```python
game_state.record_choice(
    choice_type="combat_kill",
    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
    description=f"Killed {enemy.name}",
    target=enemy.name,
)
```

## E2E Validation

To validate end-to-end:
1. Start a new game
2. Engage in combat and defeat 10+ enemies
3. Talk to any NPC
4. NPC should greet player with one of the aggressive reputation templates instead of their normal greeting
