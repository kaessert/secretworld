"""Fallback ASCII art templates for NPC roles.

Provides get_fallback_npc_ascii_art() function that returns
appropriate ASCII art based on NPC role or name.
"""

from typing import Optional


# Merchant: someone selling goods
_ASCII_ART_MERCHANT = r"""
     ___
    /   \
   | o o |
    \ = /
   __| |__
  /  | |  \
 | $$|_|$$ |
"""

# Quest Giver: wise figure with scroll
_ASCII_ART_QUEST_GIVER = r"""
     _____
    /     \
   |  o o  |
    \  ~  /
   __|   |__
  /   ~~~   \
 |  [scroll] |
"""

# Villager: simple peasant
_ASCII_ART_VILLAGER = r"""
     ___
    (   )
   | o o |
    \ u /
     | |
    /   \
   |_____|
"""

# Guard: armored figure
_ASCII_ART_GUARD = r"""
    _____
   /|   |\
  | |o o| |
   \| = |/
    |   |
   /|   |\
  |_|___|_|
"""

# Elder: old wise person
_ASCII_ART_ELDER = r"""
     ~~~
    /   \
   | o o |
    \ ~ /
   __|_|__
  /  |||  \
 |___|_|___|
"""

# Blacksmith: muscular with hammer
_ASCII_ART_BLACKSMITH = r"""
     ___
    (   )
   | o o |
    \===/
    /| |\
   / | | \
  |__|_|__|
"""

# Innkeeper: friendly with mug
_ASCII_ART_INNKEEPER = r"""
     ___
    /   \
   | ^_^ |
    \ u /
     | |__
    /|   _|
   |_|__|
"""

# Default: generic person
_ASCII_ART_DEFAULT = r"""
     ___
    /   \
   | o o |
    \ - /
     | |
    /   \
   |_____|
"""


def get_fallback_npc_ascii_art(
    role: Optional[str],
    npc_name: str
) -> str:
    """Get fallback ASCII art based on NPC role or name.

    First tries to match by role, then falls back to name-based detection.

    Args:
        role: NPC role (merchant, quest_giver, villager, guard, elder,
              blacksmith, innkeeper) or None
        npc_name: Name of the NPC for name-based fallback

    Returns:
        ASCII art string (5-7 lines, max 40 chars wide)
    """
    # Role-based matching (primary)
    if role:
        role_lower = role.lower()
        if role_lower == "merchant":
            return _ASCII_ART_MERCHANT
        if role_lower == "quest_giver":
            return _ASCII_ART_QUEST_GIVER
        if role_lower == "villager":
            return _ASCII_ART_VILLAGER
        if role_lower == "guard":
            return _ASCII_ART_GUARD
        if role_lower == "elder":
            return _ASCII_ART_ELDER
        if role_lower == "blacksmith":
            return _ASCII_ART_BLACKSMITH
        if role_lower == "innkeeper":
            return _ASCII_ART_INNKEEPER

    # Name-based fallback detection
    name_lower = npc_name.lower()

    # Merchant keywords
    if any(term in name_lower for term in ["merchant", "trader", "vendor", "seller", "shopkeeper"]):
        return _ASCII_ART_MERCHANT

    # Quest giver keywords
    if any(term in name_lower for term in ["sage", "wizard", "mage", "seer", "oracle"]):
        return _ASCII_ART_QUEST_GIVER

    # Guard keywords
    if any(term in name_lower for term in ["guard", "soldier", "knight", "captain", "warrior"]):
        return _ASCII_ART_GUARD

    # Elder keywords
    if any(term in name_lower for term in ["elder", "elder", "chief", "patriarch", "matriarch"]):
        return _ASCII_ART_ELDER

    # Blacksmith keywords
    if any(term in name_lower for term in ["smith", "blacksmith", "forger", "weaponsmith", "armorer"]):
        return _ASCII_ART_BLACKSMITH

    # Innkeeper keywords
    if any(term in name_lower for term in ["innkeeper", "barkeep", "bartender", "tavernkeep", "host"]):
        return _ASCII_ART_INNKEEPER

    # Default to generic villager for unknown NPCs
    return _ASCII_ART_DEFAULT
