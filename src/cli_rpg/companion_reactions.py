"""Companion reactions to player choices.

This module handles companion reactions when the player makes meaningful choices.
Companions react based on their personality, which affects their bond with the player.

Personality types:
- warrior: Approves of combat kills, disapproves of fleeing
- pacifist: Disapproves of kills, approves of fleeing
- pragmatic: Neutral to most choices (default)
"""

from typing import List

from cli_rpg.models.companion import Companion
from cli_rpg import colors

# Bond point changes for reactions
APPROVAL_BOND_CHANGE = 3
DISAPPROVAL_BOND_CHANGE = -3

# Personality -> choice_type -> reaction mapping
PERSONALITY_REACTIONS = {
    "warrior": {
        "combat_kill": "approval",
        "combat_flee": "disapproval",
    },
    "pacifist": {
        "combat_kill": "disapproval",
        "combat_flee": "approval",
    },
    "pragmatic": {},  # Neutral to everything
}

# Flavor text templates for approval reactions
APPROVAL_MESSAGES = {
    "warrior": {
        "combat_kill": "{name} nods approvingly. \"Well fought.\"",
    },
    "pacifist": {
        "combat_flee": "{name} sighs with relief. \"I'm glad we avoided bloodshed.\"",
    },
}

# Flavor text templates for disapproval reactions
DISAPPROVAL_MESSAGES = {
    "warrior": {
        "combat_flee": "{name} scowls. \"We should have stood and fought.\"",
    },
    "pacifist": {
        "combat_kill": "{name} looks away. \"Was that truly necessary?\"",
    },
}


def get_companion_reaction(companion: Companion, choice_type: str) -> str:
    """Get reaction type for a companion's personality and choice.

    Args:
        companion: The companion to check reaction for
        choice_type: The type of choice made (e.g., "combat_kill", "combat_flee")

    Returns:
        Reaction type: "approval", "disapproval", or "neutral"
    """
    reactions = PERSONALITY_REACTIONS.get(companion.personality, {})
    return reactions.get(choice_type, "neutral")


def process_companion_reactions(
    companions: List[Companion],
    choice_type: str
) -> List[str]:
    """Process reactions for all companions and return messages.

    This function:
    - Determines each companion's reaction based on personality
    - Adjusts bond points (+3 for approval, -3 for disapproval)
    - Returns flavor text messages for display

    Args:
        companions: List of companions to process reactions for
        choice_type: The type of choice made

    Returns:
        List of reaction messages to display
    """
    messages = []

    for companion in companions:
        reaction = get_companion_reaction(companion, choice_type)

        if reaction == "approval":
            level_msg = companion.add_bond(APPROVAL_BOND_CHANGE)
            msg_template = APPROVAL_MESSAGES.get(companion.personality, {}).get(choice_type)
            if msg_template:
                messages.append(colors.companion(msg_template.format(name=companion.name)))
            if level_msg:
                messages.append(level_msg)

        elif reaction == "disapproval":
            companion.reduce_bond(abs(DISAPPROVAL_BOND_CHANGE))
            msg_template = DISAPPROVAL_MESSAGES.get(companion.personality, {}).get(choice_type)
            if msg_template:
                messages.append(colors.companion(msg_template.format(name=companion.name)))

    return messages
