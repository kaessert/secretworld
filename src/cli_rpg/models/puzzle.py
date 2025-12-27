"""Puzzle model for dungeon puzzle mechanics (Issue #23).

Provides puzzle types and the Puzzle dataclass for interactive puzzle elements
in dungeons, caves, and other locations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PuzzleType(Enum):
    """Types of puzzles that can appear in dungeons.

    - LOCKED_DOOR: Requires specific key item to unlock
    - LEVER: Toggle to open a passage
    - PRESSURE_PLATE: Step on to trigger mechanism
    - RIDDLE: Answer correctly to pass
    - SEQUENCE: Activate objects in correct order
    """

    LOCKED_DOOR = "locked_door"
    LEVER = "lever"
    PRESSURE_PLATE = "pressure_plate"
    RIDDLE = "riddle"
    SEQUENCE = "sequence"


@dataclass
class Puzzle:
    """Represents a puzzle in a dungeon location.

    Puzzles block passage in a target_direction until solved.
    Each puzzle type has specific requirements for solving.

    Attributes:
        puzzle_type: The type of puzzle (locked door, lever, etc.)
        name: Display name of the puzzle (e.g., "Rusted Iron Door")
        description: What the player sees when examining
        solved: Whether the puzzle has been solved
        required_key: For LOCKED_DOOR - name of key item needed
        target_direction: Direction that is blocked/revealed by this puzzle
        riddle_text: For RIDDLE - the riddle question
        riddle_answer: For RIDDLE - the correct answer (case-insensitive)
        sequence_ids: For SEQUENCE - correct order of object IDs
        sequence_progress: For SEQUENCE - current player progress
        hint_threshold: INT score needed to see hint
        hint_text: Hint shown if INT >= threshold
    """

    puzzle_type: PuzzleType
    name: str
    description: str
    solved: bool = False
    # Type-specific fields
    required_key: Optional[str] = None
    target_direction: Optional[str] = None
    riddle_text: Optional[str] = None
    riddle_answer: Optional[str] = None
    sequence_ids: List[str] = field(default_factory=list)
    sequence_progress: List[str] = field(default_factory=list)
    hint_threshold: int = 14
    hint_text: Optional[str] = None

    def check_riddle_answer(self, answer: str) -> bool:
        """Check if the given answer matches the riddle answer.

        Args:
            answer: The player's answer attempt

        Returns:
            True if answer matches (case-insensitive), False otherwise
        """
        if self.riddle_answer is None:
            return False
        return answer.strip().lower() == self.riddle_answer.strip().lower()

    def check_sequence_step(self, object_id: str) -> bool:
        """Check if the given object is the next correct step in the sequence.

        Args:
            object_id: ID of the object being activated

        Returns:
            True if this is the correct next step, False otherwise
        """
        if not self.sequence_ids:
            return False
        next_index = len(self.sequence_progress)
        if next_index >= len(self.sequence_ids):
            return False
        return self.sequence_ids[next_index] == object_id

    def add_sequence_step(self, object_id: str) -> bool:
        """Add an object to the sequence progress.

        If the object is correct, adds it. If wrong, resets progress.

        Args:
            object_id: ID of the object being activated

        Returns:
            True if step was correct, False if wrong (and progress was reset)
        """
        if self.check_sequence_step(object_id):
            self.sequence_progress.append(object_id)
            return True
        else:
            self.sequence_progress = []  # Reset on wrong step
            return False

    def is_sequence_complete(self) -> bool:
        """Check if the sequence puzzle is complete.

        Returns:
            True if all sequence steps have been completed
        """
        return (
            len(self.sequence_ids) > 0
            and self.sequence_progress == self.sequence_ids
        )

    def get_hint(self, intelligence: int) -> Optional[str]:
        """Get hint if player's INT meets threshold.

        Args:
            intelligence: Player's intelligence stat

        Returns:
            Hint text if INT >= threshold, None otherwise
        """
        if intelligence >= self.hint_threshold and self.hint_text:
            return self.hint_text
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the puzzle to a dictionary.

        Returns:
            Dictionary representation of the puzzle
        """
        data: Dict[str, Any] = {
            "puzzle_type": self.puzzle_type.value,
            "name": self.name,
            "description": self.description,
            "solved": self.solved,
            "hint_threshold": self.hint_threshold,
        }
        # Only include optional fields if set
        if self.required_key is not None:
            data["required_key"] = self.required_key
        if self.target_direction is not None:
            data["target_direction"] = self.target_direction
        if self.riddle_text is not None:
            data["riddle_text"] = self.riddle_text
        if self.riddle_answer is not None:
            data["riddle_answer"] = self.riddle_answer
        if self.sequence_ids:
            data["sequence_ids"] = self.sequence_ids.copy()
        if self.sequence_progress:
            data["sequence_progress"] = self.sequence_progress.copy()
        if self.hint_text is not None:
            data["hint_text"] = self.hint_text
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Puzzle":
        """Create a puzzle from a dictionary.

        Args:
            data: Dictionary containing puzzle data

        Returns:
            A new Puzzle instance
        """
        return cls(
            puzzle_type=PuzzleType(data["puzzle_type"]),
            name=data["name"],
            description=data["description"],
            solved=data.get("solved", False),
            required_key=data.get("required_key"),
            target_direction=data.get("target_direction"),
            riddle_text=data.get("riddle_text"),
            riddle_answer=data.get("riddle_answer"),
            sequence_ids=data.get("sequence_ids", []),
            sequence_progress=data.get("sequence_progress", []),
            hint_threshold=data.get("hint_threshold", 14),
            hint_text=data.get("hint_text"),
        )
