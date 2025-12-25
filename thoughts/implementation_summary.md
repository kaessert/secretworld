# Implementation Summary: `rest` Command

## What Was Implemented

Added a new `rest` command that allows players to heal outside of combat without requiring potions.

### Features
- Heals 25% of max HP (minimum 1 HP)
- Alias `r` for quick access
- Blocked during combat (returns error message)
- Cannot rest at full health (returns error message)
- Displays the amount of HP restored

### Files Modified

1. **`src/cli_rpg/game_state.py`**
   - Added `"r": "rest"` to the aliases dictionary (line 55)
   - Added `"rest"` to the `known_commands` set (line 67)

2. **`src/cli_rpg/main.py`**
   - Added `rest` command handler in `handle_exploration_command()` (lines 819-834)
   - Added `"rest"` to blocked commands check during combat (line 836)
   - Added help text entry `"  rest (r)           - Rest to recover health (25% of max HP)"` (line 40)

### Files Created

1. **`tests/test_rest_command.py`**
   - 10 tests covering all specified behaviors:
     - `test_rest_heals_partial_health` - Verifies 25% HP heal
     - `test_rest_at_full_health_fails` - Error when already full
     - `test_rest_caps_at_max_health` - Healing capped at max HP
     - `test_rest_alias_r` - 'r' shorthand works
     - `test_rest_blocked_during_combat` - Cannot rest in combat
     - `test_rest_displays_heal_amount` - Message shows HP restored
     - `test_parse_rest_command` - 'rest' is recognized
     - `test_parse_rest_case_insensitive` - Case-insensitive parsing
     - `test_parse_r_alias` - 'r' alias parsing
     - `test_help_includes_rest` - Help text includes rest

## Test Results

All tests pass:
- 10 new tests in `test_rest_command.py`
- Full test suite: 1098 passed, 1 skipped

## E2E Validation

The following should be validated in end-to-end testing:
1. Type `rest` or `r` while exploring to heal 25% of max HP
2. Verify error message when at full health
3. Verify rest is blocked during combat
4. Check help command shows rest command with (r) alias
