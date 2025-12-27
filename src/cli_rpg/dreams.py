"""Dream sequences triggered during rest.

Dreams add atmospheric storytelling when the player rests.
High dread (50%+) triggers nightmares instead of normal dreams.
AI-generated dreams are attempted first when an ai_service is available.
"""

import logging
import random
from typing import Optional, TYPE_CHECKING

from cli_rpg import colors
from cli_rpg.frames import frame_dream
from cli_rpg.text_effects import typewriter_print, pause_medium

if TYPE_CHECKING:  # pragma: no cover
    from cli_rpg.ai_service import AIService  # pragma: no cover

logger = logging.getLogger(__name__)

DREAM_CHANCE = 0.10  # 10% chance on rest (reduced from 25%)
CAMP_DREAM_CHANCE = 0.15  # 15% chance on camp (reduced from 40%)
DREAM_COOLDOWN_HOURS = 12  # Minimum hours between dreams
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


def get_tiredness_dream_chance(tiredness: int) -> float:
    """Get dream chance based on tiredness level.

    Args:
        tiredness: Current tiredness level (0-100)

    Returns:
        Dream chance as a float (0.0 to 1.0)
    """
    if tiredness >= 80:
        return 0.40  # Deep sleep: 40% dream chance
    elif tiredness >= 60:
        return 0.20  # Normal sleep: 20%
    else:
        return 0.05  # Light sleep: 5%


def maybe_trigger_dream(
    dread: int = 0,
    choices: Optional[list[dict]] = None,
    theme: str = "fantasy",
    ai_service: Optional["AIService"] = None,
    location_name: str = "",
    dream_chance: Optional[float] = None,
    last_dream_hour: Optional[int] = None,
    current_hour: Optional[int] = None,
    tiredness: Optional[int] = None,
) -> Optional[str]:
    """Potentially trigger a dream during rest.

    Args:
        dread: Current dread level (0-100)
        choices: Player's recorded choices (from game_state.choices)
        theme: World theme for AI generation
        ai_service: Optional AI service for generating personalized dreams
        location_name: Current location name for AI context
        dream_chance: Override for dream chance (default: DREAM_CHANCE)
        last_dream_hour: Hour of last dream (for cooldown check)
        current_hour: Current game hour (for cooldown check)
        tiredness: Current tiredness level (0-100). If provided, blocks dreams
                   when tiredness < 30 and modifies dream chance based on level.

    Returns:
        Formatted dream text if triggered, None otherwise
    """
    # Block dreams if not tired enough
    if tiredness is not None and tiredness < 30:
        return None

    # Determine dream chance based on tiredness or use provided/default
    if tiredness is not None and dream_chance is None:
        chance = get_tiredness_dream_chance(tiredness)
    elif dream_chance is not None:
        chance = dream_chance
    else:
        chance = DREAM_CHANCE

    # Check cooldown: require 12+ hours since last dream
    if last_dream_hour is not None and current_hour is not None:
        hours_since = current_hour - last_dream_hour
        if hours_since < DREAM_COOLDOWN_HOURS:
            return None

    # Check dream chance
    if random.random() > chance:
        return None

    # Determine if this is a nightmare
    is_nightmare = dread >= NIGHTMARE_DREAD_THRESHOLD

    # Try AI generation first if available
    if ai_service is not None:
        try:
            dream_text = ai_service.generate_dream(
                theme=theme,
                dread=dread,
                choices=choices,
                location_name=location_name,
                is_nightmare=is_nightmare
            )
            return format_dream(dream_text)
        except Exception as e:
            # Fall back to templates on any error
            logger.debug(f"AI dream generation failed, using templates: {e}")

    # Fallback: Select dream based on dread level from templates
    if is_nightmare:
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
