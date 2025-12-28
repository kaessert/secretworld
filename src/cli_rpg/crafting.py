"""Crafting and resource gathering system.

Provides the gather command for collecting resources from wilderness and cave areas.
"""

import random
from typing import TYPE_CHECKING, Dict, Tuple

from cli_rpg.models.crafting_proficiency import CraftingLevel
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.location import Location

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


# =============================================================================
# Constants
# =============================================================================

# Location categories where gathering is allowed
GATHERABLE_CATEGORIES = {"forest", "wilderness", "cave", "dungeon", "ruins"}

# Gather mechanics (same pattern as forage)
GATHER_BASE_CHANCE = 40  # Base 40% success
GATHER_PER_BONUS = 2  # +2% per perception
GATHER_COOLDOWN = 1  # 1 hour cooldown
GATHER_TIME_HOURS = 1  # Advances 1 hour


# =============================================================================
# Resource templates by location category
# =============================================================================

RESOURCE_BY_CATEGORY = {
    "forest": [
        {
            "name": "Wood",
            "description": "A sturdy branch, suitable for crafting handles and tools.",
            "resource_type": "wood",
        },
        {
            "name": "Fiber",
            "description": "Plant fibers that can be woven into rope or cloth.",
            "resource_type": "fiber",
        },
    ],
    "wilderness": [
        {
            "name": "Stone",
            "description": "A chunk of rock suitable for crafting or construction.",
            "resource_type": "stone",
        },
        {
            "name": "Fiber",
            "description": "Plant fibers that can be woven into rope or cloth.",
            "resource_type": "fiber",
        },
    ],
    "cave": [
        {
            "name": "Iron Ore",
            "description": "Raw iron ore, valuable for smithing weapons and armor.",
            "resource_type": "ore",
        },
        {
            "name": "Stone",
            "description": "A chunk of rock suitable for crafting or construction.",
            "resource_type": "stone",
        },
    ],
    "dungeon": [
        {
            "name": "Iron Ore",
            "description": "Raw iron ore, valuable for smithing weapons and armor.",
            "resource_type": "ore",
        },
        {
            "name": "Stone",
            "description": "A chunk of rock suitable for crafting or construction.",
            "resource_type": "stone",
        },
    ],
    "ruins": [
        {
            "name": "Stone",
            "description": "Ancient masonry, perfect for construction materials.",
            "resource_type": "stone",
        },
        {
            "name": "Iron Ore",
            "description": "Rusted ore deposits found among the ruins.",
            "resource_type": "ore",
        },
    ],
}

# =============================================================================
# Crafting recipes
# =============================================================================

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
}

# =============================================================================
# Recipe level requirements
# =============================================================================

# Minimum crafting level required for each recipe
# Recipes not listed default to NOVICE (no requirement)
RECIPE_MIN_LEVEL: Dict[str, CraftingLevel] = {
    "iron sword": CraftingLevel.JOURNEYMAN,
    "iron armor": CraftingLevel.JOURNEYMAN,
}

# XP gained per successful craft
CRAFT_XP_GAIN = 5


# =============================================================================
# Rare crafting recipes (must be discovered/unlocked)
# =============================================================================

RARE_RECIPES = {
    "elixir of vitality": {
        "name": "Elixir of Vitality",
        "ingredients": {"Herbs": 2, "Iron Ore": 1},
        "output": {
            "name": "Elixir of Vitality",
            "description": "A powerful healing elixir that restores vitality.",
            "item_type": ItemType.CONSUMABLE,
            "heal_amount": 75,
        },
    },
    "steel blade": {
        "name": "Steel Blade",
        "ingredients": {"Iron Ore": 3, "Wood": 2},
        "output": {
            "name": "Steel Blade",
            "description": "A finely crafted steel blade, superior to common iron.",
            "item_type": ItemType.WEAPON,
            "damage_bonus": 8,
        },
    },
    "fortified armor": {
        "name": "Fortified Armor",
        "ingredients": {"Iron Ore": 4, "Fiber": 2},
        "output": {
            "name": "Fortified Armor",
            "description": "Reinforced armor offering exceptional protection.",
            "item_type": ItemType.ARMOR,
            "defense_bonus": 6,
        },
    },
}

