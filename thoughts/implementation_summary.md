# Implementation Summary: Fix Fallback Location Names

## What was implemented

**Issue**: WFC Playtesting Issues #4 - HIGH PRIORITY
**Problem**: Location names like "Vast Prairie (-1, 0)" exposed internal coordinates to players, breaking immersion.

### Changes Made

1. **Modified `src/cli_rpg/world.py`** (lines 165-182):
   - Replaced coordinate-based naming with direction-based suffixes
   - Location names now use immersive direction suffixes (e.g., "Stone Ridge North", "Dark Forest East")
   - Supports all 8 cardinal/ordinal directions

2. **Added test in `tests/test_infinite_world_without_ai.py`**:
   - `test_fallback_location_name_excludes_coordinates` - verifies names don't contain coordinate patterns

## Test Results

All 17 tests in `test_infinite_world_without_ai.py` pass:
- 6 TestGenerateFallbackLocation tests (including new coordinate exclusion test)
- 4 TestMoveToUnexploredDirection tests
- 3 TestWorldNeverBecomesClosed tests
- 4 TestInfiniteWorldIntegration tests

## Technical Details

Before:
```python
location_name = f"{base_name} ({target_coords[0]}, {target_coords[1]})"
# Result: "Stone Ridge (0, 1)"
```

After:
```python
DIRECTION_SUFFIXES = {
    "north": " North", "south": " South",
    "east": " East", "west": " West",
    "northeast": " Northeast", "northwest": " Northwest",
    "southeast": " Southeast", "southwest": " Southwest",
}
suffix = DIRECTION_SUFFIXES.get(direction, "")
location_name = f"{base_name}{suffix}"
# Result: "Stone Ridge North"
```

## E2E Validation

- Start game without AI service
- Explore in multiple directions (north, south, east, west)
- Verify all generated location names use direction suffixes
- Confirm no coordinates appear in location names anywhere in UI
