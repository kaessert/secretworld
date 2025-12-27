"""QuestOutcome model for tracking quest completion history."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class QuestOutcome:
    """Records the outcome of a completed quest.

    Tracks how a quest was completed, who was involved, and what consequences
    resulted. NPCs can reference these outcomes to react appropriately to
    past player actions.

    Attributes:
        quest_name: Name of the completed quest
        quest_giver: NPC who gave the quest
        completion_method: How the quest was completed:
            - "main": Standard objective completion
            - "branch_<id>": Completed via alternative branch
            - "expired": Quest failed due to time limit
            - "abandoned": Quest was abandoned by player
        completed_branch_name: Name of branch if completed via branch, else None
        timestamp: Game hour when quest was completed
        affected_npcs: NPCs involved in or affected by the quest outcome
        faction_changes: Dict mapping faction name to reputation change
    """

    quest_name: str
    quest_giver: str
    completion_method: str
    completed_branch_name: Optional[str] = None
    timestamp: int = 0
    affected_npcs: List[str] = field(default_factory=list)
    faction_changes: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate quest outcome attributes."""
        if not self.quest_name or not self.quest_name.strip():
            raise ValueError("Quest name cannot be empty")
        if not self.quest_giver or not self.quest_giver.strip():
            raise ValueError("Quest giver cannot be empty")
        if not self.completion_method or not self.completion_method.strip():
            raise ValueError("Completion method cannot be empty")

        valid_methods = {"main", "expired", "abandoned"}
        if (
            self.completion_method not in valid_methods
            and not self.completion_method.startswith("branch_")
        ):
            raise ValueError(
                f"Invalid completion method: {self.completion_method}. "
                f"Must be 'main', 'expired', 'abandoned', or 'branch_<id>'"
            )

        self.quest_name = self.quest_name.strip()
        self.quest_giver = self.quest_giver.strip()
        self.completion_method = self.completion_method.strip()

    @property
    def is_success(self) -> bool:
        """Check if the quest was completed successfully.

        Returns:
            True if quest was completed via main or branch, False if expired/abandoned.
        """
        return self.completion_method in ("main",) or self.completion_method.startswith(
            "branch_"
        )

    @property
    def is_branch_completion(self) -> bool:
        """Check if quest was completed via an alternative branch.

        Returns:
            True if completed via a branch path.
        """
        return self.completion_method.startswith("branch_")

    def to_dict(self) -> dict:
        """Serialize the quest outcome to a dictionary.

        Returns:
            Dictionary representation of the quest outcome.
        """
        return {
            "quest_name": self.quest_name,
            "quest_giver": self.quest_giver,
            "completion_method": self.completion_method,
            "completed_branch_name": self.completed_branch_name,
            "timestamp": self.timestamp,
            "affected_npcs": self.affected_npcs,
            "faction_changes": self.faction_changes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestOutcome":
        """Create a quest outcome from a dictionary.

        Args:
            data: Dictionary containing quest outcome data.

        Returns:
            QuestOutcome instance.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If validation fails.
        """
        return cls(
            quest_name=data["quest_name"],
            quest_giver=data["quest_giver"],
            completion_method=data["completion_method"],
            completed_branch_name=data.get("completed_branch_name"),
            timestamp=data.get("timestamp", 0),
            affected_npcs=data.get("affected_npcs", []),
            faction_changes=data.get("faction_changes", {}),
        )
