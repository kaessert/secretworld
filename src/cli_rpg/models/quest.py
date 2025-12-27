"""Quest model for tracking player objectives."""

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Dict, List, Optional


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


class QuestDifficulty(Enum):
    """Difficulty rating for quests."""

    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    DEADLY = "deadly"


@dataclass
class QuestBranch:
    """Alternative completion path for a quest.

    Attributes:
        id: Unique identifier (e.g., "kill", "persuade", "help")
        name: Display name (e.g., "Eliminate the Threat")
        objective_type: Type of objective to complete
        target: The target name (enemy, NPC, item, location)
        target_count: How many to complete (default 1)
        current_count: Current progress (default 0)
        description: Optional flavor text
        faction_effects: Dict of faction name to reputation change
        gold_modifier: Multiplier on base gold reward
        xp_modifier: Multiplier on base XP reward
    """

    id: str
    name: str
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0
    description: str = ""
    faction_effects: Dict[str, int] = field(default_factory=dict)
    gold_modifier: float = 1.0
    xp_modifier: float = 1.0

    def __post_init__(self) -> None:
        """Validate branch attributes after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Branch id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Branch name cannot be empty")
        if not self.target or not self.target.strip():
            raise ValueError("Branch target cannot be empty")
        if self.target_count < 1:
            raise ValueError("Branch target_count must be at least 1")
        if self.current_count < 0:
            raise ValueError("Branch current_count must be non-negative")

        self.id = self.id.strip()
        self.name = self.name.strip()
        self.target = self.target.strip()

    @property
    def is_complete(self) -> bool:
        """Check if this branch's objective has been met."""
        return self.current_count >= self.target_count

    def progress(self) -> bool:
        """Increment current_count and check if branch is complete.

        Returns:
            True if branch is now complete, False otherwise
        """
        self.current_count += 1
        return self.is_complete

    def to_dict(self) -> dict:
        """Serialize the branch to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "objective_type": self.objective_type.value,
            "target": self.target,
            "target_count": self.target_count,
            "current_count": self.current_count,
            "description": self.description,
            "faction_effects": self.faction_effects,
            "gold_modifier": self.gold_modifier,
            "xp_modifier": self.xp_modifier,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestBranch":
        """Create a branch from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            objective_type=ObjectiveType(data["objective_type"]),
            target=data["target"],
            target_count=data.get("target_count", 1),
            current_count=data.get("current_count", 0),
            description=data.get("description", ""),
            faction_effects=data.get("faction_effects", {}),
            gold_modifier=data.get("gold_modifier", 1.0),
            xp_modifier=data.get("xp_modifier", 1.0),
        )


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
    faction_affiliation: Optional[str] = field(default=None)
    faction_reward: int = field(default=0)
    faction_penalty: int = field(default=0)
    required_reputation: Optional[int] = field(default=None)
    # Quest chain fields for narrative arcs
    chain_id: Optional[str] = field(default=None)  # Groups related quests (e.g., "goblin_war")
    chain_position: int = field(default=0)  # Order in chain (0 = standalone, 1 = first, etc.)
    prerequisite_quests: List[str] = field(default_factory=list)  # Quest names that must be COMPLETED
    unlocks_quests: List[str] = field(default_factory=list)  # Quest names unlocked on completion
    # Branching quest support
    alternative_branches: List["QuestBranch"] = field(default_factory=list)  # Alternative completion paths
    completed_branch_id: Optional[str] = field(default=None)  # Which branch was completed
    # Difficulty indicators
    difficulty: QuestDifficulty = field(default=QuestDifficulty.NORMAL)
    recommended_level: int = field(default=1)

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
        if self.faction_reward < 0:
            raise ValueError("faction_reward cannot be negative")
        if self.faction_penalty < 0:
            raise ValueError("faction_penalty cannot be negative")

        # Validate difficulty fields
        if self.recommended_level < 1:
            raise ValueError("recommended_level must be at least 1")

    @property
    def is_complete(self) -> bool:
        """Check if the quest objective has been met.

        Returns:
            True if current_count >= target_count, False otherwise
        """
        return self.current_count >= self.target_count

    def prerequisites_met(self, completed_quests: List[str]) -> bool:
        """Check if all prerequisite quests have been completed.

        Args:
            completed_quests: List of completed quest names (case-insensitive)

        Returns:
            True if no prerequisites or all are in completed list
        """
        if not self.prerequisite_quests:
            return True
        completed_lower = {q.lower() for q in completed_quests}
        return all(prereq.lower() in completed_lower for prereq in self.prerequisite_quests)

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
            "faction_affiliation": self.faction_affiliation,
            "faction_reward": self.faction_reward,
            "faction_penalty": self.faction_penalty,
            "required_reputation": self.required_reputation,
            "chain_id": self.chain_id,
            "chain_position": self.chain_position,
            "prerequisite_quests": self.prerequisite_quests,
            "unlocks_quests": self.unlocks_quests,
            "alternative_branches": [b.to_dict() for b in self.alternative_branches],
            "completed_branch_id": self.completed_branch_id,
            "difficulty": self.difficulty.value,
            "recommended_level": self.recommended_level,
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
        # Deserialize branches
        branches_data = data.get("alternative_branches", [])
        branches = [QuestBranch.from_dict(b) for b in branches_data]

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
            faction_affiliation=data.get("faction_affiliation"),
            faction_reward=data.get("faction_reward", 0),
            faction_penalty=data.get("faction_penalty", 0),
            required_reputation=data.get("required_reputation"),
            chain_id=data.get("chain_id"),
            chain_position=data.get("chain_position", 0),
            prerequisite_quests=data.get("prerequisite_quests", []),
            unlocks_quests=data.get("unlocks_quests", []),
            alternative_branches=branches,
            completed_branch_id=data.get("completed_branch_id"),
            difficulty=QuestDifficulty(data.get("difficulty", "normal")),
            recommended_level=data.get("recommended_level", 1),
        )

    def get_branches_display(self) -> List[dict]:
        """Get display information for all alternative branches.

        Returns:
            List of dicts with name, objective, and progress for each branch
        """
        result = []
        for branch in self.alternative_branches:
            # Build objective string based on type
            obj_type = branch.objective_type.value.capitalize()
            if branch.objective_type == ObjectiveType.TALK:
                objective = f"Talk to {branch.target}"
            elif branch.objective_type == ObjectiveType.KILL:
                objective = f"Kill {branch.target}"
            elif branch.objective_type == ObjectiveType.COLLECT:
                objective = f"Collect {branch.target}"
            elif branch.objective_type == ObjectiveType.EXPLORE:
                objective = f"Explore {branch.target}"
            elif branch.objective_type == ObjectiveType.DROP:
                objective = f"Obtain {branch.target} drop"
            elif branch.objective_type == ObjectiveType.USE:
                objective = f"Use {branch.target}"
            else:
                objective = f"{obj_type} {branch.target}"

            result.append({
                "name": branch.name,
                "objective": objective,
                "progress": f"[{branch.current_count}/{branch.target_count}]",
                "is_complete": branch.is_complete,
            })
        return result
