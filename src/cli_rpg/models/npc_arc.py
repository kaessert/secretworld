"""NPC character arc model for tracking relationship progression with player."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class NPCArcStage(Enum):
    """Character arc stages based on accumulated interaction points."""

    # Positive stages (0 to 100)
    STRANGER = "stranger"  # 0-24: Default, no history
    ACQUAINTANCE = "acquaintance"  # 25-49: Some familiarity
    TRUSTED = "trusted"  # 50-74: Real trust established
    DEVOTED = "devoted"  # 75-100: Unbreakable bond
    # Negative stages (-1 to -100)
    WARY = "wary"  # -1 to -24: Suspicious
    HOSTILE = "hostile"  # -25 to -49: Actively unfriendly
    ENEMY = "enemy"  # -50 to -100: Refuses interaction


class InteractionType(Enum):
    """Types of player-NPC interactions that affect arc progression."""

    TALKED = "talked"  # +1-3 per conversation
    HELPED_QUEST = "helped_quest"  # +10-20 for completing their quest
    FAILED_QUEST = "failed_quest"  # -10-15 for failing their quest
    INTIMIDATED = "intimidated"  # -5-10 for intimidation
    BRIBED = "bribed"  # -2 to +5 depending on context
    DEFENDED = "defended"  # +15-25 for defending in combat
    ATTACKED = "attacked"  # -30-50 for attacking
    GIFTED = "gifted"  # +5-15 for giving gifts


@dataclass
class NPCInteraction:
    """A single recorded interaction between player and NPC."""

    interaction_type: InteractionType
    points_delta: int
    description: Optional[str] = None
    timestamp: int = 0  # Game hour when interaction occurred

    def to_dict(self) -> dict:
        return {
            "interaction_type": self.interaction_type.value,
            "points_delta": self.points_delta,
            "description": self.description,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCInteraction":
        return cls(
            interaction_type=InteractionType(data["interaction_type"]),
            points_delta=data["points_delta"],
            description=data.get("description"),
            timestamp=data.get("timestamp", 0),
        )


@dataclass
class NPCArc:
    """Tracks an NPC's relationship arc with the player."""

    arc_points: int = 0
    interactions: List[NPCInteraction] = field(default_factory=list)

    def get_stage(self) -> NPCArcStage:
        """Compute arc stage from current points."""
        if self.arc_points >= 75:
            return NPCArcStage.DEVOTED
        elif self.arc_points >= 50:
            return NPCArcStage.TRUSTED
        elif self.arc_points >= 25:
            return NPCArcStage.ACQUAINTANCE
        elif self.arc_points >= 0:
            return NPCArcStage.STRANGER
        elif self.arc_points >= -24:
            return NPCArcStage.WARY
        elif self.arc_points >= -49:
            return NPCArcStage.HOSTILE
        else:
            return NPCArcStage.ENEMY

    def record_interaction(
        self,
        interaction_type: InteractionType,
        points_delta: int,
        description: Optional[str] = None,
        timestamp: int = 0,
    ) -> Optional[str]:
        """Record an interaction and return message if stage changed."""
        old_stage = self.get_stage()

        self.arc_points = max(-100, min(100, self.arc_points + points_delta))

        self.interactions.append(
            NPCInteraction(
                interaction_type=interaction_type,
                points_delta=points_delta,
                description=description,
                timestamp=timestamp,
            )
        )
        # Cap interaction history at 20 entries
        while len(self.interactions) > 20:
            self.interactions.pop(0)

        new_stage = self.get_stage()
        if new_stage != old_stage:
            return f"Relationship changed: {old_stage.value} -> {new_stage.value}"
        return None

    def to_dict(self) -> dict:
        return {
            "arc_points": self.arc_points,
            "interactions": [i.to_dict() for i in self.interactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCArc":
        return cls(
            arc_points=data.get("arc_points", 0),
            interactions=[
                NPCInteraction.from_dict(i) for i in data.get("interactions", [])
            ],
        )
