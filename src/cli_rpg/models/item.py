"""Item model for CLI RPG inventory system."""
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.weapon_proficiency import WeaponType


class ItemType(Enum):
    """Types of items that can be in inventory."""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MISC = "misc"
    RESOURCE = "resource"
    HOLY_SYMBOL = "holy_symbol"


class ArmorWeight(Enum):
    """Armor weight categories for class restrictions.

    Spec: Mage can only equip LIGHT, Rogue/Ranger/Cleric can equip LIGHT/MEDIUM,
    Warrior can equip all weights (only class for HEAVY).
    """
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass
class Item:
    """Represents an item in the RPG.

    Attributes:
        name: Item name (2-30 characters)
        description: Item description (1-200 characters)
        item_type: Type of item (weapon/armor/consumable/misc)
        damage_bonus: Attack damage bonus when equipped (weapons)
        defense_bonus: Defense bonus when equipped (armor)
        heal_amount: Health restored when consumed (consumables)
    """

    MIN_NAME_LENGTH: ClassVar[int] = 2
    MAX_NAME_LENGTH: ClassVar[int] = 30
    MIN_DESC_LENGTH: ClassVar[int] = 1
    MAX_DESC_LENGTH: ClassVar[int] = 200

    name: str
    description: str
    item_type: ItemType
    damage_bonus: int = 0
    defense_bonus: int = 0
    heal_amount: int = 0
    mana_restore: int = 0
    stamina_restore: int = 0
    light_duration: int = 0
    is_cure: bool = False  # True for items that can cure plagues/events
    weapon_type: Optional["WeaponType"] = None  # Weapon proficiency type for weapons
    armor_weight: Optional[ArmorWeight] = None  # Armor weight for class restrictions
    divine_power: int = 0  # Holy power for holy symbols (Cleric-only)

    def __post_init__(self):
        """Validate item attributes."""
        # Validate name
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")
        if len(self.name) < self.MIN_NAME_LENGTH:
            raise ValueError(f"Name must be at least {self.MIN_NAME_LENGTH} characters")
        if len(self.name) > self.MAX_NAME_LENGTH:
            raise ValueError(f"Name must be at most {self.MAX_NAME_LENGTH} characters")

        # Validate description
        if len(self.description) < self.MIN_DESC_LENGTH:
            raise ValueError(f"description must be at least {self.MIN_DESC_LENGTH} character")
        if len(self.description) > self.MAX_DESC_LENGTH:
            raise ValueError(f"description must be at most {self.MAX_DESC_LENGTH} characters")

        # Validate stat modifiers
        if self.damage_bonus < 0:
            raise ValueError("damage_bonus cannot be negative")
        if self.defense_bonus < 0:
            raise ValueError("defense_bonus cannot be negative")
        if self.heal_amount < 0:
            raise ValueError("heal_amount cannot be negative")
        if self.mana_restore < 0:
            raise ValueError("mana_restore cannot be negative")
        if self.stamina_restore < 0:
            raise ValueError("stamina_restore cannot be negative")
        if self.light_duration < 0:
            raise ValueError("light_duration cannot be negative")
        if self.divine_power < 0:
            raise ValueError("divine_power cannot be negative")

    def to_dict(self) -> Dict:
        """Serialize item to dictionary.

        Returns:
            Dictionary containing all item attributes
        """
        data = {
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type.value,
            "damage_bonus": self.damage_bonus,
            "defense_bonus": self.defense_bonus,
            "heal_amount": self.heal_amount,
            "mana_restore": self.mana_restore,
            "stamina_restore": self.stamina_restore,
            "light_duration": self.light_duration,
            "is_cure": self.is_cure,
            "divine_power": self.divine_power,
        }
        # Only include weapon_type if set
        if self.weapon_type is not None:
            data["weapon_type"] = self.weapon_type.value
        # Only include armor_weight if set
        if self.armor_weight is not None:
            data["armor_weight"] = self.armor_weight.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "Item":
        """Deserialize item from dictionary.

        Args:
            data: Dictionary containing item attributes

        Returns:
            Item instance
        """
        # Handle weapon_type (backward compatible - defaults to None)
        weapon_type = None
        if "weapon_type" in data:
            from cli_rpg.models.weapon_proficiency import WeaponType
            weapon_type = WeaponType(data["weapon_type"])

        # Handle armor_weight (backward compatible - defaults to None)
        armor_weight = None
        if "armor_weight" in data:
            armor_weight = ArmorWeight(data["armor_weight"])

        return cls(
            name=data["name"],
            description=data["description"],
            item_type=ItemType(data["item_type"]),
            damage_bonus=data.get("damage_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
            heal_amount=data.get("heal_amount", 0),
            mana_restore=data.get("mana_restore", 0),
            stamina_restore=data.get("stamina_restore", 0),
            light_duration=data.get("light_duration", 0),
            is_cure=data.get("is_cure", False),
            weapon_type=weapon_type,
            armor_weight=armor_weight,
            divine_power=data.get("divine_power", 0),
        )

    def __str__(self) -> str:
        """String representation of item.

        Returns:
            Formatted string with item details
        """
        type_str = self.item_type.value.capitalize()

        # Show armor weight for armor items
        if self.item_type == ItemType.ARMOR and self.armor_weight is not None:
            type_str = f"{self.armor_weight.value.capitalize()} {type_str}"

        stat_parts = []

        if self.damage_bonus > 0:
            stat_parts.append(f"+{self.damage_bonus} damage")
        if self.defense_bonus > 0:
            stat_parts.append(f"+{self.defense_bonus} defense")
        if self.heal_amount > 0:
            stat_parts.append(f"heals {self.heal_amount} HP")
        if self.mana_restore > 0:
            stat_parts.append(f"restores {self.mana_restore} mana")
        if self.stamina_restore > 0:
            stat_parts.append(f"restores {self.stamina_restore} stamina")
        if self.light_duration > 0:
            stat_parts.append(f"{self.light_duration} moves of light")
        if self.is_cure:
            stat_parts.append("cures plague")
        if self.divine_power > 0:
            stat_parts.append(f"+{self.divine_power} divine power")

        stats_str = f" ({', '.join(stat_parts)})" if stat_parts else ""
        return f"{self.name} [{type_str}]{stats_str}"
