# Implementation Plan: Fix test_rest_displays_heal_amount

## Problem

The test `test_rest_displays_heal_amount` is flaky. When a dream is triggered during rest, the code prints the rest message directly to stdout (`print(result_message)`) and returns an empty string. The test expects the heal amount to be in the returned message.

Location: `src/cli_rpg/main.py`, lines 2208-2211

## Fix

Change line 2211 to return `result_message` instead of empty string, so the heal amount is always in the returned message regardless of whether a dream was triggered.

**Before:**
```python
        if dream:
            # Print rest message first, then display dream with typewriter effect
            print(result_message)
            display_dream(dream)
            return (True, "")  # Empty message since we already printed
```

**After:**
```python
        if dream:
            # Print rest message first, then display dream with typewriter effect
            print(result_message)
            display_dream(dream)
            return (True, result_message)  # Return message for test assertions
```

## Verification

```bash
pytest tests/test_rest_command.py::TestRestCommand::test_rest_displays_heal_amount -v --count=10
```
