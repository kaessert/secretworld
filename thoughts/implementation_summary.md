# Issue 22: Location-Themed Hallucinations - Implementation Summary

## What Was Implemented

Extended the hallucination system (`src/cli_rpg/hallucinations.py`) to spawn location-category-specific hallucination enemies instead of using generic templates everywhere.

### New Components

1. **`CATEGORY_HALLUCINATION_TEMPLATES`** - Dictionary mapping location categories to themed hallucination templates:
   - `dungeon`: Ghostly Prisoner, Skeletal Warrior
   - `forest`: Twisted Treant, Shadow Wolf
   - `temple`: Fallen Priest, Dark Angel
   - `cave`: Eyeless Horror, Dripping Shadow

2. **`get_hallucination_templates(category: str | None)`** - Helper function that returns templates for a given category, falling back to default `HALLUCINATION_TEMPLATES` for unknown/None categories.

3. **Updated `spawn_hallucination(level, category=None)`** - Added optional `category` parameter to spawn themed hallucinations.

4. **Updated `check_for_hallucination()`** - Now retrieves the current location's category and passes it to `spawn_hallucination()` for themed hallucinations.

### Files Modified

- `src/cli_rpg/hallucinations.py` - Added templates, helper function, updated function signatures
- `tests/test_hallucinations.py` - Added 10 new tests in `TestCategoryHallucinations` class
- `ISSUES.md` - Marked Issue 22 as COMPLETED

## Test Results

All 4560 tests pass, including:
- 27 hallucination tests (17 existing + 10 new category tests)
- All integration tests for themed hallucinations in caves

### New Tests Added

1. `test_dungeon_templates_exist` - Verifies dungeon templates
2. `test_forest_templates_exist` - Verifies forest templates
3. `test_temple_templates_exist` - Verifies temple templates
4. `test_cave_templates_exist` - Verifies cave templates
5. `test_unknown_category_uses_defaults` - Unknown category falls back
6. `test_none_category_uses_defaults` - None falls back
7. `test_spawn_with_dungeon_category` - Spawns dungeon enemy
8. `test_spawn_with_forest_category` - Spawns forest enemy
9. `test_spawn_with_no_category` - Spawns default enemy
10. `test_check_uses_location_category` - Integration test with cave location

## Design Decisions

- Followed the existing pattern from `encounter_tables.py` (Issue 21)
- Each category has exactly 2 themed templates (matching the spec)
- Unknown categories gracefully fall back to default templates
- Backward compatible - `spawn_hallucination(level)` still works without category

## E2E Validation

To validate in-game:
1. Start a new character
2. Navigate to a dungeon/cave/temple/forest location
3. Increase dread to 75%+ (via travel or other mechanics)
4. Continue moving until a hallucination triggers
5. Verify the hallucination enemy name matches the location theme
