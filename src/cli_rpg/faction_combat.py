"""Faction reputation effects from combat outcomes.

This module handles the reputation changes that occur when players defeat
enemies affiliated with various factions.
"""

from typing import Optional

from cli_rpg.models.enemy import Enemy
from cli_rpg.models.faction import Faction

# Reputation change amounts
FACTION_REPUTATION_LOSS = 5  # Reputation lost with enemy's faction
FACTION_REPUTATION_GAIN = 3  # Reputation gained with rival faction

# Mapping of enemy name patterns to faction affiliations
# Keys are lowercase patterns that can appear anywhere in the enemy name
FACTION_ENEMIES = {
    "bandit": "Thieves Guild",
    "thief": "Thieves Guild",
    "ruffian": "Thieves Guild",
    "outlaw": "Thieves Guild",
    "guard": "Town Guard",
    "soldier": "Town Guard",
    "knight": "Town Guard",
    "captain": "Town Guard",
}

# Mapping of factions to their rival factions
FACTION_RIVALRIES = {
    "Thieves Guild": "Town Guard",
    "Town Guard": "Thieves Guild",
}


def get_enemy_faction(enemy_name: str) -> Optional[str]:
    """Determine the faction affiliation of an enemy by name.

    Checks the enemy name against known patterns (case-insensitive).

    Args:
        enemy_name: The name of the enemy

    Returns:
        The faction name if a pattern matches, None otherwise
    """
    name_lower = enemy_name.lower()
    for pattern, faction in FACTION_ENEMIES.items():
        if pattern in name_lower:
            return faction
    return None


def _find_faction_by_name(factions: list[Faction], name: str) -> Optional[Faction]:
    """Find a faction by name in the factions list.

    Args:
        factions: List of factions to search
        name: Faction name to find

    Returns:
        The Faction if found, None otherwise
    """
    for faction in factions:
        if faction.name == name:
            return faction
    return None


def apply_combat_reputation(
    factions: list[Faction], enemies: list[Enemy]
) -> list[str]:
    """Apply reputation changes from defeating enemies.

    For each enemy with a faction affiliation:
    - Reduces reputation with that faction by FACTION_REPUTATION_LOSS
    - Increases reputation with rival faction by FACTION_REPUTATION_GAIN

    Args:
        factions: List of factions to modify
        enemies: List of defeated enemies

    Returns:
        List of messages describing reputation changes
    """
    messages: list[str] = []

    for enemy in enemies:
        # Get faction from enemy's explicit affiliation
        faction_name = enemy.faction_affiliation

        if not faction_name:
            continue

        # Find the affiliated faction
        affiliated = _find_faction_by_name(factions, faction_name)
        if not affiliated:
            # Enemy has an affiliation but faction doesn't exist in game
            continue

        # Reduce reputation with affiliated faction
        level_msg = affiliated.reduce_reputation(FACTION_REPUTATION_LOSS)
        messages.append(
            f"Your reputation with {affiliated.name} decreased by {FACTION_REPUTATION_LOSS}."
        )
        if level_msg:
            messages.append(level_msg)

        # Increase reputation with rival faction
        rival_name = FACTION_RIVALRIES.get(faction_name)
        if rival_name:
            rival = _find_faction_by_name(factions, rival_name)
            if rival:
                level_msg = rival.add_reputation(FACTION_REPUTATION_GAIN)
                messages.append(
                    f"Your reputation with {rival.name} increased by {FACTION_REPUTATION_GAIN}."
                )
                if level_msg:
                    messages.append(level_msg)

    return messages
