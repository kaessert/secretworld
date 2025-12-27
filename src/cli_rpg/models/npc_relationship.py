"""NPC relationship model for tracking connections between NPCs."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RelationshipType(Enum):
    """Types of relationships between NPCs."""

    FAMILY = "family"
    FRIEND = "friend"
    RIVAL = "rival"
    MENTOR = "mentor"
    EMPLOYER = "employer"
    ACQUAINTANCE = "acquaintance"


@dataclass
class NPCRelationship:
    """Represents a relationship between an NPC and another NPC.

    Attributes:
        target_npc: Name of the related NPC
        relationship_type: Type of relationship
        trust_level: Strength of relationship (1-100, default 50)
        description: Optional description (e.g., "sister", "former master")
    """

    target_npc: str
    relationship_type: RelationshipType
    trust_level: int = 50
    description: Optional[str] = None

    def __post_init__(self):
        """Validate and clamp trust_level to 1-100."""
        self.trust_level = max(1, min(100, self.trust_level))

    def to_dict(self) -> dict:
        """Serialize relationship to dictionary.

        Returns:
            Dictionary containing all relationship attributes
        """
        return {
            "target_npc": self.target_npc,
            "relationship_type": self.relationship_type.value,
            "trust_level": self.trust_level,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCRelationship":
        """Deserialize relationship from dictionary.

        Args:
            data: Dictionary containing relationship attributes

        Returns:
            NPCRelationship instance
        """
        return cls(
            target_npc=data["target_npc"],
            relationship_type=RelationshipType(data["relationship_type"]),
            trust_level=data.get("trust_level", 50),
            description=data.get("description"),
        )
