# Implementation Plan: Fix Help Command Self-Documentation

## Problem
The `help` command output doesn't list itself as an available command, making it impossible for users to rediscover it.

## Solution
Add `help - Display this command reference` to `get_command_reference()` in `main.py`.

## Implementation Steps

### 1. Add test verifying help is listed
**File:** `tests/test_main_help_command.py`

Add to `TestGetCommandReference` class:
```python
def test_get_command_reference_includes_help_command(self):
    """get_command_reference() lists 'help' as an available command."""
    result = get_command_reference()
    assert "help" in result.lower()
    assert "command reference" in result.lower() or "commands" in result.lower()
```

### 2. Add help to command reference
**File:** `src/cli_rpg/main.py`

In `get_command_reference()`, add after the `map` line (line 34):
```python
"  help           - Display this command reference",
```

## Files to Modify
- `tests/test_main_help_command.py` - Add test for help being listed
- `src/cli_rpg/main.py` - Add help line in `get_command_reference()` (line ~34)

## Verification
1. Run `pytest tests/test_main_help_command.py -v` - new test passes
2. Run `pytest` - full suite passes (716+ tests)
