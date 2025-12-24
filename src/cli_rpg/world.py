"""World module for creating and managing game locations."""

import logging
from typing import Optional, Union
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.npc import NPC
from cli_rpg.world_grid import WorldGrid

logger = logging.getLogger(__name__)

# Import AI components (optional)
try:
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_world import create_ai_world
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIService = None
    create_ai_world = None


def create_default_world() -> tuple[dict[str, Location], str]:
    """Create and return the default game world with 3 locations.

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: "Town Square" (the default starting location)

    The default world consists of:
    - Town Square: Central hub at (0, 0) with connections north to Forest and east to Cave
    - Forest: Northern location at (0, 1) with connection south to Town Square
    - Cave: Eastern location at (1, 0) with connection west to Town Square
    """
    # Create WorldGrid for consistent spatial representation
    grid = WorldGrid()

    # Create locations (connections are automatically created by WorldGrid)
    town_square = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center. People go about their daily business."
    )

    forest = Location(
        name="Forest",
        description="A dense forest with tall trees blocking most of the sunlight. Strange sounds echo in the distance."
    )

    cave = Location(
        name="Cave",
        description="A dark cave with damp walls. You can hear water dripping somewhere deeper inside."
    )

    # Place locations on grid (coordinates determine connections automatically)
    # Town Square at origin (0, 0)
    grid.add_location(town_square, 0, 0)
    # Forest is north of Town Square (0, 1)
    grid.add_location(forest, 0, 1)
    # Cave is east of Town Square (1, 0)
    grid.add_location(cave, 1, 0)

    # Add dangling exits for world expansion
    forest.add_connection("north", "Deep Woods")
    cave.add_connection("east", "Crystal Cavern")

    # Create default merchant shop
    potion = Item(
        name="Health Potion",
        description="Restores 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25
    )
    sword = Item(
        name="Iron Sword",
        description="A sturdy blade",
        item_type=ItemType.WEAPON,
        damage_bonus=5
    )
    armor = Item(
        name="Leather Armor",
        description="Light protection",
        item_type=ItemType.ARMOR,
        defense_bonus=3
    )

    shop_items = [
        ShopItem(item=potion, buy_price=50),
        ShopItem(item=sword, buy_price=100),
        ShopItem(item=armor, buy_price=80)
    ]
    shop = Shop(name="General Store", inventory=shop_items)
    merchant = NPC(
        name="Merchant",
        description="A friendly shopkeeper with various wares",
        dialogue="Welcome, traveler! Take a look at my goods.",
        is_merchant=True,
        shop=shop
    )

    # Add merchant to Town Square
    town_square.npcs.append(merchant)

    # Return world dictionary and starting location (backward compatible)
    return (grid.as_dict(), "Town Square")


def create_world(
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy"
) -> tuple[dict[str, Location], str]:
    """Create a game world, using AI if available.

    Args:
        ai_service: Optional AIService for AI-generated world
        theme: World theme (default: "fantasy")

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: Name of the starting location in the world
    """
    if ai_service is not None and AI_AVAILABLE:
        # Use AI to create world with fallback to default on error
        try:
            logger.info("Attempting to create AI-generated world")
            world, starting_location = create_ai_world(ai_service, theme=theme)
            return (world, starting_location)
        except Exception as e:
            logger.warning(f"AI world generation failed: {e}")
            logger.info("Falling back to default world")
            world, starting_location = create_default_world()
            return (world, starting_location)
    else:
        # Use default world
        world, starting_location = create_default_world()
        return (world, starting_location)
