"""Faction-based content gating for NPCs, locations, and shops.

This module provides reputation-based access control:
- NPCs can require minimum faction reputation to interact
- Locations can require minimum faction reputation to enter
- NPCs from hostile factions refuse dialogue
- Faction-aware greeting modifiers enhance NPC interactions
"""

from typing import List, Optional, Tuple

from cli_rpg.models.faction import Faction, ReputationLevel
from cli_rpg.models.npc import NPC
from cli_rpg.models.location import Location


def _find_faction_by_name(factions: List[Faction], name: str) -> Optional[Faction]:
    """Find a faction by name (case-insensitive).

    Args:
        factions: List of player's faction standings
        name: Faction name to find

    Returns:
        Faction if found, None otherwise
    """
    name_lower = name.lower()
    for faction in factions:
        if faction.name.lower() == name_lower:
            return faction
    return None


def check_npc_access(npc: NPC, factions: List[Faction]) -> Tuple[bool, str]:
    """Check if player can interact with an NPC based on faction reputation.

    Access is blocked if:
    - NPC has a faction and player's standing with that faction is HOSTILE
    - NPC has required_reputation and player doesn't meet the threshold
    - NPC has required_reputation but player has no standing with that faction

    Args:
        npc: The NPC to check access for
        factions: List of player's faction standings

    Returns:
        Tuple of (allowed: bool, message: str)
        If allowed, message is empty string
        If blocked, message explains why
    """
    # No faction = always accessible
    if not npc.faction:
        return True, ""

    # Find player's standing with the NPC's faction
    faction = _find_faction_by_name(factions, npc.faction)

    # If NPC has a required reputation but player has no standing with the faction
    if npc.required_reputation is not None and faction is None:
        return False, (
            f"{npc.name} refuses to speak with you. "
            f"Your reputation with {npc.faction} is unknown."
        )

    # If faction found, check reputation level
    if faction is not None:
        level = faction.get_reputation_level()

        # Hostile factions always block NPC interaction
        if level == ReputationLevel.HOSTILE:
            return False, (
                f"{npc.name} refuses to speak with you. "
                f"The {npc.faction} considers you hostile."
            )

        # Check required reputation threshold
        if npc.required_reputation is not None:
            if faction.reputation < npc.required_reputation:
                return False, (
                    f"{npc.name} refuses to speak with you. "
                    f"Your reputation with {npc.faction} is too low."
                )

    return True, ""


def check_location_access(location: Location, factions: List[Faction]) -> Tuple[bool, str]:
    """Check if player can enter a location based on faction reputation.

    Access is blocked if:
    - Location has required_faction and required_reputation
    - Player's standing with that faction is below the requirement
    - Player has no standing with the required faction

    Args:
        location: The location to check access for
        factions: List of player's faction standings

    Returns:
        Tuple of (allowed: bool, message: str)
        If allowed, message is empty string
        If blocked, message explains why
    """
    # No faction requirement = always accessible
    if not location.required_faction:
        return True, ""

    # Find player's standing with the required faction
    faction = _find_faction_by_name(factions, location.required_faction)

    # If player has no standing with the required faction
    if faction is None:
        return False, (
            f"The entrance to {location.name} is guarded. "
            f"You need standing with {location.required_faction} to enter."
        )

    # Check required reputation threshold
    if location.required_reputation is not None:
        if faction.reputation < location.required_reputation:
            return False, (
                f"The entrance to {location.name} is guarded. "
                f"You need higher standing with {location.required_faction} to enter."
            )

    return True, ""


def filter_visible_npcs(npcs: List[NPC], factions: List[Faction]) -> List[NPC]:
    """Filter NPCs to only show those the player can see/interact with.

    Filters out:
    - NPCs with required_reputation the player doesn't meet
    - NPCs from hostile factions (they're hiding/avoiding the player)

    Args:
        npcs: List of NPCs to filter
        factions: List of player's faction standings

    Returns:
        List of NPCs that are visible to the player
    """
    visible = []
    for npc in npcs:
        # Check if NPC is accessible
        allowed, _ = check_npc_access(npc, factions)
        if allowed:
            visible.append(npc)
    return visible


def get_faction_greeting_modifier(npc: NPC, factions: List[Faction]) -> Optional[str]:
    """Get a modified greeting based on player's faction standing with the NPC.

    Returns different greetings based on reputation level:
    - HOSTILE: Rejection message (shouldn't reach here normally, blocked by access check)
    - UNFRIENDLY: Curt, unwelcoming greeting
    - NEUTRAL: None (use default NPC greeting)
    - FRIENDLY: Warm, welcoming greeting
    - HONORED: Special exclusive greeting with hints about content

    Args:
        npc: The NPC to get greeting for
        factions: List of player's faction standings

    Returns:
        Modified greeting string, or None to use default greeting
    """
    # No faction = use default greeting
    if not npc.faction:
        return None

    # Find player's standing with the NPC's faction
    faction = _find_faction_by_name(factions, npc.faction)

    # No standing = use default greeting
    if faction is None:
        return None

    level = faction.get_reputation_level()

    if level == ReputationLevel.HOSTILE:
        return (
            f"*{npc.name} glares at you with open hostility* "
            "I won't speak with an enemy of my people. Leave now."
        )
    elif level == ReputationLevel.UNFRIENDLY:
        return (
            f"*{npc.name} eyes you warily* "
            "Make it quick. I don't trust your kind."
        )
    elif level == ReputationLevel.NEUTRAL:
        # Neutral = use default greeting
        return None
    elif level == ReputationLevel.FRIENDLY:
        return (
            f"*{npc.name} greets you warmly* "
            "Ah, a friend of our guild! Welcome, welcome!"
        )
    elif level == ReputationLevel.HONORED:
        return (
            f"*{npc.name} bows with deep respect* "
            "It is an honor to meet someone so esteemed by our people. "
            "How may I serve you, distinguished friend?"
        )

    return None
