# Implementation Summary: Fix Confusing Camp Error Message

## What Was Implemented

Fixed the confusing error message when a player tries to `camp` at an overworld landmark with sub-locations.

### Changes Made

**1. `src/cli_rpg/camping.py`**

- Modified `is_campable_location()` function (lines 155-158) to return `False` for overworld locations that have sub-locations. This prevents camping at overworld landmarks where the player should instead use `enter` to access a sub-location.

- Modified `execute_camp()` function (lines 336-343) to show an improved error message when camping fails at an overworld location with sub-locations. The new message:
  - Mentions `'enter <name>'` to guide the user
  - Lists all available sub-locations (e.g., "Forest Edge, Deep Woods")

**2. `tests/test_camping.py`**

- Added new test class `TestOverworldErrorMessage` with test `test_camp_at_overworld_shows_enter_hint` that verifies:
  - Camp command fails at an overworld location with sub-locations
  - Error message contains "enter" hint
  - Error message lists available sub-locations

### New Error Message

Before:
```
You can't camp here. Find a wilderness location.
```

After (for overworld with sub-locations):
```
You can't camp at overworld landmarks. Use 'enter <name>' to find a suitable campsite in: Forest Edge, Deep Woods.
```

## Test Results

```
tests/test_camping.py: 45 passed
```

All 45 camping tests pass, including the new test.

## E2E Validation

To validate manually:
1. Navigate to an overworld location with sub-locations (e.g., "Forest" with "Forest Edge", "Deep Woods")
2. Run `camp` command
3. Should see the new helpful error message mentioning `enter` and listing sub-locations
