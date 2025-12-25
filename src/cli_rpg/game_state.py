"""GameState class for managing game state and gameplay."""

import logging
import random
from typing import ClassVar, Optional
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop
from cli_rpg.combat import CombatEncounter, spawn_enemy, ai_spawn_enemy
from cli_rpg.autosave import autosave
from cli_rpg import colors

# Import AI components (with optional support)
try:
    from cli_rpg.ai_service import AIService, AIServiceError
    from cli_rpg.ai_world import expand_world, expand_area
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIService = None
    AIServiceError = Exception
    expand_area = None

logger = logging.getLogger(__name__)


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

    # Expand shorthand aliases
    aliases = {
        "g": "go", "l": "look", "a": "attack", "c": "cast",
        "d": "defend", "f": "flee", "s": "status", "i": "inventory",
        "m": "map", "h": "help", "t": "talk", "u": "use", "e": "equip",
        "q": "quests", "dr": "drop"
    }
    command = aliases.get(command, command)

    # Expand direction shorthands for go command
    if command == "go" and args:
        direction_aliases = {"n": "north", "s": "south", "e": "east", "w": "west"}
        args[0] = direction_aliases.get(args[0], args[0])

    # Validate known commands
    known_commands = {"look", "go", "save", "quit", "attack", "defend", "flee", "status", "cast",
                      "inventory", "equip", "unequip", "use", "drop", "talk", "buy", "sell", "shop",
                      "map", "help", "quests", "quest", "accept", "complete", "lore"}
    
    if command not in known_commands:
        return ("unknown", [])
    
    return (command, args)


