"""Elemental damage calculation module.

This module handles elemental strengths and weaknesses in combat:
- FIRE is strong vs ICE (1.5x damage)
- ICE is strong vs FIRE (1.5x damage)
- Same element resists itself (0.5x damage)
- PHYSICAL is neutral to all elements
"""

from typing import Tuple

from cli_rpg.models.enemy import ElementType


# Weakness relations: attacker element -> list of defender elements it's strong against
WEAKNESSES = {
    ElementType.FIRE: [ElementType.ICE],
    ElementType.ICE: [ElementType.FIRE],
}

# Resistance relations: attacker element -> list of defender elements that resist it
RESISTANCES = {
    ElementType.FIRE: [ElementType.FIRE],
    ElementType.ICE: [ElementType.ICE],
    ElementType.POISON: [ElementType.POISON],
}

# Damage multipliers
WEAKNESS_MULTIPLIER = 1.5
RESISTANCE_MULTIPLIER = 0.5


def calculate_elemental_modifier(
    attacker_element: ElementType,
    defender_element: ElementType,
) -> Tuple[float, str]:
    """
    Calculate damage modifier and message based on elemental interaction.

    Args:
        attacker_element: Element type of the attack/spell
        defender_element: Element type of the defending creature

    Returns:
        Tuple of (modifier, message) where:
        - modifier: Damage multiplier (1.5x for weakness, 0.5x for resistance, 1.0x neutral)
        - message: Description of the interaction ("It's super effective!", etc.)
                   Empty string if neutral.
    """
    # Check for weakness (attacker has advantage)
    if defender_element in WEAKNESSES.get(attacker_element, []):
        return WEAKNESS_MULTIPLIER, "It's super effective!"

    # Check for resistance (defender resists this element)
    if defender_element in RESISTANCES.get(attacker_element, []):
        return RESISTANCE_MULTIPLIER, "It's not very effective..."

    # Neutral interaction
    return 1.0, ""
