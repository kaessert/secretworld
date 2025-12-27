"""Tile definitions and adjacency rules for Wave Function Collapse world generation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.wfc_chunks import ChunkManager


# Region planning constants
REGION_SIZE = 16  # 16x16 tiles per region
REGION_BOUNDARY_PROXIMITY = 2  # Pre-generate when within 2 tiles of boundary


def get_region_coords(world_x: int, world_y: int) -> tuple[int, int]:
    """Convert world coordinates to region coordinates.

    Uses floor division to handle negative coordinates correctly.

    Args:
        world_x: World x coordinate
        world_y: World y coordinate

    Returns:
        Tuple of (region_x, region_y) coordinates
    """
    return (world_x // REGION_SIZE, world_y // REGION_SIZE)


def check_region_boundary_proximity(
    world_x: int, world_y: int
) -> list[tuple[int, int]]:
    """Return adjacent region coords if player is within REGION_BOUNDARY_PROXIMITY of boundary.

    Checks all 4 cardinal directions plus diagonals to detect when player is
    approaching region boundaries.

    Args:
        world_x: World x coordinate
        world_y: World y coordinate

    Returns:
        List of adjacent region coordinate tuples that should be pre-generated
    """
    current_region = get_region_coords(world_x, world_y)
    adjacent_regions: list[tuple[int, int]] = []

    # Calculate position within current region (0 to REGION_SIZE-1)
    local_x = world_x % REGION_SIZE
    local_y = world_y % REGION_SIZE

    # Handle negative coordinates - Python's modulo always returns positive
    # but we need to account for being in negative regions
    if world_x < 0 and local_x != 0:
        local_x = REGION_SIZE + (world_x % REGION_SIZE)
    if world_y < 0 and local_y != 0:
        local_y = REGION_SIZE + (world_y % REGION_SIZE)

    # Check proximity to each edge
    near_east = local_x >= REGION_SIZE - REGION_BOUNDARY_PROXIMITY
    near_west = local_x < REGION_BOUNDARY_PROXIMITY
    near_north = local_y >= REGION_SIZE - REGION_BOUNDARY_PROXIMITY
    near_south = local_y < REGION_BOUNDARY_PROXIMITY

    # Add adjacent regions based on proximity
    if near_east:
        adjacent_regions.append((current_region[0] + 1, current_region[1]))
    if near_west:
        adjacent_regions.append((current_region[0] - 1, current_region[1]))
    if near_north:
        adjacent_regions.append((current_region[0], current_region[1] + 1))
    if near_south:
        adjacent_regions.append((current_region[0], current_region[1] - 1))

    # Add diagonal corners if near both edges
    if near_east and near_north:
        adjacent_regions.append((current_region[0] + 1, current_region[1] + 1))
    if near_east and near_south:
        adjacent_regions.append((current_region[0] + 1, current_region[1] - 1))
    if near_west and near_north:
        adjacent_regions.append((current_region[0] - 1, current_region[1] + 1))
    if near_west and near_south:
        adjacent_regions.append((current_region[0] - 1, current_region[1] - 1))

    return adjacent_regions


class TerrainType(Enum):
    """Terrain types for WFC generation."""
    FOREST = "forest"
    MOUNTAIN = "mountain"
    PLAINS = "plains"
    WATER = "water"
    DESERT = "desert"
    SWAMP = "swamp"
    HILLS = "hills"
    BEACH = "beach"
    FOOTHILLS = "foothills"


# Adjacency rules: which terrain types can be adjacent to each other
# Key = terrain type, Value = set of valid adjacent terrain types
ADJACENCY_RULES: Dict[str, Set[str]] = {
    "forest": {"forest", "plains", "hills", "swamp", "foothills"},
    "mountain": {"mountain", "hills", "foothills"},
    "plains": {"plains", "forest", "hills", "desert", "beach", "foothills"},
    "water": {"water", "beach", "swamp"},
    "desert": {"desert", "plains", "hills", "beach"},
    "swamp": {"swamp", "forest", "water", "plains"},
    "hills": {"hills", "forest", "plains", "mountain", "foothills", "desert"},
    "beach": {"beach", "water", "plains", "forest", "desert"},
    "foothills": {"foothills", "hills", "mountain", "plains", "forest"},
}

# Frequency weights for terrain generation (higher = more common)
TERRAIN_WEIGHTS: Dict[str, float] = {
    "forest": 2.0,
    "mountain": 0.8,
    "plains": 2.5,
    "water": 1.0,
    "desert": 0.6,
    "swamp": 0.5,
    "hills": 1.5,
    "beach": 0.4,
    "foothills": 0.8,
}


# Region terrain biases for coherent mega-biomes
# Maps region theme -> terrain type -> weight multiplier
# Boosted (3x): terrain strongly associated with region theme
# Normal (1x): neutral terrain
# Reduced (0.3x): terrain incompatible with region theme
REGION_TERRAIN_BIASES: Dict[str, Dict[str, float]] = {
    "mountains": {
        "mountain": 3.0, "foothills": 3.0, "hills": 3.0,  # Boosted
        "plains": 1.0, "forest": 1.0,  # Normal
        "beach": 0.3, "swamp": 0.3, "desert": 0.3, "water": 0.3,  # Reduced
    },
    "forest": {
        "forest": 3.0,  # Boosted
        "plains": 1.0, "hills": 1.0, "swamp": 1.0,  # Normal
        "mountain": 0.3, "desert": 0.3, "beach": 0.3, "water": 0.3, "foothills": 0.3,
    },
    "swamp": {
        "swamp": 3.0, "forest": 3.0, "water": 3.0,  # Boosted
        "plains": 1.0,  # Normal
        "mountain": 0.3, "desert": 0.3, "beach": 0.3, "hills": 0.3, "foothills": 0.3,
    },
    "desert": {
        "desert": 3.0, "plains": 3.0,  # Boosted
        "hills": 1.0, "beach": 1.0,  # Normal
        "forest": 0.3, "swamp": 0.3, "mountain": 0.3, "water": 0.3, "foothills": 0.3,
    },
    "coastal": {
        "beach": 3.0, "water": 3.0, "plains": 3.0,  # Boosted
        "forest": 1.0,  # Normal
        "mountain": 0.3, "swamp": 0.3, "desert": 0.3, "hills": 0.3, "foothills": 0.3,
    },
    "beach": {  # Alias for coastal
        "beach": 3.0, "water": 3.0, "plains": 3.0,  # Boosted
        "forest": 1.0,  # Normal
        "mountain": 0.3, "swamp": 0.3, "desert": 0.3, "hills": 0.3, "foothills": 0.3,
    },
    "plains": {
        "plains": 3.0, "forest": 3.0, "hills": 3.0,  # Boosted
        # Everything else at normal weight (1x default)
    },
    "wilderness": {
        "plains": 3.0, "forest": 3.0, "hills": 3.0,  # Boosted
        # Everything else at normal weight (1x default)
    },
}


def get_biased_weights(region_theme: str) -> Dict[str, float]:
    """Get terrain weights modified by region theme bias.

    Applies multipliers from REGION_TERRAIN_BIASES to base TERRAIN_WEIGHTS
    to create biased weight distributions for WFC generation.

    Args:
        region_theme: Region theme name (e.g., "mountains", "forest", "swamp")

    Returns:
        Dictionary mapping terrain types to biased weights.
        Returns unmodified TERRAIN_WEIGHTS if theme is unknown.
    """
    biases = REGION_TERRAIN_BIASES.get(region_theme.lower())

    if biases is None:
        # Unknown theme - return base weights unchanged
        return TERRAIN_WEIGHTS.copy()

    # Apply multipliers to base weights
    biased_weights = {}
    for terrain, base_weight in TERRAIN_WEIGHTS.items():
        # Use bias multiplier if defined, otherwise 1.0 (unchanged)
        multiplier = biases.get(terrain, 1.0)
        biased_weights[terrain] = base_weight * multiplier

    return biased_weights


# Location types that can spawn on each terrain
TERRAIN_TO_LOCATIONS: Dict[str, List[str]] = {
    "forest": ["ruins", "grove", "hermit_hut", "bandit_camp", "ancient_tree", "hunter_lodge"],
    "mountain": ["cave", "mine", "peak", "monastery", "eagle_nest", "frozen_pass"],
    "plains": ["village", "farm", "crossroads", "tower", "windmill", "merchant_camp"],
    "water": [],  # Impassable - no locations
    "desert": ["oasis", "tomb", "abandoned_outpost", "sand_temple", "nomad_camp"],
    "swamp": ["witch_hut", "sunken_ruins", "fishing_village", "frog_shrine", "dead_tree"],
    "hills": ["watchtower", "shepherd_camp", "ancient_stones", "hill_fort", "burial_mound"],
    "beach": ["dock", "shipwreck", "lighthouse", "fishing_hut", "sea_cave"],
    "foothills": ["mountain_pass", "inn", "mining_camp", "hermit_cave", "hot_springs"],
}

# Probability of a location spawning on a tile (0.0 to 1.0)
LOCATION_SPAWN_CHANCE: float = 0.3

# Whether terrain is passable
TERRAIN_PASSABLE: Dict[str, bool] = {
    "forest": True,
    "mountain": True,
    "plains": True,
    "water": False,  # Cannot walk on water
    "desert": True,
    "swamp": True,
    "hills": True,
    "beach": True,
    "foothills": True,
}

# Terrain that players can traverse (derived from TERRAIN_PASSABLE)
PASSABLE_TERRAIN: frozenset = frozenset(
    terrain for terrain, passable in TERRAIN_PASSABLE.items() if passable
)

# Terrain that blocks movement
IMPASSABLE_TERRAIN: frozenset = frozenset(
    terrain for terrain, passable in TERRAIN_PASSABLE.items() if not passable
)

# Direction offsets for coordinate navigation
DIRECTION_OFFSETS: Dict[str, tuple] = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0),
}

# Dread modifier per terrain type
TERRAIN_DREAD_MODIFIER: Dict[str, int] = {
    "forest": 3,
    "mountain": 5,
    "plains": 0,
    "water": 0,
    "desert": 4,
    "swamp": 8,
    "hills": 2,
    "beach": 0,
    "foothills": 3,
}

# Category mapping for location generation
TERRAIN_TO_CATEGORY: Dict[str, str] = {
    "forest": "forest",
    "mountain": "mountain",
    "plains": "wilderness",
    "water": "water",
    "desert": "desert",
    "swamp": "swamp",
    "hills": "wilderness",
    "beach": "beach",
    "foothills": "mountain",
}


@dataclass
class TileDefinition:
    """Definition of a terrain tile type."""
    name: str
    weight: float
    passable: bool
    dread_modifier: int
    category: str
    valid_neighbors: Set[str]
    location_types: List[str]


@dataclass
class TileRegistry:
    """Registry of all tile definitions."""
    tiles: Dict[str, TileDefinition] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize with default tiles if empty."""
        if not self.tiles:
            self._load_default_tiles()

    def _load_default_tiles(self) -> None:
        """Load default tile definitions from constants."""
        for terrain in TerrainType:
            name = terrain.value
            self.tiles[name] = TileDefinition(
                name=name,
                weight=TERRAIN_WEIGHTS.get(name, 1.0),
                passable=TERRAIN_PASSABLE.get(name, True),
                dread_modifier=TERRAIN_DREAD_MODIFIER.get(name, 0),
                category=TERRAIN_TO_CATEGORY.get(name, "wilderness"),
                valid_neighbors=ADJACENCY_RULES.get(name, set()),
                location_types=TERRAIN_TO_LOCATIONS.get(name, []),
            )

    def get_tile(self, name: str) -> Optional[TileDefinition]:
        """Get a tile definition by name."""
        return self.tiles.get(name)

    def get_all_tile_names(self) -> Set[str]:
        """Get all registered tile names."""
        return set(self.tiles.keys())

    def get_valid_neighbors(self, tile_name: str) -> Set[str]:
        """Get valid neighbor tiles for a given tile."""
        tile = self.tiles.get(tile_name)
        if tile:
            return tile.valid_neighbors
        return set()

    def is_passable(self, tile_name: str) -> bool:
        """Check if a tile type is passable."""
        tile = self.tiles.get(tile_name)
        return tile.passable if tile else False

    def get_weight(self, tile_name: str) -> float:
        """Get the weight of a tile type."""
        tile = self.tiles.get(tile_name)
        return tile.weight if tile else 1.0


