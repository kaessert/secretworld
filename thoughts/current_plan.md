# Plan: Fix "up, down" direction mention in error message

## Task (Simple)
Remove "up, down" from the `go` command error message since the game uses a 2D grid system.

## Implementation
1. Edit `src/cli_rpg/main.py` line 271
2. Change: `"Go where? Specify a direction (north, south, east, west, up, down)"`
3. To: `"Go where? Specify a direction (north, south, east, west)"`

## Verification
- Run existing tests: `pytest tests/test_main.py -v` to ensure no regressions
- Search for any test that validates this specific error message and update if needed
