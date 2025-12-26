"""Weapon proficiency model for CLI RPG.

Implements a weapon proficiency system where using a weapon type increases skill,
providing damage bonuses and eventually unlocking special moves.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class WeaponType(Enum):
    """Types of weapons that can have proficiencies."""

    SWORD = "sword"
    AXE = "axe"
    DAGGER = "dagger"
    MACE = "mace"
    BOW = "bow"
    STAFF = "staff"
    UNKNOWN = "unknown"  # For weapons that don't fit categories


class ProficiencyLevel(Enum):
    """Proficiency skill levels.

    | Level | XP Required | Damage Bonus | Special |
    |-------|-------------|--------------|---------|
    | Novice | 0 | +0% | - |
    | Apprentice | 25 | +5% | - |
    | Journeyman | 50 | +10% | Unlock special move |
    | Expert | 75 | +15% | - |
    | Master | 100 | +20% | Enhanced special move |
    """

    NOVICE = "Novice"
    APPRENTICE = "Apprentice"
    JOURNEYMAN = "Journeyman"
    EXPERT = "Expert"
    MASTER = "Master"


# XP thresholds for each level
LEVEL_THRESHOLDS = {
    ProficiencyLevel.NOVICE: 0,
    ProficiencyLevel.APPRENTICE: 25,
    ProficiencyLevel.JOURNEYMAN: 50,
    ProficiencyLevel.EXPERT: 75,
    ProficiencyLevel.MASTER: 100,
}

# Damage bonus multiplier for each level
LEVEL_DAMAGE_BONUS = {
    ProficiencyLevel.NOVICE: 1.0,
    ProficiencyLevel.APPRENTICE: 1.05,
    ProficiencyLevel.JOURNEYMAN: 1.10,
    ProficiencyLevel.EXPERT: 1.15,
    ProficiencyLevel.MASTER: 1.20,
}


@dataclass
class WeaponProficiency:
    """Tracks proficiency with a specific weapon type.

    Attributes:
        weapon_type: The type of weapon this proficiency tracks
        xp: Current experience points (0-100)
    """

    weapon_type: WeaponType
    xp: int = 0

    def get_level(self) -> ProficiencyLevel:
        """Get the current proficiency level based on XP.

        Returns:
            ProficiencyLevel corresponding to current XP
        """
        if self.xp >= 100:
            return ProficiencyLevel.MASTER
        elif self.xp >= 75:
            return ProficiencyLevel.EXPERT
        elif self.xp >= 50:
            return ProficiencyLevel.JOURNEYMAN
        elif self.xp >= 25:
            return ProficiencyLevel.APPRENTICE
        else:
            return ProficiencyLevel.NOVICE

    def get_damage_bonus(self) -> float:
        """Get the damage multiplier for current proficiency level.

        Returns:
            Damage multiplier (1.0, 1.05, 1.10, 1.15, or 1.20)
        """
        return LEVEL_DAMAGE_BONUS[self.get_level()]

    def can_use_special(self) -> bool:
        """Check if special move is unlocked (Journeyman+).

        Returns:
            True if player can use the special move for this weapon type
        """
        level = self.get_level()
        return level in (
            ProficiencyLevel.JOURNEYMAN,
            ProficiencyLevel.EXPERT,
            ProficiencyLevel.MASTER,
        )

    def is_special_enhanced(self) -> bool:
        """Check if special move is enhanced (Master only).

        Returns:
            True if special move has enhanced effects
        """
        return self.get_level() == ProficiencyLevel.MASTER

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
            weapon_name = self.weapon_type.value.capitalize()
            return f"Your {weapon_name} proficiency increased to {new_level.value}!"

        return None

    def to_dict(self) -> Dict:
        """Serialize proficiency to dictionary.

        Returns:
            Dictionary containing weapon_type and xp
        """
        return {
            "weapon_type": self.weapon_type.value,
            "xp": self.xp,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WeaponProficiency":
        """Deserialize proficiency from dictionary.

        Args:
            data: Dictionary containing weapon_type and xp

        Returns:
            WeaponProficiency instance
        """
        return cls(
            weapon_type=WeaponType(data["weapon_type"]),
            xp=data.get("xp", 0),
        )


def infer_weapon_type(item_name: str) -> WeaponType:
    """Infer weapon type from item name.

    Args:
        item_name: Name of the weapon item

    Returns:
        WeaponType based on name matching
    """
    name_lower = item_name.lower()

    # Sword keywords
    if any(
        kw in name_lower
        for kw in ["sword", "blade", "rapier", "claymore", "longsword", "shortsword"]
    ):
        return WeaponType.SWORD

    # Axe keywords
    if any(kw in name_lower for kw in ["axe", "hatchet"]):
        return WeaponType.AXE

    # Dagger keywords
    if any(kw in name_lower for kw in ["dagger", "knife", "stiletto", "shiv"]):
        return WeaponType.DAGGER

    # Mace keywords
    if any(kw in name_lower for kw in ["mace", "hammer", "morning star", "flail", "club"]):
        return WeaponType.MACE

    # Bow keywords
    if any(kw in name_lower for kw in ["bow", "crossbow"]):
        return WeaponType.BOW

    # Staff keywords
    if any(kw in name_lower for kw in ["staff", "wand", "rod", "scepter"]):
        return WeaponType.STAFF

    return WeaponType.UNKNOWN
