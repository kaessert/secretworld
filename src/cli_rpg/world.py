"""World module for creating and managing game locations."""

import logging
from typing import Optional
from cli_rpg.models.location import Location

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


def create_default_world() -> dict[str, Location]:
    """Create and return the default game world with 3 locations.
    
    Returns:
        Dictionary mapping location names to Location instances
        
    The default world consists of:
    - Town Square: Central hub with connections north to Forest and east to Cave
    - Forest: Northern location with connection south to Town Square
    - Cave: Eastern location with connection west to Town Square
    """
    # Create locations (without connections first to avoid validation issues)
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
    
    # Add connections
    town_square.add_connection("north", "Forest")
    town_square.add_connection("east", "Cave")
    
    forest.add_connection("south", "Town Square")
    
    cave.add_connection("west", "Town Square")
    
    # Return world dictionary
    return {
        "Town Square": town_square,
        "Forest": forest,
        "Cave": cave
    }


def create_world(
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy"
) -> dict[str, Location]:
    """Create a game world, using AI if available.

    Args:
        ai_service: Optional AIService for AI-generated world
        theme: World theme (default: "fantasy")

    Returns:
        Dictionary mapping location names to Location instances
    """
    if ai_service is not None and AI_AVAILABLE:
        # Use AI to create world with fallback to default on error
        try:
            logger.info("Attempting to create AI-generated world")
            return create_ai_world(ai_service, theme=theme)
        except Exception as e:
            logger.warning(f"AI world generation failed: {e}")
            logger.info("Falling back to default world")
            return create_default_world()
    else:
        # Use default world
        return create_default_world()
