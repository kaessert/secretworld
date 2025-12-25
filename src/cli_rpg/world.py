"""World module for creating and managing game locations."""

import logging
import random
from typing import Optional, Tuple
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.npc import NPC
from cli_rpg.world_grid import WorldGrid, OPPOSITE_DIRECTIONS

logger = logging.getLogger(__name__)


# Fallback location templates for when AI is unavailable
# Each template has a name pattern and descriptions based on direction
FALLBACK_LOCATION_TEMPLATES = [
    {
        "name_patterns": ["Wilderness", "Wild Plains", "Open Land", "Frontier"],
        "descriptions": [
            "An untamed wilderness stretches before you. The land here is wild and unexplored.",
            "Tall grass sways in the breeze across this open expanse. Few have traveled this way.",
            "The frontier beckons with promise of adventure. The path ahead is uncertain.",
        ]
    },
    {
        "name_patterns": ["Rocky Outcrop", "Stone Ridge", "Craggy Hills", "Boulder Field"],
        "descriptions": [
            "Large rocks and boulders dot the landscape. This terrain is rough but passable.",
            "A ridge of ancient stones rises from the earth. The rocks seem weathered by time.",
            "Craggy hills create an uneven terrain. Something about this place feels ancient.",
        ]
    },
    {
        "name_patterns": ["Misty Hollow", "Foggy Vale", "Shadowed Dell", "Dim Glade"],
        "descriptions": [
            "A mysterious mist hangs low over this hollow. Visibility is limited here.",
            "Shadows gather in this secluded dell. The air is cool and still.",
            "Fog drifts lazily through this vale. Sounds seem muffled and distant.",
        ]
    },
    {
        "name_patterns": ["Grassy Meadow", "Sunny Fields", "Rolling Hills", "Green Expanse"],
        "descriptions": [
            "A peaceful meadow extends in all directions. Wildflowers bloom among the grass.",
            "Rolling hills covered in lush grass create a gentle landscape.",
            "Sunlight warms this open field. It seems a good place to rest.",
        ]
    },
    {
        "name_patterns": ["Dense Thicket", "Tangled Woods", "Overgrown Path", "Wild Grove"],
        "descriptions": [
            "Thick vegetation crowds the path here. Branches reach out like grasping fingers.",
            "An overgrown grove where nature has reclaimed the land. Travel is slow but possible.",
            "Tangled underbrush makes movement difficult. This area sees few visitors.",
        ]
    },
]


def generate_fallback_location(
    direction: str,
    source_location: Location,
    target_coords: Tuple[int, int]
) -> Location:
    """Generate a fallback location when AI is unavailable.

    Creates a template-based location with appropriate name, description,
    coordinates, and connections. The generated location will always have
    at least one frontier exit for future expansion.

    Args:
        direction: The direction of travel from source (e.g., "north")
        source_location: The location the player is coming from
        target_coords: The (x, y) coordinates for the new location

    Returns:
        A new Location instance with proper connections
    """
    # Select a random template
    template = random.choice(FALLBACK_LOCATION_TEMPLATES)

    # Generate unique name with coordinate suffix to ensure uniqueness
    base_name = random.choice(template["name_patterns"])
    # Add coordinate suffix for uniqueness (e.g., "Wilderness (1, 2)")
    location_name = f"{base_name} ({target_coords[0]}, {target_coords[1]})"

    # Select random description
    description = random.choice(template["descriptions"])

    # Calculate back connection direction
    back_direction = OPPOSITE_DIRECTIONS[direction]

    # Create the new location
    new_location = Location(
        name=location_name,
        description=description,
        connections={back_direction: source_location.name},
        coordinates=target_coords
    )

    # Add at least one frontier exit for future expansion
    # Exclude the back direction and any direction that might conflict
    available_directions = [
        d for d in Location.VALID_DIRECTIONS
        if d != back_direction
    ]

    if available_directions:
        # Add 1-2 dangling exits for expansion
        num_exits = random.randint(1, min(2, len(available_directions)))
        chosen_exits = random.sample(available_directions, num_exits)
        for exit_dir in chosen_exits:
            placeholder_name = f"Unexplored {exit_dir.title()}"
            new_location.add_connection(exit_dir, placeholder_name)

    logger.info(f"Generated fallback location '{location_name}' at {target_coords}")
    return new_location


# Import AI components (optional)
try:
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_world import create_ai_world
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIService = None  # type: ignore[misc, assignment]
    create_ai_world = None  # type: ignore[assignment]


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
    torch = Item(
        name="Torch",
        description="A wooden torch that provides light in dark places",
        item_type=ItemType.CONSUMABLE,
        light_duration=5
    )

    shop_items = [
        ShopItem(item=potion, buy_price=50),
        ShopItem(item=sword, buy_price=100),
        ShopItem(item=armor, buy_price=80),
        ShopItem(item=torch, buy_price=15)
    ]
    shop = Shop(name="General Store", inventory=shop_items)
    merchant = NPC(
        name="Merchant",
        description="A friendly shopkeeper with various wares",
        dialogue="Welcome, traveler! Take a look at my goods.",
        is_merchant=True,
        shop=shop,
        greetings=[
            "Welcome, traveler! Take a look at my goods.",
            "Ah, a customer! What can I get for you today?",
            "Come in, come in! Best prices in town!",
        ]
    )

    # Add merchant to Town Square
    town_square.npcs.append(merchant)

    # Create Guard NPC for Town Square
    guard = NPC(
        name="Guard",
        description="A vigilant town guard keeping watch over the square",
        dialogue="Stay out of trouble, adventurer.",
        greetings=[
            "Stay out of trouble, adventurer.",
            "The roads have been dangerous lately.",
            "Keep your weapons sheathed in town.",
        ]
    )
    town_square.npcs.append(guard)

    # Return world dictionary and starting location (backward compatible)
    return (grid.as_dict(), "Town Square")


def create_world(
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy",
    strict: bool = True
) -> tuple[dict[str, Location], str]:
    """Create a game world, using AI if available.

    Args:
        ai_service: Optional AIService for AI-generated world
        theme: World theme (default: "fantasy")
        strict: If True (default), AI generation failures raise exceptions.
                If False, falls back to default world on AI error.

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: Name of the starting location in the world

    Raises:
        Exception: If strict=True and AI generation fails
    """
    if ai_service is not None and AI_AVAILABLE:
        if strict:
            # Strict mode: let exceptions propagate
            logger.info("Attempting to create AI-generated world (strict mode)")
            world, starting_location = create_ai_world(ai_service, theme=theme)
            return (world, starting_location)
        else:
            # Non-strict mode: fallback to default on error
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
