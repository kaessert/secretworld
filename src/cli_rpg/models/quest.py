"""Quest model for tracking player objectives."""

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Dict, List, Optional, Tuple


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
class WorldEffect:
    """Effect on world state when quest completes.

    Attributes:
        effect_type: Type of effect (area_cleared, location_transformed, npc_moved, etc.)
        target: Location/NPC name affected
        description: Human-readable description of the effect
        metadata: Extra data (new_category, etc.)
    """

    effect_type: str
    target: str
    description: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate effect attributes."""
        if not self.target or not self.target.strip():
            raise ValueError("target cannot be empty")
        self.target = self.target.strip()

    def to_dict(self) -> dict:
        """Serialize the effect to a dictionary."""
        return {
            "effect_type": self.effect_type,
            "target": self.target,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldEffect":
        """Create an effect from a dictionary."""
        return cls(
            effect_type=data["effect_type"],
            target=data["target"],
            description=data["description"],
            metadata=data.get("metadata", {}),
        )


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
class QuestStage:
    """A single stage within a multi-stage quest.

    Attributes:
        name: Stage title (cannot be empty)
        description: Stage-specific flavor text
        objective_type: Type of objective (KILL, TALK, EXPLORE, etc.)
        target: The target name (cannot be empty)
        target_count: How many to complete (default 1, must be >= 1)
        current_count: Current progress (default 0, must be >= 0)
    """

    name: str
    description: str
    objective_type: ObjectiveType
    target: str
    target_count: int = 1
    current_count: int = 0

    def __post_init__(self) -> None:
        """Validate stage attributes."""
        if not self.name or not self.name.strip():
            raise ValueError("Stage name cannot be empty")
        if not self.target or not self.target.strip():
            raise ValueError("Stage target cannot be empty")
        if self.target_count < 1:
            raise ValueError("Stage target_count must be at least 1")
        if self.current_count < 0:
            raise ValueError("Stage current_count must be non-negative")
        self.name = self.name.strip()
        self.target = self.target.strip()

    @property
    def is_complete(self) -> bool:
        """Check if this stage's objective has been met."""
        return self.current_count >= self.target_count

    def progress(self) -> bool:
        """Increment current_count and check if stage is complete.

        Returns:
            True if stage is now complete, False otherwise.
        """
        self.current_count += 1
        return self.is_complete

    def to_dict(self) -> dict:
        """Serialize the stage to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "objective_type": self.objective_type.value,
            "target": self.target,
            "target_count": self.target_count,
            "current_count": self.current_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestStage":
        """Create a stage from a dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            objective_type=ObjectiveType(data["objective_type"]),
            target=data["target"],
            target_count=data.get("target_count", 1),
            current_count=data.get("current_count", 0),
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
    required_arc_stage: Optional[str] = field(default=None)  # NPC arc stage required to accept
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
    # Time limit fields for urgent quests
    time_limit_hours: Optional[int] = field(default=None)
    accepted_at: Optional[int] = field(default=None)
    # Multi-stage quest fields
    stages: List["QuestStage"] = field(default_factory=list)
    current_stage: int = field(default=0)
    # World effects applied when quest completes
    world_effects: List["WorldEffect"] = field(default_factory=list)

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

        # Validate time limit fields
        if self.time_limit_hours is not None and self.time_limit_hours < 1:
            raise ValueError("time_limit_hours must be at least 1")

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

    def is_expired(self, current_game_hour: int) -> bool:
        """Check if quest has expired based on time limit.

        Args:
            current_game_hour: The current game hour (total hours elapsed)

        Returns:
            True if quest has exceeded its time limit, False otherwise
        """
        if self.time_limit_hours is None or self.accepted_at is None:
            return False
        return (current_game_hour - self.accepted_at) >= self.time_limit_hours

    def get_time_remaining(self, current_game_hour: int) -> Optional[int]:
        """Return hours remaining until quest expires, or None if no time limit.

        Args:
            current_game_hour: The current game hour (total hours elapsed)

        Returns:
            Hours remaining (floored at 0), or None if quest has no time limit
        """
        if self.time_limit_hours is None or self.accepted_at is None:
            return None
        remaining = self.time_limit_hours - (current_game_hour - self.accepted_at)
        return max(0, remaining)

    def get_active_stage(self) -> Optional["QuestStage"]:
        """Return the currently active stage, or None if no stages.

        Returns:
            The current QuestStage or None if quest has no stages or is past all stages.
        """
        if not self.stages or self.current_stage >= len(self.stages):
            return None
        return self.stages[self.current_stage]

    def advance_stage(self) -> bool:
        """Advance to next stage.

        Returns:
            True if quest is now complete (past all stages), False otherwise.
        """
        if not self.stages:
            return False
        self.current_stage += 1
        return self.current_stage >= len(self.stages)

    def get_active_objective(self) -> Tuple[ObjectiveType, str, int, int]:
        """Return (objective_type, target, target_count, current_count) for active objective.

        Uses current stage if stages exist, otherwise uses root quest fields.

        Returns:
            Tuple of (objective_type, target, target_count, current_count)
        """
        stage = self.get_active_stage()
        if stage:
            return (stage.objective_type, stage.target, stage.target_count, stage.current_count)
        return (self.objective_type, self.target, self.target_count, self.current_count)

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
            "required_arc_stage": self.required_arc_stage,
            "chain_id": self.chain_id,
            "chain_position": self.chain_position,
            "prerequisite_quests": self.prerequisite_quests,
            "unlocks_quests": self.unlocks_quests,
            "alternative_branches": [b.to_dict() for b in self.alternative_branches],
            "completed_branch_id": self.completed_branch_id,
            "difficulty": self.difficulty.value,
            "recommended_level": self.recommended_level,
            "time_limit_hours": self.time_limit_hours,
            "accepted_at": self.accepted_at,
            "stages": [s.to_dict() for s in self.stages],
            "current_stage": self.current_stage,
            "world_effects": [e.to_dict() for e in self.world_effects],
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

        # Deserialize stages
        stages_data = data.get("stages", [])
        stages = [QuestStage.from_dict(s) for s in stages_data]

        # Deserialize world effects
        effects_data = data.get("world_effects", [])
        world_effects = [WorldEffect.from_dict(e) for e in effects_data]

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
            required_arc_stage=data.get("required_arc_stage"),
            chain_id=data.get("chain_id"),
            chain_position=data.get("chain_position", 0),
            prerequisite_quests=data.get("prerequisite_quests", []),
            unlocks_quests=data.get("unlocks_quests", []),
            alternative_branches=branches,
            completed_branch_id=data.get("completed_branch_id"),
            difficulty=QuestDifficulty(data.get("difficulty", "normal")),
            recommended_level=data.get("recommended_level", 1),
            time_limit_hours=data.get("time_limit_hours"),
            accepted_at=data.get("accepted_at"),
            stages=stages,
            current_stage=data.get("current_stage", 0),
            world_effects=world_effects,
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
