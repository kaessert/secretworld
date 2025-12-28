"""Dialogue choice system for NPC conversations affecting relationships.

Provides 3 dialogue tone options during NPC conversations:
- Friendly (+3 arc points)
- Neutral (+1 arc point)
- Aggressive (-2 arc points)

These choices integrate with NPCArc.record_interaction() to affect NPC relationships.
"""
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, List

from cli_rpg.models.npc_arc import NPCArc, InteractionType

if TYPE_CHECKING:
    from cli_rpg.models.npc import NPC


@dataclass
class DialogueChoice:
    """Represents a dialogue tone option during NPC conversation.

    Attributes:
        label: Short name for the choice (e.g., "Friendly")
        description: What this choice means/does
        arc_delta: How many arc points this choice adds (positive) or removes (negative)
    """

    label: str
    description: str
    arc_delta: int


# Standard dialogue choices available in all NPC conversations
DIALOGUE_CHOICES: List[DialogueChoice] = [
    DialogueChoice("Friendly", "Respond warmly and helpfully", 3),
    DialogueChoice("Neutral", "Keep things polite but businesslike", 1),
    DialogueChoice("Aggressive", "Be blunt or threatening", -2),
]


def format_dialogue_choices() -> str:
    """Format dialogue choices for display during conversation.

    Returns:
        Formatted string with numbered options and descriptions.
    """
    lines = ["How do you respond?"]
    for i, choice in enumerate(DIALOGUE_CHOICES, start=1):
        lines.append(f"  [{i}] {choice.label} - {choice.description}")
    return "\n".join(lines)


def parse_dialogue_input(input_str: str) -> Optional[int]:
    """Parse player input to get dialogue choice index.

    Args:
        input_str: Player's input string (number or word)

    Returns:
        Choice index (0, 1, or 2) if valid, None otherwise.
    """
    input_str = input_str.strip().lower()

    # Try numeric input
    if input_str == "1":
        return 0
    elif input_str == "2":
        return 1
    elif input_str == "3":
        return 2

    # Try word input
    if input_str == "friendly":
        return 0
    elif input_str == "neutral":
        return 1
    elif input_str == "aggressive":
        return 2

    return None


# Reaction message templates for each dialogue choice type
_REACTION_TEMPLATES = {
    "Friendly": [
        "{name} smiles at your kindness.",
        "{name} seems to appreciate your warmth.",
        "{name} looks pleased by your friendly demeanor.",
        "{name} relaxes, warming to your approach.",
    ],
    "Neutral": [
        "{name} nods, acknowledging your words.",
        "{name} listens with a measured expression.",
        "{name} responds in kind with a polite nod.",
        "{name} accepts your businesslike manner.",
    ],
    "Aggressive": [
        "{name} frowns at your harsh tone.",
        "{name}'s eyes narrow with displeasure.",
        "The atmosphere grows cold between you and {name}.",
        "{name} tenses at your aggressive words.",
    ],
}


def get_reaction_message(npc_name: str, choice_label: str) -> str:
    """Get an NPC reaction message based on dialogue choice.

    Args:
        npc_name: Name of the NPC being spoken to
        choice_label: The dialogue choice label ("Friendly", "Neutral", "Aggressive")

    Returns:
        A reaction message with the NPC's name inserted.
    """
    templates = _REACTION_TEMPLATES.get(choice_label, _REACTION_TEMPLATES["Neutral"])
    template = random.choice(templates)
    return template.format(name=npc_name)


def apply_dialogue_choice(npc: "NPC", choice_index: int, timestamp: int) -> str:
    """Apply a dialogue choice to an NPC's arc.

    Args:
        npc: The NPC to modify
        choice_index: Index into DIALOGUE_CHOICES (0, 1, or 2)
        timestamp: Current game time in hours

    Returns:
        Feedback message about the NPC's reaction (includes stage change if applicable).
    """
    # Initialize arc if not present
    if npc.arc is None:
        npc.arc = NPCArc()

    choice = DIALOGUE_CHOICES[choice_index]

    # Record the interaction
    stage_change_msg = npc.arc.record_interaction(
        interaction_type=InteractionType.DIALOGUE_CHOICE,
        points_delta=choice.arc_delta,
        description=f"Dialogue choice: {choice.label}",
        timestamp=timestamp,
    )

    # Build response message
    reaction = get_reaction_message(npc.name, choice.label)

    if stage_change_msg:
        return f"{reaction}\n{stage_change_msg}"
    return reaction
