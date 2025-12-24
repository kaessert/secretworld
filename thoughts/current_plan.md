# Implementation Plan: Add `help` Command

## Spec
Add a `help` command that displays the full command reference during gameplay (both exploration and combat modes), matching the text shown at game start.

## Tests (create first)
File: `tests/test_main_help_command.py`

```python
# Test exploration mode:
# - test_help_command_during_exploration: 'help' returns command reference with exploration commands
# - test_help_command_shows_combat_commands: output includes combat commands (attack, defend, cast, flee)
# - test_help_continues_game: returns (True, message) - doesn't exit game

# Test combat mode:
# - test_help_command_during_combat: 'help' works during combat and returns command reference
# - test_help_combat_continues_game: returns (True, message) - doesn't exit game
```

## Implementation Steps

### Step 1: Extract command reference to reusable function
**File**: `src/cli_rpg/main.py`

Create `get_command_reference() -> str` function that returns the formatted command reference string (lines 533-554 content).

### Step 2: Add `help` handler to `handle_exploration_command()`
**File**: `src/cli_rpg/main.py` (in `handle_exploration_command` function, around line 266)

Add:
```python
elif command == "help":
    return (True, "\n" + get_command_reference())
```

### Step 3: Add `help` handler to `handle_combat_command()`
**File**: `src/cli_rpg/main.py` (in `handle_combat_command` function, around line 234)

Add:
```python
elif command == "help":
    return (True, "\n" + get_command_reference())
```

### Step 4: Update `start_game()` and load game welcome
Replace inline command reference prints with `print(get_command_reference())`.

### Step 5: Update unknown command error messages
Add 'help' to the list of valid commands in error messages (lines 439, 442, and combat line 252).

### Step 6: Update ISSUES.md
Mark the help command issue as RESOLVED.
