# Tab Auto-completion Implementation Summary

## What Was Implemented

### New Module: `src/cli_rpg/completer.py`
- **CommandCompleter class**: Readline-compatible completer implementing the `complete(text, state)` interface
- **Command completion**: Completes partial command names (e.g., `lo<tab>` → `look`)
- **Contextual argument completion** based on game state:
  - `go <tab>` → shows available exit directions from current location
  - `talk <tab>` → shows NPCs at current location
  - `equip <tab>` → shows only WEAPON/ARMOR items in inventory
  - `use <tab>` → shows only CONSUMABLE items in inventory
  - `buy <tab>` → shows shop items (when in a shop)
- **Module-level singleton**: `completer` instance for use by input_handler

### Updated: `src/cli_rpg/input_handler.py`
- Added imports for completer module and TYPE_CHECKING
- Updated `init_readline()` to:
  - Set the completer function with `readline.set_completer(completer.complete)`
  - Enable tab completion with `readline.parse_and_bind("tab: complete")`
  - Configure word delimiters with `readline.set_completer_delims(" \t\n")`
- Added `set_completer_context(game_state)` function to update completer's game state

### Updated: `src/cli_rpg/main.py`
- Added import of `set_completer_context` from input_handler
- Modified `run_game_loop()` to:
  - Set completer context at start with `set_completer_context(game_state)`
  - Clear completer context in `finally` block with `set_completer_context(None)`

### New Test File: `tests/test_completer.py`
18 tests covering:
- Command completion (prefix, multiple matches, exact match, unknown prefix)
- Contextual completions (go directions, talk NPCs, equip items, use consumables, buy shop items)
- Edge cases (no game state, empty locations, not in shop)
- Integration with input_handler (set_completer_context function, init_readline setup)

## Test Results
- All 18 new tests pass
- Full test suite: **1534 tests pass**

## Technical Details

### Readline Integration
The completer follows the standard readline interface:
1. On state=0, computes all matching completions and caches them in `_matches`
2. Returns the state-th match for subsequent calls
3. Returns None when all matches are exhausted

### Contextual Completion Logic
- Uses `readline.get_line_buffer()` to read the full command line
- Uses `readline.get_begidx()` to determine if completing first word (command) or argument
- Dispatches to command-specific completers based on parsed command

### Graceful Fallback
- If readline is unavailable (Windows without pyreadline), completion is disabled
- If no game state is set, only command names are completed (no contextual arguments)

## Manual Testing Verification
To verify manually:
1. Run `cli-rpg`
2. Type partial commands and press Tab (e.g., `lo<tab>` → `look`)
3. After starting a game, type `go <tab>` to see available directions
4. Type `talk <tab>` to see NPCs at current location
