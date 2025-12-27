# Implementation Plan: Fix `travel` Command UnboundLocalError

## Summary
Add missing `colors` module import to `handle_exploration_command()` function to fix crash when listing fast travel destinations.

## Root Cause
The `travel` command in `main.py` uses `colors.location()` at line 1828 but the `colors` module is never imported within `handle_exploration_command()`. Other functions like `handle_stance_command()` correctly use local imports (`from cli_rpg import colors`), but this function lacks it.

## Test (verify the bug exists)
```bash
pytest tests/test_fast_travel.py -v -k "destinations" --tb=short
```

This should pass if the bug is fixed (destinations listing uses `colors.location()`).

## Implementation

### 1. Add import to `handle_exploration_command()` in `src/cli_rpg/main.py`

At line 1049 (after the docstring, before the function body starts):

```python
def handle_exploration_command(game_state: GameState, command: str, args: list[str], non_interactive: bool = False) -> tuple[bool, str]:
    """Handle commands during exploration.

    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments

    Returns:
        Tuple of (continue_game, message)
    """
    from cli_rpg import colors  # <-- ADD THIS LINE

    # Decrement haggle cooldown on current NPC (if any)
    ...
```

### 2. Run tests to verify fix
```bash
pytest tests/test_fast_travel.py -v
pytest tests/test_main.py -v -k "travel"
```

## File Changes
| File | Change |
|------|--------|
| `src/cli_rpg/main.py` | Add `from cli_rpg import colors` at start of `handle_exploration_command()` function body (line ~1049) |
