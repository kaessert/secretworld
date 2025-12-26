# Implementation Summary: Improve `enter` Command Error Messages

## What was implemented

### Code Changes

1. **`src/cli_rpg/game_state.py` (line 809-822)**: Modified the error handling when `enter` command fails to find a matching location:
   - Now collects available locations from both `sub_grid` and `sub_locations`
   - Removes duplicates while preserving order
   - Shows "Available: Tavern, Market" in the error message
   - Shows "There are no locations to enter here." if no locations exist

### Tests Added

2. **`tests/test_game_state.py`**: Added two new tests to `TestEnterExitCommands` class:
   - `test_enter_case_insensitive_multiword_name`: Verifies multi-word location names work with lowercase input (e.g., "spectral grove" matches "Spectral Grove")
   - `test_enter_invalid_location_shows_available`: Verifies error message lists available sub-locations

## Test Results

- All 13 enter-related tests pass
- All 4 subgrid enter tests pass
- Full test suite: 3436 passed

## Design Decisions

- Error message uses proper casing from the location names (e.g., "Tavern" not "tavern")
- Duplicates are removed using `dict.fromkeys()` to preserve insertion order
- SubGrid locations are listed first, then traditional sub_locations (matches lookup order)

## E2E Test Validation

The implementation should be validated by:
1. Starting at an overworld location with sub-locations
2. Running `enter nonexistent` and verifying available locations are shown
3. Running `enter spectral grove` (lowercase) to verify case-insensitive multi-word matching
