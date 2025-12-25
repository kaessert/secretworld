"""Fallback ASCII art templates for location categories.

Provides get_fallback_location_ascii_art() function that returns
appropriate ASCII art based on location category or name.
"""

from typing import Optional


# Town/city: buildings and shops
_ASCII_ART_TOWN = r"""
     ___     ___
    /   \   /   \
   |  _  | |  _  |
   | |_| | | |_| |
   |_____|_|_____|
    |  |   |  |
"""

# Village: small houses
_ASCII_ART_VILLAGE = r"""
      /\
     /  \
    /    \
   |  __  |
   | |  | |
   |_|__|_|
"""

# Forest: trees
_ASCII_ART_FOREST = r"""
      /\
     /  \
    /    \
   /______\
      ||
   /\||||/\
  /  \||/  \
"""

# Dungeon: dark entrance
_ASCII_ART_DUNGEON = r"""
   ___________
  |           |
  |   _____   |
  |  |     |  |
  |  |  .  |  |
  |__|     |__|
     |_____|
"""

# Cave: cavern opening
_ASCII_ART_CAVE = r"""
       ___
    __/   \__
   /         \
  |   ~   ~   |
   \   ___   /
    \_/   \_/
"""

# Ruins: crumbling structures
_ASCII_ART_RUINS = r"""
     _   _
    | |_| |
   _|     |_
  |  ___    |
  | |   |   '
  |_|   |___|
"""

# Mountain: peaks
_ASCII_ART_MOUNTAIN = r"""
       /\
      /  \
     /    \
    /  /\  \
   /  /  \  \
  /__/____\__\
"""

# Wilderness: open landscape
_ASCII_ART_WILDERNESS = r"""
           ~
    ~~~       ~~~
  ~~~~~~~~~~~~~~~~~
 ___________________
      ~     ~
   ~     ~     ~
"""

# Settlement: mixed buildings
_ASCII_ART_SETTLEMENT = r"""
    /\    /\
   /  \  /  \
  |    ||    |
  | [] || [] |
  |____||____|
"""


def get_fallback_location_ascii_art(
    category: Optional[str],
    location_name: str
) -> str:
    """Get fallback ASCII art based on location category or name.

    First tries to match by category, then falls back to name-based detection.

    Args:
        category: Location category (town, village, forest, dungeon, cave,
                  ruins, mountain, wilderness, settlement) or None
        location_name: Name of the location for name-based fallback

    Returns:
        ASCII art string (5-10 lines, max 50 chars wide)
    """
    # Category-based matching (primary)
    if category:
        category_lower = category.lower()
        if category_lower == "town":
            return _ASCII_ART_TOWN
        if category_lower == "village":
            return _ASCII_ART_VILLAGE
        if category_lower == "forest":
            return _ASCII_ART_FOREST
        if category_lower == "dungeon":
            return _ASCII_ART_DUNGEON
        if category_lower == "cave":
            return _ASCII_ART_CAVE
        if category_lower == "ruins":
            return _ASCII_ART_RUINS
        if category_lower == "mountain":
            return _ASCII_ART_MOUNTAIN
        if category_lower == "wilderness":
            return _ASCII_ART_WILDERNESS
        if category_lower == "settlement":
            return _ASCII_ART_SETTLEMENT

    # Name-based fallback detection
    name_lower = location_name.lower()

    # Town/city keywords
    if any(term in name_lower for term in ["town", "city", "market", "bazaar", "plaza"]):
        return _ASCII_ART_TOWN

    # Village keywords
    if any(term in name_lower for term in ["village", "hamlet", "homestead"]):
        return _ASCII_ART_VILLAGE

    # Forest keywords
    if any(term in name_lower for term in ["forest", "wood", "grove", "glade", "thicket"]):
        return _ASCII_ART_FOREST

    # Dungeon keywords
    if any(term in name_lower for term in ["dungeon", "crypt", "tomb", "prison", "keep"]):
        return _ASCII_ART_DUNGEON

    # Cave keywords
    if any(term in name_lower for term in ["cave", "cavern", "grotto", "hollow"]):
        return _ASCII_ART_CAVE

    # Ruins keywords
    if any(term in name_lower for term in ["ruins", "ruin", "ancient", "temple", "shrine"]):
        return _ASCII_ART_RUINS

    # Mountain keywords
    if any(term in name_lower for term in ["mountain", "peak", "summit", "cliff", "ridge"]):
        return _ASCII_ART_MOUNTAIN

    # Settlement keywords
    if any(term in name_lower for term in ["camp", "outpost", "fort", "post", "settlement"]):
        return _ASCII_ART_SETTLEMENT

    # Default to wilderness for unknown locations
    return _ASCII_ART_WILDERNESS
