"""Item model for CLI RPG inventory system."""
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Dict


class ItemType(Enum):
    """Types of items that can be in inventory."""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MISC = "misc"


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
    light_duration: int = 0

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
        if self.light_duration < 0:
            raise ValueError("light_duration cannot be negative")

    def to_dict(self) -> Dict:
        """Serialize item to dictionary.

        Returns:
            Dictionary containing all item attributes
        """
        return {
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type.value,
            "damage_bonus": self.damage_bonus,
            "defense_bonus": self.defense_bonus,
            "heal_amount": self.heal_amount,
            "light_duration": self.light_duration
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Item":
        """Deserialize item from dictionary.

        Args:
            data: Dictionary containing item attributes

        Returns:
            Item instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            item_type=ItemType(data["item_type"]),
            damage_bonus=data.get("damage_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
            heal_amount=data.get("heal_amount", 0),
            light_duration=data.get("light_duration", 0)
        )

    def __str__(self) -> str:
        """String representation of item.

        Returns:
            Formatted string with item details
        """
        type_str = self.item_type.value.capitalize()
        stat_parts = []

        if self.damage_bonus > 0:
            stat_parts.append(f"+{self.damage_bonus} damage")
        if self.defense_bonus > 0:
            stat_parts.append(f"+{self.defense_bonus} defense")
        if self.heal_amount > 0:
            stat_parts.append(f"heals {self.heal_amount} HP")
        if self.light_duration > 0:
            stat_parts.append(f"{self.light_duration} moves of light")

        stats_str = f" ({', '.join(stat_parts)})" if stat_parts else ""
        return f"{self.name} [{type_str}]{stats_str}"
