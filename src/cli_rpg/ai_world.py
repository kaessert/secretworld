"""AI-powered world generation module."""

import logging
from typing import Optional
from cli_rpg.ai_service import AIService
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.world_grid import WorldGrid, SubGrid, DIRECTION_OFFSETS
from cli_rpg.location_art import get_fallback_location_ascii_art


# Set up logging
logger = logging.getLogger(__name__)


# Safe zone categories (no random encounters)
SAFE_ZONE_CATEGORIES = {"town", "village", "settlement"}


def _infer_hierarchy_from_category(category: Optional[str]) -> tuple[bool, bool]:
    """Infer hierarchy fields from location category.

    Args:
        category: Location category (town, dungeon, forest, etc.)

    Returns:
        Tuple of (is_overworld, is_safe_zone):
        - is_overworld: True for all AI-generated locations (overworld by default)
        - is_safe_zone: True for safe categories (town, village, settlement)
    """
    is_safe = category in SAFE_ZONE_CATEGORIES if category else False
    return (True, is_safe)


def _create_npcs_from_data(npcs_data: list[dict]) -> list[NPC]:
    """Create NPC objects from parsed NPC data.

    Args:
        npcs_data: List of NPC dictionaries from AI service

    Returns:
        List of NPC objects
    """
    npcs = []
    for npc_data in npcs_data:
        try:
            role = npc_data.get("role", "villager")
            is_merchant = role == "merchant"
            is_quest_giver = role == "quest_giver"

            npc = NPC(
                name=npc_data["name"],
                description=npc_data["description"],
                dialogue=npc_data.get("dialogue", "Hello, traveler."),
                is_merchant=is_merchant,
                is_quest_giver=is_quest_giver
            )
            npcs.append(npc)
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to create NPC from data: {e}")
            continue
    return npcs


