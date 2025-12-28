"""Ambient sound system for SubGrid exploration.

This module provides atmospheric ambient sound descriptions that trigger
during movement within SubGrid locations (dungeons, caves, ruins, temples).
Sounds have depth-based intensity and category-specific pools.

Weather penetration: When near an exit point (is_exit_point) at z=0,
players may hear muffled weather sounds from outside during rain/storm.
"""

import random
from typing import Optional

from cli_rpg import colors

# Constants
AMBIENT_SOUND_CHANCE = 0.15  # 15% base chance per move
DEPTH_SOUND_CHANCE_BONUS = 0.05  # +5% per depth level
SOUND_COOLDOWN_MOVES = 3  # Minimum moves between sounds

# Weather penetration chance by distance from exit (z=0 only)
WEATHER_PENETRATION_CHANCE_EXIT = 0.30  # 30% at exit room
WEATHER_PENETRATION_CHANCE_NEAR = 0.15  # 15% one room away
# 2+ rooms away: 0% (no weather sounds)

# Sound pools by category (8-10 sounds each)
CATEGORY_SOUNDS: dict[str, list[str]] = {
    "dungeon": [
        "Chains rattle somewhere in the darkness...",
        "Dripping water echoes through the corridors...",
        "A distant door creaks on rusted hinges...",
        "Footsteps echo... but not your own...",
        "Metal scrapes against stone far below...",
        "The wind moans through unseen passages...",
        "Something skitters across the floor ahead...",
        "A faint groan rises from the depths...",
        "Dust falls from the ceiling as something shifts above...",
        "The torches flicker as if breathing...",
    ],
    "cave": [
        "Water drips steadily into an unseen pool...",
        "Bats screech and flutter overhead...",
        "Stones clatter in the darkness...",
        "An underground stream rushes somewhere nearby...",
        "The cave walls groan under the weight of the mountain...",
        "Echoes of your movement return strangely distorted...",
        "Something splashes in the distance...",
        "Stalactites creak ominously above...",
        "A cold breeze carries an earthy scent...",
        "Crystal formations hum with an inner resonance...",
    ],
    "ruins": [
        "Stone groans and settles around you...",
        "Wind howls through broken windows...",
        "Ancient timbers creak overhead...",
        "Rubble shifts somewhere in the shadows...",
        "A cold draft carries whispers of the past...",
        "Moss-covered stones crack underfoot...",
        "Something scratches at the walls behind you...",
        "The ruins sigh with forgotten memories...",
        "Dust motes dance in pale shafts of light...",
        "A statue's eyes seem to follow your movement...",
    ],
    "temple": [
        "Distant chanting echoes from unknown chambers...",
        "A bell tolls from somewhere deep within...",
        "Incense smoke drifts through the sacred halls...",
        "Candles flicker though there is no wind...",
        "Stone carvings seem to whisper prayers...",
        "The altar hums with residual power...",
        "Footsteps approach... then fade to silence...",
        "Sacred texts rustle on their ancient pedestals...",
        "A choir of voices rises and falls in the distance...",
        "The air grows thick with devotion and dread...",
    ],
}

# Depth-based sounds (increasingly ominous)
DEPTH_SOUNDS: dict[int, list[str]] = {
    -1: [
        "Echoes take longer to fade here...",
        "The darkness feels thicker at this depth...",
        "Something watches from the shadows...",
        "The air grows cold and still...",
        "Your torchlight struggles against the gloom...",
    ],
    -2: [
        "Something scrapes against stone nearby...",
        "The walls feel closer, pressing in...",
        "An unnatural silence hangs heavy...",
        "The darkness moves when you blink...",
        "Breathing sounds come from everywhere and nowhere...",
        "Ancient malice seeps from the very stones...",
    ],
    -3: [
        "Inhuman sounds rise from below...",
        "The darkness has weight here...",
        "Something massive stirs in its slumber...",
        "Reality feels thin and fragile...",
        "Whispers speak in languages never meant for mortal ears...",
        "The abyss gazes back at you...",
        "Time itself seems to flow differently here...",
    ],
}

# Weather penetration sounds (muffled sounds from outside near exit)
WEATHER_PENETRATION_SOUNDS: dict[str, list[str]] = {
    "rain": [
        "The distant patter of rain echoes from the entrance...",
        "A damp breeze carries the smell of rain from outside...",
        "Muffled raindrops drum against stone near the exit...",
        "You hear the gentle rhythm of rainfall somewhere behind you...",
        "Water trickles in from outside, pooling near the threshold...",
    ],
    "storm": [
        "Thunder rumbles distantly through the entrance...",
        "The howling wind echoes from the way you came in...",
        "A flash of lightning briefly illuminates the passage to the exit...",
        "The storm's fury is muffled but unmistakable from outside...",
        "Rain hammers against the entrance, a wall of sound nearby...",
        "Thunder shakes dust from the ceiling near the exit...",
    ],
}


