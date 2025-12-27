# Implementation Summary: Fast Travel Between Discovered Overworld Locations

## What Was Implemented

Added a `travel` command that allows players to teleport to any previously-visited named overworld location. Travel consumes time proportional to distance, increases tiredness and dread, and has a chance for random encounters.

## Files Modified

### 1. `src/cli_rpg/game_state.py`
- Added `"travel"` to `KNOWN_COMMANDS` set (line 81)
- Added `get_fast_travel_destinations()` method (lines 1199-1216)
  - Returns alphabetically sorted list of named overworld locations (excluding current location)
  - Filters out: unnamed locations, sub-locations (with parent_location), locations without coordinates
- Added `fast_travel(destination)` method (lines 1218-1313)
  - Block conditions: combat, conversation, inside sub-location
  - Case-insensitive partial name matching for destinations
  - Travel time calculation: Manhattan distance // 4, clamped to 1-8 hours
  - Per-hour effects: time advance, weather transition, +3 tiredness, +5 dread
  - 15% encounter chance per hour (skipped if in safe zone)
  - Autosave on arrival

### 2. `src/cli_rpg/main.py`
- Added help text entry (line 53): `"  travel <location>  - Fast travel to a discovered named location"`
- Added command handler (lines 1782-1803):
  - `travel` (no args): Lists available destinations with travel times
  - `travel <location>`: Invokes `fast_travel()` method

### 3. `src/cli_rpg/completer.py`
- Added `travel` case in `_complete_argument()` (lines 151-152)
- Added `_complete_travel()` method (lines 305-320)
  - Returns matching destination names for tab completion

### 4. `tests/test_fast_travel.py` (NEW)
- 22 tests covering:
  - `TestGetFastTravelDestinations`: 6 tests for destination filtering logic
  - `TestFastTravelBlocks`: 4 tests for blocking conditions (combat, conversation, subgrid, unknown destination)
  - `TestFastTravelMechanics`: 8 tests for travel time, tiredness, arrival
  - `TestFastTravelEncounters`: 2 tests for random encounter interruption
  - `TestFastTravelCompletion`: 2 tests for tab completion

## Test Results

```
tests/test_fast_travel.py: 22 passed
Full test suite: 3902 passed in 104.10s
```

## Design Decisions

1. **Safe zone check**: Encounters are skipped when starting from a safe zone (e.g., town), since you're already in a protected area.

2. **Partial name matching**: Allows typing `travel for` to match "Forest Clearing" - case-insensitive with both prefix and substring matching.

3. **Weather transitions**: Weather changes during long travel, providing atmospheric variety.

4. **Dread accumulation**: Fixed 5 dread per hour (wilderness average) rather than calculating from intermediate terrain.

## E2E Test Scenarios

1. **Basic travel**: From Town Square, type `travel` to see destinations, then `travel Forest` to arrive
2. **Blocked travel**: Enter a building, try `travel` - should show "must exit" message
3. **Combat interrupt**: Travel long distance with random seed that triggers encounter
4. **Tab completion**: Type `travel For<TAB>` to complete to "Forest Clearing"
