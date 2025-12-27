"""Location model for the game world."""

import hashlib
from dataclasses import dataclass, field
from typing import Any, ClassVar, List, Optional, Tuple, Union, TYPE_CHECKING

from cli_rpg import colors

if TYPE_CHECKING:
    from cli_rpg.models.npc import NPC
    from cli_rpg.world_grid import SubGrid
    from cli_rpg.wfc_chunks import ChunkManager


@dataclass
class Location:
    """Represents a location in the game world.

    A location has a name, description, and coordinates for grid-based navigation.
    Movement between locations is determined by coordinate adjacency.

    Attributes:
        name: The location's name (2-50 characters)
        description: The location's description (1-500 characters)
    """

    # Class constants
    MIN_NAME_LENGTH: ClassVar[int] = 2
    MAX_NAME_LENGTH: ClassVar[int] = 50
    MIN_DESCRIPTION_LENGTH: ClassVar[int] = 1
    MAX_DESCRIPTION_LENGTH: ClassVar[int] = 500
    VALID_DIRECTIONS: ClassVar[set[str]] = {"north", "south", "east", "west"}

    name: str
    description: str
    npcs: List["NPC"] = field(default_factory=list)
    # Coordinates can be 2D (x, y) for overworld or 3D (x, y, z) for SubGrid
    coordinates: Optional[Union[Tuple[int, int], Tuple[int, int, int]]] = None
    category: Optional[str] = None
    ascii_art: str = ""
    details: Optional[str] = None  # Second-look environmental details
    secrets: Optional[str] = None  # Third-look hidden secrets
    # Hierarchy fields for overworld/sub-location system
    is_overworld: bool = False  # Is this an overworld landmark?
    parent_location: Optional[str] = None  # Parent landmark (for sub-locations)
    sub_locations: List[str] = field(default_factory=list)  # Child locations
    is_safe_zone: bool = False  # No random encounters if True
    entry_point: Optional[str] = None  # Default sub-location when entering
    boss_enemy: Optional[str] = None  # Boss template name (e.g., "stone_sentinel")
    boss_defeated: bool = False  # True if boss has been defeated (prevents respawn)
    treasures: List[dict] = field(default_factory=list)  # Treasure chests with loot
    hidden_secrets: List[dict] = field(default_factory=list)  # Secrets with detection thresholds
    is_exit_point: bool = False  # Only these rooms allow 'exit' command
    sub_grid: Optional["SubGrid"] = None  # Interior grid for landmarks (overworld only)
    terrain: Optional[str] = None  # WFC terrain type (forest, plains, etc.)
    is_named: bool = False  # True for story-important POIs, False for terrain filler
    required_faction: Optional[str] = None  # Faction required for entry
    required_reputation: Optional[int] = None  # Min faction rep for entry (1-100)

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
    
    def get_available_directions(
        self,
        world: Optional[dict] = None,
        sub_grid: Optional["SubGrid"] = None,
    ) -> list[str]:
        """Get available exit directions based on adjacent locations.

        Checks neighboring coordinates for locations. Requires either a world dict
        or sub_grid to perform coordinate lookups.

        For SubGrid (interior navigation), includes vertical directions (up/down)
        when adjacent locations exist at different z-levels.

        Args:
            world: Optional world dict mapping names to Locations (for overworld)
            sub_grid: Optional SubGrid instance (for interior navigation)

        Returns:
            A sorted list of direction names with adjacent locations
        """
        if self.coordinates is None:
            return []

        directions = []
        x, y = self.coordinates[:2]
        z = self.coordinates[2] if len(self.coordinates) > 2 else 0

        if sub_grid is not None:
            # 3D navigation for SubGrid (includes up/down)
            offsets_3d = {
                "north": (0, 1, 0),
                "south": (0, -1, 0),
                "east": (1, 0, 0),
                "west": (-1, 0, 0),
                "up": (0, 0, 1),
                "down": (0, 0, -1),
            }
            for direction, (dx, dy, dz) in offsets_3d.items():
                target = (x + dx, y + dy, z + dz)
                # Check sub_grid for interior navigation
                if sub_grid.is_within_bounds(*target) and sub_grid.get_by_coordinates(*target):
                    directions.append(direction)
        elif world is not None:
            # 2D navigation for overworld
            offsets_2d = {
                "north": (0, 1),
                "south": (0, -1),
                "east": (1, 0),
                "west": (-1, 0),
            }
            for direction, (dx, dy) in offsets_2d.items():
                target = (x + dx, y + dy)
                # Check world dict for overworld navigation
                for loc in world.values():
                    if loc.coordinates == target:
                        directions.append(direction)
                        break

        return sorted(directions)

    def get_filtered_directions(
        self,
        chunk_manager: Optional["ChunkManager"],
        world: Optional[dict] = None,
        sub_grid: Optional["SubGrid"] = None,
    ) -> list[str]:
        """Get exit directions filtered by WFC terrain passability.

        For overworld navigation with WFC:
            Uses terrain passability directly (via get_valid_moves) to determine
            exits. This ensures exits are stable - they depend on terrain, not
            whether Location objects have been generated yet.

        For interior (SubGrid) navigation:
            Uses location-based logic (via get_available_directions) since
            interiors have predefined bounded layouts.

        Args:
            chunk_manager: Optional ChunkManager for WFC terrain lookup.
                          If None, returns all available directions.
            world: Optional world dict mapping names to Locations (for overworld)
            sub_grid: Optional SubGrid instance (for interior navigation)

        Returns:
            A sorted list of direction names with passable terrain
        """
        # For sub-grid locations (interiors), use location-based logic
        # Interiors have bounded grids with predefined room layouts
        if sub_grid is not None:
            return self.get_available_directions(sub_grid=sub_grid)

        # For overworld WITH WFC: use terrain passability directly
        # This ensures exits are stable (terrain doesn't depend on exploration)
        if chunk_manager is not None and self.coordinates is not None:
            from cli_rpg.world_tiles import get_valid_moves
            return get_valid_moves(chunk_manager, self.coordinates[0], self.coordinates[1])

        # Fallback (no WFC): use existing location-based logic
        return self.get_available_directions(world=world, sub_grid=sub_grid)

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

    def get_z(self) -> int:
        """Get the z-coordinate (vertical level) of this location.

        Returns 0 if coordinates are None or 2D (no z component).
        For 3D coordinates, returns the z value.

        Returns:
            The z-coordinate, or 0 if not applicable
        """
        if self.coordinates is None:
            return 0
        if len(self.coordinates) == 3:
            return self.coordinates[2]
        return 0

    def get_layered_description(
        self,
        look_count: int = 1,
        visibility: str = "full",
        chunk_manager: Optional["ChunkManager"] = None,
        world: Optional[dict] = None,
        sub_grid: Optional["SubGrid"] = None,
    ) -> str:
        """Get description with appropriate layers based on look count and visibility.

        Args:
            look_count: Number of times player has looked at this location
            visibility: Visibility level affecting what's shown:
                - "full": Everything shown normally
                - "reduced": Description truncated to first sentence, no details/secrets
                - "obscured": Some exits hidden (50% each)
            chunk_manager: Optional ChunkManager for WFC terrain-based exit filtering.
                          When provided, exits to impassable terrain are hidden.
            world: Optional world dict mapping names to Locations (for overworld)
            sub_grid: Optional SubGrid instance (for interior navigation)

        Returns:
            Formatted string with name, description, and appropriate detail layers
        """
        result = f"{colors.location(self.name)}\n"

        # Add ASCII art if present (after name, before description)
        if self.ascii_art:
            result += self.ascii_art.rstrip() + "\n"

        # Handle description based on visibility
        description = self.description
        if visibility == "reduced":
            # Truncate to first sentence
            for delimiter in [". ", "! ", "? "]:
                if delimiter in description:
                    description = description.split(delimiter)[0] + delimiter[0]
                    break
        result += f"{description}\n"

        # NPCs are always visible at the player's current location
        if self.npcs:
            npc_names = [colors.npc(npc.name) for npc in self.npcs]
            result += f"NPCs: {', '.join(npc_names)}\n"

        # Handle exits based on visibility and WFC terrain passability
        directions = self.get_filtered_directions(chunk_manager, world=world, sub_grid=sub_grid)
        if directions:
            if visibility == "obscured":
                # Hide ~50% of remaining exits, seeded by location name for consistency
                directions = self._filter_exits_for_fog(directions)
            result += f"Exits: {', '.join(directions)}"
        else:
            result += "Exits: None"

        # Show sub-locations if any exist
        if self.sub_grid is not None:
            # Only show entry point for sub_grid locations
            if self.entry_point:
                result += f"\nEnter: {colors.location(self.entry_point)}"
            else:
                # Find first is_exit_point location in sub_grid
                for loc in self.sub_grid._by_name.values():
                    if loc.is_exit_point:
                        result += f"\nEnter: {colors.location(loc.name)}"
                        break
        elif self.sub_locations:
            sub_loc_names = [colors.location(name) for name in self.sub_locations]
            result += f"\nEnter: {', '.join(sub_loc_names)}"

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
            "npcs": [npc.to_dict() for npc in self.npcs]
        }
        # Only include coordinates if present (backward compatibility)
        # Serialize as 2 or 3 elements depending on tuple length
        if self.coordinates is not None:
            data["coordinates"] = list(self.coordinates)
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
        # Only include hierarchy fields if non-default (backward compatibility)
        if self.is_overworld:
            data["is_overworld"] = self.is_overworld
        if self.parent_location is not None:
            data["parent_location"] = self.parent_location
        if self.sub_locations:
            data["sub_locations"] = self.sub_locations.copy()
        if self.is_safe_zone:
            data["is_safe_zone"] = self.is_safe_zone
        if self.entry_point is not None:
            data["entry_point"] = self.entry_point
        if self.boss_enemy is not None:
            data["boss_enemy"] = self.boss_enemy
        if self.boss_defeated:
            data["boss_defeated"] = self.boss_defeated
        if self.treasures:
            data["treasures"] = self.treasures.copy()
        if self.hidden_secrets:
            data["hidden_secrets"] = [secret.copy() for secret in self.hidden_secrets]
        if self.is_exit_point:
            data["is_exit_point"] = self.is_exit_point
        if self.sub_grid is not None:
            data["sub_grid"] = self.sub_grid.to_dict()
        if self.terrain is not None:
            data["terrain"] = self.terrain
        if self.is_named:
            data["is_named"] = self.is_named
        if self.required_faction is not None:
            data["required_faction"] = self.required_faction
        if self.required_reputation is not None:
            data["required_reputation"] = self.required_reputation
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
        # Supports both 2D (x, y) and 3D (x, y, z) coordinates
        coordinates = None
        if "coordinates" in data and data["coordinates"] is not None:
            coords = data["coordinates"]
            coordinates = tuple(coords)  # Preserve 2D or 3D as-is
        # Parse category if present (for backward compatibility)
        category = data.get("category")
        # Parse ascii_art if present (for backward compatibility)
        ascii_art = data.get("ascii_art", "")
        # Parse details if present (for backward compatibility)
        details = data.get("details")
        # Parse secrets if present (for backward compatibility)
        secrets = data.get("secrets")
        # Parse hierarchy fields if present (backward compatibility)
        is_overworld = data.get("is_overworld", False)
        parent_location = data.get("parent_location")
        sub_locations = data.get("sub_locations", [])
        is_safe_zone = data.get("is_safe_zone", False)
        entry_point = data.get("entry_point")
        # Parse boss fields if present (backward compatibility)
        boss_enemy = data.get("boss_enemy")
        boss_defeated = data.get("boss_defeated", False)
        # Parse treasures if present (backward compatibility)
        treasures = data.get("treasures", [])
        # Parse hidden_secrets if present (backward compatibility)
        hidden_secrets = data.get("hidden_secrets", [])
        # Parse is_exit_point if present (backward compatibility)
        is_exit_point = data.get("is_exit_point", False)
        # Parse sub_grid if present (backward compatibility)
        sub_grid = None
        if "sub_grid" in data:
            from cli_rpg.world_grid import SubGrid
            sub_grid = SubGrid.from_dict(data["sub_grid"])
        # Parse terrain if present (backward compatibility)
        terrain = data.get("terrain")
        # Parse is_named if present (backward compatibility)
        is_named = data.get("is_named", False)
        # Parse faction requirement fields (backward compatibility)
        required_faction = data.get("required_faction")
        required_reputation = data.get("required_reputation")
        # Note: Legacy 'connections' field is ignored if present (backward compatibility)
        return cls(
            name=data["name"],
            description=data["description"],
            npcs=npcs,
            coordinates=coordinates,
            category=category,
            ascii_art=ascii_art,
            details=details,
            secrets=secrets,
            is_overworld=is_overworld,
            parent_location=parent_location,
            sub_locations=sub_locations,
            is_safe_zone=is_safe_zone,
            entry_point=entry_point,
            boss_enemy=boss_enemy,
            boss_defeated=boss_defeated,
            treasures=treasures,
            hidden_secrets=hidden_secrets,
            is_exit_point=is_exit_point,
            sub_grid=sub_grid,
            terrain=terrain,
            is_named=is_named,
            required_faction=required_faction,
            required_reputation=required_reputation,
        )
    
    def __str__(self) -> str:
        """Return a human-readable string representation of the location.

        Returns:
            A formatted string with name, ASCII art (if present), description, and exits
        """
        result = f"{colors.location(self.name)}\n"

        # Add ASCII art if present (after name, before description)
        if self.ascii_art:
            result += self.ascii_art.rstrip() + "\n"

        result += f"{self.description}\n"

        if self.npcs:
            npc_names = [colors.npc(npc.name) for npc in self.npcs]
            result += f"NPCs: {', '.join(npc_names)}\n"

        # Note: __str__ cannot show exits without world/sub_grid context
        # Use get_layered_description() for full exit display
        result += "Exits: (use look command)"

        if self.sub_grid is not None:
            # Only show entry point for sub_grid locations
            if self.entry_point:
                result += f"\nEnter: {self.entry_point}"
            else:
                # Find first is_exit_point location in sub_grid
                for loc in self.sub_grid._by_name.values():
                    if loc.is_exit_point:
                        result += f"\nEnter: {loc.name}"
                        break
        elif self.sub_locations:
            result += f"\nEnter: {', '.join(self.sub_locations)}"

        return result
