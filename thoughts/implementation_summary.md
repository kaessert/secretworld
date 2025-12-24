# Implementation Summary: Direction Shorthands for Movement

## What Was Implemented

Added direction shorthand expansion for the `go` command:
- `n` expands to `north`
- `s` expands to `south`
- `e` expands to `east`
- `w` expands to `west`

## Files Modified

1. **`src/cli_rpg/game_state.py`** - Added direction alias expansion in `parse_command()` function (lines 57-60):
   ```python
   # Expand direction shorthands for go command
   if command == "go" and args:
       direction_aliases = {"n": "north", "s": "south", "e": "east", "w": "west"}
       args[0] = direction_aliases.get(args[0], args[0])
   ```

2. **`tests/test_shorthand_commands.py`** - Added `TestDirectionShorthands` test class with 7 tests verifying:
   - `g n` → `go north`
   - `g s` → `go south`
   - `g e` → `go east`
   - `g w` → `go west`
   - `go n` → `go north` (full command with shorthand direction)
   - `G N` → `go north` (case-insensitive)
   - `g north` → `go north` (full direction still works)

## Test Results

- All 21 shorthand tests pass
- Full test suite: 804 passed, 1 skipped (no regressions)

## Design Decisions

- Direction expansion happens after command alias expansion, so both `g n` and `go n` work correctly
- Expansion is case-insensitive because the input is lowercased early in `parse_command()`
- Only the first argument is expanded (the direction), leaving any additional arguments unchanged
- Non-matching directions (like "north") pass through unchanged via `.get()`'s default behavior
