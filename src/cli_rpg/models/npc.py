"""NPC model for non-hostile characters."""
import random
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.shop import Shop
    from cli_rpg.models.quest import Quest


@dataclass
class NPC:
    """Represents a non-player character in the RPG.

    Attributes:
        name: NPC name (2-30 characters)
        description: What player sees (1-200 characters)
        dialogue: What NPC says when talked to
        is_merchant: Whether NPC runs a shop
        shop: Optional shop if NPC is a merchant
        is_quest_giver: Whether NPC offers quests
        offered_quests: List of quests this NPC offers
        conversation_history: List of conversation exchanges with player
        ascii_art: ASCII art representation of the NPC
        available_at_night: Whether NPC is available at night (default True)
    """

    name: str
    description: str
    dialogue: str
    is_merchant: bool = False
    shop: Optional["Shop"] = None
    is_quest_giver: bool = False
    offered_quests: List["Quest"] = field(default_factory=list)
    greetings: List[str] = field(default_factory=list)
    conversation_history: List[dict] = field(default_factory=list)
    ascii_art: str = ""  # ASCII art representation of the NPC
    available_at_night: bool = True  # Whether NPC is available at night

    def __post_init__(self):
        """Validate NPC attributes."""
        if not 2 <= len(self.name) <= 30:
            raise ValueError("NPC name must be 2-30 characters")
        if not 1 <= len(self.description) <= 200:
            raise ValueError("Description must be 1-200 characters")

    def get_greeting(self) -> str:
        """Get a greeting to display when talking to this NPC.

        Returns a random greeting from the greetings list if available,
        otherwise falls back to the dialogue field.
        """
        if self.greetings:
            return random.choice(self.greetings)
        return self.dialogue

    def add_conversation(self, role: str, content: str) -> None:
        """Add a conversation entry to the history.

        Maintains a maximum of 10 entries, removing oldest when exceeded.

        Args:
            role: The role of the speaker ("player" or "npc")
            content: The message content
        """
        self.conversation_history.append({"role": role, "content": content})
        # Cap at 10 entries
        while len(self.conversation_history) > 10:
            self.conversation_history.pop(0)

    def to_dict(self) -> dict:
        """Serialize NPC to dictionary.

        Returns:
            Dictionary containing all NPC attributes
        """
        result = {
            "name": self.name,
            "description": self.description,
            "dialogue": self.dialogue,
            "is_merchant": self.is_merchant,
            "shop": self.shop.to_dict() if self.shop else None,
            "is_quest_giver": self.is_quest_giver,
            "offered_quests": [q.to_dict() for q in self.offered_quests],
            "greetings": self.greetings,
            "conversation_history": self.conversation_history,
            "available_at_night": self.available_at_night
        }
        # Only include ascii_art if it's not empty
        if self.ascii_art:
            result["ascii_art"] = self.ascii_art
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        """Deserialize NPC from dictionary.

        Args:
            data: Dictionary containing NPC attributes

        Returns:
            NPC instance
        """
        from cli_rpg.models.shop import Shop
        from cli_rpg.models.quest import Quest

        shop = Shop.from_dict(data["shop"]) if data.get("shop") else None
        offered_quests = [
            Quest.from_dict(q) for q in data.get("offered_quests", [])
        ]
        return cls(
            name=data["name"],
            description=data["description"],
            dialogue=data["dialogue"],
            is_merchant=data.get("is_merchant", False),
            shop=shop,
            is_quest_giver=data.get("is_quest_giver", False),
            offered_quests=offered_quests,
            greetings=data.get("greetings", []),
            conversation_history=data.get("conversation_history", []),
            ascii_art=data.get("ascii_art", ""),
            available_at_night=data.get("available_at_night", True)
        )
