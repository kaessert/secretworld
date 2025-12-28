"""Inventory model for CLI RPG."""
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional

from cli_rpg.models.item import Item, ItemType
from cli_rpg import colors


@dataclass
class Inventory:
    """Manages a collection of items with equipment slots.

    Attributes:
        capacity: Maximum number of items (default 20)
        items: List of items in inventory (not equipped)
        equipped_weapon: Currently equipped weapon or None
        equipped_armor: Currently equipped armor or None
    """

    DEFAULT_CAPACITY: ClassVar[int] = 20

    capacity: int = DEFAULT_CAPACITY
    items: List[Item] = field(default_factory=list)
    equipped_weapon: Optional[Item] = None
    equipped_armor: Optional[Item] = None
    equipped_holy_symbol: Optional[Item] = None

    def add_item(self, item: Item) -> bool:
        """Add an item to the inventory.

        Args:
            item: Item to add

        Returns:
            True if item was added, False if inventory is full
        """
        if self.is_full():
            return False
        self.items.append(item)
        return True

    def remove_item(self, item: Item) -> bool:
        """Remove an item from the inventory.

        Args:
            item: Item to remove

        Returns:
            True if item was removed, False if not found
        """
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def remove_item_by_name(self, name: str) -> bool:
        """Remove an item from the inventory by name.

        Args:
            name: Name of item to remove

        Returns:
            True if item was removed, False if not found
        """
        item = self.find_item_by_name(name)
        if item:
            return self.remove_item(item)
        return False

    def is_full(self) -> bool:
        """Check if inventory is at capacity.

        Returns:
            True if inventory is full, False otherwise
        """
        return len(self.items) >= self.capacity

    def remaining_space(self) -> int:
        """Get remaining inventory slots.

        Returns:
            Number of empty slots
        """
        return self.capacity - len(self.items)

    def equip(self, item: Item) -> bool:
        """Equip an item from the inventory.

        Args:
            item: Item to equip (must be weapon or armor)

        Returns:
            True if equipped successfully, False otherwise
        """
        # Check if item is in inventory
        if item not in self.items:
            return False

        # Check if item is equippable
        if item.item_type == ItemType.WEAPON:
            # Unequip current weapon if any (return to inventory)
            if self.equipped_weapon is not None:
                self.items.append(self.equipped_weapon)

            # Remove from inventory and equip
            self.items.remove(item)
            self.equipped_weapon = item
            return True

        elif item.item_type == ItemType.ARMOR:
            # Unequip current armor if any (return to inventory)
            if self.equipped_armor is not None:
                self.items.append(self.equipped_armor)

            # Remove from inventory and equip
            self.items.remove(item)
            self.equipped_armor = item
            return True

        elif item.item_type == ItemType.HOLY_SYMBOL:
            # Unequip current holy symbol if any (return to inventory)
            if self.equipped_holy_symbol is not None:
                self.items.append(self.equipped_holy_symbol)

            # Remove from inventory and equip
            self.items.remove(item)
            self.equipped_holy_symbol = item
            return True

        # Can't equip consumables or misc items
        return False

    def unequip(self, slot: str) -> bool:
        """Unequip an item and return it to inventory.

        Args:
            slot: "weapon" or "armor"

        Returns:
            True if unequipped successfully, False otherwise
        """
        if slot == "weapon":
            if self.equipped_weapon is None:
                return False
            # Check if inventory has space
            if self.is_full():
                return False
            self.items.append(self.equipped_weapon)
            self.equipped_weapon = None
            return True

        elif slot == "armor":
            if self.equipped_armor is None:
                return False
            # Check if inventory has space
            if self.is_full():
                return False
            self.items.append(self.equipped_armor)
            self.equipped_armor = None
            return True

        elif slot == "holy_symbol":
            if self.equipped_holy_symbol is None:
                return False
            # Check if inventory has space
            if self.is_full():
                return False
            self.items.append(self.equipped_holy_symbol)
            self.equipped_holy_symbol = None
            return True

        return False

    def get_damage_bonus(self) -> int:
        """Get total damage bonus from equipped weapon.

        Returns:
            Damage bonus from equipped weapon, or 0 if none
        """
        if self.equipped_weapon is not None:
            return self.equipped_weapon.damage_bonus
        return 0

    def get_defense_bonus(self) -> int:
        """Get total defense bonus from equipped armor.

        Returns:
            Defense bonus from equipped armor, or 0 if none
        """
        if self.equipped_armor is not None:
            return self.equipped_armor.defense_bonus
        return 0

    def get_divine_power_bonus(self) -> int:
        """Get divine power bonus from equipped holy symbol.

        Returns:
            Divine power from equipped holy symbol, or 0 if none
        """
        if self.equipped_holy_symbol is not None:
            return self.equipped_holy_symbol.divine_power
        return 0

    def find_item_by_name(self, name: str) -> Optional[Item]:
        """Find an item in inventory by name (case-insensitive).

        Args:
            name: Name to search for

        Returns:
            Item if found, None otherwise
        """
        name_lower = name.lower()
        for item in self.items:
            if item.name.lower() == name_lower:
                return item
        return None

    def list_items(self) -> List[Item]:
        """Get a copy of all items in inventory.

        Returns:
            List of items (not including equipped items)
        """
        return list(self.items)

    def to_dict(self) -> Dict:
        """Serialize inventory to dictionary.

        Returns:
            Dictionary containing inventory data
        """
        return {
            "capacity": self.capacity,
            "items": [item.to_dict() for item in self.items],
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "equipped_armor": self.equipped_armor.to_dict() if self.equipped_armor else None,
            "equipped_holy_symbol": (
                self.equipped_holy_symbol.to_dict() if self.equipped_holy_symbol else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Inventory":
        """Deserialize inventory from dictionary.

        Args:
            data: Dictionary containing inventory data

        Returns:
            Inventory instance
        """
        items = [Item.from_dict(item_data) for item_data in data.get("items", [])]
        equipped_weapon = None
        equipped_armor = None
        equipped_holy_symbol = None

        if data.get("equipped_weapon"):
            equipped_weapon = Item.from_dict(data["equipped_weapon"])
        if data.get("equipped_armor"):
            equipped_armor = Item.from_dict(data["equipped_armor"])
        if data.get("equipped_holy_symbol"):
            equipped_holy_symbol = Item.from_dict(data["equipped_holy_symbol"])

        return cls(
            capacity=data.get("capacity", cls.DEFAULT_CAPACITY),
            items=items,
            equipped_weapon=equipped_weapon,
            equipped_armor=equipped_armor,
            equipped_holy_symbol=equipped_holy_symbol,
        )

    def __str__(self) -> str:
        """String representation of inventory.

        Returns:
            Formatted string with inventory contents
        """
        lines = [f"{colors.stat_header('Inventory')} ({len(self.items)}/{self.capacity}):"]

        if self.equipped_weapon:
            lines.append(f"  [{colors.stat_header('Weapon')}] {colors.item(self.equipped_weapon.name)}")
        if self.equipped_armor:
            lines.append(f"  [{colors.stat_header('Armor')}] {colors.item(self.equipped_armor.name)}")
        if self.equipped_holy_symbol:
            lines.append(
                f"  [{colors.stat_header('Holy Symbol')}] "
                f"{colors.item(self.equipped_holy_symbol.name)}"
            )

        if self.items:
            lines.append("  Items:")
            for item in self.items:
                lines.append(f"    - {colors.item(item.name)}")
        else:
            lines.append("  No items")

        return "\n".join(lines)