class GameState:
    """Manages the current game state including character, location, and world.
    
    Attributes:
        current_character: The player's character
        current_location: Name of the current location
        world: Dictionary mapping location names to Location objects
        current_combat: Active combat encounter or None
    """
    
    def __init__(
        self,
        character: Character,
        world: dict[str, Location],
        starting_location: str = "Town Square",
        ai_service: Optional["AIService"] = None,
        theme: str = "fantasy"
    ):
        """Initialize game state.
        
        Args:
            character: The player's character
            world: Dictionary mapping location names to Location objects
            starting_location: Name of starting location (default: "Town Square")
            ai_service: Optional AIService for dynamic world generation
            theme: World theme for AI generation (default: "fantasy")
            
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
        
        # Note: Dangling connections (pointing to non-existent locations) are allowed.
        # These support the "infinite world" principle where all locations have
        # forward paths for exploration. When traveled to:
        # - With AI service: the destination is generated dynamically
        # - Without AI service: the move returns an error message
        
        # Set attributes
        self.current_character = character
        self.world = world
        self.current_location = starting_location
        self.ai_service = ai_service
        self.theme = theme
        self.current_combat: Optional[CombatEncounter] = None
        self.current_shop: Optional[Shop] = None  # Active shop interaction
        self.current_npc: Optional[NPC] = None  # NPC being talked to (for accept command)
    
    def get_current_location(self) -> Location:
        """Get the current Location object.

        Returns:
            The Location object for the current location
        """
        return self.world[self.current_location]

    def _get_location_by_coordinates(
        self, coords: tuple[int, int]
    ) -> Optional[Location]:
        """Find a location by its coordinates.

        Args:
            coords: (x, y) coordinate tuple

        Returns:
            Location at those coordinates, or None if not found
        """
        for location in self.world.values():
            if location.coordinates == coords:
                return location
        return None
    
    def look(self) -> str:
        """Get a formatted description of the current location.
        
        Returns:
            String description of current location with name, description, and exits
        """
        location = self.get_current_location()
        return str(location)
    
    def is_in_combat(self) -> bool:
        """Check if combat is currently active.
        
        Returns:
            True if in combat, False otherwise
        """
        return self.current_combat is not None and self.current_combat.is_active
    
    def trigger_encounter(self, location_name: str) -> Optional[str]:
        """Potentially spawn an enemy based on location.

        Uses AI-generated enemies when AIService is available, with fallback
        to template-based enemies.

        Args:
            location_name: Name of the location for encounter

        Returns:
            Message about encounter if triggered, None otherwise
        """
        # 30% chance of encounter
        if random.random() < 0.3:
            enemy = ai_spawn_enemy(
                location_name=location_name,
                player_level=self.current_character.level,
                ai_service=self.ai_service,
                theme=self.theme
            )
            self.current_combat = CombatEncounter(self.current_character, enemy)
            return self.current_combat.start()
        return None
    
    def move(self, direction: str) -> tuple[bool, str]:
        """Move to a connected location in the specified direction.

        Uses coordinate-based movement when locations have coordinates,
        falling back to connection-based movement for legacy saves.

        Args:
            direction: The direction to move (e.g., "north", "south", etc.)

        Returns:
            Tuple of (success, message) where:
            - success is True if move was successful, False otherwise
            - message describes the result
        """
        from cli_rpg.world_grid import DIRECTION_OFFSETS

        current = self.get_current_location()

        # Check if direction is valid (north, south, east, west)
        valid_game_directions = {"north", "south", "east", "west"}
        if direction not in valid_game_directions:
            return (False, "Invalid direction. Use: north, south, east, or west.")

        # Use coordinate-based movement if current location has coordinates
        if current.coordinates is not None:
            # Validate that the direction exists as an exit
            if not current.has_connection(direction):
                return (False, "You can't go that way.")

            # Calculate target coordinates
            dx, dy = DIRECTION_OFFSETS[direction]
            target_coords = (current.coordinates[0] + dx, current.coordinates[1] + dy)

            # Find location at target coordinates
            target_location = self._get_location_by_coordinates(target_coords)

            if target_location is not None:
                # Location exists at target coordinates - move there
                self.current_location = target_location.name
            else:
                # No location at target - try AI area generation or fail
                if self.ai_service is not None and AI_AVAILABLE and expand_area is not None:
                    try:
                        logger.info(
                            f"Generating area at {target_coords} from {current.name}"
                        )
                        expand_area(
                            world=self.world,
                            ai_service=self.ai_service,
                            from_location=self.current_location,
                            direction=direction,
                            theme=self.theme,
                            target_coords=target_coords,
                        )
                        # Find the newly generated location
                        target_location = self._get_location_by_coordinates(target_coords)
                        if target_location:
                            self.current_location = target_location.name
                        else:
                            return (False, "Failed to generate destination.")
                    except (AIServiceError, Exception) as e:
                        logger.error(f"Failed to generate area: {e}")
                        return (False, f"Failed to generate destination: {str(e)}")
                else:
                    return (False, "You can't go that way.")
        else:
            # Legacy fallback: use connection-based movement
            if not current.has_connection(direction):
                return (False, "You can't go that way.")

            destination_name = current.get_connection(direction)

            if destination_name not in self.world:
                # Try to generate it with AI if available
                if self.ai_service is not None and AI_AVAILABLE:
                    try:
                        logger.info(f"Generating missing destination: {destination_name}")
                        expand_world(
                            world=self.world,
                            ai_service=self.ai_service,
                            from_location=self.current_location,
                            direction=direction,
                            theme=self.theme,
                        )
                        # Re-read destination name after expansion (may have changed)
                        current = self.get_current_location()
                        destination_name = current.get_connection(direction)
                    except (AIServiceError, Exception) as e:
                        logger.error(f"Failed to generate location: {e}")
                        return (False, f"Failed to generate destination: {str(e)}")
                else:
                    return (False, f"Destination '{destination_name}' not found in world.")

            self.current_location = destination_name

        # Autosave after successful movement
        try:
            autosave(self)
        except IOError:
            pass  # Silent failure - don't interrupt gameplay

        message = f"You head {direction} to {colors.location(self.current_location)}."

        # Check for random encounter
        encounter_message = self.trigger_encounter(self.current_location)
        if encounter_message:
            message += f"\n{encounter_message}"

        return (True, message)
    
    def to_dict(self) -> dict:
        """Serialize game state to dictionary.
        
        Returns:
            Dictionary containing character, current_location, world data, and theme
        """
        return {
            "character": self.current_character.to_dict(),
            "current_location": self.current_location,
            "world": {
                name: location.to_dict()
                for name, location in self.world.items()
            },
            "theme": self.theme
        }
    
    @classmethod
    def from_dict(cls, data: dict, ai_service: Optional["AIService"] = None) -> "GameState":
        """Deserialize game state from dictionary.
        
        Args:
            data: Dictionary containing game state data
            ai_service: Optional AIService to enable dynamic world generation
            
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
        
        # Get theme (default to "fantasy" for backward compatibility)
        theme = data.get("theme", "fantasy")
        
        # Create and return game state
        return cls(character, world, current_location, ai_service=ai_service, theme=theme)