# Global default registry
DEFAULT_TILE_REGISTRY = TileRegistry()


# Unnamed location templates by terrain type
# Each terrain has a list of (name_template, description_template) tuples
UNNAMED_LOCATION_TEMPLATES: Dict[str, List[tuple]] = {
    "forest": [
        ("Dense Woods", "Tall trees crowd together, their canopy blocking most sunlight."),
        ("Wooded Trail", "A narrow path winds through towering oaks and elms."),
        ("Forest Clearing", "A small gap in the trees lets dappled light through."),
    ],
    "mountain": [
        ("Rocky Pass", "Jagged peaks rise on either side of this narrow mountain trail."),
        ("Steep Cliffs", "The path hugs a sheer rock face, wind howling past."),
        ("Alpine Meadow", "A grassy plateau offers respite between stone peaks."),
    ],
    "plains": [
        ("Open Grassland", "Tall grass sways in the wind under an open sky."),
        ("Rolling Hills", "Gentle slopes covered in wildflowers stretch to the horizon."),
        ("Dusty Road", "A well-worn path cuts through the flat landscape."),
    ],
    "water": [
        ("Riverbank", "The sound of rushing water fills the air."),
    ],
    "desert": [
        ("Sand Dunes", "Endless waves of golden sand shimmer in the heat."),
        ("Rocky Desert", "Cracked earth and scattered boulders dot the wasteland."),
        ("Desert Trail", "A faint path marks where others have crossed before."),
    ],
    "swamp": [
        ("Murky Bog", "Dark water pools between twisted, moss-covered trees."),
        ("Fetid Marsh", "The air hangs thick with moisture and decay."),
        ("Swamp Trail", "Rotting planks form a rickety path over the mire."),
    ],
    "hills": [
        ("Grassy Knoll", "A gentle slope offers a view of the surrounding land."),
        ("Hilltop Path", "The trail winds up and down rolling terrain."),
        ("Valley Floor", "You walk between two grass-covered rises."),
    ],
    "beach": [
        ("Sandy Shore", "Waves lap at the golden sand beneath your feet."),
        ("Rocky Beach", "Tide pools dot the coast between weathered stones."),
        ("Coastal Path", "A trail follows the line where land meets sea."),
    ],
    "foothills": [
        ("Mountain Base", "The terrain rises sharply toward distant peaks."),
        ("Foothill Trail", "A winding path leads up from the lowlands."),
        ("Rocky Slope", "Scattered boulders mark the transition to mountains."),
    ],
}


