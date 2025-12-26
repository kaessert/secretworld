"""Secret discovery mechanics using Perception stat."""
from enum import Enum
from typing import List, Tuple

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


class SecretType(Enum):
    """Types of secrets that can be discovered."""

    HIDDEN_DOOR = "hidden_door"
    HIDDEN_TREASURE = "hidden_treasure"
    TRAP = "trap"
    LORE_HINT = "lore_hint"


# Bonuses for active search
SEARCH_BONUS = 5  # Bonus to PER when actively searching
LIGHT_BONUS = 2  # Additional bonus when character has active light


def check_passive_detection(char: Character, location: Location) -> List[dict]:
    """Check for automatic secret detection based on PER when entering a location.

    Secrets with threshold <= character's perception are automatically detected
    and marked as discovered. Already discovered secrets are skipped.

    Args:
        char: The player character with perception stat
        location: The location being entered/examined

    Returns:
        List of secrets that were newly detected (dicts with type, description, threshold)
    """
    detected = []
    for secret in location.hidden_secrets:
        # Skip already discovered secrets
        if secret.get("discovered"):
            continue
        # Check if perception meets threshold
        if char.perception >= secret.get("threshold", 15):
            secret["discovered"] = True
            detected.append(secret)
    return detected


def perform_active_search(char: Character, location: Location) -> Tuple[bool, str]:
    """Perform active search for hidden secrets using the 'search' command.

    Active search grants a +5 bonus to perception, plus +2 if the character
    has an active light source. Secrets found are marked as discovered.

    Args:
        char: The player character performing the search
        location: The location being searched

    Returns:
        Tuple of (found_something, message):
        - found_something: True if any secrets were discovered
        - message: Description of what was found or a message if nothing found
    """
    # Calculate effective perception with bonuses
    effective_per = char.perception + SEARCH_BONUS
    if char.has_active_light():
        effective_per += LIGHT_BONUS

    # Get undiscovered secrets
    undiscovered = [s for s in location.hidden_secrets if not s.get("discovered")]

    if not undiscovered:
        return (False, "You search carefully but find nothing hidden.")

    # Check each secret against effective perception
    found = []
    for secret in undiscovered:
        if effective_per >= secret.get("threshold", 15):
            secret["discovered"] = True
            found.append(secret)

    if not found:
        return (False, "You search but don't notice anything unusual.")

    # Build discovery message
    descriptions = [s["description"] for s in found]
    return (True, f"You discover: {', '.join(descriptions)}")
