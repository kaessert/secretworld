# Implementation Summary: NPC Persistence Bug Investigation

## Summary

The investigation confirmed that the bug report about NPCs showing as "???" when revisiting locations is **NOT reproducible** in the current codebase. The behavior never existed in the implementation - the codebase explicitly tests that NPC names should always be visible.

## What Was Done

### 1. Created Regression Test Suite
**File:** `tests/test_npc_persistence_navigation.py`

Added 6 comprehensive regression tests to ensure NPC persistence during navigation:

1. `test_npcs_persist_after_leaving_and_returning` - Basic navigation round-trip
2. `test_npcs_persist_after_multiple_navigation_cycles` - Multiple navigation cycles
3. `test_npcs_persist_wfc_fallback_generation` - With WFC chunk manager active
4. `test_npcs_with_special_names_persist` - NPCs with special characters (apostrophes, hyphens)
5. `test_multiple_npcs_all_persist` - Multiple NPCs all retained
6. `test_npc_names_never_show_question_marks` - Comprehensive check against "???" appearing

### 2. Fixed Stale Docstring
**File:** `tests/test_weather.py` (line 361)

Removed outdated reference to NPCs being obscured with "???":

**Before:**
```python
- Fog: Hides some exits (50% chance each exit hidden), obscures NPC names with "???"
```

**After:**
```python
- Fog: Hides some exits (50% chance each exit hidden)
```

## Test Results

All tests pass:
- 6 new regression tests in `test_npc_persistence_navigation.py`
- 13 weather visibility tests still pass after docstring fix

## Conclusion

The bug report was likely based on:
1. An outdated docstring that mentioned "???" behavior that was never implemented
2. A misunderstanding of fog weather effects (which hides exits, not NPC names)
3. Possibly confusion with a different display issue

The codebase has always maintained NPC visibility - the `get_layered_description()` method in Location explicitly shows NPC names regardless of weather/visibility settings, as verified by existing tests in `test_weather.py`.

## E2E Validation

If E2E tests are run, they should validate:
- Creating a character and navigating to a location with NPCs
- Moving away and returning to the same location
- Verifying NPCs are still displayed by name (not "???")
