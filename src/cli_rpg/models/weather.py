"""Weather model for weather system.

The weather system tracks atmospheric conditions that affect gameplay:
- clear: Default weather, no modifiers
- rain: Atmospheric, +2 dread per move
- storm: Dangerous, +5 dread per move, +1 hour travel time
- fog: Mysterious, +3 dread per move
"""

import random
from dataclasses import dataclass, field
from typing import Optional


# Weather flavor text for movement messages
WEATHER_FLAVOR = {
    "clear": [
        "The sky is clear above you.",
        "Sunlight warms your path.",
        "A pleasant breeze accompanies you.",
    ],
    "rain": [
        "Rain patters against your gear.",
        "You trudge through the mud.",
        "Cold rain drips down your collar.",
        "The drizzle makes the path slick.",
    ],
    "storm": [
        "Thunder rumbles ominously overhead.",
        "Lightning illuminates the path ahead.",
        "The storm howls around you.",
        "Rain lashes at you from all sides.",
    ],
    "fog": [
        "Mist swirls around you.",
        "Shapes move in the fog...",
        "The fog muffles all sound.",
        "Visibility drops as fog thickens.",
    ],
}

# Display symbols for each weather type
WEATHER_DISPLAY = {
    "clear": "Clear ☀",
    "rain": "Rain ☔",
    "storm": "Storm ⛈",
    "fog": "Fog 🌫",
}

# Visibility levels for each weather type
# - "full": No visibility reduction (clear/rain)
# - "reduced": Truncated descriptions, no details/secrets (storm)
# - "obscured": Some exits hidden, NPC names obscured (fog)
VISIBILITY_LEVELS = {
    "clear": "full",
    "rain": "full",
    "storm": "reduced",
    "fog": "obscured",
}


@dataclass
class Weather:
    """Tracks the current weather condition.

    Attributes:
        condition: Current weather state (clear, rain, storm, fog)
    """

    condition: str = "clear"

    # Class-level constants
    WEATHER_STATES: list[str] = field(
        default_factory=lambda: ["clear", "rain", "storm", "fog"],
        repr=False,
        compare=False,
    )
    DREAD_MODIFIERS: dict[str, int] = field(
        default_factory=lambda: {"clear": 0, "rain": 2, "storm": 5, "fog": 3},
        repr=False,
        compare=False,
    )
    TRAVEL_MODIFIERS: dict[str, int] = field(
        default_factory=lambda: {"clear": 0, "rain": 0, "storm": 1, "fog": 0},
        repr=False,
        compare=False,
    )

    # Override class attributes to be actual class constants (not instance fields)
    def __post_init__(self) -> None:
        """Initialize class-level constants after dataclass init."""
        pass

    def get_display(self) -> str:
        """Get a human-readable weather display with emoji.

        Returns:
            Formatted string like "Clear ☀" or "Rain ☔"
        """
        return WEATHER_DISPLAY.get(self.condition, f"{self.condition.capitalize()}")

    def get_dread_modifier(self) -> int:
        """Get the dread modifier for current weather.

        Returns:
            Dread points added per movement (0, 2, 3, or 5)
        """
        return self.DREAD_MODIFIERS.get(self.condition, 0)

    def get_travel_modifier(self) -> int:
        """Get the travel time modifier for current weather.

        Returns:
            Extra hours added to travel (0 or 1)
        """
        return self.TRAVEL_MODIFIERS.get(self.condition, 0)

    def get_flavor_text(self) -> str:
        """Get a random flavor text for the current weather.

        Returns:
            A descriptive string for the current weather
        """
        texts = WEATHER_FLAVOR.get(self.condition, ["The weather is unremarkable."])
        return random.choice(texts)

    def get_effective_condition(self, location_category: Optional[str] = None) -> str:
        """Get the effective weather condition, accounting for location.

        Some locations (like caves) are sheltered from weather.

        Args:
            location_category: The category of the current location

        Returns:
            The effective weather condition (always 'clear' in caves)
        """
        # Caves are underground - always clear
        if location_category == "cave":
            return "clear"
        return self.condition

    def get_visibility_level(self, location_category: Optional[str] = None) -> str:
        """Get the visibility level for the current weather.

        Visibility affects what players can see when looking at locations:
        - "full": No visibility reduction (clear/rain)
        - "reduced": Truncated descriptions, no details/secrets (storm)
        - "obscured": Some exits hidden, NPC names obscured (fog)

        Cave locations (underground) always have full visibility.

        Args:
            location_category: The category of the current location

        Returns:
            Visibility level string ("full", "reduced", or "obscured")
        """
        # Caves are underground - always full visibility
        if location_category == "cave":
            return "full"
        return VISIBILITY_LEVELS.get(self.condition, "full")

    def transition(self) -> Optional[str]:
        """Potentially change weather state (10% chance per hour).

        Returns:
            New weather condition if changed, None otherwise
        """
        # 10% chance of weather change per hour
        if random.random() < 0.1:
            # Pick a new weather state (can be the same)
            new_condition = random.choice(self.WEATHER_STATES)
            if new_condition != self.condition:
                self.condition = new_condition
                return new_condition
        return None

    def to_dict(self) -> dict:
        """Serialize weather to dictionary.

        Returns:
            Dictionary containing weather condition
        """
        return {"condition": self.condition}

    @classmethod
    def from_dict(cls, data: dict) -> "Weather":
        """Deserialize weather from dictionary.

        Args:
            data: Dictionary containing weather condition

        Returns:
            Weather instance
        """
        return cls(condition=data.get("condition", "clear"))


# Make WEATHER_STATES a class-level constant (not instance field)
Weather.WEATHER_STATES = ["clear", "rain", "storm", "fog"]
Weather.DREAD_MODIFIERS = {"clear": 0, "rain": 2, "storm": 5, "fog": 3}
Weather.TRAVEL_MODIFIERS = {"clear": 0, "rain": 0, "storm": 1, "fog": 0}