# Minimum crafting level required for rare recipes
RARE_RECIPE_LEVEL: Dict[str, CraftingLevel] = {
    "elixir of vitality": CraftingLevel.MASTER,
    "steel blade": CraftingLevel.EXPERT,
    "fortified armor": CraftingLevel.EXPERT,
}


# =============================================================================
# Helper functions
# =============================================================================

def is_gatherable_location(location: Location) -> bool:
    """Check if a location is suitable for resource gathering.

    Gathering is allowed in wilderness/forest/cave/dungeon/ruins areas
    but NOT in safe zones (towns, villages).

    Args:
        location: The location to check

    Returns:
        True if gathering is allowed, False otherwise
    """
    if location.is_safe_zone:
        return False

    category = location.category or ""
    return category.lower() in GATHERABLE_CATEGORIES


def _generate_resource_item(category: str) -> Item:
    """Generate a random resource item based on location category.

    Args:
        category: The location category (forest, cave, etc.)

    Returns:
        An Item instance representing the gathered resource
    """
    category = category.lower()

    # Get resources for this category, default to wilderness if unknown
    available = RESOURCE_BY_CATEGORY.get(category, RESOURCE_BY_CATEGORY["wilderness"])

    # Random selection (equal weight for now)
    chosen = random.choice(available)

    return Item(
        name=chosen["name"],
        description=chosen["description"],
        item_type=ItemType.RESOURCE,
    )


# =============================================================================
# Main command function
# =============================================================================

def execute_gather(game_state: "GameState") -> Tuple[bool, str]:
    """Execute the gather command.

    Search the area for resources like wood, fiber, ore, and stone.
    Success chance based on perception. Has a 1-hour cooldown.

    Args:
        game_state: The current game state

    Returns:
        Tuple of (success, message)
    """
    location = game_state.get_current_location()
    character = game_state.current_character

    # Check location suitability
    if not is_gatherable_location(location):
        if location.is_safe_zone:
            return (False, "You can't gather here. Visit the wilderness or caves instead.")
        category = location.category or "this area"
        return (False, f"You can't gather in {category}. Find a forest, cave, or wilderness.")

    # Check cooldown
    if game_state.gather_cooldown > 0:
        return (False, f"You've recently gathered. Wait {game_state.gather_cooldown} hour(s).")

    # Calculate success chance
    success_chance = GATHER_BASE_CHANCE + (character.perception * GATHER_PER_BONUS)
    success_chance = min(95, success_chance)  # Cap at 95%

    # Advance time (always, whether success or failure)
    game_state.game_time.advance(GATHER_TIME_HOURS)

    # Set cooldown
    game_state.gather_cooldown = GATHER_COOLDOWN

    # Roll for success
    roll = random.random() * 100
    if roll < success_chance:
        # Success - find resource
        item = _generate_resource_item(location.category or "wilderness")

        if character.inventory.is_full():
            return (True, f"You found {item.name}, but your inventory is full!")

        character.inventory.add_item(item)
        return (True, f"You search the area and found {item.name}!")
    else:
        # Failure
        return (True, "You search but find nothing useful.")


# =============================================================================
# Crafting command functions
# =============================================================================


def get_recipes_list(character: "Character" = None) -> str:
    """Return formatted list of available crafting recipes.

    Args:
        character: Optional character to show unlocked rare recipes for

    Returns:
        Formatted string with all recipes and their ingredients
    """
    from cli_rpg.models.character import Character

    lines = ["Available Crafting Recipes:", "=" * 30]
    for key, recipe in CRAFTING_RECIPES.items():
        ingredients = ", ".join(
            f"{count}x {name}" for name, count in recipe["ingredients"].items()
        )
        lines.append(f"  {recipe['name']}: {ingredients}")

    # Show discovered rare recipes if character provided
    if character is not None:
        unlocked = [
            key for key in RARE_RECIPES.keys()
            if character.has_recipe(key)
        ]
        if unlocked:
            lines.append("")
            lines.append("Discovered Rare Recipes:")
            lines.append("=" * 30)
            for key in unlocked:
                recipe = RARE_RECIPES[key]
                ingredients = ", ".join(
                    f"{count}x {name}" for name, count in recipe["ingredients"].items()
                )
                lines.append(f"  {recipe['name']}: {ingredients}")

    return "\n".join(lines)


