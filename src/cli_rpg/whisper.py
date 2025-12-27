"""Whisper system for ambient narrative hints.

The whisper system displays random narrative hints when entering locations.
Whispers are triggered with a 30% chance and are based on location category
or player history.
"""

import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.character import Character
    from cli_rpg.ai_service import AIService

WHISPER_CHANCE = 0.30  # 30% chance of whisper on location entry
PLAYER_HISTORY_CHANCE = 0.10  # 10% of whispers are player-history-aware
NIGHT_WHISPER_CHANCE = 0.40  # 40% chance of night whisper when it's night
DEPTH_WHISPER_CHANCE = 0.40  # 40% chance of depth whisper when underground
WHISPER_TYPEWRITER_DELAY = 0.03  # Slightly faster than dreams' 0.04

# Night-specific whispers (eerie atmosphere)
NIGHT_WHISPERS = [
    "The darkness presses in around you...",
    "Shadows dance at the edge of your vision.",
    "The night is alive with unseen things.",
    "A cold wind whispers secrets in the dark.",
    "Stars peer down like countless watchful eyes.",
    "The moon casts long, sinister shadows.",
    "Something prowls in the darkness nearby...",
    "Night creatures stir in their hidden lairs.",
]

# Dread-induced paranoid whispers (triggered when dread >= 50%)
DREAD_WHISPERS = [
    "They're watching you. They've always been watching.",
    "That shadow moved. You're certain it moved.",
    "You hear your name whispered, but there's no one there.",
    "Something is following you. Don't look back.",
    "The walls have eyes. The darkness has teeth.",
    "Your heartbeat sounds like footsteps behind you.",
    "Trust no one. Not even yourself.",
    "The silence is screaming at you.",
    "Is that your reflection, or something else wearing your face?",
    "They want you to keep going. Into the dark. Forever.",
]
DREAD_WHISPER_CHANCE = 0.50  # 50% chance of dread whisper when dread >= 50

# Template whispers by location category
CATEGORY_WHISPERS = {
    "town": [
        "The cobblestones have heard a thousand footsteps...",
        "Somewhere nearby, a door creaks on rusty hinges.",
        "The smell of bread and distant forge fires fills the air.",
        "Hushed voices carry secrets through narrow alleys.",
        "A cat watches you from a shadowed windowsill.",
        "The town bell tolls, marking hours that blur together.",
        "Laughter echoes from a tavern, warm and distant.",
        "The market stalls stand silent, waiting for dawn.",
    ],
    "dungeon": [
        "Something skitters in the darkness ahead...",
        "The walls are damp with moisture... or something else.",
        "Ancient carvings here speak of a warning long forgotten.",
        "Rust-colored stains mark the walls...",
        "The scent of decay lingers here.",
        "Chains rattle somewhere in the dark.",
        "Faint scratching sounds from behind the stones.",
        "The torchlight seems dimmer here...",
    ],
    "wilderness": [
        "The wind carries whispers from far-off places.",
        "Nature reclaims what was once taken from her.",
        "Somewhere, a creature watches your passage.",
        "The grass bends beneath an invisible presence.",
        "A distant howl cuts through the silence.",
        "Old paths cross here, worn by countless travelers.",
        "The horizon shimmers with heat or cold.",
        "Something moves at the edge of your vision.",
    ],
    "ruins": [
        "Echoes of the past linger in these broken stones.",
        "Once, this place knew glory. Now only silence remains.",
        "The dust here has settled for centuries.",
        "Faded murals hint at forgotten stories.",
        "Crumbled statues watch with empty eyes.",
        "The wind plays a mournful tune through cracks.",
        "Time has been cruel to this place.",
        "Ghosts of memory drift through empty halls.",
    ],
    "cave": [
        "Dripping water marks the passage of eons.",
        "The darkness here is absolute and patient.",
        "Something ancient sleeps in the depths below.",
        "Strange formations gleam in the dim light.",
        "The echo of your footsteps returns distorted.",
        "Phosphorescent moss traces hidden paths.",
        "The air grows colder as you venture deeper.",
        "Underground streams whisper of buried secrets.",
    ],
    "forest": [
        "The trees seem to lean in, listening...",
        "Shafts of light pierce the canopy like golden spears.",
        "The forest remembers those who pass through.",
        "Birdsong falls silent as you approach.",
        "Roots twist across the path like grasping fingers.",
        "The undergrowth rustles with unseen life.",
        "Old growth hides things best left undiscovered.",
        "The canopy filters light into emerald shadows.",
    ],
    "temple": [
        "Incense lingers, though no candles burn.",
        "Sacred symbols watch over forgotten altars.",
        "The air hums with residual prayers.",
        "Shadows gather in corners untouched by light.",
        "Ancient hymns seem to echo from nowhere.",
        "Offerings lie scattered, aged beyond recognition.",
        "The divine once dwelt here. Perhaps still does.",
        "Silence weighs heavy, like a held breath.",
    ],
    "default": [
        "A strange feeling washes over you...",
        "The air here feels different somehow.",
        "You sense you are not entirely alone.",
        "Something about this place sets you on edge.",
        "The quiet here is too complete.",
        "Your instincts whisper of hidden dangers.",
        "This place holds secrets you cannot yet see.",
        "An unexplained chill runs down your spine.",
    ],
}

