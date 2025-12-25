"""Location model for the game world."""

import hashlib
from dataclasses import dataclass, field
from typing import Any, ClassVar, List, Optional, Tuple, TYPE_CHECKING

from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.models.npc import NPC


@dataclass
class Location:
    """Represents a location in the game world.
    
    A location has a name, description, and connections to other locations
    via directional exits (north, south, east, west).
    
    Attributes:
        name: The location's name (2-50 characters)
        description: The location's description (1-500 characters)
        connections: Dictionary mapping directions to location names
    """
    
    # Class constants
    MIN_NAME_LENGTH: ClassVar[int] = 2
    MAX_NAME_LENGTH: ClassVar[int] = 50
    MIN_DESCRIPTION_LENGTH: ClassVar[int] = 1
    MAX_DESCRIPTION_LENGTH: ClassVar[int] = 500
    VALID_DIRECTIONS: ClassVar[set[str]] = {"north", "south", "east", "west"}
    
    name: str
    description: str
    connections: dict[str, str] = field(default_factory=dict)
    npcs: List["NPC"] = field(default_factory=list)
    coordinates: Optional[Tuple[int, int]] = None
    category: Optional[str] = None
    ascii_art: str = ""
    details: Optional[str] = None  # Second-look environmental details
    secrets: Optional[str] = None  # Third-look hidden secrets
    
    def __post_init__(self) -> None:
        """Validate location attributes after initialization."""
        # Validate and normalize name
        if not self.name or not self.name.strip():
            raise ValueError("Location name cannot be empty")
        
        self.name = self.name.strip()
        
        if len(self.name) < self.MIN_NAME_LENGTH:
            raise ValueError(
                f"Location name must be at least {self.MIN_NAME_LENGTH} characters long"
            )
        
        if len(self.name) > self.MAX_NAME_LENGTH:
            raise ValueError(
                f"Location name must be at most {self.MAX_NAME_LENGTH} characters long"
            )
        
        # Validate and normalize description
        if not self.description or not self.description.strip():
            raise ValueError("Location description cannot be empty")
        
        self.description = self.description.strip()

        if len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Location description must be at most {self.MAX_DESCRIPTION_LENGTH} characters long"
            )
        
        # Validate connections
        for direction, location_name in self.connections.items():
            if direction not in self.VALID_DIRECTIONS:
                raise ValueError(
                    f"Invalid direction '{direction}'. Must be one of: {', '.join(sorted(self.VALID_DIRECTIONS))}"
                )
            
            if not location_name or not location_name.strip():
                raise ValueError(
                    f"Location name for direction '{direction}' cannot be empty"
                )
    
    def add_connection(self, direction: str, location_name: str) -> None:
        """Add or update a connection to another location.
        
        Args:
            direction: The direction of the connection (must be in VALID_DIRECTIONS)
            location_name: The name of the connected location (non-empty)
        
        Raises:
            ValueError: If direction is invalid or location_name is empty
        """
        if direction not in self.VALID_DIRECTIONS:
            raise ValueError(
                f"Invalid direction '{direction}'. Must be one of: {', '.join(sorted(self.VALID_DIRECTIONS))}"
            )
        
        if not location_name or not location_name.strip():
            raise ValueError("Location name cannot be empty")
        
        self.connections[direction] = location_name
    
    def remove_connection(self, direction: str) -> None:
        """Remove a connection in the specified direction.
        
        If the connection doesn't exist, this method does nothing (silent removal).
        
        Args:
            direction: The direction of the connection to remove
        """
        self.connections.pop(direction, None)
    
    def get_connection(self, direction: str) -> Optional[str]:
        """Get the location name connected in the specified direction.
        
        Args:
            direction: The direction to check
        
        Returns:
            The connected location name, or None if no connection exists
        """
        return self.connections.get(direction)
    
    def has_connection(self, direction: str) -> bool:
        """Check if a connection exists in the specified direction.
        
        Args:
            direction: The direction to check
        
        Returns:
            True if a connection exists, False otherwise
        """
        return direction in self.connections
    
    def get_available_directions(self) -> list[str]:
        """Get a sorted list of all available exit directions.

        Returns:
            A sorted list of direction names with connections
        """
        return sorted(list(self.connections.keys()))

    def find_npc_by_name(self, name: str) -> Optional["NPC"]:
        """Find an NPC by name (case-insensitive).

        Args:
            name: NPC name to search for

        Returns:
            NPC if found, None otherwise
        """
        name_lower = name.lower()
        for npc in self.npcs:
            if npc.name.lower() == name_lower:
                return npc
        return None

    def get_layered_description(self, look_count: int = 1, visibility: str = "full") -> str:
        """Get description with appropriate layers based on look count and visibility.

        Args:
            look_count: Number of times player has looked at this location
            visibility: Visibility level affecting what's shown:
                - "full": Everything shown normally
                - "reduced": Description truncated to first sentence, no details/secrets
                - "obscured": Some exits hidden (50% each), NPC names shown as "???"

        Returns:
            Formatted string with name, description, and appropriate detail layers
        """
        result = f"{colors.location(self.name)}\n"

        # Add ASCII art if present (after name, before description)
        if self.ascii_art:
            result += self.ascii_art.strip() + "\n"

        # Handle description based on visibility
        description = self.description
        if visibility == "reduced":
            # Truncate to first sentence
            for delimiter in [". ", "! ", "? "]:
                if delimiter in description:
                    description = description.split(delimiter)[0] + delimiter[0]
                    break
        result += f"{description}\n"

        # Handle NPCs based on visibility
        if self.npcs:
            if visibility == "obscured":
                # Show "???" for each NPC instead of their names
                obscured_names = [colors.npc("???") for _ in self.npcs]
                result += f"NPCs: {', '.join(obscured_names)}\n"
            else:
                npc_names = [colors.npc(npc.name) for npc in self.npcs]
                result += f"NPCs: {', '.join(npc_names)}\n"

        # Handle exits based on visibility
        if self.connections:
            directions = self.get_available_directions()
            if visibility == "obscured":
                # Hide ~50% of exits, seeded by location name for consistency
                directions = self._filter_exits_for_fog(directions)
            result += f"Exits: {', '.join(directions)}"
        else:
            result += "Exits: None"

        # Add details layer (look_count >= 2) - hidden in reduced visibility
        if visibility != "reduced" and look_count >= 2 and self.details:
            result += f"\n\nUpon closer inspection, you notice:\n{self.details}"

        # Add secrets layer (look_count >= 3) - hidden in reduced visibility
        if visibility != "reduced" and look_count >= 3 and self.secrets:
            result += f"\n\nHidden secrets reveal themselves:\n{self.secrets}"

        return result

    def _filter_exits_for_fog(self, directions: list[str]) -> list[str]:
        """Filter exits for fog visibility, hiding ~50% of them.

        Uses location name as seed for deterministic, consistent results.
        Always keeps at least one exit visible.

        Args:
            directions: List of available direction names

        Returns:
            Filtered list of visible directions
        """
        if len(directions) <= 1:
            return directions

        # Use location name hash for deterministic seeding
        seed = int(hashlib.md5(self.name.encode()).hexdigest(), 16)

        # Determine which exits to show (~50% hidden)
        visible = []
        for i, direction in enumerate(directions):
            # Use seed + index to determine if exit is visible
            if (seed + i) % 2 == 0:
                visible.append(direction)

        # Ensure at least one exit is always visible
        if not visible:
            # Show the first exit if all were hidden
            visible = [directions[0]]

        return visible

    def to_dict(self) -> dict[str, Any]:
        """Serialize the location to a dictionary.

        Returns:
            A dictionary representation of the location
        """
        data: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "connections": self.connections.copy(),
            "npcs": [npc.to_dict() for npc in self.npcs]
        }
        # Only include coordinates if present (backward compatibility)
        if self.coordinates is not None:
            data["coordinates"] = [self.coordinates[0], self.coordinates[1]]
        # Only include category if present (backward compatibility)
        if self.category is not None:
            data["category"] = self.category
        # Only include ascii_art if non-empty (backward compatibility)
        if self.ascii_art:
            data["ascii_art"] = self.ascii_art
        # Only include details if present (backward compatibility)
        if self.details is not None:
            data["details"] = self.details
        # Only include secrets if present (backward compatibility)
        if self.secrets is not None:
            data["secrets"] = self.secrets
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Location":
        """Create a location from a dictionary.

        Args:
            data: Dictionary containing location data

        Returns:
            A new Location instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If validation fails
        """
        from cli_rpg.models.npc import NPC
        npcs = [NPC.from_dict(npc_data) for npc_data in data.get("npcs", [])]
        # Parse coordinates if present (convert list to tuple)
        coordinates = None
        if "coordinates" in data and data["coordinates"] is not None:
            coords = data["coordinates"]
            coordinates = (coords[0], coords[1])
        # Parse category if present (for backward compatibility)
        category = data.get("category")
        # Parse ascii_art if present (for backward compatibility)
        ascii_art = data.get("ascii_art", "")
        # Parse details if present (for backward compatibility)
        details = data.get("details")
        # Parse secrets if present (for backward compatibility)
        secrets = data.get("secrets")
        return cls(
            name=data["name"],
            description=data["description"],
            connections=data.get("connections", {}),
            npcs=npcs,
            coordinates=coordinates,
            category=category,
            ascii_art=ascii_art,
            details=details,
            secrets=secrets
        )
    
    def __str__(self) -> str:
        """Return a human-readable string representation of the location.

        Returns:
            A formatted string with name, ASCII art (if present), description, and exits
        """
        result = f"{colors.location(self.name)}\n"

        # Add ASCII art if present (after name, before description)
        if self.ascii_art:
            result += self.ascii_art.strip() + "\n"

        result += f"{self.description}\n"

        if self.npcs:
            npc_names = [colors.npc(npc.name) for npc in self.npcs]
            result += f"NPCs: {', '.join(npc_names)}\n"

        if self.connections:
            directions = self.get_available_directions()
            result += f"Exits: {', '.join(directions)}"
        else:
            result += "Exits: None"

        return result
