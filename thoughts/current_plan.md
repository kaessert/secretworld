# Enhancement: "Did You Mean?" Command Suggestions

## Overview
Add fuzzy matching to suggest similar commands when a player types an unrecognized command (e.g., typing "attakc" suggests "Did you mean: attack?").

## Spec
- When an unknown command is entered, find the most similar known command using string similarity
- If similarity exceeds a threshold (e.g., 60%), suggest it: `"Unknown command 'attakc'. Did you mean 'attack'?"`
- If no close match, fall back to current message: `"Unknown command. Type 'help' for a list of commands."`
- Use Python's built-in `difflib.get_close_matches()` for simplicity (no external dependencies)

## Implementation

### 1. Update `game_state.py`

**Location:** `parse_command()` function (lines 28-74)

Add a helper function and modify the unknown command return:

```python
import difflib

def suggest_command(unknown_cmd: str, known_commands: set[str]) -> Optional[str]:
    """Suggest a similar command for typos."""
    matches = difflib.get_close_matches(unknown_cmd, known_commands, n=1, cutoff=0.6)
    return matches[0] if matches else None
```

Modify `parse_command()` to return the original input for better error messages:
- Current: Returns `("unknown", [])`
- New: Returns `("unknown", [original_command])` so the error handler can show suggestions

### 2. Update `main.py`

**Location:** `handle_exploration_command()` (lines 965-969) and `handle_combat_command()` (line 401-402)

Update unknown command handling to use suggestion:

```python
elif command == "unknown":
    if args and args[0]:
        from cli_rpg.game_state import suggest_command, KNOWN_COMMANDS
        suggestion = suggest_command(args[0], KNOWN_COMMANDS)
        if suggestion:
            return (True, f"\n✗ Unknown command '{args[0]}'. Did you mean '{suggestion}'?")
    return (True, "\n✗ Unknown command. Type 'help' for a list of commands.")
```

## Tests

**File:** `tests/test_command_suggestions.py`

```python
"""Tests for 'Did you mean?' command suggestions."""

class TestSuggestCommand:
    def test_suggests_attack_for_attakc(self):
        """'attakc' should suggest 'attack'."""

    def test_suggests_inventory_for_invnetory(self):
        """Common typo 'invnetory' should suggest 'inventory'."""

    def test_no_suggestion_for_gibberish(self):
        """Random gibberish like 'xyzzy' should not suggest anything."""

    def test_suggestion_threshold(self):
        """Only suggests when similarity is >= 60%."""

class TestUnknownCommandWithSuggestion:
    def test_exploration_shows_suggestion(self):
        """Unknown command during exploration shows suggestion."""

    def test_combat_shows_suggestion(self):
        """Unknown command during combat shows suggestion."""
```

## Files to Modify
1. `src/cli_rpg/game_state.py` - Add `suggest_command()` helper, export `KNOWN_COMMANDS`
2. `src/cli_rpg/main.py` - Update unknown command handlers in both exploration and combat
3. `tests/test_command_suggestions.py` - New test file for the feature
