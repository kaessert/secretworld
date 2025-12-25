"""Companion model for party members with bond mechanics.

The bond system tracks the player's relationship with companions:
- Bond points range from 0-100
- Bond levels are computed from points: STRANGER (0-24), ACQUAINTANCE (25-49),
  TRUSTED (50-74), DEVOTED (75-100)
- Higher bond levels unlock companion abilities and dialogue options
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cli_rpg import colors


class BondLevel(Enum):
    """Bond level thresholds for companion relationships.

    Each level represents a tier of trust and familiarity:
    - STRANGER: Just met, no trust (0-24 points)
    - ACQUAINTANCE: Some familiarity (25-49 points)
    - TRUSTED: Genuine trust (50-74 points)
    - DEVOTED: Unbreakable bond (75-100 points)
    """

    STRANGER = "Stranger"
    ACQUAINTANCE = "Acquaintance"
    TRUSTED = "Trusted"
    DEVOTED = "Devoted"


# Bond level thresholds (minimum points for each level)
BOND_THRESHOLDS = {
    BondLevel.STRANGER: 0,
    BondLevel.ACQUAINTANCE: 25,
    BondLevel.TRUSTED: 50,
    BondLevel.DEVOTED: 75,
}

# Messages for level up transitions
BOND_LEVEL_UP_MESSAGES = {
    BondLevel.ACQUAINTANCE: "{name} begins to trust you more. (Acquaintance)",
    BondLevel.TRUSTED: "{name} truly trusts you now. (Trusted)",
    BondLevel.DEVOTED: "{name}'s bond with you is unbreakable. (Devoted)",
}


@dataclass
class Companion:
    """Represents a companion who has joined the player's party.

    Attributes:
        name: The companion's name
        description: Brief description of the companion
        recruited_at: Name of location where the companion was recruited
        bond_points: Current bond points (0-100)
    """

    name: str
    description: str
    recruited_at: str
    bond_points: int = 0

    def get_bond_level(self) -> BondLevel:
        """Compute the bond level from current bond points.

        Returns:
            BondLevel enum value based on current bond_points
        """
        if self.bond_points >= 75:
            return BondLevel.DEVOTED
        elif self.bond_points >= 50:
            return BondLevel.TRUSTED
        elif self.bond_points >= 25:
            return BondLevel.ACQUAINTANCE
        else:
            return BondLevel.STRANGER

    def add_bond(self, amount: int) -> Optional[str]:
        """Add bond points and return a message if level increases.

        Args:
            amount: Amount of bond points to add (positive integer)

        Returns:
            Level-up message if a bond threshold was crossed, None otherwise
        """
        old_level = self.get_bond_level()
        self.bond_points = min(100, self.bond_points + amount)
        new_level = self.get_bond_level()

        if new_level != old_level and new_level in BOND_LEVEL_UP_MESSAGES:
            return BOND_LEVEL_UP_MESSAGES[new_level].format(name=self.name)

        return None

    def get_bond_display(self) -> str:
        """Get a visual bar representation of the bond level.

        Returns:
            Formatted string like "Bond: ████████░░░░░░░░ Trusted (50%)"
        """
        bar_width = 16
        filled = round(bar_width * self.bond_points / 100)
        empty = bar_width - filled

        bar = "█" * filled + "░" * empty

        # Color based on bond level
        level = self.get_bond_level()
        if level == BondLevel.DEVOTED:
            colored_bar = colors.heal(bar)
        elif level == BondLevel.TRUSTED:
            colored_bar = colors.gold(bar)
        elif level == BondLevel.ACQUAINTANCE:
            colored_bar = colors.warning(bar)
        else:
            colored_bar = bar

        return f"Bond: {colored_bar} {level.value} ({self.bond_points}%)"

    def to_dict(self) -> dict:
        """Serialize companion to dictionary.

        Returns:
            Dictionary containing all companion attributes
        """
        return {
            "name": self.name,
            "description": self.description,
            "recruited_at": self.recruited_at,
            "bond_points": self.bond_points,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Companion":
        """Deserialize companion from dictionary.

        Args:
            data: Dictionary containing companion attributes

        Returns:
            Companion instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            recruited_at=data["recruited_at"],
            bond_points=data.get("bond_points", 0),
        )
