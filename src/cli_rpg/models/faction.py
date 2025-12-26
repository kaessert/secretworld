"""Faction model for tracking player reputation with different groups.

The reputation system tracks the player's standing with various factions:
- Reputation points range from 1-100
- Reputation levels are computed from points: HOSTILE (1-19), UNFRIENDLY (20-39),
  NEUTRAL (40-59), FRIENDLY (60-79), HONORED (80-100)
- Higher reputation levels unlock better prices, quests, and exclusive content
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from cli_rpg import colors


class ReputationLevel(Enum):
    """Reputation level thresholds for faction relationships.

    Each level represents a tier of standing with a faction:
    - HOSTILE: Faction members attack on sight (1-19 points)
    - UNFRIENDLY: Won't trade or offer quests (20-39 points)
    - NEUTRAL: Basic interactions available (40-59 points)
    - FRIENDLY: Discounts, additional quests (60-79 points)
    - HONORED: Best prices, exclusive content (80-100 points)
    """

    HOSTILE = "Hostile"
    UNFRIENDLY = "Unfriendly"
    NEUTRAL = "Neutral"
    FRIENDLY = "Friendly"
    HONORED = "Honored"


# Reputation level thresholds (minimum points for each level)
REPUTATION_THRESHOLDS = {
    ReputationLevel.HOSTILE: 1,
    ReputationLevel.UNFRIENDLY: 20,
    ReputationLevel.NEUTRAL: 40,
    ReputationLevel.FRIENDLY: 60,
    ReputationLevel.HONORED: 80,
}

# Messages for level up transitions
REPUTATION_LEVEL_UP_MESSAGES = {
    ReputationLevel.UNFRIENDLY: "Your standing with {name} has improved to Unfriendly.",
    ReputationLevel.NEUTRAL: "Your standing with {name} has improved to Neutral.",
    ReputationLevel.FRIENDLY: "{name} now considers you a friend. (Friendly)",
    ReputationLevel.HONORED: "You are now honored by {name}! (Honored)",
}

# Messages for level down transitions
REPUTATION_LEVEL_DOWN_MESSAGES = {
    ReputationLevel.HOSTILE: "Your standing with {name} has fallen to Hostile!",
    ReputationLevel.UNFRIENDLY: "Your standing with {name} has fallen to Unfriendly.",
    ReputationLevel.NEUTRAL: "Your standing with {name} has fallen to Neutral.",
    ReputationLevel.FRIENDLY: "Your standing with {name} has fallen to Friendly.",
}


def _clamp_reputation(value: int) -> int:
    """Clamp reputation value to valid range (1-100).

    Args:
        value: The raw reputation value

    Returns:
        Clamped value between 1 and 100
    """
    return max(1, min(100, value))


@dataclass
class Faction:
    """Represents a faction and the player's reputation with it.

    Attributes:
        name: The faction's name
        description: Brief description of the faction
        reputation: Current reputation points (1-100), defaults to 50 (neutral)
    """

    name: str
    description: str
    reputation: int = 50

    def __post_init__(self):
        """Clamp reputation to valid range after initialization."""
        self.reputation = _clamp_reputation(self.reputation)

    def get_reputation_level(self) -> ReputationLevel:
        """Compute the reputation level from current reputation points.

        Returns:
            ReputationLevel enum value based on current reputation
        """
        if self.reputation >= 80:
            return ReputationLevel.HONORED
        elif self.reputation >= 60:
            return ReputationLevel.FRIENDLY
        elif self.reputation >= 40:
            return ReputationLevel.NEUTRAL
        elif self.reputation >= 20:
            return ReputationLevel.UNFRIENDLY
        else:
            return ReputationLevel.HOSTILE

    def add_reputation(self, amount: int) -> Optional[str]:
        """Add reputation points and return a message if level increases.

        Args:
            amount: Amount of reputation points to add (positive integer)

        Returns:
            Level-up message if a reputation threshold was crossed, None otherwise
        """
        old_level = self.get_reputation_level()
        self.reputation = _clamp_reputation(self.reputation + amount)
        new_level = self.get_reputation_level()

        if new_level != old_level and new_level in REPUTATION_LEVEL_UP_MESSAGES:
            return REPUTATION_LEVEL_UP_MESSAGES[new_level].format(name=self.name)

        return None

    def reduce_reputation(self, amount: int) -> Optional[str]:
        """Reduce reputation points and return a message if level decreases.

        Args:
            amount: Amount of reputation points to reduce (positive integer)

        Returns:
            Level-down message if a reputation threshold was crossed, None otherwise
        """
        old_level = self.get_reputation_level()
        self.reputation = _clamp_reputation(self.reputation - amount)
        new_level = self.get_reputation_level()

        if new_level != old_level and new_level in REPUTATION_LEVEL_DOWN_MESSAGES:
            return REPUTATION_LEVEL_DOWN_MESSAGES[new_level].format(name=self.name)

        return None

    def get_reputation_display(self) -> str:
        """Get a visual bar representation of the reputation level.

        Returns:
            Formatted string like "Reputation: ████████░░░░░░░░ Neutral (50%)"
        """
        bar_width = 16
        filled = round(bar_width * self.reputation / 100)
        empty = bar_width - filled

        bar = "█" * filled + "░" * empty

        # Color based on reputation level
        level = self.get_reputation_level()
        if level == ReputationLevel.HONORED:
            colored_bar = colors.heal(bar)
        elif level == ReputationLevel.FRIENDLY:
            colored_bar = colors.gold(bar)
        elif level == ReputationLevel.NEUTRAL:
            colored_bar = bar
        elif level == ReputationLevel.UNFRIENDLY:
            colored_bar = colors.warning(bar)
        else:  # HOSTILE
            colored_bar = colors.damage(bar)

        return f"Reputation: {colored_bar} {level.value} ({self.reputation}%)"

    def to_dict(self) -> dict:
        """Serialize faction to dictionary.

        Returns:
            Dictionary containing all faction attributes
        """
        return {
            "name": self.name,
            "description": self.description,
            "reputation": self.reputation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Faction":
        """Deserialize faction from dictionary.

        Args:
            data: Dictionary containing faction attributes

        Returns:
            Faction instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            reputation=data.get("reputation", 50),
        )
