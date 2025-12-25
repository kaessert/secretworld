"""Companion banter system for travel dialogue.

The banter system displays companion comments during travel:
- 25% trigger chance per move when companions are present
- Only one banter per move (pick random companion if multiple)
- Context-aware: location, weather, time, dread influence banter
- Bond-level depth: TRUSTED/DEVOTED companions have richer banter
"""

import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.companion import Companion

from cli_rpg.models.companion import BondLevel

BANTER_CHANCE = 0.25  # 25% chance per move

# Template banter by location category
CATEGORY_BANTER = {
    "town": [
        "It's nice to be somewhere civilized for a change.",
        "I could use a warm meal and a soft bed.",
        "These markets remind me of home...",
        "The smell of fresh bread is comforting.",
        "Plenty of eyes here. Some friendly, some not.",
    ],
    "dungeon": [
        "Stay close. I don't like the look of this place.",
        "What manner of creature lives in such darkness?",
        "I've got a bad feeling about this...",
        "These walls have seen terrible things.",
        "Watch your step. Who knows what traps await.",
    ],
    "forest": [
        "The trees here are ancient. They've seen much.",
        "Listen to the birds. They know when danger is near.",
        "This path looks rarely traveled.",
        "The forest has a way of swallowing travelers whole.",
        "I can hear the wind whispering through the leaves.",
    ],
    "wilderness": [
        "Wild lands ahead. Stay on your guard.",
        "I've crossed terrain like this before. It's unforgiving.",
        "The horizon stretches endlessly...",
        "Nature cares not for our journey.",
    ],
    "cave": [
        "The darkness down here is absolute.",
        "I can feel the weight of rock above us.",
        "Something's dripping. I hope it's water.",
        "Caves like this often hold secrets. And dangers.",
    ],
    "ruins": [
        "Who built this place? And why did they abandon it?",
        "The stones here whisper of fallen glory.",
        "Be careful. Old structures can be unstable.",
        "I wonder what treasures lie buried here.",
    ],
    "default": [
        "Interesting place...",
        "I wonder what we'll find here.",
        "Stay alert.",
        "Let's keep moving.",
        "I've never been somewhere quite like this.",
    ],
}

# Weather-specific banter
WEATHER_BANTER = {
    "rain": [
        "This rain is relentless.",
        "At least it covers our tracks.",
        "I'm soaked to the bone.",
        "The rain makes everything glisten strangely.",
    ],
    "storm": [
        "We should find shelter!",
        "I can barely see in this storm!",
        "The thunder shakes the very ground!",
        "This storm is unnaturally fierce...",
    ],
    "fog": [
        "Stay close, I can barely see you.",
        "Something feels wrong in this fog.",
        "The mist plays tricks on the eyes.",
        "Anything could be lurking just out of sight.",
    ],
}

# Night-specific banter
NIGHT_BANTER = [
    "The darkness makes every sound seem louder.",
    "I'll keep watch. You look tired.",
    "Stars are beautiful tonight, at least.",
    "Night brings out the worst in this land.",
    "I can barely see the path ahead.",
    "Stay close. It's easy to get separated in the dark.",
]

# High-dread banter (50%+)
DREAD_BANTER = [
    "Did you hear that? ...Never mind.",
    "I don't like this. Not one bit.",
    "Something is watching us. I can feel it.",
    "My hands won't stop shaking.",
    "We should leave this place. Now.",
    "I've seen brave warriors break in places like this.",
]

# Bond-level specific banter (unlocked at higher levels)
TRUSTED_BANTER = [
    "I'm glad you're the one leading us.",
    "We've been through a lot together, haven't we?",
    "I trust your judgment. Where you go, I follow.",
    "You've proven yourself many times over.",
]

DEVOTED_BANTER = [
    "There's no one else I'd rather face this with.",
    "Whatever happens, I've got your back.",
    "I'd follow you into the abyss itself.",
    "You've given me purpose again. Thank you.",
    "When this is over, remind me to tell you something important.",
]

# Chances for conditional banter types
WEATHER_BANTER_CHANCE = 0.40  # 40% chance to use weather banter when weather is active
NIGHT_BANTER_CHANCE = 0.35   # 35% chance to use night banter at night
DREAD_BANTER_CHANCE = 0.45   # 45% chance to use dread banter when dread >= 50
BOND_BANTER_CHANCE = 0.25    # 25% chance to use bond-level banter


class CompanionBanterService:
    """Service for generating companion banter during travel."""

    def get_banter(
        self,
        companions: list["Companion"],
        location_category: Optional[str],
        weather: str = "clear",
        is_night: bool = False,
        dread: int = 0,
    ) -> Optional[tuple[str, str]]:
        """Get banter from a random companion.

        Args:
            companions: List of companions in the party
            location_category: The category of the current location
            weather: Current weather condition (clear, rain, storm, fog)
            is_night: Whether it's currently night time
            dread: Current dread level (0-100)

        Returns:
            Tuple of (companion_name, banter_text) or None if no banter triggers
        """
        # No banter if no companions
        if not companions:
            return None

        # Check if banter triggers (25% chance)
        if random.random() > BANTER_CHANCE:
            return None

        # Pick a random companion
        companion = random.choice(companions)
        bond_level = companion.get_bond_level()

        # Try conditional banter types in priority order

        # 1. High dread (50%+) - nervous comments
        if dread >= 50 and random.random() < DREAD_BANTER_CHANCE:
            return (companion.name, random.choice(DREAD_BANTER))

        # 2. Bond-level specific banter (DEVOTED gets priority)
        if bond_level == BondLevel.DEVOTED and random.random() < BOND_BANTER_CHANCE:
            return (companion.name, random.choice(DEVOTED_BANTER))

        if bond_level == BondLevel.TRUSTED and random.random() < BOND_BANTER_CHANCE:
            return (companion.name, random.choice(TRUSTED_BANTER))

        # 3. Weather banter (if weather is not clear)
        if weather != "clear" and weather in WEATHER_BANTER:
            if random.random() < WEATHER_BANTER_CHANCE:
                return (companion.name, random.choice(WEATHER_BANTER[weather]))

        # 4. Night banter
        if is_night and random.random() < NIGHT_BANTER_CHANCE:
            return (companion.name, random.choice(NIGHT_BANTER))

        # 5. Default: location category banter
        category_banters = CATEGORY_BANTER.get(
            location_category or "default",
            CATEGORY_BANTER["default"]
        )
        return (companion.name, random.choice(category_banters))


def format_banter(companion_name: str, banter_text: str) -> str:
    """Format banter for display.

    Args:
        companion_name: Name of the companion speaking
        banter_text: The banter text

    Returns:
        Formatted banter with [Companion] prefix and styling
    """
    from cli_rpg import colors
    prefix = colors.companion("[Companion]")
    name = colors.companion(companion_name)
    return f'{prefix} {name}: "{banter_text}"'
