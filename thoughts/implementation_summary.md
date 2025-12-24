# Implementation Summary: Map Alignment and Exits Display Fix

## What was implemented

### 1. Fixed Column Alignment for Colored Markers (map_renderer.py)

**Problem:** ANSI color codes in the player's `@` marker (14 bytes for `\x1b[1m\x1b[36m@\x1b[0m`) broke Python's string formatting width calculation. When using `f"{marker:>{cell_width}}"`, Python counts all bytes including invisible ANSI codes, resulting in no padding being added to colored markers.

**Solution:** Changed the approach to:
1. Store uncolored markers in `coord_to_marker` (plain "@" instead of colored "@")
2. Apply padding to the uncolored marker first: `f"{marker:>{cell_width}}"`
3. Only then colorize the marker character while preserving the padding: `padded[:-1] + colors.bold_colorize("@", colors.CYAN)`

**Files modified:** `src/cli_rpg/map_renderer.py` (lines 57-90)

### 2. Added Exits Display on Map

**Feature:** The map now displays available exits from the current location below the legend.

**Implementation:**
- Get available directions using `current_loc.get_available_directions()`
- Display "Exits: east, north" (sorted alphabetically) or "Exits: None" if no connections

**Files modified:** `src/cli_rpg/map_renderer.py` (lines 92-107)

## Tests Added (tests/test_map_renderer.py)

1. `test_colored_marker_alignment` - Verifies that colored @ marker aligns correctly with uncolored markers by checking character positions after stripping ANSI codes

2. `test_exits_displayed_on_map` - Verifies "Exits:" line appears with correct directions

3. `test_exits_displayed_when_no_connections` - Verifies "Exits: None" is shown for isolated locations

## Test Results

All 896 tests pass (1 skipped).

## Verification

Before fix:
```
Header:      -2 -1  0  1  2
Row:      0      W@  E       <- @ and E misaligned (@ at pos 9, E at pos 12)
```

After fix:
```
Header:      -2 -1  0  1  2
Row:      0      W  @  E     <- Correctly aligned (W at 8, @ at 11, E at 14)
Exits: east, north           <- New exits line
```

## E2E Validation

The map command should now display properly aligned markers with exits:
- Player marker @ aligns with column headers
- Other location markers (first letter of name) align correctly
- Exits from current location are listed at the bottom
