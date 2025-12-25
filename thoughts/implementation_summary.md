# Implementation Summary: "Did You Mean?" Command Suggestions

## What Was Implemented

Added fuzzy matching to suggest similar commands when a player types an unrecognized command.

### Changes Made

#### 1. `src/cli_rpg/game_state.py`
- Added `import difflib` for fuzzy string matching
- Added `KNOWN_COMMANDS` constant (set of all valid commands) at module level
- Added `suggest_command(unknown_cmd, known_commands)` helper function
  - Uses `difflib.get_close_matches()` with 60% similarity threshold
  - Returns the best match or `None` if no close match found
- Modified `parse_command()` to return `("unknown", [original_command])` instead of `("unknown", [])` for unrecognized commands, enabling error messages to show what was typed

#### 2. `src/cli_rpg/main.py`
- Added import for `suggest_command` and `KNOWN_COMMANDS`
- Updated exploration mode unknown command handler to show suggestion
- Updated combat mode unknown command handler to show suggestion (using combat-specific command set)

#### 3. `tests/test_command_suggestions.py` (new file)
- 21 tests covering:
  - `suggest_command()` function for various typos
  - `parse_command()` returning original input
  - Message formatting
  - `KNOWN_COMMANDS` set contents

#### 4. `tests/test_game_state.py`
- Updated `test_parse_command_unknown` to expect new behavior

## Test Results

All 1445 tests pass.

## Behavior

**With suggestion (typo is close to a known command):**
```
> attakc
✗ Unknown command 'attakc'. Did you mean 'attack'?
```

**Without suggestion (too different from any command):**
```
> xyzzy
✗ Unknown command. Type 'help' for a list of commands.
```

**In combat (suggests from combat-specific commands only):**
```
> attak
✗ Unknown command 'attak'. Did you mean 'attack'?
```

## E2E Validation

To manually verify:
1. Start the game: `cli-rpg`
2. At any exploration prompt, type a typo like `"attakc"` or `"lokk"`
3. Verify the "Did you mean 'X'?" suggestion appears
4. Enter combat and type a typo like `"attak"` to verify combat suggestions work
