# Implementation Plan: Fix Help Command Regression

## Problem
The `help` command returns "Unknown command" because `parse_command()` in `game_state.py` doesn't include `"help"` in its `known_commands` set.

## Root Cause
- `parse_command()` (line 48-49 in `game_state.py`) validates commands against a whitelist
- `"help"` is missing from `known_commands`, so it returns `("unknown", [])`
- `handle_exploration_command()` has the handler at line 450-451, but never receives `"help"`

## Implementation Steps

1. **Add `"help"` to `known_commands` in `game_state.py`** (line 48-49)
   - Add `"help"` to the set of known commands

2. **Verify existing tests pass**
   - Run `pytest tests/test_main_help_command.py -v` - should all pass
   - Run `pytest tests/test_game_state.py -v` - verify no regressions

3. **Add integration test for parse_command**
   - Add test in `tests/test_game_state.py` to verify `parse_command("help")` returns `("help", [])`

## Files to Modify
- `src/cli_rpg/game_state.py` - Add "help" to known_commands set (line 48-49)
- `tests/test_game_state.py` - Add test for parse_command("help")

## Verification
- Manual test: Start game, type `help`, should display command reference
- `pytest tests/test_main_help_command.py -v` - all 8 tests pass
- `pytest --cov=src/cli_rpg` - full test suite passes
