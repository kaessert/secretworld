# Implementation Summary: Make All Named Locations Enterable

## What Was Implemented

### 1. New Wilderness Enterable Categories
Added 5 new wilderness POI categories to `ENTERABLE_CATEGORIES` in `src/cli_rpg/world_tiles.py`:
- `grove` - Forest clearing with druid/hermit
- `waystation` - Mountain/road rest stop
- `campsite` - Wilderness camp
- `hollow` - Hidden forest area
- `overlook` - Scenic viewpoint with structure

### 2. Wilderness Enterable Fallback System
Created `WILDERNESS_ENTERABLE_FALLBACK` dict mapping non-enterable categories to enterable ones:
- forest → grove
- wilderness → campsite
- mountain → waystation
- desert → campsite
- swamp → hollow
- beach → campsite
- plains → waystation
- hills → overlook
- foothills → waystation

### 3. get_enterable_category() Helper Function
Added function to convert non-enterable categories to enterable ones:
- Returns category unchanged if already enterable
- Uses terrain-based fallback if category is non-enterable
- Defaults to "campsite" if no fallback found

### 4. SubGrid Bounds for New Categories
Added bounds in `src/cli_rpg/world_grid.py`:
- All 5 new categories use tiny 3x3 single-level bounds: `(-1, 1, -1, 1, 0, 0)`

### 5. Generator Mappings
Updated `CATEGORY_GENERATORS` in `src/cli_rpg/procedural_interiors.py`:
- All 5 wilderness POIs use "SingleRoomGenerator"

### 6. Fallback Content Templates
Added templates in `src/cli_rpg/fallback_content.py` for all 5 new categories:
- Room descriptions for ENTRY, CORRIDOR, and CHAMBER room types
- Treasure chest names and descriptions

## Files Modified
1. `src/cli_rpg/world_tiles.py` - New categories, fallback mapping, helper function
2. `src/cli_rpg/world_grid.py` - SubGrid bounds for new categories
3. `src/cli_rpg/procedural_interiors.py` - Generator mappings
4. `src/cli_rpg/fallback_content.py` - Room and treasure templates
5. `tests/test_named_locations_enterable.py` - New test file (20 tests)

## Test Results
- **20 new tests** verifying:
  - New wilderness categories are in ENTERABLE_CATEGORIES
  - Fallback mapping values are all enterable
  - get_enterable_category() always returns enterable result
  - is_enterable_category() works correctly with new categories
- **5634 total tests pass** - No regressions

## Design Decisions
- **3x3 bounds** for wilderness POIs keep exploration quick
- **SingleRoomGenerator** appropriate for small outdoor clearings
- **campsite as default fallback** ensures safety net for edge cases
- **Case-insensitive matching** in get_enterable_category() for robustness

## E2E Validation
Manual testing should verify:
1. Navigate to named wilderness location
2. Run `enter` command
3. Verify SubGrid is generated with appropriate content
4. Verify `exit` returns to overworld
