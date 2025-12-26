# Implementation Summary: AI World Generation Hierarchy Support

## What Was Implemented

Updated `ai_world.py` to generate locations with hierarchy fields (`is_overworld`, `parent_location`, `sub_locations`, `is_safe_zone`, `entry_point`), enabling AI-generated areas to support hierarchical navigation (`enter`/`exit` commands).

### Files Modified

1. **`src/cli_rpg/ai_world.py`**
   - Added `SAFE_ZONE_CATEGORIES` constant defining safe location categories
   - Added `_infer_hierarchy_from_category()` helper function that maps categories to hierarchy fields
   - Updated `create_ai_world()` to set `is_overworld` and `is_safe_zone` on starting and subsequent locations
   - Updated `expand_world()` to set `is_overworld` and `is_safe_zone` on expanded locations
   - Updated `expand_area()` with full hierarchy support:
     - Entry location (rel 0,0): `is_overworld=True`
     - Sub-locations: `is_overworld=False`, `parent_location=entry_name`
     - Entry's `sub_locations` list populated with child names
     - Entry's `entry_point` set to first sub-location
     - All locations get `is_safe_zone` based on category

2. **`tests/test_ai_world_hierarchy.py`** (new file)
   - 26 tests covering all hierarchy functionality
   - Tests for `_infer_hierarchy_from_category()` helper
   - Tests for `create_ai_world()` hierarchy fields
   - Tests for `expand_world()` hierarchy fields
   - Tests for `expand_area()` hierarchy fields
   - Tests for graceful defaults when AI omits hierarchy fields

### Category-to-Hierarchy Mapping

| Category | is_overworld | is_safe_zone |
|----------|--------------|--------------|
| town | True | True |
| village | True | True |
| settlement | True | True |
| dungeon | True | False |
| wilderness | True | False |
| ruins | True | False |
| cave | True | False |
| forest | True | False |
| mountain | True | False |
| None/missing | True | False |

## Test Results

- **New tests:** 26 passed (`tests/test_ai_world_hierarchy.py`)
- **Existing AI world tests:** 54 passed (`tests/test_ai_world_generation.py`)
- **Full test suite:** 2496 passed, 0 failed

## E2E Validation Points

1. Creating a new AI world should result in starting location having `is_overworld=True` and `is_safe_zone` based on category
2. Expanding to a village should have `is_safe_zone=True`
3. Expanding to a dungeon should have `is_safe_zone=False`
4. Area generation should create proper parent-child relationships
5. Entry locations should list their sub-locations and have an entry_point set

## Design Decisions

1. **All AI-generated locations default to `is_overworld=True`** - This ensures compatibility with existing behavior where all locations are traversable via cardinal directions.

2. **Only area sub-locations get `is_overworld=False` and `parent_location`** - This matches the spec for hierarchical navigation where entering an area takes you into sub-locations.

3. **`entry_point` set to first sub-location** - Provides consistent behavior when entering an area.

4. **Graceful defaults when category missing** - Locations without categories default to unsafe (danger zone) behavior for safety.
