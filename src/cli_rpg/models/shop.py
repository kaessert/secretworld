"""Shop model for merchant NPCs."""
from dataclasses import dataclass, field
from typing import List, Optional
from cli_rpg.models.item import Item


@dataclass
class ShopItem:
    """An item available in a shop with pricing.

    Attributes:
        item: The item being sold
        buy_price: Cost to buy from shop
    """

    item: Item
    buy_price: int

    @property
    def sell_price(self) -> int:
        """Sell price is 50% of buy price (integer division)."""
        return self.buy_price // 2

    def to_dict(self) -> dict:
        """Serialize ShopItem to dictionary.

        Returns:
            Dictionary containing item and buy_price
        """
        return {
            "item": self.item.to_dict(),
            "buy_price": self.buy_price
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShopItem":
        """Deserialize ShopItem from dictionary.

        Args:
            data: Dictionary containing item and buy_price

        Returns:
            ShopItem instance
        """
        return cls(
            item=Item.from_dict(data["item"]),
            buy_price=data["buy_price"]
        )


@dataclass
class Shop:
    """A shop with inventory for buying/selling.

    Attributes:
        name: Shop name
        inventory: List of ShopItems for sale
    """

    name: str
    inventory: List[ShopItem] = field(default_factory=list)

    def find_item_by_name(self, name: str) -> Optional[ShopItem]:
        """Find a shop item by name (case-insensitive).

        Args:
            name: Item name to search for

        Returns:
            ShopItem if found, None otherwise
        """
        name_lower = name.lower()
        for shop_item in self.inventory:
            if shop_item.item.name.lower() == name_lower:
                return shop_item
        return None

    def find_items_by_partial_name(self, partial_name: str) -> List[ShopItem]:
        """Find shop items where name contains partial_name (case-insensitive).

        Args:
            partial_name: Partial item name to search for

        Returns:
            List of matching ShopItems
        """
        partial_lower = partial_name.lower()
        return [si for si in self.inventory if partial_lower in si.item.name.lower()]

    def to_dict(self) -> dict:
        """Serialize Shop to dictionary.

        Returns:
            Dictionary containing name and inventory
        """
        return {
            "name": self.name,
            "inventory": [si.to_dict() for si in self.inventory]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Shop":
        """Deserialize Shop from dictionary.

        Args:
            data: Dictionary containing name and inventory

        Returns:
            Shop instance
        """
        return cls(
            name=data["name"],
            inventory=[ShopItem.from_dict(si) for si in data.get("inventory", [])]
        )
