# Implementation Plan: Fix `quit` Command Crash in Non-Interactive Mode

## Problem
When using `--non-interactive` or `--json` mode, the `quit` command crashes with `EOFError` because it calls `input()` to prompt "Save before quitting?" when stdin is already exhausted.

## Spec
1. **Detect non-interactive mode** in quit handlers
2. **Skip save prompt** in non-interactive mode (default to not saving)
3. **Apply to both handlers**: exploration quit (line 967) and combat quit (line 404)

## Files to Modify
- `src/cli_rpg/main.py` - `handle_exploration_command()` (line 965-977) and `handle_combat_command()` (line 399-409)

## Implementation Steps

### 1. Add `non_interactive` parameter to command handlers

Both `handle_exploration_command()` and `handle_combat_command()` need a `non_interactive: bool = False` parameter.

### 2. Update exploration quit handler (line 965-977)

```python
elif command == "quit":
    if non_interactive:
        # In non-interactive mode, skip save prompt and exit directly
        return (False, "\nExiting game...")
    print("\n" + "=" * 50)
    response = input("Save before quitting? (y/n): ").strip().lower()
    # ... rest unchanged
```

### 3. Update combat quit handler (line 399-409)

```python
elif command == "quit":
    if non_interactive:
        # In non-interactive mode, skip confirmation and exit directly
        return (False, "\nExiting game...")
    print("\n" + "=" * 50)
    print("Warning: You are in combat! Saving is disabled during combat.")
    # ... rest unchanged
```

### 4. Update call sites

- `run_non_interactive()` (line 1454, 1458): Pass `non_interactive=True`
- `run_json_mode()` (similar location): Pass `non_interactive=True`
- `run_game_loop()`: Leave as `non_interactive=False` (default)

## Test Plan

### New tests in `tests/test_non_interactive.py`

```python
def test_quit_command_exits_cleanly_non_interactive(self):
    """Quit command should exit without EOFError in non-interactive mode."""
    result = subprocess.run(
        [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
        input="quit\n",
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0
    assert "EOFError" not in result.stderr
    assert "Traceback" not in result.stderr

def test_quit_command_exits_cleanly_json_mode(self):
    """Quit command should exit without EOFError in JSON mode."""
    result = subprocess.run(
        [sys.executable, "-m", "cli_rpg.main", "--json"],
        input="quit\n",
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0
    assert "EOFError" not in result.stderr
```

## Verification
1. Run new tests: `pytest tests/test_non_interactive.py -v -k quit`
2. Run full suite: `pytest`
3. Manual verification: `echo "quit" | cli-rpg --non-interactive`
