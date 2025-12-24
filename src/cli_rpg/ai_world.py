"""AI-powered world generation module."""

import logging
from typing import Optional
from cli_rpg.ai_service import AIService, AIServiceError
from cli_rpg.models.location import Location


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
    """Create an AI-generated world.
    
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
    world: dict[str, Location] = {}
    
    # Generate starting location
    logger.info(f"Generating starting location: {starting_location_name}")
    starting_data = ai_service.generate_location(
        theme=theme,
        context_locations=[],
        source_location=None,
        direction=None
    )
    
    # Create starting location
    starting_location = Location(
        name=starting_data["name"],
        description=starting_data["description"],
        connections={}  # Will add connections as we generate them
    )
    world[starting_location.name] = starting_location
    
    # Keep track of connections to generate
    connections_to_generate = []
    for direction, target_name in starting_data["connections"].items():
        connections_to_generate.append((starting_location.name, direction, target_name))
    
    # Generate connected locations up to initial_size
    generated_count = 1
    attempts = 0
    max_attempts = initial_size * 3  # Prevent infinite loops
    
    while generated_count < initial_size and connections_to_generate and attempts < max_attempts:
        attempts += 1
        
        # Get next connection to generate
        source_name, direction, suggested_name = connections_to_generate.pop(0)
        
        # Skip if target already exists
        if suggested_name in world:
            # Just add the connection
            if source_name in world and direction in Location.VALID_DIRECTIONS:
                world[source_name].add_connection(direction, suggested_name)
                # Add reverse connection
                opposite = get_opposite_direction(direction)
                if opposite in Location.VALID_DIRECTIONS:
                    world[suggested_name].add_connection(opposite, source_name)
            continue
        
        # Skip if direction is invalid
        if direction not in Location.VALID_DIRECTIONS:
            logger.warning(f"Skipping invalid direction: {direction}")
            continue
        
        try:
            # Generate new location
            logger.info(f"Generating location in direction {direction} from {source_name}")
            location_data = ai_service.generate_location(
                theme=theme,
                context_locations=list(world.keys()),
                source_location=source_name,
                direction=direction
            )
            
            # Create location
            new_location = Location(
                name=location_data["name"],
                description=location_data["description"],
                connections={}
            )
            
            # Add to world if name is unique
            if new_location.name not in world:
                world[new_location.name] = new_location
                generated_count += 1
                
                # Add bidirectional connection
                world[source_name].add_connection(direction, new_location.name)
                opposite = get_opposite_direction(direction)
                new_location.add_connection(opposite, source_name)
                
                # Add suggested connections from new location to queue
                for new_dir, new_target in location_data["connections"].items():
                    if new_dir != opposite:  # Don't re-add the back connection
                        connections_to_generate.append((new_location.name, new_dir, new_target))
            else:
                logger.warning(f"Duplicate location name generated: {new_location.name}")
        
        except Exception as e:
            logger.warning(f"Failed to generate location: {e}")
            continue
    
    logger.info(f"Generated world with {len(world)} locations")

    # Ensure all locations have at least one dangling exit for future expansion
    import random
    for loc_name, location in world.items():
        # Find non-dangling connections (those pointing to existing locations)
        back_connections = [d for d, target in location.connections.items() if target in world]

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

    return (world, actual_starting_location)


def expand_world(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str
) -> dict[str, Location]:
    """Expand world by generating a new location.
    
    Args:
        world: Existing world dictionary
        ai_service: AIService instance
        from_location: Source location name
        direction: Direction to expand in
        theme: World theme
    
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
    
    # Create new location
    new_location = Location(
        name=location_data["name"],
        description=location_data["description"],
        connections={}
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
