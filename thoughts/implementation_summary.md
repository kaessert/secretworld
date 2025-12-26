# Implementation Summary: Crafting Recipes Feature

## What Was Implemented

### New Commands
1. **`craft <recipe>` command** (alias: `cr`) - Combines gathered resources into useful items
2. **`recipes` command** - Lists all available crafting recipes with their ingredients

### Crafting Recipes Added
| Recipe | Ingredients | Output |
|--------|-------------|--------|
| Torch | 1 Wood + 1 Fiber | Torch (consumable, 10 moves of light) |
| Iron Sword | 2 Iron Ore + 1 Wood | Iron Sword (weapon, +5 damage) |
| Iron Armor | 3 Iron Ore + 1 Fiber | Iron Armor (armor, +4 defense) |
| Rope | 2 Fiber | Rope (misc item) |
| Stone Hammer | 2 Stone + 1 Wood | Stone Hammer (weapon, +3 damage) |
| **Healing Salve** | 2 Herbs | Healing Salve (consumable, heals 25 HP) |
| **Bandage** | 2 Fiber | Bandage (consumable, heals 15 HP) |
| **Wooden Shield** | 2 Wood + 1 Fiber | Wooden Shield (armor, +2 defense) |

## Latest Changes (New Recipes)

Added 3 new recipes that leverage foraged/gathered resources:

1. **Healing Salve** - Combines 2 Herbs into a consumable that heals 25 HP
2. **Bandage** - Combines 2 Fiber into a consumable that heals 15 HP
3. **Wooden Shield** - Combines 2 Wood + 1 Fiber into armor with +2 defense

Also fixed `execute_craft()` to include `heal_amount` parameter when creating items.

## Files Modified

### src/cli_rpg/crafting.py
- Added `CRAFTING_RECIPES` dictionary defining all 8 recipes
- Added 3 new recipes: healing salve, bandage, wooden shield (lines 151-180)
- Fixed `execute_craft()` to include `heal_amount` in Item creation (line 358)
- Added `get_recipes_list()` function - displays available recipes
- Added `execute_craft()` function:
  - Case-insensitive recipe lookup
  - Ingredient verification with specific missing item feedback
  - Smart inventory space check (accounts for ingredients being consumed)
  - Consumes ingredients and creates output item

### src/cli_rpg/game_state.py
- Added `"craft"` and `"recipes"` to `KNOWN_COMMANDS` set
- Added `"cr": "craft"` alias

### src/cli_rpg/main.py
- Added command routing for `craft` and `recipes` commands
- Updated help text with craft and recipes commands

## Tests Added (tests/test_crafting.py)

14 tests for crafting recipes including 4 new tests:
1. `test_torch_recipe_exists` - Verifies torch recipe structure
2. `test_iron_sword_recipe_exists` - Verifies iron sword recipe structure
3. `test_craft_torch_consumes_ingredients` - Ingredients removed on craft
4. `test_craft_adds_item_to_inventory` - Output item added correctly
5. `test_craft_torch_has_light_duration` - Torch has correct properties
6. `test_craft_fails_missing_ingredients` - Error when missing all ingredients
7. `test_craft_fails_partial_ingredients` - Error when only some ingredients present
8. `test_craft_fails_unknown_recipe` - Error for invalid recipe names
9. `test_craft_succeeds_when_ingredients_free_space` - Smart inventory check works
10. `test_recipes_list_shows_all_recipes` - All recipes displayed
11. **`test_healing_salve_recipe_exists`** - Verifies healing salve recipe (2 Herbs -> 25 HP)
12. **`test_bandage_recipe_exists`** - Verifies bandage recipe (2 Fiber -> 15 HP)
13. **`test_wooden_shield_recipe_exists`** - Verifies wooden shield recipe (2 Wood + 1 Fiber -> +2 defense)
14. **`test_craft_healing_salve_works`** - End-to-end test for crafting healing salve

## Test Results

- All 25 crafting tests pass
- No regressions introduced

## Design Decisions

1. **Case-insensitive recipes**: `craft torch`, `craft TORCH`, `craft Torch` all work
2. **Smart inventory check**: Accounts for ingredients being consumed (2->1 crafts work even at full inventory)
3. **Specific error messages**: Tells player exactly which ingredients are missing
4. **Item properties preserved**: Crafted items have correct damage_bonus, defense_bonus, heal_amount, light_duration

## E2E Tests Should Validate

1. Use `recipes` command to view available recipes
2. Gather Wood and Fiber in forest, then `craft torch`
3. Verify torch appears in inventory with light_duration=10
4. Try `craft iron sword` without enough Iron Ore to see error message
5. Use `cr` alias for craft command
6. Craft when inventory nearly full to verify smart space check
7. **Forage Herbs, then `craft healing salve` and use it to heal**
8. **Gather Fiber, then `craft bandage` and use it to heal**
9. **Gather Wood+Fiber, then `craft wooden shield` and equip it for +2 defense**
