"""NPC model for non-hostile characters."""
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.shop import Shop


@dataclass
class NPC:
    """Represents a non-player character in the RPG.

    Attributes:
        name: NPC name (2-30 characters)
        description: What player sees (1-200 characters)
        dialogue: What NPC says when talked to
        is_merchant: Whether NPC runs a shop
        shop: Optional shop if NPC is a merchant
    """

    name: str
    description: str
    dialogue: str
    is_merchant: bool = False
    shop: Optional["Shop"] = None

    def __post_init__(self):
        """Validate NPC attributes."""
        if not 2 <= len(self.name) <= 30:
            raise ValueError("NPC name must be 2-30 characters")
        if not 1 <= len(self.description) <= 200:
            raise ValueError("Description must be 1-200 characters")

    def to_dict(self) -> dict:
        """Serialize NPC to dictionary.

        Returns:
            Dictionary containing all NPC attributes
        """
        return {
            "name": self.name,
            "description": self.description,
            "dialogue": self.dialogue,
            "is_merchant": self.is_merchant,
            "shop": self.shop.to_dict() if self.shop else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        """Deserialize NPC from dictionary.

        Args:
            data: Dictionary containing NPC attributes

        Returns:
            NPC instance
        """
        from cli_rpg.models.shop import Shop
        shop = Shop.from_dict(data["shop"]) if data.get("shop") else None
        return cls(
            name=data["name"],
            description=data["description"],
            dialogue=data["dialogue"],
            is_merchant=data.get("is_merchant", False),
            shop=shop
        )
