"""GameState class for managing game state and gameplay."""

from typing import ClassVar
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


def parse_command(command_str: str) -> tuple[str, list[str]]:
    """Parse a command string into command and arguments.
    
    Args:
        command_str: The command string to parse
        
    Returns:
        Tuple of (command, args) where command is lowercase and args is a list
        Returns ("unknown", []) for unrecognized commands
    """
    # Strip and lowercase the input
    command_str = command_str.strip().lower()
    
    # Split into parts
    parts = command_str.split()
    
    if not parts:
        return ("unknown", [])
    
    command = parts[0]
    args = parts[1:]
    
    # Validate known commands
    known_commands = {"look", "go", "save", "quit"}
    
    if command not in known_commands:
        return ("unknown", [])
    
    return (command, args)


class GameState:
    """Manages the current game state including character, location, and world.
    
    Attributes:
        current_character: The player's character
        current_location: Name of the current location
        world: Dictionary mapping location names to Location objects
    """
    
    def __init__(
        self,
        character: Character,
        world: dict[str, Location],
        starting_location: str = "Town Square"
    ):
        """Initialize game state.
        
        Args:
            character: The player's character
            world: Dictionary mapping location names to Location objects
            starting_location: Name of starting location (default: "Town Square")
            
        Raises:
            TypeError: If character is not a Character instance
            ValueError: If world is empty, starting_location not in world,
                       or world connections are invalid
        """
        # Validate character
        if not isinstance(character, Character):
            raise TypeError("character must be a Character instance")
        
        # Validate world
        if not world:
            raise ValueError("world cannot be empty")
        
        # Validate starting location
        if starting_location not in world:
            raise ValueError(f"starting_location '{starting_location}' not found in world")
        
        # Validate world connections
        for location_name, location in world.items():
            for direction, target in location.connections.items():
                if target not in world:
                    raise ValueError(
                        f"Connection from '{location_name}' via '{direction}' "
                        f"points to non-existent location '{target}'"
                    )
        
        # Set attributes
        self.current_character = character
        self.world = world
        self.current_location = starting_location
    
    def get_current_location(self) -> Location:
        """Get the current Location object.
        
        Returns:
            The Location object for the current location
        """
        return self.world[self.current_location]
    
    def look(self) -> str:
        """Get a formatted description of the current location.
        
        Returns:
            String description of current location with name, description, and exits
        """
        location = self.get_current_location()
        return str(location)
    
    def move(self, direction: str) -> tuple[bool, str]:
        """Move to a connected location in the specified direction.
        
        Args:
            direction: The direction to move (e.g., "north", "south", etc.)
            
        Returns:
            Tuple of (success, message) where:
            - success is True if move was successful, False otherwise
            - message describes the result
        """
        current = self.get_current_location()
        
        # Check if direction exists
        if not current.has_connection(direction):
            return (False, "You can't go that way.")
        
        # Get destination
        destination_name = current.get_connection(direction)
        
        # Update location
        self.current_location = destination_name
        
        return (True, f"You head {direction} to {destination_name}.")
    
    def to_dict(self) -> dict:
        """Serialize game state to dictionary.
        
        Returns:
            Dictionary containing character, current_location, and world data
        """
        return {
            "character": self.current_character.to_dict(),
            "current_location": self.current_location,
            "world": {
                name: location.to_dict()
                for name, location in self.world.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Deserialize game state from dictionary.
        
        Args:
            data: Dictionary containing game state data
            
        Returns:
            GameState instance
            
        Raises:
            KeyError: If required fields are missing
        """
        # Deserialize character
        character = Character.from_dict(data["character"])
        
        # Deserialize world
        world = {
            name: Location.from_dict(location_data)
            for name, location_data in data["world"].items()
        }
        
        # Get current location
        current_location = data["current_location"]
        
        # Create and return game state
        return cls(character, world, current_location)
