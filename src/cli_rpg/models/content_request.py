"""Content request/response models for the ContentLayer.

This module defines typed dataclass schemas for content requests and responses,
providing a formal interface between procedural generators and content providers
(AIService, FallbackContentProvider).

Request models describe what content is needed (room, NPC, item, quest).
Response models describe what content is returned (names, descriptions, stats).
"""

from dataclasses import dataclass
from typing import Optional


# =============================================================================
# Request Models
# =============================================================================


@dataclass
class RoomContentRequest:
    """Request for room name and description content.

    Attributes:
        room_type: Type of room (entry, corridor, chamber, boss_room, treasure, puzzle).
        category: Location category (dungeon, cave, temple, etc.) for thematic content.
        connections: List of connected directions (north, south, east, west, up, down).
        is_entry: Whether this is an entry/exit point to the overworld.
        coordinates: 3D coordinates (x, y, z) for cache keying and context.
    """

    room_type: str
    category: str
    connections: list[str]
    is_entry: bool
    coordinates: tuple[int, int, int]


@dataclass
class NPCContentRequest:
    """Request for NPC name, description, and dialogue content.

    Attributes:
        role: NPC's role (merchant, guard, quest_giver, villager, elder, etc.).
        category: Location category for contextual content.
        coordinates: 3D coordinates for cache keying.
    """

    role: str
    category: str
    coordinates: tuple[int, int, int]


@dataclass
class ItemContentRequest:
    """Request for item name, description, and stats content.

    Attributes:
        item_type: Type of item (weapon, armor, consumable, misc).
        category: Location category for thematic items.
        coordinates: 3D coordinates for cache keying.
    """

    item_type: str
    category: str
    coordinates: tuple[int, int, int]


@dataclass
class QuestContentRequest:
    """Request for quest name, description, and objective content.

    Attributes:
        category: Location category for thematic quests.
        coordinates: 3D coordinates for cache keying.
    """

    category: str
    coordinates: tuple[int, int, int]


# =============================================================================
# Response Models
# =============================================================================


@dataclass
class RoomContentResponse:
    """Response containing room name and description.

    Attributes:
        name: The room's display name.
        description: The room's description text.
    """

    name: str
    description: str

    @classmethod
    def from_dict(cls, data: dict) -> "RoomContentResponse":
        """Create RoomContentResponse from dictionary.

        Args:
            data: Dictionary with "name" and "description" keys.

        Returns:
            RoomContentResponse instance.
        """
        return cls(
            name=data.get("name", "Unknown Chamber"),
            description=data.get("description", "A mysterious room."),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary with "name" and "description" keys.
        """
        return {"name": self.name, "description": self.description}


@dataclass
class NPCContentResponse:
    """Response containing NPC name, description, and dialogue.

    Attributes:
        name: The NPC's display name.
        description: The NPC's physical/contextual description.
        dialogue: The NPC's initial dialogue line.
    """

    name: str
    description: str
    dialogue: str

    @classmethod
    def from_dict(cls, data: dict) -> "NPCContentResponse":
        """Create NPCContentResponse from dictionary.

        Args:
            data: Dictionary with "name", "description", and "dialogue" keys.

        Returns:
            NPCContentResponse instance.
        """
        return cls(
            name=data.get("name", "Mysterious Stranger"),
            description=data.get("description", "A person of unknown purpose."),
            dialogue=data.get("dialogue", "..."),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary with "name", "description", and "dialogue" keys.
        """
        return {
            "name": self.name,
            "description": self.description,
            "dialogue": self.dialogue,
        }


@dataclass
class ItemContentResponse:
    """Response containing item name, description, and stats.

    Attributes:
        name: The item's display name.
        description: The item's description text.
        item_type: Type of item (weapon, armor, consumable, misc).
        damage_bonus: Weapon damage bonus (weapons only).
        defense_bonus: Armor defense bonus (armor only).
        heal_amount: Healing amount (consumables only).
    """

    name: str
    description: str
    item_type: str
    damage_bonus: Optional[int] = None
    defense_bonus: Optional[int] = None
    heal_amount: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ItemContentResponse":
        """Create ItemContentResponse from dictionary.

        Args:
            data: Dictionary with item fields.

        Returns:
            ItemContentResponse instance.
        """
        return cls(
            name=data.get("name", "Unknown Item"),
            description=data.get("description", "A mysterious object."),
            item_type=data.get("item_type", "misc"),
            damage_bonus=data.get("damage_bonus"),
            defense_bonus=data.get("defense_bonus"),
            heal_amount=data.get("heal_amount"),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary with item fields.
        """
        result = {
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
        }
        if self.damage_bonus is not None:
            result["damage_bonus"] = self.damage_bonus
        if self.defense_bonus is not None:
            result["defense_bonus"] = self.defense_bonus
        if self.heal_amount is not None:
            result["heal_amount"] = self.heal_amount
        return result


@dataclass
class QuestContentResponse:
    """Response containing quest name, description, and objective.

    Attributes:
        name: The quest's display name.
        description: The quest's description text.
        objective_type: Type of objective (kill, collect, explore, talk).
        target: The objective's target (enemy name, item name, location, NPC).
    """

    name: str
    description: str
    objective_type: str
    target: str

    @classmethod
    def from_dict(cls, data: dict) -> "QuestContentResponse":
        """Create QuestContentResponse from dictionary.

        Args:
            data: Dictionary with quest fields.

        Returns:
            QuestContentResponse instance.
        """
        return cls(
            name=data.get("name", "A Simple Task"),
            description=data.get("description", "Complete an objective."),
            objective_type=data.get("objective_type", "explore"),
            target=data.get("target", "Destination"),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary with quest fields.
        """
        return {
            "name": self.name,
            "description": self.description,
            "objective_type": self.objective_type,
            "target": self.target,
        }