# Depth-based whispers for underground exploration (dungeons, caves, etc.)
# Deeper levels (more negative z) have increasingly ominous whispers
DEPTH_WHISPERS = {
    0: [],  # Surface level uses standard category whispers
    -1: [
        "The weight of stone presses down above you...",
        "Echoes seem to take longer to fade here.",
        "The air grows stale, away from the surface.",
        "You've descended beyond the reach of sunlight.",
    ],
    -2: [
        "The air grows thick and stale...",
        "Something ancient stirs in the depths below.",
        "Few have ventured this deep and returned.",
        "The walls seem to pulse with an inner darkness.",
    ],
    -3: [
        "You sense you've gone where few return from...",
        "The darkness here feels alive, hungry.",
        "Whispers from the abyss call your name.",
        "Even the stone seems afraid of what lies below.",
    ],
}

# Player-history-aware whisper templates
PLAYER_HISTORY_WHISPERS = {
    "high_gold": [
        "Your purse weighs heavy. Others have noticed...",
        "Wealth attracts attention, not all of it friendly.",
    ],
    "high_level": [
        "Your reputation precedes you, adventurer.",
        "The shadows recognize a seasoned warrior.",
    ],
    "low_health": [
        "Your wounds cry out for rest...",
        "Death watches those who push too far.",
    ],
    "many_kills": [
        "The spirits of the fallen trail behind you.",
        "Blood leaves stains that water cannot wash away.",
    ],
}


def get_depth_dread_modifier(z: int) -> float:
    """Get dread accumulation modifier based on depth.

    Deeper dungeon levels increase dread accumulation rate to reflect
    the psychological pressure of exploring underground.

    Args:
        z: Z-coordinate (0 = surface, negative = underground)

    Returns:
        Dread multiplier (1.0 at surface, up to 2.0 at depth -3+)
    """
    if z >= 0:
        return 1.0
    elif z == -1:
        return 1.25
    elif z == -2:
        return 1.5
    else:  # z <= -3
        return 2.0