def _generate_location_ascii_art(
    ai_service: AIService,
    location_name: str,
    location_description: str,
    location_category: Optional[str],
    theme: str
) -> str:
    """Generate ASCII art for a location using AI with fallback.

    Tries to generate ASCII art using the AI service. If that fails,
    falls back to template-based art from location_art module.

    Args:
        ai_service: AIService instance
        location_name: Name of the location
        location_description: Description of the location
        location_category: Category of the location (town, forest, etc.)
        theme: World theme (e.g., "fantasy", "sci-fi")

    Returns:
        ASCII art string
    """
    try:
        return ai_service.generate_location_ascii_art(
            location_name=location_name,
            location_description=location_description,
            location_category=location_category,
            theme=theme
        )
    except Exception as e:
        logger.warning(f"AI location ASCII art generation failed, using fallback: {e}")
        return get_fallback_location_ascii_art(
            category=location_category,
            location_name=location_name
        )


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

    # Generate ASCII art for starting location
    starting_ascii_art = _generate_location_ascii_art(
        ai_service=ai_service,
        location_name=starting_data["name"],
        location_description=starting_data["description"],
        location_category=starting_data.get("category"),
        theme=theme
    )

    # Infer hierarchy fields from category
    starting_category = starting_data.get("category")
    is_overworld, is_safe_zone = _infer_hierarchy_from_category(starting_category)

    # Create starting location at origin (0, 0)
    starting_location = Location(
        name=starting_data["name"],
        description=starting_data["description"],
        connections={},  # WorldGrid will add connections
        category=starting_category,
        ascii_art=starting_ascii_art,
        is_overworld=is_overworld,
        is_safe_zone=is_safe_zone
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

    # Add quest giver NPC to starting location
    quest_giver = NPC(
        name="Town Elder",
        description="A wise figure who knows of many adventures",
        dialogue="Ah, a new adventurer! I may have tasks for you.",
        is_quest_giver=True,
        offered_quests=[]
    )
    starting_location.npcs.append(quest_giver)

    # Add AI-generated NPCs to starting location (if any)
    ai_npcs = _create_npcs_from_data(starting_data.get("npcs", []))
    for npc in ai_npcs:
        starting_location.npcs.append(npc)

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

        # Note: direction is always in DIRECTION_OFFSETS because we filter
        # at lines 125 and 178 when adding to the queue

        try:
            # Generate new location
            logger.info(f"Generating location at ({target_x}, {target_y}) from {source_name}")
            location_data = ai_service.generate_location(
                theme=theme,
                context_locations=list(grid.keys()),
                source_location=source_name,
                direction=direction
            )

            # Generate ASCII art for the new location
            new_ascii_art = _generate_location_ascii_art(
                ai_service=ai_service,
                location_name=location_data["name"],
                location_description=location_data["description"],
                location_category=location_data.get("category"),
                theme=theme
            )

            # Infer hierarchy fields from category
            new_category = location_data.get("category")
            new_is_overworld, new_is_safe_zone = _infer_hierarchy_from_category(new_category)

            # Create location
            new_location = Location(
                name=location_data["name"],
                description=location_data["description"],
                connections={},
                category=new_category,
                ascii_art=new_ascii_art,
                is_overworld=new_is_overworld,
                is_safe_zone=new_is_safe_zone
            )

            # Add AI-generated NPCs to the new location
            location_npcs = _create_npcs_from_data(location_data.get("npcs", []))
            for npc in location_npcs:
                new_location.npcs.append(npc)

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

    # Generate ASCII art for the new location
    new_ascii_art = _generate_location_ascii_art(
        ai_service=ai_service,
        location_name=location_data["name"],
        location_description=location_data["description"],
        location_category=location_data.get("category"),
        theme=theme
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

    # Infer hierarchy fields from category
    new_category = location_data.get("category")
    new_is_overworld, new_is_safe_zone = _infer_hierarchy_from_category(new_category)

    # Create new location with coordinates
    new_location = Location(
        name=location_data["name"],
        description=location_data["description"],
        connections={},
        coordinates=new_coordinates,
        category=new_category,
        ascii_art=new_ascii_art,
        is_overworld=new_is_overworld,
        is_safe_zone=new_is_safe_zone
    )

    # Add AI-generated NPCs to the new location
    location_npcs = _create_npcs_from_data(location_data.get("npcs", []))
    for npc in location_npcs:
        new_location.npcs.append(npc)

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


def expand_area(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str,
    target_coords: tuple[int, int],
    size: int = 5
) -> dict[str, Location]:
    """Expand world by generating an entire thematic area (4-7 locations).

    This function generates a cluster of connected locations at the target
    coordinates, placing them on the grid and connecting them to the source
    location.

    Args:
        world: Existing world dictionary
        ai_service: AIService instance with generate_area capability
        from_location: Source location name (where player is coming from)
        direction: Direction of expansion from source
        theme: World theme for generation
        target_coords: Coordinates where the entry location should be placed
        size: Target number of locations in the area (4-7, default 5)

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

    # Generate area sub-theme hint based on source location
    # This could be enhanced with more sophisticated theme selection
    sub_theme_hints = [
        "mystical forest", "ancient ruins", "haunted grounds",
        "mountain pass", "coastal region", "underground cavern",
        "enchanted garden", "abandoned settlement", "wild frontier"
    ]
    import random
    sub_theme = random.choice(sub_theme_hints)

    # Generate the area
    logger.info(f"Expanding area: {direction} from {from_location} with theme '{sub_theme}'")
    area_data = ai_service.generate_area(
        theme=theme,
        sub_theme_hint=sub_theme,
        entry_direction=direction,
        context_locations=list(world.keys()),
        size=size
    )

    if not area_data:
        logger.warning("No area data generated, falling back to single location")
        return expand_world(
            world=world,
            ai_service=ai_service,
            from_location=from_location,
            direction=direction,
            theme=theme,
            target_coords=target_coords
        )

    # Place area locations on the grid
    opposite = get_opposite_direction(direction)
    entry_name = None
    placed_locations = {}

    # First pass: create Location objects and calculate absolute coordinates
    for loc_data in area_data:
        rel_x, rel_y = loc_data["relative_coords"]
        abs_x = target_coords[0] + rel_x
        abs_y = target_coords[1] + rel_y

        # Skip if coordinates already occupied
        existing = None
        for loc in world.values():
            if loc.coordinates == (abs_x, abs_y):
                existing = loc
                break

        if existing is not None:
            logger.warning(
                f"Skipping {loc_data['name']}: coordinates ({abs_x}, {abs_y}) "
                f"already occupied by {existing.name}"
            )
            continue

        # Skip if name already exists
        if loc_data["name"] in world:
            logger.warning(f"Skipping duplicate location name: {loc_data['name']}")
            continue

        # Generate ASCII art using fallback (to avoid extra API calls for area locations)
        loc_ascii_art = get_fallback_location_ascii_art(
            category=loc_data.get("category"),
            location_name=loc_data["name"]
        )

        # Infer hierarchy fields from category
        loc_category = loc_data.get("category")
        _, loc_is_safe_zone = _infer_hierarchy_from_category(loc_category)

        # Determine if this is the entry location (at relative 0,0)
        is_entry = (rel_x == 0 and rel_y == 0)

        # Entry location is overworld, sub-locations are not
        loc_is_overworld = is_entry

        # Create the location with hierarchy fields
        new_loc = Location(
            name=loc_data["name"],
            description=loc_data["description"],
            connections={},
            coordinates=(abs_x, abs_y),
            category=loc_category,
            ascii_art=loc_ascii_art,
            is_overworld=loc_is_overworld,
            is_safe_zone=loc_is_safe_zone
        )

        # Add AI-generated NPCs to the location
        location_npcs = _create_npcs_from_data(loc_data.get("npcs", []))
        for npc in location_npcs:
            new_loc.npcs.append(npc)

        placed_locations[loc_data["name"]] = {
            "location": new_loc,
            "connections": loc_data["connections"],
            "coords": (abs_x, abs_y),
            "relative_coords": (rel_x, rel_y),
            "is_entry": is_entry
        }

        # Track entry location (at relative 0,0)
        if is_entry:
            entry_name = loc_data["name"]

    # If no entry location was placed, fall back to single location expansion
    if entry_name is None and placed_locations:
        # Use first placed location as entry
        entry_name = next(iter(placed_locations.keys()))
        # Mark first location as entry (overworld)
        placed_locations[entry_name]["location"].is_overworld = True
        placed_locations[entry_name]["is_entry"] = True
    elif not placed_locations:
        logger.warning("No locations could be placed, falling back to single location")
        return expand_world(
            world=world,
            ai_service=ai_service,
            from_location=from_location,
            direction=direction,
            theme=theme,
            target_coords=target_coords
        )

    # Set up hierarchy relationships between entry and sub-locations
    if entry_name is not None:
        entry_loc = placed_locations[entry_name]["location"]
        sub_location_names = []

        for name, data in placed_locations.items():
            if not data.get("is_entry", False):
                # This is a sub-location - set parent reference
                data["location"].parent_location = entry_name
                sub_location_names.append(name)

        # Set entry's sub_locations list and entry_point
        entry_loc.sub_locations = sub_location_names
        if sub_location_names:
            entry_loc.entry_point = sub_location_names[0]

    # Second pass: add connections
    for name, data in placed_locations.items():
        loc = data["location"]
        connections = data["connections"]

        for conn_dir, conn_target in connections.items():
            # Replace EXISTING_WORLD placeholder with actual source location
            if conn_target == "EXISTING_WORLD":
                conn_target = from_location

            # Check if target is another placed location or existing location
            if conn_target in placed_locations or conn_target in world:
                loc.add_connection(conn_dir, conn_target)

    # Add locations to world - use SubGrid for sub-locations
    if entry_name is not None and len(placed_locations) > 1:
        entry_loc = placed_locations[entry_name]["location"]

        # Create SubGrid for interior (7x7 area)
        sub_grid = SubGrid(bounds=(-3, 3, -3, 3), parent_name=entry_name)

        # Add sub-locations to SubGrid (not to world)
        first_subloc = True
        for name, data in placed_locations.items():
            if data.get("is_entry", False):
                continue  # Skip entry, it goes to world

            loc = data["location"]
            rel_x, rel_y = data["relative_coords"]

            # Check SubGrid bounds before adding
            if not sub_grid.is_within_bounds(rel_x, rel_y):
                logger.warning(
                    f"Skipping {name}: coords ({rel_x}, {rel_y}) outside SubGrid bounds "
                    f"{sub_grid.bounds}"
                )
                continue

            # Clear overworld coordinates (sub-locations get SubGrid coords)
            loc.coordinates = None

            # First sub-location is exit point (entry into the SubGrid)
            loc.is_exit_point = first_subloc
            first_subloc = False

            sub_grid.add_location(loc, rel_x, rel_y)

        # Attach sub_grid to entry
        entry_loc.sub_grid = sub_grid
        entry_loc.is_exit_point = True  # Can exit from entry back to overworld

        # Only add entry to world
        world[entry_name] = entry_loc
    else:
        # Single location or no entry - add all to world (legacy behavior)
        for name, data in placed_locations.items():
            world[name] = data["location"]

    # Connect source location to entry
    if entry_name:
        world[from_location].add_connection(direction, entry_name)
        # Ensure entry has back-connection
        if not world[entry_name].has_connection(opposite):
            world[entry_name].add_connection(opposite, from_location)

    # Add bidirectional connections between placed locations based on coordinates
    for name, data in placed_locations.items():
        loc = data["location"]
        coords = data["coords"]

        for check_dir, offset in DIRECTION_OFFSETS.items():
            neighbor_coords = (coords[0] + offset[0], coords[1] + offset[1])

            # Find neighbor by coordinates
            neighbor = None
            for n_name, n_data in placed_locations.items():
                if n_data["coords"] == neighbor_coords:
                    neighbor = n_data["location"]
                    break

            # Also check existing world locations
            if neighbor is None:
                for existing_loc in world.values():
                    if existing_loc.coordinates == neighbor_coords:
                        neighbor = existing_loc
                        break

            if neighbor is not None:
                # Ensure bidirectional connection
                if not loc.has_connection(check_dir):
                    loc.add_connection(check_dir, neighbor.name)
                rev_dir = get_opposite_direction(check_dir)
                if not neighbor.has_connection(rev_dir):
                    neighbor.add_connection(rev_dir, loc.name)

    # Ensure the world still has at least one frontier exit for future expansion
    # Build a temporary WorldGrid to check and fix expansion exits
    temp_grid = WorldGrid()
    for name, loc in world.items():
        if loc.coordinates is not None:
            temp_grid._grid[loc.coordinates] = loc
            temp_grid._by_name[name] = loc

    if temp_grid.ensure_expansion_possible():
        logger.debug("Added frontier exit to ensure world can expand")

    logger.info(
        f"Added area with {len(placed_locations)} locations, "
        f"entry: '{entry_name}'"
    )
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
