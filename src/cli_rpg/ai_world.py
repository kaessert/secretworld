"""AI-powered world generation module."""

import logging
from typing import Optional
from cli_rpg.ai_service import AIService, AIServiceError
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.world_grid import WorldGrid, DIRECTION_OFFSETS


# Set up logging
logger = logging.getLogger(__name__)


def get_opposite_direction(direction: str) -> str:
    """Get the opposite direction.
    
    Args:
        direction: A valid direction (north, south, east, west, up, down)
    
    Returns:
        The opposite direction
    
    Raises:
        ValueError: If direction is invalid
    """
    opposites = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
        "up": "down",
        "down": "up"
    }
    
    if direction not in opposites:
        raise ValueError(f"Invalid direction: {direction}")
    
    return opposites[direction]


def create_ai_world(
    ai_service: AIService,
    theme: str = "fantasy",
    starting_location_name: str = "Town Square",
    initial_size: int = 3
) -> tuple[dict[str, Location], str]:
    """Create an AI-generated world using grid-based placement.

    Args:
        ai_service: AIService instance for generating locations
        theme: World theme (e.g., "fantasy", "sci-fi")
        starting_location_name: Name for the starting location
        initial_size: Target number of locations to generate

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: Actual name of the starting location (may differ from parameter)

    Raises:
        AIServiceError: If generation fails
        ValueError: If generated locations fail validation
    """
    grid = WorldGrid()

    # Track coordinates for each location we place
    coord_queue = []  # List of (name, x, y, direction, suggested_target)

    # Generate starting location
    logger.info(f"Generating starting location: {starting_location_name}")
    starting_data = ai_service.generate_location(
        theme=theme,
        context_locations=[],
        source_location=None,
        direction=None
    )

    # Create starting location at origin (0, 0)
    starting_location = Location(
        name=starting_data["name"],
        description=starting_data["description"],
        connections={}  # WorldGrid will add connections
    )
    grid.add_location(starting_location, 0, 0)

    # Add default merchant NPC to starting location for shop access
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
    starting_location.npcs.append(merchant)

    # Queue connections to explore
    for direction, target_name in starting_data["connections"].items():
        if direction in DIRECTION_OFFSETS:
            dx, dy = DIRECTION_OFFSETS[direction]
            coord_queue.append((starting_location.name, 0 + dx, 0 + dy, direction, target_name))

    # Generate connected locations up to initial_size
    generated_count = 1
    attempts = 0
    max_attempts = initial_size * 3  # Prevent infinite loops

    while generated_count < initial_size and coord_queue and attempts < max_attempts:
        attempts += 1

        # Get next position to generate
        source_name, target_x, target_y, direction, suggested_name = coord_queue.pop(0)

        # Skip if position already occupied
        if grid.get_by_coordinates(target_x, target_y) is not None:
            continue

        # Skip if name already exists
        if suggested_name in grid:
            continue

        # Skip if direction is invalid for grid
        if direction not in DIRECTION_OFFSETS:
            logger.warning(f"Skipping non-grid direction: {direction}")
            continue

        try:
            # Generate new location
            logger.info(f"Generating location at ({target_x}, {target_y}) from {source_name}")
            location_data = ai_service.generate_location(
                theme=theme,
                context_locations=list(grid.keys()),
                source_location=source_name,
                direction=direction
            )

            # Create location
            new_location = Location(
                name=location_data["name"],
                description=location_data["description"],
                connections={}
            )

            # Add to grid if name is unique (WorldGrid handles connections)
            if new_location.name not in grid:
                grid.add_location(new_location, target_x, target_y)
                generated_count += 1

                # Queue suggested connections from new location
                opposite = get_opposite_direction(direction)
                for new_dir, new_target in location_data["connections"].items():
                    if new_dir != opposite and new_dir in DIRECTION_OFFSETS:
                        dx, dy = DIRECTION_OFFSETS[new_dir]
                        coord_queue.append((new_location.name, target_x + dx, target_y + dy, new_dir, new_target))
            else:
                logger.warning(f"Duplicate location name generated: {new_location.name}")

        except Exception as e:
            logger.warning(f"Failed to generate location: {e}")
            continue

    logger.info(f"Generated world with {len(grid)} locations")

    # Ensure all locations have at least one dangling exit for future expansion
    import random
    for loc_name, location in grid.items():
        # Find non-dangling connections (those pointing to existing locations in grid)
        back_connections = [d for d, target in location.connections.items() if target in grid]

        # If location only has back-connections, add a dangling exit
        if len(location.connections) <= len(back_connections):
            available_dirs = [d for d in Location.VALID_DIRECTIONS
                            if d not in location.connections]
            if available_dirs:
                dangling_dir = random.choice(available_dirs)
                placeholder_name = f"Unexplored {dangling_dir.title()}"
                location.add_connection(dangling_dir, placeholder_name)

    # Get the actual starting location name (first generated location)
    actual_starting_location = starting_location.name

    return (grid.as_dict(), actual_starting_location)