def get_unnamed_location_template(terrain: str) -> tuple:
    """Get a random unnamed location template for a terrain type.

    Args:
        terrain: Terrain type (forest, plains, mountain, etc.)

    Returns:
        Tuple of (name, description) for the unnamed location
    """
    import random
    templates = UNNAMED_LOCATION_TEMPLATES.get(terrain, UNNAMED_LOCATION_TEMPLATES["plains"])
    return random.choice(templates)


def is_passable(terrain: str) -> bool:
    """Check if a terrain type allows player movement.

    Args:
        terrain: Terrain type name (e.g., "forest", "water")

    Returns:
        True if the terrain is passable, False for impassable or unknown terrain
    """
    return terrain in PASSABLE_TERRAIN


def get_valid_moves(chunk_manager: "ChunkManager", x: int, y: int) -> List[str]:
    """Return sorted list of valid cardinal directions from position based on terrain passability.

    Args:
        chunk_manager: ChunkManager instance for terrain lookups
        x: Current x coordinate
        y: Current y coordinate

    Returns:
        Sorted list of valid direction names (e.g., ["east", "north", "south", "west"])
    """
    valid_directions = []

    for direction, (dx, dy) in DIRECTION_OFFSETS.items():
        target_x = x + dx
        target_y = y + dy
        terrain = chunk_manager.get_tile_at(target_x, target_y)

        if is_passable(terrain):
            valid_directions.append(direction)

    return sorted(valid_directions)


