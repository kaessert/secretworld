"""Location-specific encounter tables for random encounters.

Provides category-specific enemy pools, encounter rates, and merchant inventories
for different location types (dungeons, caves, ruins, forests, temples, etc.).

Issue 21: Location-Specific Random Encounters
"""

# Default encounter rate (15%) - used when category is unknown
DEFAULT_ENCOUNTER_RATE = 0.15

# Category-specific enemy tables
# Spec: Different enemy pools for dungeon, cave, ruins, forest, temple
CATEGORY_ENEMIES: dict[str, list[str]] = {
    # Dungeon: undead, constructs, cultists
    "dungeon": [
        "Skeleton Warrior",
        "Zombie",
        "Stone Construct",
        "Cultist",
        "Bone Golem",
        "Dark Acolyte",
    ],
    # Cave: beasts, spiders, giant bats
    "cave": [
        "Giant Spider",
        "Cave Bear",
        "Giant Bat",
        "Goblin",
        "Troll",
        "Cave Beetle",
    ],
    # Ruins: ghosts, treasure hunters, golems
    "ruins": [
        "Restless Ghost",
        "Stone Golem",
        "Treasure Hunter",
        "Phantom",
        "Ancient Guardian",
        "Ruin Lurker",
    ],
    # Forest: wolves, bandits, fey creatures
    "forest": [
        "Wolf",
        "Bandit",
        "Wild Boar",
        "Dryad",
        "Forest Spirit",
        "Giant Spider",
    ],
    # Temple: dark priests, animated statues
    "temple": [
        "Dark Priest",
        "Animated Statue",
        "Temple Guardian",
        "Cultist Zealot",
        "Stone Sentinel",
        "Shadow Monk",
    ],
}

# Default enemies when category is unknown
DEFAULT_ENEMIES: list[str] = ["Bandit", "Wild Beast", "Wandering Spirit", "Rogue"]

# Category-specific encounter rates
# Higher values = more frequent encounters
CATEGORY_ENCOUNTER_RATES: dict[str, float] = {
    "dungeon": 0.25,  # Higher danger - frequent encounters
    "cave": 0.20,
    "ruins": 0.20,
    "temple": 0.20,
    "forest": 0.15,  # Default overworld rate
    "town": 0.05,  # Safe zones - rare encounters
    "village": 0.05,
    "city": 0.05,
}

# Category-specific merchant item templates
# These are item type keywords that influence what wandering merchants sell
CATEGORY_MERCHANT_ITEMS: dict[str, list[str]] = {
    "dungeon": ["healing_potion", "antidote", "torch"],
    "cave": ["torch", "rope", "healing_potion"],
    "ruins": ["lockpick", "healing_potion", "antidote"],
    "temple": ["holy_water", "healing_potion", "blessed_charm"],
    "forest": ["rations", "healing_potion", "rope"],
}

# Default merchant items when category is unknown
DEFAULT_MERCHANT_ITEMS: list[str] = ["healing_potion", "torch", "rations"]

# Night undead modifier (50% increase)
# Issue 27: Undead enemies are more active at night
UNDEAD_NIGHT_ENCOUNTER_MODIFIER = 1.5

# Categories that have undead enemies
UNDEAD_CATEGORIES = {"dungeon", "ruins", "cave"}


def get_enemies_for_category(category: str) -> list[str]:
    """Get enemy list for a location category.

    Args:
        category: Location category (e.g., "dungeon", "cave", "ruins")

    Returns:
        List of enemy names appropriate for the category,
        or DEFAULT_ENEMIES if category is unknown
    """
    return CATEGORY_ENEMIES.get(category, DEFAULT_ENEMIES)


def get_encounter_rate(category: str) -> float:
    """Get encounter rate for a location category.

    Args:
        category: Location category (e.g., "dungeon", "cave", "town")

    Returns:
        Encounter probability (0.0 to 1.0),
        or DEFAULT_ENCOUNTER_RATE if category is unknown
    """
    return CATEGORY_ENCOUNTER_RATES.get(category, DEFAULT_ENCOUNTER_RATE)


def get_merchant_items(category: str) -> list[str]:
    """Get merchant item templates for a location category.

    Args:
        category: Location category (e.g., "dungeon", "cave")

    Returns:
        List of item template keywords for the category,
        or DEFAULT_MERCHANT_ITEMS if category is unknown
    """
    return CATEGORY_MERCHANT_ITEMS.get(category, DEFAULT_MERCHANT_ITEMS)


def get_undead_night_modifier(category: str, is_night: bool) -> float:
    """Get encounter rate modifier for undead at night.

    Issue 27: Undead enemies are more active at night.
    At night (18:00-5:59), undead encounter rates increase by 50%.

    Args:
        category: Location category (e.g., "dungeon", "cave", "ruins")
        is_night: Whether it's currently night

    Returns:
        1.5 if night and undead category, 1.0 otherwise
    """
    if is_night and category in UNDEAD_CATEGORIES:
        return UNDEAD_NIGHT_ENCOUNTER_MODIFIER
    return 1.0
