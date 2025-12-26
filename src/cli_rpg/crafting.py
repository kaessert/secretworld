"""Crafting and resource gathering system.

Provides the gather command for collecting resources from wilderness and cave areas.
"""

import random
from typing import TYPE_CHECKING, Tuple

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