# Configuration for named location generation
NAMED_LOCATION_CONFIG = {
    "base_interval": 15,  # Generate named location every N tiles on average
    "terrain_modifiers": {
        # Terrain types more likely to have POIs
        "mountain": 0.6,  # 60% of base interval → more POIs
        "swamp": 0.7,
        "foothills": 0.8,
        "forest": 1.0,  # Normal
        "plains": 1.2,  # Slightly fewer POIs
        "hills": 1.0,
        "beach": 0.8,
        "desert": 0.9,
        "water": 999.0,  # Never (impassable)
    },
}


def should_generate_named_location(
    tiles_since_named: int,
    terrain: str,
    rng: Optional["random.Random"] = None
) -> bool:
    """Determine if a named location should be generated.

    Uses a probability curve that increases with tiles since last named.
    Terrain type modifies the effective interval.

    Args:
        tiles_since_named: Number of tiles traveled since last named location
        terrain: Current terrain type
        rng: Optional random number generator for determinism

    Returns:
        True if a named location should be generated
    """
    import random as random_module

    if rng is None:
        rng = random_module.Random()

    base_interval = NAMED_LOCATION_CONFIG["base_interval"]
    modifier = NAMED_LOCATION_CONFIG["terrain_modifiers"].get(terrain, 1.0)
    effective_interval = base_interval * modifier

    # Probability increases linearly from 0 at tile 0 to 100% at 2x interval
    # At interval, probability is 50%
    probability = min(1.0, tiles_since_named / (effective_interval * 2))

    return rng.random() < probability
