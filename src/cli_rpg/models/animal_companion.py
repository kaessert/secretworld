"""Animal companion model for Ranger class.

Spec: Rangers can tame a single animal companion that provides combat assistance:
- Flank Bonus: +10% damage by default, +15% for wolves
- Companion Attack: Secondary attack each round (50% of Ranger's base damage)
- Out-of-Combat Perks: Track bonus (+15%), Perception bonus (+3 for hawks)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

from cli_rpg import colors
from cli_rpg.models.companion import BondLevel, BOND_THRESHOLDS, BOND_LEVEL_UP_MESSAGES


class AnimalType(Enum):
    """Types of animals that can be tamed by Rangers.

    Each type has unique bonuses:
    - WOLF: +15% flank bonus (pack tactics)
    - HAWK: +3 PER bonus for secrets/tracking
    - BEAR: 2x health, can tank hits
    """

    WOLF = "Wolf"
    HAWK = "Hawk"
    BEAR = "Bear"


# Base health for animal companions
BASE_COMPANION_HEALTH = 30

# Bonuses by animal type (Spec values)
ANIMAL_TYPE_BONUSES: Dict[AnimalType, Dict[str, float]] = {
    AnimalType.WOLF: {"flank_bonus": 0.15, "perception_bonus": 0, "health_multiplier": 1.0},
    AnimalType.HAWK: {"flank_bonus": 0.10, "perception_bonus": 3, "health_multiplier": 0.5},
    AnimalType.BEAR: {"flank_bonus": 0.10, "perception_bonus": 0, "health_multiplier": 2.0},
}

# Base flank bonus for all companions
BASE_FLANK_BONUS = 0.10


@dataclass
class AnimalCompanion:
    """Represents a Ranger's animal companion.

    Attributes:
        name: The companion's given name
        animal_type: Type of animal (Wolf, Hawk, Bear)
        health: Current health points
        max_health: Maximum health points (varies by type)
        bond_points: Bond level with the Ranger (0-100)
        is_present: Whether companion is currently summoned
    """

    name: str
    animal_type: AnimalType
    health: int
    max_health: int
    bond_points: int = 0
    is_present: bool = True

    @classmethod
    def create(cls, name: str, animal_type: AnimalType) -> "AnimalCompanion":
        """Create a new animal companion with proper health based on type.

        Args:
            name: Name for the companion
            animal_type: Type of animal

        Returns:
            New AnimalCompanion instance with calculated health
        """
        bonuses = ANIMAL_TYPE_BONUSES[animal_type]
        max_health = int(BASE_COMPANION_HEALTH * bonuses["health_multiplier"])
        return cls(
            name=name,
            animal_type=animal_type,
            health=max_health,
            max_health=max_health,
        )

    def get_bond_level(self) -> BondLevel:
        """Compute the bond level from current bond points.

        Uses same thresholds as humanoid companions:
        - STRANGER: 0-24 points
        - ACQUAINTANCE: 25-49 points
        - TRUSTED: 50-74 points
        - DEVOTED: 75-100 points

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

    def reduce_bond(self, amount: int) -> None:
        """Reduce bond points, clamping to 0.

        Args:
            amount: Amount of bond points to reduce (positive integer)
        """
        self.bond_points = max(0, self.bond_points - amount)

    def get_flank_bonus(self) -> float:
        """Get the flank damage bonus for combat.

        Wolf provides +15% flank bonus, others provide +10%.
        Returns 0 if companion is not present.

        Returns:
            Flank bonus as a decimal (0.10 to 0.15), or 0.0 if not present
        """
        if not self.is_present:
            return 0.0
        return ANIMAL_TYPE_BONUSES[self.animal_type]["flank_bonus"]

    def get_perception_bonus(self) -> int:
        """Get perception bonus for tracking/secrets.

        Hawk provides +3 PER, others provide +0.
        Returns 0 if companion is not present.

        Returns:
            PER bonus (0 or 3), or 0 if not present
        """
        if not self.is_present:
            return 0
        return int(ANIMAL_TYPE_BONUSES[self.animal_type]["perception_bonus"])

    def get_attack_damage(self, ranger_strength: int) -> int:
        """Calculate companion's attack damage.

        Companion deals 50% of Ranger's base strength as damage.
        Returns 0 if companion is not present or dead.

        Args:
            ranger_strength: The Ranger's strength stat

        Returns:
            Attack damage (minimum 1), or 0 if not present/dead
        """
        if not self.is_present or not self.is_alive():
            return 0
        return max(1, ranger_strength // 2)

    def is_alive(self) -> bool:
        """Check if companion is alive.

        Returns:
            True if health > 0, False otherwise
        """
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        """Reduce health by damage amount, minimum 0.

        Args:
            amount: Amount of damage to take
        """
        self.health = max(0, self.health - amount)

    def heal(self, amount: int) -> int:
        """Increase health by heal amount, maximum max_health.

        Args:
            amount: Amount of health to restore

        Returns:
            Amount actually healed
        """
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - old_health

    def summon(self) -> bool:
        """Summon the companion (set is_present to True).

        Returns:
            True if companion was summoned (was dismissed), False if already present
        """
        if self.is_present:
            return False
        self.is_present = True
        return True

    def dismiss(self) -> bool:
        """Dismiss the companion (set is_present to False).

        Returns:
            True if companion was dismissed (was present), False if already dismissed
        """
        if not self.is_present:
            return False
        self.is_present = False
        return True

    def get_status_display(self) -> str:
        """Get a formatted display of companion status.

        Returns:
            Formatted string with companion details
        """
        status = colors.heal("Present") if self.is_present else colors.warning("Dismissed")
        alive_status = colors.heal("Alive") if self.is_alive() else colors.damage("Dead")

        # Color health based on percentage
        health_pct = self.health / self.max_health if self.max_health > 0 else 0
        if health_pct > 0.5:
            health_str = colors.heal(f"{self.health}/{self.max_health}")
        elif health_pct > 0.25:
            health_str = colors.gold(f"{self.health}/{self.max_health}")
        else:
            health_str = colors.damage(f"{self.health}/{self.max_health}")

        # Bond display
        level = self.get_bond_level()
        bar_width = 16
        filled = round(bar_width * self.bond_points / 100)
        empty = bar_width - filled
        bar = "█" * filled + "░" * empty

        if level == BondLevel.DEVOTED:
            colored_bar = colors.heal(bar)
        elif level == BondLevel.TRUSTED:
            colored_bar = colors.gold(bar)
        elif level == BondLevel.ACQUAINTANCE:
            colored_bar = colors.warning(bar)
        else:
            colored_bar = bar

        bond_display = f"Bond: {colored_bar} {level.value} ({self.bond_points}%)"

        # Type-specific bonuses
        bonuses = ANIMAL_TYPE_BONUSES[self.animal_type]
        flank_pct = int(bonuses["flank_bonus"] * 100)
        bonus_info = f"Flank: +{flank_pct}%"
        if bonuses["perception_bonus"] > 0:
            bonus_info += f" | PER: +{int(bonuses['perception_bonus'])}"
        if bonuses["health_multiplier"] != 1.0:
            health_mult = bonuses["health_multiplier"]
            if health_mult > 1:
                bonus_info += f" | Health: {health_mult:.0f}x"
            else:
                bonus_info += f" | Health: {health_mult:.1f}x"

        return (
            f"{self.name} the {self.animal_type.value} - {status} ({alive_status})\n"
            f"Health: {health_str}\n"
            f"{bond_display}\n"
            f"Bonuses: {bonus_info}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize companion to dictionary for save/load.

        Returns:
            Dictionary containing all companion attributes
        """
        return {
            "name": self.name,
            "animal_type": self.animal_type.value,
            "health": self.health,
            "max_health": self.max_health,
            "bond_points": self.bond_points,
            "is_present": self.is_present,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimalCompanion":
        """Deserialize companion from dictionary.

        Args:
            data: Dictionary containing companion attributes

        Returns:
            AnimalCompanion instance
        """
        # Convert animal_type string back to enum
        animal_type_str = data["animal_type"]
        animal_type = None
        for at in AnimalType:
            if at.value == animal_type_str:
                animal_type = at
                break
        if animal_type is None:
            # Fallback to Wolf if unknown type
            animal_type = AnimalType.WOLF

        return cls(
            name=data["name"],
            animal_type=animal_type,
            health=data["health"],
            max_health=data["max_health"],
            bond_points=data.get("bond_points", 0),
            is_present=data.get("is_present", True),
        )
