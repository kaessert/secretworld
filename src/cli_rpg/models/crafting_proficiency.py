"""Crafting proficiency model for CLI RPG.

Implements a crafting skill system where successful crafts increase skill,
providing success rate bonuses and unlocking advanced recipes.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class CraftingLevel(Enum):
    """Crafting skill levels.

    | Level | XP Required | Success Bonus | Notes |
    |-------|-------------|---------------|-------|
    | Novice | 0 | +0% | Basic recipes only |
    | Apprentice | 25 | +5% | - |
    | Journeyman | 50 | +10% | Unlock iron recipes |
    | Expert | 75 | +15% | - |
    | Master | 100 | +20% | - |
    """

    NOVICE = "Novice"
    APPRENTICE = "Apprentice"
    JOURNEYMAN = "Journeyman"
    EXPERT = "Expert"
    MASTER = "Master"


# XP thresholds for each level
LEVEL_THRESHOLDS = {
    CraftingLevel.NOVICE: 0,
    CraftingLevel.APPRENTICE: 25,
    CraftingLevel.JOURNEYMAN: 50,
    CraftingLevel.EXPERT: 75,
    CraftingLevel.MASTER: 100,
}

# Success bonus multiplier for each level (additive, e.g., 0.05 = +5%)
LEVEL_SUCCESS_BONUS = {
    CraftingLevel.NOVICE: 0.0,
    CraftingLevel.APPRENTICE: 0.05,
    CraftingLevel.JOURNEYMAN: 0.10,
    CraftingLevel.EXPERT: 0.15,
    CraftingLevel.MASTER: 0.20,
}


@dataclass
class CraftingProficiency:
    """Tracks crafting proficiency for a character.

    Attributes:
        xp: Current experience points (0-100)
    """

    xp: int = 0

    def get_level(self) -> CraftingLevel:
        """Get the current crafting level based on XP.

        Returns:
            CraftingLevel corresponding to current XP
        """
        if self.xp >= 100:
            return CraftingLevel.MASTER
        elif self.xp >= 75:
            return CraftingLevel.EXPERT
        elif self.xp >= 50:
            return CraftingLevel.JOURNEYMAN
        elif self.xp >= 25:
            return CraftingLevel.APPRENTICE
        else:
            return CraftingLevel.NOVICE

    def get_success_bonus(self) -> float:
        """Get the success rate bonus for current crafting level.

        Returns:
            Success bonus (0.0, 0.05, 0.10, 0.15, or 0.20)
        """
        return LEVEL_SUCCESS_BONUS[self.get_level()]

    def gain_xp(self, amount: int) -> Optional[str]:
        """Add XP and check for level-up.

        Args:
            amount: Amount of XP to gain

        Returns:
            Level-up message if leveled up, None otherwise
        """
        old_level = self.get_level()
        self.xp = min(100, self.xp + amount)  # Cap at 100
        new_level = self.get_level()

        if new_level != old_level:
            return f"Your crafting proficiency increased to {new_level.value}!"

        return None

    def to_dict(self) -> Dict:
        """Serialize proficiency to dictionary.

        Returns:
            Dictionary containing xp
        """
        return {
            "xp": self.xp,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CraftingProficiency":
        """Deserialize proficiency from dictionary.

        Args:
            data: Dictionary containing xp

        Returns:
            CraftingProficiency instance
        """
        return cls(
            xp=data.get("xp", 0),
        )
