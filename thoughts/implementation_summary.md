# Implementation Summary: Crafting System Foundation

## What Was Implemented

### 1. New ItemType.RESOURCE enum value (src/cli_rpg/models/item.py)
- Added `RESOURCE = "resource"` to the ItemType enum
- This enables resource items to be distinguished from MISC items for future crafting recipes

### 2. New crafting.py module (src/cli_rpg/crafting.py)
Created a new module with the gather command implementation:
- **Constants**: `GATHERABLE_CATEGORIES`, `GATHER_BASE_CHANCE` (40%), `GATHER_PER_BONUS` (+2% per PER), `GATHER_COOLDOWN` (1 hour), `GATHER_TIME_HOURS` (1 hour)
- **Resource templates**: `RESOURCE_BY_CATEGORY` - location-specific resources:
  - Forest: Wood, Fiber
  - Wilderness: Stone, Fiber
  - Cave/Dungeon: Iron Ore, Stone
  - Ruins: Stone, Iron Ore
- **Helper functions**: `is_gatherable_location()`, `_generate_resource_item()`
- **Main command**: `execute_gather()` - handles location checks, cooldown, success roll (PER-based), time advancement, and inventory management

### 3. GameState updates (src/cli_rpg/game_state.py)
- Added `gather_cooldown: int = 0` attribute
- Added `"gather"` to `KNOWN_COMMANDS` set
- Added `"ga": "gather"` alias
- Added serialization in `to_dict()` and deserialization in `from_dict()` with backward compatibility

### 4. Camping.py updates (src/cli_rpg/camping.py)
- Updated `decrement_cooldowns()` to also decrement `gather_cooldown`

### 5. Main.py updates (src/cli_rpg/main.py)
- Added `gather (ga)` to command reference help text
- Added command handler for `gather` that calls `execute_gather()`

## Test Results

All 11 new tests in tests/test_crafting.py pass:
1. `test_gather_in_forest_succeeds` - Verifies gather works in forest category
2. `test_gather_in_town_fails` - Verifies gather fails in safe zones
3. `test_gather_in_dungeon_succeeds` - Verifies gather works in cave/dungeon
4. `test_gather_respects_cooldown` - Verifies cooldown enforcement
5. `test_gather_advances_time` - Verifies 1-hour time advancement
6. `test_gather_adds_item_to_inventory` - Verifies resource item added on success
7. `test_gather_fails_when_inventory_full` - Verifies full inventory handling
8. `test_gather_success_scales_with_per` - Verifies PER bonus calculation
9. `test_resource_item_serialization` - Verifies RESOURCE items serialize/deserialize
10. `test_forest_yields_wood_or_fiber` - Verifies forest resource types
11. `test_cave_yields_ore_or_stone` - Verifies cave resource types

Full test suite: **3073 tests passed**

## Design Decisions

1. **Follows existing patterns**: The gather command mirrors the forage command structure from camping.py
2. **Location-specific resources**: Different areas yield different resources to encourage exploration
3. **Future-proof**: The RESOURCE item type and resource templates enable future crafting recipe implementation
4. **Backward compatible**: gather_cooldown defaults to 0 for loading old saves

## E2E Tests Should Validate

1. Player can use `gather` or `ga` command in wilderness/cave locations
2. Gather fails in towns/villages with appropriate message
3. Gathered resources appear in inventory as RESOURCE type items
4. Cooldown prevents immediate re-gathering
5. Save/load preserves gather_cooldown value
