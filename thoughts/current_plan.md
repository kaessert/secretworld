# Implementation Plan: Character Creation in Non-Interactive Mode

## Problem
Non-interactive mode (`--non-interactive` and `--json`) completely bypasses character creation, hardcoding a default "Agent" character. Users expect to provide character creation inputs via stdin, but those inputs are treated as "Unknown command" because the game loop starts immediately.

## Design Decision
Add a `--skip-character-creation` flag (default: false) to control whether to use the quick default character or run the full character creation flow in non-interactive mode. This preserves backward compatibility while enabling character customization.

## Spec
1. **New CLI flag**: `--skip-character-creation` - When set, use default "Agent" character (current behavior). When not set, read character creation inputs from stdin.
2. **Character creation inputs** in non-interactive mode (when not skipped):
   - Line 1: Character name (string, 2-30 chars)
   - Line 2: Stat allocation method ("1" or "2" / "manual" or "random")
   - If manual: Lines 3-5: strength, dexterity, intelligence (integers 1-20)
   - Final line: Confirmation ("yes" or "y")
3. **Error handling**: Invalid inputs should print error and exit with code 1 (no retry loops in non-interactive mode)
4. **JSON mode**: Same behavior, but errors emit JSON error objects

## Tests (new file: tests/test_non_interactive_character_creation.py)

1. `test_non_interactive_with_skip_flag_uses_default_character`: `--skip-character-creation` uses "Agent" (preserves current behavior)
2. `test_non_interactive_character_creation_manual_stats`: Provide name, "1", str/dex/int, "yes" → custom character
3. `test_non_interactive_character_creation_random_stats`: Provide name, "2", "yes" → custom character with random stats
4. `test_non_interactive_character_creation_invalid_name_exits`: Invalid name (empty or too short) → exit code 1
5. `test_non_interactive_character_creation_invalid_stat_exits`: Invalid stat value → exit code 1
6. `test_json_mode_character_creation`: Same as above but verify JSON output format
7. `test_json_mode_with_skip_flag`: `--json --skip-character-creation` works

## Implementation Steps

### 1. Add CLI flag to main.py
Location: `main()` function, argparse section (~line 1537)
```python
parser.add_argument(
    "--skip-character-creation",
    action="store_true",
    help="Skip character creation and use default character (non-interactive/JSON modes only)"
)
```

### 2. Create `create_character_non_interactive()` in character_creation.py
Add new function that reads from stdin without retry loops:
- Read name, validate, print error and return None if invalid
- Read allocation method, validate
- If manual: read 3 stat values, validate each
- Read confirmation
- Return Character or None

### 3. Update `run_non_interactive()` in main.py (~line 1397)
Before creating the default character:
```python
if not skip_character_creation:
    character = create_character_non_interactive()
    if character is None:
        return 1  # Exit with error
else:
    character = Character(name="Agent", strength=10, dexterity=10, intelligence=10)
```

### 4. Update `run_json_mode()` in main.py (~line 1208)
Same logic as step 3, but emit JSON error on failure

### 5. Pass flag through to run functions
Update `run_non_interactive()` and `run_json_mode()` signatures to accept `skip_character_creation: bool` parameter

## Files to Modify
1. `src/cli_rpg/character_creation.py` - Add `create_character_non_interactive()`
2. `src/cli_rpg/main.py` - Add CLI flag, update `run_non_interactive()` and `run_json_mode()`
3. `tests/test_non_interactive_character_creation.py` - New test file
