# Implementation Summary: Fix test_rest_displays_heal_amount

## What was implemented

Fixed a flaky test by ensuring the rest command always returns the heal message in its return value, regardless of whether a dream was triggered.

## Change made

**File:** `src/cli_rpg/main.py`, line 2211

Changed the return value when a dream is triggered from returning an empty string to returning the `result_message`:

```python
# Before
return (True, "")  # Empty message since we already printed

# After
return (True, result_message)  # Return message for test assertions
```

## Why this fixes the flakiness

The test `test_rest_displays_heal_amount` expects the heal amount to be in the returned message. Previously, when `maybe_trigger_dream()` randomly returned a dream, the code would print the message to stdout but return an empty string, causing the test assertion to fail. Now the message is always returned, making the test deterministic.

## Test Results

Ran the test 10 times with `--count=10` - all 10 passed consistently.

## E2E Validation

The game behavior is unchanged: the rest message is still printed before the dream display. The only difference is the return value now includes the message for programmatic access.
