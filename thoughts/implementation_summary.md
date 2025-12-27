# Implementation Summary: Issue 17 - AI-Generated Treasure Chests

## What Was Implemented

AI-generated areas (via `expand_area()` and `generate_subgrid_for_location()`) now include treasure chests that:

1. **Scale with area size**: 1 chest for 2-3 rooms, 2 for 4-5 rooms, 3 for 6+ rooms
2. **Are distributed across non-entry rooms**: Treasures are spread using a step-based distribution algorithm
3. **Match location category thematically**: Each category has a loot table with thematic items
4. **Have lock difficulty scaling**: Difficulty = Manhattan distance from entry + random(0,1)
5. **Exclude boss rooms**: Boss room doesn't get treasure (boss IS the reward)
6. **Exclude entry rooms**: Entry/exit points don't get treasure
7. **Only apply to appropriate categories**: dungeon, cave, ruins, temple, forest

## Files Modified

### `src/cli_rpg/ai_world.py`

Added:
- `import random` at top
- `TREASURE_LOOT_TABLES` constant: Category-specific loot tables with items (weapons, armor, consumables, misc)
- `TREASURE_CHEST_NAMES` constant: Thematic chest names per category
- `TREASURE_CATEGORIES` constant: frozenset of categories that get treasures
- `_place_treasures()` function: Places treasures in non-entry, non-boss rooms with scaling based on room count
- `_create_treasure_chest()` function: Creates a treasure dict with items, difficulty, and schema

Integrated treasure placement into:
- `generate_subgrid_for_location()` (line ~717): Places treasures after boss placement
- `expand_area()` (line ~1445): Places treasures after boss placement

### `tests/test_ai_world_treasure.py` (NEW)

Created comprehensive test file with 28 tests covering:
- `TestTreasureLootTables`: Verifies loot tables exist and have required fields
- `TestTreasureChestNames`: Verifies chest names exist for categories
- `TestPlaceTreasuresHelper`: Tests the placement algorithm (scaling, distribution, exclusions)
- `TestExpandAreaTreasurePlacement`: Integration tests for expand_area()
- `TestGenerateSubgridTreasurePlacement`: Integration tests for generate_subgrid_for_location()

## Treasure Schema

Treasures follow the existing schema from Location.treasures:
```python
{
    "name": "Iron Chest",
    "description": "An old chest left behind by previous adventurers.",
    "locked": True,
    "difficulty": 2,  # Scales with distance from entry
    "opened": False,
    "items": [
        {"name": "Ancient Blade", "item_type": "weapon", "damage_bonus": 4},
        {"name": "Health Potion", "item_type": "consumable", "heal_amount": 25}
    ],
    "requires_key": None
}
```

## Test Results

```
tests/test_ai_world_treasure.py: 28 passed
tests/test_ai_world*.py: 137 passed
Full test suite: 4312 passed
```

## Design Decisions

1. **Boss rooms excluded**: The boss itself is the reward, so no additional treasure in boss rooms
2. **Category-limited**: Only dungeons, caves, ruins, temples, and forests get treasures (not towns)
3. **Distance-based difficulty**: Harder locks further from entry encourages exploration
4. **Spread distribution**: Uses step-based selection to avoid clustering all treasures together
5. **Edge case handling**: Small areas (2 rooms with boss) correctly have no treasure candidates

## E2E Validation

To verify in-game:
1. Enter a dungeon/cave/ruins location
2. Navigate to non-entry, non-boss rooms
3. Look for treasure chests in those rooms
4. Verify chest names and items match the category theme
5. Verify lock difficulty increases with distance from entry
