# Implementation Summary: Rest Command Tiredness Threshold Fix

## What Was Implemented

Fixed the rest command to enforce the documented 30% tiredness threshold for sleep. Previously, the rest command would reduce tiredness at any level above 0%, but documentation (README, model docstring, `can_sleep()` method) all specified that rest should only reduce tiredness when it's >= 30.

## Files Modified

### `src/cli_rpg/main.py` (lines 2376-2431)

Changed the tiredness check logic in the rest command handler:

**Before:**
```python
no_tiredness = char.tiredness.current == 0
if at_full_health and at_full_stamina and no_dread and no_tiredness:
    return (True, "\nYou're already at full health, stamina, and feeling calm and rested!")
# ...
if not no_tiredness:
    quality = char.tiredness.sleep_quality()
    # ...
```

**After:**
```python
can_sleep_for_tiredness = char.tiredness.can_sleep()  # True when tiredness >= 30
if at_full_health and at_full_stamina and no_dread and not can_sleep_for_tiredness:
    return (True, "\nYou're already at full health, stamina, and feeling calm and rested!")
# ...
if can_sleep_for_tiredness:
    quality = char.tiredness.sleep_quality()
    # ...
```

### `tests/test_rest_command.py`

Added new test class `TestRestTirednessThreshold` with test `test_rest_blocked_when_tiredness_below_30` that verifies:
- When tiredness is at 20 (below 30 threshold), resting does NOT reduce tiredness
- Other rest benefits (stamina recovery, etc.) still work

### `ISSUES.md`

Updated the "Rest Command Tiredness Threshold Mismatch" issue status from ACTIVE to COMPLETED.

## Test Results

All 4658 tests pass, including:
- 13 rest command tests (including new threshold test)
- 34 tiredness model tests
- No regressions in any other modules

## Design Decisions

The fix uses the existing `Tiredness.can_sleep()` method rather than duplicating the threshold check. This:
1. Keeps the threshold value (30) defined in one place (`models/tiredness.py`)
2. Makes the intent clear in the code ("can player sleep for tiredness?")
3. Follows the existing pattern established by other `can_*()` methods

## E2E Testing Recommendations

To validate this fix in actual gameplay:
1. Create a new character
2. Move around until tiredness reaches 20-29%
3. Use `rest` command - verify tiredness does NOT decrease
4. Move until tiredness reaches 30%+
5. Use `rest` command - verify tiredness now decreases appropriately
