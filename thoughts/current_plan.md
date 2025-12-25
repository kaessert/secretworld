# Implementation Plan: Non-Interactive Mode for AI Agent Playtesting (Increment 1)

## Summary
Add `--non-interactive` flag that reads commands from stdin when not connected to a terminal, exiting gracefully when stdin is exhausted.

## Spec
- Add `--non-interactive` CLI flag via argparse
- When flag is set, game reads commands from stdin line-by-line instead of blocking on `input()`
- When stdin is exhausted (EOF), game exits gracefully with exit code 0
- Disable ANSI colors when in non-interactive mode (use `colors.py` existing infrastructure)
- Works with piped input: `echo "look" | cli-rpg --non-interactive`

## Tests

### File: `tests/test_non_interactive.py`

```python
"""Tests for non-interactive mode."""
import pytest
import subprocess
import sys


class TestNonInteractiveMode:
    """Test non-interactive mode functionality."""

    def test_non_interactive_flag_accepted(self):
        """--non-interactive flag is accepted without error."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="",
            capture_output=True,
            text=True,
            timeout=5
        )
        # Should exit cleanly (0) when stdin is empty
        assert result.returncode == 0

    def test_non_interactive_reads_stdin(self):
        """Non-interactive mode reads commands from stdin."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Should show location description from "look" command
        assert "Town Square" in result.stdout or "location" in result.stdout.lower()

    def test_non_interactive_exits_on_eof(self):
        """Non-interactive mode exits gracefully when stdin is exhausted."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\nstatus\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0

    def test_non_interactive_no_ansi_codes(self):
        """Non-interactive mode disables ANSI color codes."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        # ANSI escape codes start with \x1b[
        assert "\x1b[" not in result.stdout

    def test_non_interactive_multiple_commands(self):
        """Non-interactive mode processes multiple commands."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\nstatus\ninventory\nhelp\n",
            capture_output=True,
            text=True,
            timeout=15
        )
        assert result.returncode == 0
        # Should have processed help command
        assert "help" in result.stdout.lower() or "command" in result.stdout.lower()
```

## Implementation Steps

### 1. Add argparse to `main()` in `src/cli_rpg/main.py`

At the top of `main()` function (line 1152), add argument parsing:

```python
def main() -> int:
    """Main function to start the CLI RPG game.

    Returns:
        Exit code (0 for success)
    """
    import argparse

    parser = argparse.ArgumentParser(description="CLI RPG - A command-line role-playing game")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode, reading commands from stdin"
    )
    args = parser.parse_args()

    if args.non_interactive:
        return run_non_interactive()

    # ... existing main menu code ...
```

### 2. Create `run_non_interactive()` function in `src/cli_rpg/main.py`

Add after `run_game_loop()` function (around line 1050):

```python
def run_non_interactive() -> int:
    """Run game in non-interactive mode, reading commands from stdin.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import sys
    from cli_rpg.colors import set_colors_enabled

    # Disable ANSI colors for machine-readable output
    set_colors_enabled(False)

    # Create a default character and world for non-interactive mode
    from cli_rpg.models.character import Character
    from cli_rpg.world import create_world

    character = Character(name="Agent", character_class="warrior")
    world, starting_location = create_world(ai_service=None, theme="fantasy", strict=False)

    game_state = GameState(
        character,
        world,
        starting_location=starting_location,
        ai_service=None,
        theme="fantasy"
    )

    # Show starting location
    print(game_state.look())

    # Read commands from stdin until EOF
    for line in sys.stdin:
        command_input = line.strip()
        if not command_input:
            continue

        # Parse and execute command
        command, args = parse_command(command_input)

        if game_state.is_in_combat():
            continue_game, message = handle_combat_command(game_state, command, args)
        elif game_state.is_in_conversation and command == "unknown":
            continue_game, message = handle_conversation_input(game_state, command_input)
        else:
            continue_game, message = handle_exploration_command(game_state, command, args)

        print(message)

        # Show combat status if in combat
        if game_state.is_in_combat() and game_state.current_combat is not None:
            print(game_state.current_combat.get_status())

        if not continue_game:
            break

        # Check if player died
        if not game_state.current_character.is_alive():
            print("GAME OVER - You have fallen in battle.")
            break

    return 0
```

### 3. Add `set_colors_enabled()` to `src/cli_rpg/colors.py`

Check if colors.py has a way to disable colors globally. If not, add:

```python
_colors_enabled = True

def set_colors_enabled(enabled: bool) -> None:
    """Enable or disable ANSI color output globally."""
    global _colors_enabled
    _colors_enabled = enabled

def colors_enabled() -> bool:
    """Check if colors are enabled."""
    return _colors_enabled
```

Then update all color functions to check this flag before emitting ANSI codes.

### 4. Update `__main__.py` if needed

Ensure `python -m cli_rpg.main` works by checking/creating `src/cli_rpg/__main__.py`:

```python
"""Allow running as python -m cli_rpg.main"""
from cli_rpg.main import main

if __name__ == "__main__":
    exit(main())
```

## Verification
```bash
# Run tests
pytest tests/test_non_interactive.py -v

# Manual verification
echo "look" | python -m cli_rpg.main --non-interactive
echo -e "look\nstatus\ninventory" | python -m cli_rpg.main --non-interactive

# Verify no ANSI codes in output
echo "look" | python -m cli_rpg.main --non-interactive | cat -v
```

## Files Modified
1. `src/cli_rpg/main.py` - Add argparse, `run_non_interactive()` function
2. `src/cli_rpg/colors.py` - Add `set_colors_enabled()` function
3. `src/cli_rpg/__main__.py` - Create if needed for `-m` invocation
4. `tests/test_non_interactive.py` - New test file