def execute_craft(game_state: "GameState", recipe_name: str) -> Tuple[bool, str]:
    """Execute the craft command.

    Combines gathered resources into useful items according to recipes.

    Args:
        game_state: The current game state
        recipe_name: Name of the recipe to craft (case-insensitive)

    Returns:
        Tuple of (success, message)
    """
    # 1. Lookup recipe (case-insensitive)
    recipe_key = recipe_name.lower()
    character = game_state.current_character
    inventory = character.inventory

    # Check if it's a rare recipe
    is_rare = recipe_key in RARE_RECIPES

    if is_rare:
        # Check if the rare recipe is unlocked
        if not character.has_recipe(recipe_key):
            return (
                False,
                f"You don't know this recipe. It must be discovered through "
                "quests, treasure, or secrets.",
            )
        recipe = RARE_RECIPES[recipe_key]
        required_level = RARE_RECIPE_LEVEL.get(recipe_key, CraftingLevel.NOVICE)
    elif recipe_key in CRAFTING_RECIPES:
        recipe = CRAFTING_RECIPES[recipe_key]
        required_level = RECIPE_MIN_LEVEL.get(recipe_key, CraftingLevel.NOVICE)
    else:
        return (False, f"Unknown recipe: {recipe_name}. Use 'recipes' to see available recipes.")

    # 2. Check crafting level requirement
    current_level = character.crafting_proficiency.get_level()

    # Compare levels by their XP thresholds
    from cli_rpg.models.crafting_proficiency import LEVEL_THRESHOLDS

    if LEVEL_THRESHOLDS[current_level] < LEVEL_THRESHOLDS[required_level]:
        return (
            False,
            f"This recipe requires {required_level.value} crafting level. "
            f"(Current: {current_level.value})",
        )

    # 3. Check all ingredients present
    missing = []
    for ingredient_name, required_count in recipe["ingredients"].items():
        # Count matching items in inventory
        count = sum(1 for item in inventory.items if item.name == ingredient_name)
        if count < required_count:
            missing.append(f"{required_count - count}x {ingredient_name}")

    if missing:
        return (False, f"Missing ingredients: {', '.join(missing)}")

    # 4. Check inventory not full (we'll remove N ingredients and add 1 item)
    # Net change = 1 - len(ingredients), so only full if net positive and full
    ingredient_count = sum(recipe["ingredients"].values())
    if ingredient_count <= 1 and inventory.is_full():
        return (False, "Your inventory is full.")

    # 5. Remove ingredients
    for ingredient_name, required_count in recipe["ingredients"].items():
        for _ in range(required_count):
            item = inventory.find_item_by_name(ingredient_name)
            inventory.remove_item(item)

    # 6. Create and add output item
    output_data = recipe["output"]
    crafted_item = Item(
        name=output_data["name"],
        description=output_data["description"],
        item_type=output_data["item_type"],
        damage_bonus=output_data.get("damage_bonus", 0),
        defense_bonus=output_data.get("defense_bonus", 0),
        heal_amount=output_data.get("heal_amount", 0),
        light_duration=output_data.get("light_duration", 0),
    )
    inventory.add_item(crafted_item)

    # 7. Grant crafting XP
    levelup_msg = character.crafting_proficiency.gain_xp(CRAFT_XP_GAIN)

    # 8. Build result message
    result_msg = f"Crafted {crafted_item.name}!"
    if levelup_msg:
        result_msg += f"\n{levelup_msg}"

    return (True, result_msg)
