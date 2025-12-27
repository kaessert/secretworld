# Fix colors.success AttributeError

## Issue
`game_state.py` line 470 calls `colors.success()` which doesn't exist, crashing SubGrid movement.

## Fix
Add `success()` function to `colors.py` (green color, matches semantic pattern of existing helpers).

## Implementation

**File:** `src/cli_rpg/colors.py`

Add after `heal()` function (line 179):

```python
def success(text: str) -> str:
    """Color text as success message (green).

    Args:
        text: Success message text.

    Returns:
        Green-colored text.
    """
    return colorize(text, GREEN)
```

## Test

**File:** `tests/test_colors.py`

Add test:
```python
def test_success_colorizes_green():
    result = colors.success("You notice:")
    assert "\x1b[32m" in result  # GREEN
    assert "You notice:" in result
```

## Verification
- Run `pytest tests/test_colors.py -v`
- Run demo mode and test SubGrid movement: `cli-rpg --demo` then `enter` and `go north`
