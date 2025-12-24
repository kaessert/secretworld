"""World module for creating and managing game locations."""

from cli_rpg.models.location import Location


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
