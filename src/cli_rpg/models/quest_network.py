"""Quest Network Manager for managing interconnected quest storylines."""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from cli_rpg.models.quest import Quest


@dataclass
class QuestNetworkManager:
    """Manages interconnected quest networks.

    Provides functionality for:
    - Registering and looking up quests by name
    - Chain progression tracking
    - Dependency-based availability queries
    - Storyline path finding
    """

    _quests: Dict[str, Quest] = field(default_factory=dict)

    # Registration
    def add_quest(self, quest: Quest) -> None:
        """Register a quest by name (case-insensitive)."""
        self._quests[quest.name.lower()] = quest

    def get_quest(self, name: str) -> Optional[Quest]:
        """Look up a quest by name (case-insensitive)."""
        return self._quests.get(name.lower())

    def get_all_quests(self) -> List[Quest]:
        """Get all registered quests."""
        return list(self._quests.values())

    # Chain management
    def get_chain_quests(self, chain_id: str) -> List[Quest]:
        """Get all quests in a chain, sorted by chain_position."""
        quests = [q for q in self._quests.values() if q.chain_id == chain_id]
        return sorted(quests, key=lambda q: q.chain_position)

    def get_chain_progression(
        self, chain_id: str, completed_quests: List[str]
    ) -> Tuple[int, int]:
        """Get (completed_count, total_count) for a chain."""
        chain = self.get_chain_quests(chain_id)
        completed_lower = {q.lower() for q in completed_quests}
        completed = sum(1 for q in chain if q.name.lower() in completed_lower)
        return (completed, len(chain))

    def get_next_in_chain(
        self, chain_id: str, completed_quests: List[str]
    ) -> Optional[Quest]:
        """Get first incomplete quest in a chain."""
        chain = self.get_chain_quests(chain_id)
        completed_lower = {q.lower() for q in completed_quests}
        for quest in chain:
            if quest.name.lower() not in completed_lower:
                return quest
        return None

    # Dependency queries
    def get_available_quests(self, completed_quests: List[str]) -> List[Quest]:
        """Get quests with satisfied prerequisites (or no prerequisites)."""
        return [
            q for q in self._quests.values()
            if q.prerequisites_met(completed_quests)
        ]

    def get_unlocked_quests(self, completed_quest_name: str) -> List[Quest]:
        """Get quests unlocked by completing a quest."""
        completed = self.get_quest(completed_quest_name)
        if not completed:
            return []
        return [
            self.get_quest(name)
            for name in completed.unlocks_quests
            if self.get_quest(name) is not None
        ]

    # Storyline queries
    def get_prerequisites_of(self, quest_name: str) -> List[Quest]:
        """Get Quest objects for a quest's prerequisites."""
        quest = self.get_quest(quest_name)
        if not quest:
            return []
        return [
            self.get_quest(name)
            for name in quest.prerequisite_quests
            if self.get_quest(name) is not None
        ]

    def get_unlocks_of(self, quest_name: str) -> List[Quest]:
        """Get Quest objects for quests this quest unlocks."""
        quest = self.get_quest(quest_name)
        if not quest:
            return []
        return [
            self.get_quest(name)
            for name in quest.unlocks_quests
            if self.get_quest(name) is not None
        ]

    def find_path(
        self, start_quest: str, end_quest: str
    ) -> Optional[List[str]]:
        """Find shortest path between quests via unlocks_quests.

        Uses BFS to find the shortest chain from start to end.

        Returns:
            List of quest names forming the path (including start and end),
            or None if no path exists.
        """
        start = self.get_quest(start_quest)
        end = self.get_quest(end_quest)
        if not start or not end:
            return None
        if start_quest.lower() == end_quest.lower():
            return [start.name]

        visited = {start_quest.lower()}
        queue: deque[List[str]] = deque([[start.name]])

        while queue:
            path = queue.popleft()
            current_name = path[-1]
            current = self.get_quest(current_name)
            if not current:
                continue

            for unlock_name in current.unlocks_quests:
                if unlock_name.lower() == end_quest.lower():
                    return path + [end.name]
                if unlock_name.lower() not in visited:
                    visited.add(unlock_name.lower())
                    queue.append(path + [unlock_name])

        return None

    # Serialization
    def to_dict(self) -> dict:
        """Serialize the manager to a dictionary."""
        return {"quests": [q.to_dict() for q in self._quests.values()]}

    @classmethod
    def from_dict(cls, data: dict) -> "QuestNetworkManager":
        """Deserialize the manager from a dictionary."""
        manager = cls()
        for quest_data in data.get("quests", []):
            quest = Quest.from_dict(quest_data)
            manager.add_quest(quest)
        return manager
