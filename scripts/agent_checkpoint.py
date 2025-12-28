"""Agent checkpoint dataclass for persistence.

Defines the AgentCheckpoint dataclass that captures complete agent state
for save/restore capabilities during simulations.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentCheckpoint:
    """Complete agent state for persistence.

    Captures all necessary state to resume an agent session from a checkpoint,
    including exploration history, goals, and statistics.

    Attributes:
        current_goal: AgentGoal enum value as string
        visited_coordinates: List of (x, y) coordinate tuples visited
        current_coords: Current position as (x, y) tuple
        direction_history: Recent directions taken
        talked_this_location: NPCs talked to at current location
        sub_location_moves: Moves since entering sub-location
        stats: SessionStats as dictionary
        checkpoint_type: Type of checkpoint (auto, quest, boss, dungeon, branch)
        game_save_path: Path to linked game save file
        seed: RNG seed for reproducibility
        timestamp: ISO format timestamp
        command_index: Command count at checkpoint
    """

    current_goal: str
    visited_coordinates: list[tuple[int, int]]
    current_coords: tuple[int, int]
    direction_history: list[str]
    talked_this_location: list[str]
    sub_location_moves: int
    stats: dict[str, Any]
    checkpoint_type: str
    game_save_path: str
    seed: int
    timestamp: str
    command_index: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize checkpoint to dictionary.

        Returns:
            Dictionary representation of checkpoint state.
        """
        return {
            "current_goal": self.current_goal,
            "visited_coordinates": list(self.visited_coordinates),
            "current_coords": self.current_coords,
            "direction_history": list(self.direction_history),
            "talked_this_location": list(self.talked_this_location),
            "sub_location_moves": self.sub_location_moves,
            "stats": dict(self.stats),
            "checkpoint_type": self.checkpoint_type,
            "game_save_path": self.game_save_path,
            "seed": self.seed,
            "timestamp": self.timestamp,
            "command_index": self.command_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentCheckpoint":
        """Deserialize checkpoint from dictionary.

        Args:
            data: Dictionary representation of checkpoint state.

        Returns:
            AgentCheckpoint instance.
        """
        # Convert coordinate lists back to tuples
        visited = [tuple(coord) for coord in data.get("visited_coordinates", [])]
        current = tuple(data.get("current_coords", (0, 0)))

        return cls(
            current_goal=data.get("current_goal", "EXPLORE_OVERWORLD"),
            visited_coordinates=visited,
            current_coords=current,
            direction_history=list(data.get("direction_history", [])),
            talked_this_location=list(data.get("talked_this_location", [])),
            sub_location_moves=data.get("sub_location_moves", 0),
            stats=dict(data.get("stats", {})),
            checkpoint_type=data.get("checkpoint_type", "auto"),
            game_save_path=data.get("game_save_path", ""),
            seed=data.get("seed", 0),
            timestamp=data.get("timestamp", ""),
            command_index=data.get("command_index", 0),
        )