class WhisperService:
    """Service for generating ambient whispers."""

    def __init__(self, ai_service: Optional["AIService"] = None):
        """Initialize the whisper service.

        Args:
            ai_service: Optional AI service for dynamic whisper generation
        """
        self.ai_service = ai_service

    def get_whisper(
        self,
        location_category: Optional[str],
        character: Optional["Character"] = None,
        theme: str = "fantasy",
        is_night: bool = False,
        dread: int = 0,
        depth: int = 0
    ) -> Optional[str]:
        """Get a whisper for the current location, if one triggers.

        Args:
            location_category: The category of the current location
            character: Optional player character for history-aware whispers
            theme: World theme for AI generation
            is_night: Whether it's currently night time
            dread: Current dread level (0-100) for paranoid whispers
            depth: Z-coordinate for depth-based whispers (0 = surface, negative = underground)

        Returns:
            Whisper text or None if no whisper triggers
        """
        # Check if whisper triggers (30% chance)
        if random.random() > WHISPER_CHANCE:
            return None

        # High dread (50%+) triggers paranoid whispers
        if dread >= 50 and random.random() < DREAD_WHISPER_CHANCE:
            return random.choice(DREAD_WHISPERS)

        # Check for player-history-aware whisper (10% of whispers)
        if character and random.random() < PLAYER_HISTORY_CHANCE:
            history_whisper = self._get_player_history_whisper(character)
            if history_whisper:
                return history_whisper

        # Try AI generation if available
        if self.ai_service:
            try:
                return self._generate_ai_whisper(location_category, theme)
            except Exception:
                pass  # Fall back to templates

        # Use template whispers
        return self._get_template_whisper(location_category, is_night=is_night, depth=depth)

    def _get_template_whisper(
        self, category: Optional[str], is_night: bool = False, depth: int = 0
    ) -> str:
        """Get a random template whisper for the location category.

        Args:
            category: Location category (town, dungeon, etc.)
            is_night: Whether it's currently night time
            depth: Z-coordinate for depth-based whispers (0 = surface, negative = underground)

        Returns:
            A random whisper string from the category, night, or depth templates
        """
        # At night, chance to use night-specific whispers
        if is_night and random.random() < NIGHT_WHISPER_CHANCE:
            return random.choice(NIGHT_WHISPERS)

        # Underground, chance to use depth whispers
        if depth < 0 and random.random() < DEPTH_WHISPER_CHANCE:
            # Cap at -3 for whisper lookup
            depth_key = max(depth, -3)
            depth_whispers = DEPTH_WHISPERS.get(depth_key, [])
            if depth_whispers:
                return random.choice(depth_whispers)

        whispers = CATEGORY_WHISPERS.get(category or "default", CATEGORY_WHISPERS["default"])
        return random.choice(whispers)

    def _get_player_history_whisper(self, character: "Character") -> Optional[str]:
        """Get a whisper based on player's history/stats.

        Checks various conditions in priority order:
        1. High gold (500+)
        2. High level (5+)
        3. Low health (<30%)
        4. Many kills (10+)

        Args:
            character: The player character

        Returns:
            A history-aware whisper string, or None if no conditions match
        """
        # Check various conditions in priority order
        if character.gold >= 500:
            return random.choice(PLAYER_HISTORY_WHISPERS["high_gold"])
        if character.level >= 5:
            return random.choice(PLAYER_HISTORY_WHISPERS["high_level"])
        if character.health < character.max_health * 0.3:
            return random.choice(PLAYER_HISTORY_WHISPERS["low_health"])
        # Check bestiary for kill count
        total_kills = sum(entry.get("count", 0) for entry in character.bestiary.values())
        if total_kills >= 10:
            return random.choice(PLAYER_HISTORY_WHISPERS["many_kills"])
        return None

    def _generate_ai_whisper(self, category: Optional[str], theme: str) -> str:
        """Generate an AI whisper (requires ai_service).

        Args:
            category: Location category for context
            theme: World theme for generation

        Returns:
            Generated whisper string from AI service

        Raises:
            Any exception from ai_service.generate_whisper (handled by caller)
        """
        if self.ai_service is None:
            raise RuntimeError("AI service not available")

        return self.ai_service.generate_whisper(
            theme=theme,
            location_category=category
        )


def format_whisper(whisper_text: str) -> str:
    """Format a whisper for display.

    Args:
        whisper_text: The whisper text

    Returns:
        Formatted whisper with styling and [Whisper]: prefix
    """
    from cli_rpg import colors
    return colors.colorize(f'[Whisper]: "{whisper_text}"', colors.MAGENTA)


def display_whisper(whisper_text: str) -> None:
    """Display a whisper with typewriter effect.

    The whisper is formatted with styling and displayed character-by-character
    for enhanced atmosphere. The effect is skippable via Ctrl+C and respects
    the global effects toggle.

    Args:
        whisper_text: The whisper text to display
    """
    from cli_rpg.text_effects import typewriter_print

    formatted = format_whisper(whisper_text)
    typewriter_print(formatted, delay=WHISPER_TYPEWRITER_DELAY)
