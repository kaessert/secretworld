"""Tile definitions and adjacency rules for Wave Function Collapse world generation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, List, Optional


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