def expand_world(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str,
    target_coords: Optional[tuple[int, int]] = None
) -> dict[str, Location]:
    """Expand world by generating a new location.

    Args:
        world: Existing world dictionary
        ai_service: AIService instance
        from_location: Source location name
        direction: Direction to expand in
        theme: World theme
        target_coords: Optional target coordinates for the new location.
                       If provided, the new location will be placed at these
                       coordinates. Otherwise, coordinates are calculated from
                       the source location.

    Returns:
        Updated world dictionary (same object, modified in place)

    Raises:
        ValueError: If source location not found or direction invalid
        AIServiceError: If generation fails
    """
    # Validate inputs
    if from_location not in world:
        raise ValueError(f"Location '{from_location}' not found in world")

    if direction not in Location.VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid direction '{direction}'. Must be one of: "
            f"{', '.join(sorted(Location.VALID_DIRECTIONS))}"
        )

    # Generate new location
    logger.info(f"Expanding world: {direction} from {from_location}")
    location_data = ai_service.generate_location(
        theme=theme,
        context_locations=list(world.keys()),
        source_location=from_location,
        direction=direction
    )

    # Determine coordinates for the new location
    source_loc = world[from_location]
    if target_coords is not None:
        # Use explicitly provided target coordinates
        new_coordinates = target_coords
    elif source_loc.coordinates is not None and direction in DIRECTION_OFFSETS:
        # Calculate from source location
        dx, dy = DIRECTION_OFFSETS[direction]
        new_coordinates = (source_loc.coordinates[0] + dx, source_loc.coordinates[1] + dy)
    else:
        new_coordinates = None

    # Create new location with coordinates
    new_location = Location(
        name=location_data["name"],
        description=location_data["description"],
        connections={},
        coordinates=new_coordinates
    )

    # Add to world
    world[new_location.name] = new_location

    # Add bidirectional connections
    world[from_location].add_connection(direction, new_location.name)
    opposite = get_opposite_direction(direction)
    new_location.add_connection(opposite, from_location)

    # Add suggested dangling connections (keep them even if targets don't exist)
    for new_dir, target_name in location_data["connections"].items():
        if new_dir != opposite:  # Skip the back-connection we already added
            new_location.add_connection(new_dir, target_name)
            # Also add bidirectional connection if target exists
            if target_name in world:
                rev_dir = get_opposite_direction(new_dir)
                if not world[target_name].has_connection(rev_dir):
                    world[target_name].add_connection(rev_dir, new_location.name)

    # Ensure at least one dangling connection for future expansion
    non_back_connections = [d for d in new_location.connections if d != opposite]
    if not non_back_connections:
        import random
        available_dirs = [d for d in Location.VALID_DIRECTIONS
                         if d not in new_location.connections]
        if available_dirs:
            dangling_dir = random.choice(available_dirs)
            placeholder_name = f"Unexplored {dangling_dir.title()}"
            new_location.add_connection(dangling_dir, placeholder_name)

    logger.info(f"Added location '{new_location.name}' to world")
    return world


def create_world_with_fallback(
    ai_service: Optional[AIService] = None,
    theme: str = "fantasy"
) -> tuple[dict[str, Location], str]:
    """Create world with AI or raise exception.

    Note: This function is deprecated. Use create_ai_world directly
    and handle fallback in the caller.

    Args:
        ai_service: Optional AIService instance
        theme: World theme

    Returns:
        Tuple of (world, starting_location)

    Raises:
        ValueError: If ai_service is None
        AIServiceError: If generation fails
    """
    if ai_service is None:
        raise ValueError("AI service is required")

    logger.info("Attempting to create AI-generated world")
    return create_ai_world(ai_service, theme=theme)
