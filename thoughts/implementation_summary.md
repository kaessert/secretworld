# Implementation Summary: Fix "up, down" direction mention in error message

## What was implemented
- Fixed the error message in `src/cli_rpg/main.py` line 271
- Changed `"Go where? Specify a direction (north, south, east, west, up, down)"` to `"Go where? Specify a direction (north, south, east, west)"`

## Rationale
The game uses a 2D grid system that only supports north, south, east, and west directions. The "up, down" directions were incorrectly mentioned in the error message.

## Test results
- All 5 tests in `tests/test_main.py` pass
- No tests verified the specific error message text, so no test updates were needed

## Files modified
- `src/cli_rpg/main.py` (line 271)
