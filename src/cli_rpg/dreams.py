"""Dream sequences triggered during rest.

Dreams add atmospheric storytelling when the player rests.
High dread (50%+) triggers nightmares instead of normal dreams.
"""

import random
from typing import Optional

from cli_rpg import colors
from cli_rpg.frames import frame_dream
from cli_rpg.text_effects import typewriter_print, pause_medium

DREAM_CHANCE = 0.25  # 25% chance on rest
NIGHTMARE_DREAD_THRESHOLD = 50

# Prophetic dreams - hints at future/foreshadowing
PROPHETIC_DREAMS = [
    "You stand at a crossroads. One path glows with warmth, the other with shadow...",
    "A voice whispers a name you've never heard, yet it feels like your own...",
    "You see a mountain crumbling in the distance. Something stirs beneath.",
    "Three doors stand before you. Only one leads forward. The others... consume.",
]

# Atmospheric dreams - surreal mood-setting
ATMOSPHERIC_DREAMS = [
    "You drift through clouds of starlight, formless and free...",
    "The world shifts like water beneath your feet...",
    "Colors you cannot name swirl around you, singing...",
    "You float in an endless library. The books whisper secrets.",
]

# Memory/choice-based dream templates (keyed by choice_type)
CHOICE_DREAMS = {
    "combat_flee": [
        "You run through endless corridors, but the exit always moves...",
        "Something pursues you. Your legs feel like lead...",
    ],
    "combat_kill": [
        "Faces of the fallen watch you from mirrors that line an infinite hall...",
        "A battlefield stretches endlessly. You stand alone among the silence.",
    ],
}

# Nightmares (triggered at high dread 50%+)
NIGHTMARES = [
    "Something hunts you through the dark. You cannot scream.",
    "Your reflection doesn't move when you do...",
    "You fall endlessly through nothing. The nothing watches back.",
    "Hands reach from the shadows. They know your name.",
    "The walls breathe. They've always been breathing.",
    "You wake in your childhood bed. Something is in the closet. It remembers you.",
]


def maybe_trigger_dream(
    dread: int = 0,
    choices: Optional[list[dict]] = None,
    theme: str = "fantasy"
) -> Optional[str]:
    """Potentially trigger a dream during rest.

    Args:
        dread: Current dread level (0-100)
        choices: Player's recorded choices (from game_state.choices)
        theme: World theme (unused for now, for future AI dreams)

    Returns:
        Formatted dream text if triggered, None otherwise
    """
    # 25% chance to dream
    if random.random() > DREAM_CHANCE:
        return None

    # Select dream based on dread level
    if dread >= NIGHTMARE_DREAD_THRESHOLD:
        dream_text = random.choice(NIGHTMARES)
    else:
        dream_text = _select_dream(choices)

    return format_dream(dream_text)


def _select_dream(choices: Optional[list[dict]]) -> str:
    """Select a dream based on player choices or random pool.

    Args:
        choices: Player's recorded choices

    Returns:
        Dream text string
    """
    # 30% chance for choice-based dream if choices exist
    if choices and random.random() < 0.30:
        # Count choice types
        flee_count = sum(1 for c in choices if c.get("choice_type") == "combat_flee")
        kill_count = sum(1 for c in choices if c.get("choice_type") == "combat_kill")

        if flee_count >= 3 and "combat_flee" in CHOICE_DREAMS:
            return random.choice(CHOICE_DREAMS["combat_flee"])
        if kill_count >= 10 and "combat_kill" in CHOICE_DREAMS:
            return random.choice(CHOICE_DREAMS["combat_kill"])

    # Default: random from prophetic or atmospheric
    all_dreams = PROPHETIC_DREAMS + ATMOSPHERIC_DREAMS
    return random.choice(all_dreams)


def format_dream(dream_text: str) -> str:
    """Format a dream for display with borders and intro/outro.

    Args:
        dream_text: The dream content

    Returns:
        Formatted string with decorative borders
    """
    intro = colors.colorize("You drift into an uneasy sleep...", colors.MAGENTA)
    outro = colors.colorize("You wake with fragments of the dream still lingering...", colors.MAGENTA)

    dream_content = colors.colorize(dream_text, colors.CYAN)
    framed_dream = frame_dream(dream_content)

    return f"""
{intro}

{framed_dream}

{outro}"""


# Slower delay for atmospheric dream display
DREAM_TYPEWRITER_DELAY = 0.04


def display_dream(dream_text: str) -> None:
    """Display a formatted dream with typewriter effect.

    Uses a slower delay for atmospheric effect. The typewriter_print
    function handles the effects_enabled toggle internally.

    Args:
        dream_text: The formatted dream text to display
    """
    # Print each line with typewriter effect for atmosphere
    for line in dream_text.split("\n"):
        typewriter_print(line, delay=DREAM_TYPEWRITER_DELAY)
    pause_medium()  # Pause after dream ends for reflection