def get_weather_penetration_sound(
    weather_condition: str, distance_from_exit: int
) -> Optional[str]:
    """Get a weather penetration sound based on weather and distance from exit.

    Weather sounds are only audible near exit points at ground level (z=0).
    Chance decreases with distance:
    - At exit (distance=0): 30% chance
    - 1 room away: 15% chance
    - 2+ rooms away: 0% chance

    Args:
        weather_condition: Current weather ("rain", "storm", "clear", "fog")
        distance_from_exit: Manhattan distance to nearest exit point

    Returns:
        Weather penetration sound text if triggered, None otherwise
    """
    # Only rain and storm have audible penetration
    if weather_condition not in WEATHER_PENETRATION_SOUNDS:
        return None

    # Determine chance based on distance
    if distance_from_exit == 0:
        chance = WEATHER_PENETRATION_CHANCE_EXIT
    elif distance_from_exit == 1:
        chance = WEATHER_PENETRATION_CHANCE_NEAR
    else:
        # 2+ rooms away, no weather sounds
        return None

    # Roll for weather sound
    if random.random() < chance:
        return random.choice(WEATHER_PENETRATION_SOUNDS[weather_condition])

    return None


def format_ambient_sound(text: str) -> str:
    """Format an ambient sound with [Sound]: prefix and styling.

    Args:
        text: The ambient sound text to format.

    Returns:
        Formatted sound with styling and [Sound]: prefix.
    """
    return colors.colorize(f"[Sound]: {text}", colors.BLUE)


class AmbientSoundService:
    """Service for managing ambient sounds during SubGrid exploration.

    Tracks cooldown between sounds and handles trigger chance calculations
    with depth-based scaling. Also handles weather penetration sounds near exits.
    """

    def __init__(self) -> None:
        """Initialize the ambient sound service."""
        self.moves_since_last_sound = SOUND_COOLDOWN_MOVES  # Start ready to play

    def get_ambient_sound(
        self,
        category: str,
        depth: int = 0,
        weather_condition: Optional[str] = None,
        distance_from_exit: int = -1,
    ) -> Optional[str]:
        """Get an ambient sound for the current location.

        May return weather penetration sounds when near exit at z=0 with
        rain/storm weather, otherwise returns category/depth sounds.

        Args:
            category: The location category (dungeon, cave, ruins, temple).
            depth: The current z-level (negative for underground).
            weather_condition: Optional weather for penetration sounds
                ("rain", "storm", "clear", "fog").
            distance_from_exit: Manhattan distance to nearest exit point.
                -1 if not inside a SubGrid or no exits exist.

        Returns:
            A sound string if triggered, None otherwise.
        """
        # Increment move counter
        self.moves_since_last_sound += 1

        # Check cooldown
        if self.moves_since_last_sound <= SOUND_COOLDOWN_MOVES:
            return None

        # Check for weather penetration first (only at z=0, near exit)
        # Weather sounds bypass the normal ambient sound roll
        if depth == 0 and weather_condition and distance_from_exit >= 0:
            weather_sound = get_weather_penetration_sound(
                weather_condition, distance_from_exit
            )
            if weather_sound:
                self.moves_since_last_sound = 0
                return weather_sound

        # Calculate effective chance with depth bonus
        # Deeper levels (more negative z) have higher chance
        depth_bonus = abs(depth) * DEPTH_SOUND_CHANCE_BONUS
        effective_chance = AMBIENT_SOUND_CHANCE + depth_bonus

        # Random check
        if random.random() >= effective_chance:
            return None

        # Reset cooldown
        self.moves_since_last_sound = 0

        # Decide between category sound and depth sound
        # At deeper levels, higher chance of depth-specific sound
        use_depth_sound = False
        if depth < 0 and depth in DEPTH_SOUNDS:
            # 30% base chance + 20% per depth level to use depth sound
            depth_sound_chance = 0.30 + (abs(depth) * 0.20)
            use_depth_sound = random.random() < depth_sound_chance

        if use_depth_sound:
            return random.choice(DEPTH_SOUNDS[depth])

        # Use category sound if available, otherwise return generic
        if category in CATEGORY_SOUNDS:
            return random.choice(CATEGORY_SOUNDS[category])

        # Default sounds for unknown categories
        return random.choice([
            "Something stirs in the darkness...",
            "An echo fades into silence...",
            "The air feels thick and heavy...",
        ])
