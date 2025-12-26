# Implementation Plan: Add New Crafting Recipes

## Spec

Add 3 new crafting recipes to `crafting.py` that leverage existing foraged/hunted resources:

1. **Healing Salve** - `{Herbs: 2}` → Consumable, heals 25 HP
2. **Bandage** - `{Fiber: 2}` → Consumable, heals 15 HP
3. **Wooden Shield** - `{Wood: 2, Fiber: 1}` → Armor, +2 defense

These recipes create a meaningful loop between foraging/gathering and crafting, making wilderness survival more valuable.

## Tests First

Add to `tests/test_crafting.py`:

```python
def test_healing_salve_recipe_exists():
    """Spec: healing salve recipe should exist (2 Herbs → 25 HP heal)."""
    from cli_rpg.crafting import CRAFTING_RECIPES
    assert "healing salve" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["healing salve"]
    assert recipe["ingredients"] == {"Herbs": 2}
    assert recipe["output"]["heal_amount"] == 25

def test_bandage_recipe_exists():
    """Spec: bandage recipe should exist (2 Fiber → 15 HP heal)."""
    from cli_rpg.crafting import CRAFTING_RECIPES
    assert "bandage" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["bandage"]
    assert recipe["ingredients"] == {"Fiber": 2}
    assert recipe["output"]["heal_amount"] == 15

def test_wooden_shield_recipe_exists():
    """Spec: wooden shield recipe should exist (2 Wood + 1 Fiber → +2 defense)."""
    from cli_rpg.crafting import CRAFTING_RECIPES
    assert "wooden shield" in CRAFTING_RECIPES
    recipe = CRAFTING_RECIPES["wooden shield"]
    assert recipe["ingredients"] == {"Wood": 2, "Fiber": 1}
    assert recipe["output"]["defense_bonus"] == 2

def test_craft_healing_salve_works():
    """Spec: crafting healing salve consumes 2 Herbs and creates salve."""
    from cli_rpg.crafting import execute_craft
    game_state = make_game_state()
    inv = game_state.current_character.inventory
    # Add 2 Herbs
    for _ in range(2):
        inv.add_item(Item(name="Herbs", description="Healing herbs", item_type=ItemType.CONSUMABLE, heal_amount=10))
    success, msg = execute_craft(game_state, "healing salve")
    assert success is True
    salve = inv.find_item_by_name("Healing Salve")
    assert salve is not None
    assert salve.heal_amount == 25
```

## Implementation

Edit `src/cli_rpg/crafting.py` - add 3 new entries to `CRAFTING_RECIPES` dict after `"stone hammer"` (line 150):

```python
"healing salve": {
    "name": "Healing Salve",
    "ingredients": {"Herbs": 2},
    "output": {
        "name": "Healing Salve",
        "description": "A soothing salve made from crushed healing herbs.",
        "item_type": ItemType.CONSUMABLE,
        "heal_amount": 25,
    },
},
"bandage": {
    "name": "Bandage",
    "ingredients": {"Fiber": 2},
    "output": {
        "name": "Bandage",
        "description": "A simple bandage woven from plant fibers.",
        "item_type": ItemType.CONSUMABLE,
        "heal_amount": 15,
    },
},
"wooden shield": {
    "name": "Wooden Shield",
    "ingredients": {"Wood": 2, "Fiber": 1},
    "output": {
        "name": "Wooden Shield",
        "description": "A sturdy wooden shield bound with fiber.",
        "item_type": ItemType.ARMOR,
        "defense_bonus": 2,
    },
},
```

## Verify

Run: `pytest tests/test_crafting.py -v`
