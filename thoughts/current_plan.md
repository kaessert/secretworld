# Crafting Recipes Implementation Plan

## Feature Spec

Add a `craft` command that allows players to combine gathered resources (Wood, Fiber, Iron Ore, Stone) into useful items. The system should:

1. Accept `craft <recipe>` command (alias: `cr`)
2. Check player has required resources in inventory
3. Consume resources and produce the crafted item
4. Provide `recipes` command to list available recipes

### Initial Recipes
| Recipe | Ingredients | Output |
|--------|-------------|--------|
| Torch | 1 Wood + 1 Fiber | Torch (light source, 10 moves) |
| Iron Sword | 2 Iron Ore + 1 Wood | Iron Sword (+5 damage weapon) |
| Iron Armor | 3 Iron Ore + 1 Fiber | Iron Armor (+4 defense armor) |
| Rope | 2 Fiber | Rope (misc item, quest/puzzle use) |
| Stone Hammer | 2 Stone + 1 Wood | Stone Hammer (+3 damage weapon) |

---

## Implementation Steps

### 1. Add recipe definitions to `crafting.py`

**File:** `src/cli_rpg/crafting.py`

Add after `RESOURCE_BY_CATEGORY` constant (~line 95):
```python
CRAFTING_RECIPES = {
    "torch": {
        "name": "Torch",
        "ingredients": {"Wood": 1, "Fiber": 1},
        "output": {
            "name": "Torch",
            "description": "A wooden torch that provides light in dark places.",
            "item_type": ItemType.CONSUMABLE,
            "light_duration": 10,
        },
    },
    "iron sword": {
        "name": "Iron Sword",
        "ingredients": {"Iron Ore": 2, "Wood": 1},
        "output": {
            "name": "Iron Sword",
            "description": "A sturdy sword forged from iron ore.",
            "item_type": ItemType.WEAPON,
            "damage_bonus": 5,
        },
    },
    "iron armor": {
        "name": "Iron Armor",
        "ingredients": {"Iron Ore": 3, "Fiber": 1},
        "output": {
            "name": "Iron Armor",
            "description": "Protective armor crafted from iron plates.",
            "item_type": ItemType.ARMOR,
            "defense_bonus": 4,
        },
    },
    "rope": {
        "name": "Rope",
        "ingredients": {"Fiber": 2},
        "output": {
            "name": "Rope",
            "description": "A sturdy rope woven from plant fibers.",
            "item_type": ItemType.MISC,
        },
    },
    "stone hammer": {
        "name": "Stone Hammer",
        "ingredients": {"Stone": 2, "Wood": 1},
        "output": {
            "name": "Stone Hammer",
            "description": "A crude but effective hammer made from stone.",
            "item_type": ItemType.WEAPON,
            "damage_bonus": 3,
        },
    },
}
```

### 2. Add crafting functions to `crafting.py`

**File:** `src/cli_rpg/crafting.py`

Add after `execute_gather` function:

```python
def get_recipes_list() -> str:
    """Return formatted list of available crafting recipes."""
    lines = ["Available Crafting Recipes:", "=" * 30]
    for key, recipe in CRAFTING_RECIPES.items():
        ingredients = ", ".join(f"{count}x {name}" for name, count in recipe["ingredients"].items())
        lines.append(f"  {recipe['name']}: {ingredients}")
    return "\n".join(lines)


def execute_craft(game_state: "GameState", recipe_name: str) -> Tuple[bool, str]:
    """Execute the craft command."""
    # 1. Lookup recipe (case-insensitive)
    recipe_key = recipe_name.lower()
    if recipe_key not in CRAFTING_RECIPES:
        return (False, f"Unknown recipe: {recipe_name}. Use 'recipes' to see available recipes.")

    recipe = CRAFTING_RECIPES[recipe_key]
    inventory = game_state.current_character.inventory

    # 2. Check all ingredients present
    missing = []
    for ingredient_name, required_count in recipe["ingredients"].items():
        # Count matching items in inventory
        count = sum(1 for item in inventory.items if item.name == ingredient_name)
        if count < required_count:
            missing.append(f"{required_count - count}x {ingredient_name}")

    if missing:
        return (False, f"Missing ingredients: {', '.join(missing)}")

    # 3. Check inventory not full
    if inventory.is_full():
        return (False, "Your inventory is full.")

    # 4. Remove ingredients
    for ingredient_name, required_count in recipe["ingredients"].items():
        for _ in range(required_count):
            item = inventory.find_item_by_name(ingredient_name)
            inventory.remove_item(item)

    # 5. Create and add output item
    output_data = recipe["output"]
    crafted_item = Item(
        name=output_data["name"],
        description=output_data["description"],
        item_type=output_data["item_type"],
        damage_bonus=output_data.get("damage_bonus", 0),
        defense_bonus=output_data.get("defense_bonus", 0),
        light_duration=output_data.get("light_duration", 0),
    )
    inventory.add_item(crafted_item)

    return (True, f"Crafted {crafted_item.name}!")
```

### 3. Register commands in `game_state.py`

**File:** `src/cli_rpg/game_state.py`

- Add `"craft"`, `"recipes"` to `KNOWN_COMMANDS` set (line ~52-66)
- Add alias `"cr": "craft"` to aliases dict (line ~121-140)

### 4. Add command routing in `main.py`

**File:** `src/cli_rpg/main.py`

After the `elif command == "gather":` block (~line 2162-2165), add:
```python
elif command == "craft":
    from cli_rpg.crafting import execute_craft
    if not args:
        return (True, "\nCraft what? Use 'recipes' to see available recipes.")
    recipe_name = " ".join(args)
    success, msg = execute_craft(game_state, recipe_name)
    return (True, f"\n{msg}")

elif command == "recipes":
    from cli_rpg.crafting import get_recipes_list
    return (True, f"\n{get_recipes_list()}")
```

### 5. Update help text in `main.py`

**File:** `src/cli_rpg/main.py`

In `get_command_reference()` (~line 58), add after `gather` line:
```python
"  craft (cr) <recipe> - Craft an item from gathered resources",
"  recipes             - List available crafting recipes",
```

---

## Test Plan

**File:** `tests/test_crafting.py`

Add tests after existing gather tests (~line 280):

### Recipe existence tests
- `test_torch_recipe_exists` - Verify torch recipe defined with correct ingredients
- `test_iron_sword_recipe_exists` - Verify iron sword recipe defined

### Crafting success tests
- `test_craft_torch_consumes_ingredients` - Craft torch, verify Wood/Fiber removed
- `test_craft_adds_item_to_inventory` - Verify crafted item added with correct type
- `test_craft_torch_has_light_duration` - Torch item has light_duration=10

### Crafting failure tests
- `test_craft_fails_missing_ingredients` - Error when missing all resources
- `test_craft_fails_partial_ingredients` - Error when only some resources present
- `test_craft_fails_unknown_recipe` - Error for invalid recipe name
- `test_craft_fails_inventory_full` - Error when no room for output

### Recipe list test
- `test_recipes_list_shows_all_recipes` - Verify get_recipes_list() output contains all recipes
