"""Quest model for tracking player objectives."""

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, List, Optional


class QuestStatus(Enum):
    """Status of a quest."""

    AVAILABLE = "available"
    ACTIVE = "active"
    READY_TO_TURN_IN = "ready_to_turn_in"
    COMPLETED = "completed"
    FAILED = "failed"


class ObjectiveType(Enum):
    """Type of quest objective."""

    KILL = "kill"
    COLLECT = "collect"
    EXPLORE = "explore"
    TALK = "talk"
    DROP = "drop"
    USE = "use"


@dataclass
class Quest:
    """Represents a quest in the game.

    A quest has a name, description, status, objective type, and tracks progress
    toward a target count.

    Attributes:
        name: The quest's name (2-30 characters)
        description: The quest's description (1-200 characters)
        status: Current status of the quest
        objective_type: Type of objective to complete
        target: The target name (enemy type, item name, location, or NPC)
        target_count: How many to complete (default 1)
        current_count: Current progress (default 0)
    """

    # Class constants
    MIN_NAME_LENGTH: ClassVar[int] = 2
    MAX_NAME_LENGTH: ClassVar[int] = 30
    MIN_DESCRIPTION_LENGTH: ClassVar[int] = 1
    MAX_DESCRIPTION_LENGTH: ClassVar[int] = 200

    name: str
    description: str
    objective_type: ObjectiveType
    target: str
    status: QuestStatus = field(default=QuestStatus.AVAILABLE)
    target_count: int = field(default=1)
    current_count: int = field(default=0)
    gold_reward: int = field(default=0)
    xp_reward: int = field(default=0)
    item_rewards: List[str] = field(default_factory=list)
    quest_giver: Optional[str] = field(default=None)
    drop_item: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """Validate quest attributes after initialization."""
        # Validate and normalize name
        if not self.name or not self.name.strip():
            raise ValueError("Quest name cannot be empty")

        self.name = self.name.strip()

        if len(self.name) < self.MIN_NAME_LENGTH:
            raise ValueError(
                f"Quest name must be at least {self.MIN_NAME_LENGTH} characters long"
            )

        if len(self.name) > self.MAX_NAME_LENGTH:
            raise ValueError(
                f"Quest name must be at most {self.MAX_NAME_LENGTH} characters long"
            )

        # Validate and normalize description
        if not self.description or not self.description.strip():
            raise ValueError("Quest description cannot be empty")

        self.description = self.description.strip()

        if len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Quest description must be at most {self.MAX_DESCRIPTION_LENGTH} characters long"
            )

        # Validate target_count
        if self.target_count < 1:
            raise ValueError("target_count must be at least 1")

        # Validate current_count
        if self.current_count < 0:
            raise ValueError("current_count must be at least 0")

        # Validate reward fields
        if self.gold_reward < 0:
            raise ValueError("gold_reward cannot be negative")
        if self.xp_reward < 0:
            raise ValueError("xp_reward cannot be negative")

    @property
    def is_complete(self) -> bool:
        """Check if the quest objective has been met.

        Returns:
            True if current_count >= target_count, False otherwise
        """
        return self.current_count >= self.target_count

    def progress(self) -> bool:
        """Increment current_count and check if quest is complete.

        Returns:
            True if quest is now complete, False otherwise
        """
        self.current_count += 1
        return self.is_complete

    def to_dict(self) -> dict:
        """Serialize the quest to a dictionary.

        Returns:
            A dictionary representation of the quest
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "objective_type": self.objective_type.value,
            "target": self.target,
            "target_count": self.target_count,
            "current_count": self.current_count,
            "gold_reward": self.gold_reward,
            "xp_reward": self.xp_reward,
            "item_rewards": self.item_rewards,
            "quest_giver": self.quest_giver,
            "drop_item": self.drop_item,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        """Create a quest from a dictionary.

        Args:
            data: Dictionary containing quest data

        Returns:
            A new Quest instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If validation fails
        """
        return cls(
            name=data["name"],
            description=data["description"],
            status=QuestStatus(data["status"]),
            objective_type=ObjectiveType(data["objective_type"]),
            target=data["target"],
            target_count=data.get("target_count", 1),
            current_count=data.get("current_count", 0),
            gold_reward=data.get("gold_reward", 0),
            xp_reward=data.get("xp_reward", 0),
            item_rewards=data.get("item_rewards", []),
            quest_giver=data.get("quest_giver"),
            drop_item=data.get("drop_item"),
        )
