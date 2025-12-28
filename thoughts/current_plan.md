# Implementation Plan: Rare Crafting Recipes as Rewards

## Overview
Add rare/advanced crafting recipes that are gated behind discovery (not available from the start). Recipes are unlocked through gameplay rewards: quest completions, treasure chests, and secret discoveries.

## Spec

### New Recipes (Rare/Discoverable)
1. **Elixir of Vitality** (Master-level consumable)
   - Ingredients: 2x Herbs, 1x Iron Ore
   - Effect: heal_amount=75 (superior to Healing Salve's 25)
   - Discovery: Quest reward or treasure chest

2. **Steel Blade** (Expert-level weapon)
   - Ingredients: 3x Iron Ore, 2x Wood
   - Effect: damage_bonus=8 (superior to Iron Sword's 5)
   - Discovery: Quest reward or secret discovery

3. **Fortified Armor** (Expert-level armor)
   - Ingredients: 4x Iron Ore, 2x Fiber
   - Effect: defense_bonus=6 (superior to Iron Armor's 4)
   - Discovery: Treasure chest or secret discovery

### Data Model Changes
- Add `unlocked_recipes: Set[str]` to `Character` model (default: empty set)
- Add `RARE_RECIPES` dict to `crafting.py` (separate from `CRAFTING_RECIPES`)
- Add `RARE_RECIPE_LEVEL: Dict[str, CraftingLevel]` for level requirements

### Recipe Unlock Sources
1. **Quest completion** - Add rare recipe names to `quest.item_rewards`
2. **Treasure chests** - Add recipe items to chest loot tables in `content_layer.py`/`fallback_content.py`
3. **Secret discovery** - Add to `secrets.py` treasure rewards

### UI/UX
- `recipes` command shows two sections: "Available Recipes" and "Discovered Rare Recipes"
- Attempting to craft an undiscovered recipe shows: "You don't know this recipe. It must be discovered."
- Recipe discovery shows: "You learned a rare recipe: {name}!"

---

## Test Plan

### File: `tests/test_crafting.py` (add to existing)

```python
# Tests for rare recipe discovery system

def test_rare_recipes_not_in_base_recipes():
    """Rare recipes should be in RARE_RECIPES, not CRAFTING_RECIPES."""

def test_character_has_unlocked_recipes():
    """Character should have unlocked_recipes set (default empty)."""

def test_craft_fails_for_undiscovered_rare_recipe():
    """Crafting rare recipe without unlocking should fail with appropriate message."""

def test_craft_succeeds_after_unlocking_recipe():
    """Crafting rare recipe should work after unlock_recipe() is called."""

def test_unlock_recipe_adds_to_set():
    """unlock_recipe() should add recipe key to unlocked_recipes."""

def test_recipes_list_shows_rare_section():
    """get_recipes_list() should show discovered rare recipes separately."""

def test_rare_recipe_serialization():
    """unlocked_recipes should serialize/deserialize correctly."""

def test_rare_recipes_require_expert_level():
    """Steel Blade and Fortified Armor require EXPERT level."""
```

---

## Implementation Steps

### Step 1: Update `Character` model (`src/cli_rpg/models/character.py`)
- Add `unlocked_recipes: Set[str] = field(default_factory=set)` field
- Add `unlock_recipe(recipe_key: str) -> str` method
- Add `has_recipe(recipe_key: str) -> bool` method
- Update `to_dict()` to serialize `unlocked_recipes` as list
- Update `from_dict()` to deserialize `unlocked_recipes`

### Step 2: Update `crafting.py` (`src/cli_rpg/crafting.py`)
- Add `RARE_RECIPES` dict with 3 rare recipes
- Add `RARE_RECIPE_LEVEL` dict with level requirements (EXPERT for advanced)
- Update `execute_craft()` to check `RARE_RECIPES` and require unlock
- Update `get_recipes_list()` to show discovered rare recipes section

### Step 3: Add recipe rewards to existing systems

#### 3a: Treasure chests (`src/cli_rpg/fallback_content.py`)
- Add recipe items to `TREASURE_LOOT_TABLES` with low probability
- Recipe items have `item_type=MISC` and special `is_recipe=True` flag

#### 3b: Quest rewards (`src/cli_rpg/models/quest.py`)
- No model changes needed - just use existing `item_rewards` field
- Quest givers can include "Recipe: Steel Blade" in rewards

#### 3c: Secret discovery (`src/cli_rpg/secrets.py`)
- Add recipe drops to `_apply_treasure_reward()` logic
- Check for recipe items and call character.unlock_recipe()

### Step 4: Handle recipe item usage (`src/cli_rpg/main.py`)
- When player uses/obtains a recipe item (name starts with "Recipe:"):
  - Auto-unlock the recipe via `character.unlock_recipe()`
  - Show discovery message
  - Remove the recipe item from inventory (it's "learned")

### Step 5: Write tests (`tests/test_crafting.py`)
- Add tests for rare recipe discovery and gating

---

## Files Modified
1. `src/cli_rpg/models/character.py` - Add unlocked_recipes field and methods
2. `src/cli_rpg/crafting.py` - Add RARE_RECIPES and update craft/list logic
3. `src/cli_rpg/fallback_content.py` - Add recipe items to treasure loot
4. `src/cli_rpg/secrets.py` - Add recipe rewards to treasure secrets
5. `src/cli_rpg/main.py` - Handle recipe item auto-learning on pickup/open
6. `tests/test_crafting.py` - Add rare recipe tests
