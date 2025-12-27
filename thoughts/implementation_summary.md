# Implementation Summary: Rest Command Output UX Improvement

## What Was Implemented

Modified the `rest` command in `src/cli_rpg/main.py` to show explicit status messages when HP or stamina are already full (instead of silently omitting them).

### Changes Made

**src/cli_rpg/main.py (lines ~2247-2265)**
- Added conditional branch to show `HP: X/X (already full)` when resting at full health
- Added conditional branch to show `Stamina: X/X (already full)` when resting at full stamina
- Previously, these stats were silently omitted from the rest message when already full

**tests/test_rest_command.py**
- Added new test class `TestRestOutputWhenAlreadyFull` with 2 tests:
  - `test_rest_at_full_health_but_not_stamina_shows_hp_status`: Verifies HP status message appears when HP is full but stamina is low
  - `test_rest_at_full_stamina_but_not_health_shows_stamina_status`: Verifies stamina status message appears when stamina is full but HP is low

## Test Results

All 12 rest command tests pass:
- 6 existing `TestRestCommand` tests
- 3 existing `TestParseCommandRest` tests
- 2 new `TestRestOutputWhenAlreadyFull` tests
- 1 existing `TestHelpIncludesRest` test

## Example Output

Before (resting with full HP but low stamina):
```
You recover 10 stamina.
```

After:
```
HP: 100/100 (already full) You recover 10 stamina.
```

This improves UX by making it clear what happened with each stat during rest.
