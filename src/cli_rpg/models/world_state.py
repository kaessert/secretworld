"""World state tracking for persistent world changes.

This module provides the WorldStateManager and WorldStateChange classes
for tracking permanent changes to the game world from quest outcomes,
combat victories, and player actions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from cli_rpg.models.quest import WorldEffect


class WorldStateChangeType(Enum):
    """Types of world state changes that can be recorded."""

    LOCATION_DESTROYED = "location_destroyed"  # Location no longer exists
    LOCATION_TRANSFORMED = "location_transformed"  # Category/description changed
    NPC_KILLED = "npc_killed"  # NPC removed from world
    NPC_MOVED = "npc_moved"  # NPC relocated
    FACTION_ELIMINATED = "faction_eliminated"  # Faction no longer exists
    BOSS_DEFEATED = "boss_defeated"  # Boss permanently killed
    AREA_CLEARED = "area_cleared"  # All hostiles removed from location
    QUEST_WORLD_EFFECT = "quest_world_effect"  # Custom quest-triggered effect


@dataclass
class WorldStateChange:
    """A record of a permanent change to the game world.

    Attributes:
        change_type: The type of world change
        target: The location/NPC/faction name affected
        description: Human-readable summary of what happened
        timestamp: Game hour when the change occurred
        caused_by: Quest name or action that caused the change (optional)
        metadata: Type-specific additional data
    """

    change_type: WorldStateChangeType
    target: str
    description: str
    timestamp: int
    caused_by: Optional[str]
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate the change data."""
        if not self.target or not self.target.strip():
            raise ValueError("target cannot be empty")

    def to_dict(self) -> dict:
        """Serialize to dictionary for save/load."""
        return {
            "change_type": self.change_type.value,
            "target": self.target,
            "description": self.description,
            "timestamp": self.timestamp,
            "caused_by": self.caused_by,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldStateChange":
        """Deserialize from dictionary."""
        return cls(
            change_type=WorldStateChangeType(data["change_type"]),
            target=data["target"],
            description=data["description"],
            timestamp=data["timestamp"],
            caused_by=data.get("caused_by"),
            metadata=data.get("metadata", {}),
        )


class WorldStateManager:
    """Manages persistent world state changes.

    Tracks all permanent changes to the game world and provides methods
    for recording new changes and querying existing ones.
    """

    def __init__(self):
        """Initialize an empty world state manager."""
        self._changes: list[WorldStateChange] = []

    def record_change(self, change: WorldStateChange) -> Optional[str]:
        """Record a world state change.

        Args:
            change: The WorldStateChange to record

        Returns:
            Optional message describing the change
        """
        self._changes.append(change)
        return change.description

    def record_location_transformed(
        self,
        name: str,
        new_category: str,
        desc: str,
        caused_by: str,
        timestamp: int = 0,
    ) -> Optional[str]:
        """Record a location transformation.

        Args:
            name: Name of the location
            new_category: The new category of the location
            desc: Description of the transformation
            caused_by: What caused this transformation
            timestamp: Game hour when this occurred

        Returns:
            Optional message describing the change
        """
        change = WorldStateChange(
            change_type=WorldStateChangeType.LOCATION_TRANSFORMED,
            target=name,
            description=desc,
            timestamp=timestamp,
            caused_by=caused_by,
            metadata={"new_category": new_category},
        )
        return self.record_change(change)

    def record_npc_killed(
        self,
        npc_name: str,
        location: str,
        caused_by: Optional[str],
        timestamp: int = 0,
    ) -> Optional[str]:
        """Record an NPC being killed.

        Args:
            npc_name: Name of the NPC
            location: Where the NPC was killed
            caused_by: What caused the death
            timestamp: Game hour when this occurred

        Returns:
            Optional message describing the change
        """
        change = WorldStateChange(
            change_type=WorldStateChangeType.NPC_KILLED,
            target=npc_name,
            description=f"{npc_name} was killed",
            timestamp=timestamp,
            caused_by=caused_by,
            metadata={"location": location},
        )
        return self.record_change(change)

    def record_boss_defeated(
        self,
        boss_name: str,
        location: str,
        timestamp: int = 0,
    ) -> Optional[str]:
        """Record a boss being defeated.

        Args:
            boss_name: Name of the boss
            location: Where the boss was defeated
            timestamp: Game hour when this occurred

        Returns:
            Optional message describing the change
        """
        change = WorldStateChange(
            change_type=WorldStateChangeType.BOSS_DEFEATED,
            target=boss_name,
            description=f"{boss_name} was defeated at {location}",
            timestamp=timestamp,
            caused_by=None,
            metadata={"location": location},
        )
        return self.record_change(change)

    def record_area_cleared(
        self,
        location: str,
        caused_by: Optional[str],
        timestamp: int = 0,
    ) -> Optional[str]:
        """Record an area being cleared of hostiles.

        Args:
            location: Name of the location
            caused_by: What caused the clearing
            timestamp: Game hour when this occurred

        Returns:
            Optional message describing the change
        """
        change = WorldStateChange(
            change_type=WorldStateChangeType.AREA_CLEARED,
            target=location,
            description=f"{location} has been cleared",
            timestamp=timestamp,
            caused_by=caused_by,
            metadata={},
        )
        return self.record_change(change)

    def record_quest_world_effect(
        self,
        effect: "WorldEffect",
        quest_name: str,
        timestamp: int,
    ) -> Optional[str]:
        """Record a world effect from quest completion.

        This method bridges quest WorldEffect objects to WorldStateChange records.
        For area_cleared effects, it also records an AREA_CLEARED change for
        backwards compatibility with is_area_cleared() queries.

        Args:
            effect: The WorldEffect from the completed quest
            quest_name: Name of the quest that caused this effect
            timestamp: Game hour when the quest was completed

        Returns:
            Optional message describing the change
        """
        # Build metadata that includes the original effect type and any effect metadata
        metadata = {"effect_type": effect.effect_type}
        metadata.update(effect.metadata)

        # Record the main quest world effect
        change = WorldStateChange(
            change_type=WorldStateChangeType.QUEST_WORLD_EFFECT,
            target=effect.target,
            description=effect.description,
            timestamp=timestamp,
            caused_by=quest_name,
            metadata=metadata,
        )
        result = self.record_change(change)

        # For area_cleared effects, also record an AREA_CLEARED change
        # so is_area_cleared() works correctly
        if effect.effect_type == "area_cleared":
            self.record_area_cleared(
                location=effect.target,
                caused_by=quest_name,
                timestamp=timestamp,
            )

        return result

    def get_changes_for_location(self, location: str) -> list[WorldStateChange]:
        """Get all changes that affect a specific location.

        Args:
            location: The location name to query

        Returns:
            List of changes affecting that location
        """
        result = []
        for change in self._changes:
            # Check if the target is the location or if location is in metadata
            if change.target == location:
                result.append(change)
            elif change.metadata.get("location") == location:
                result.append(change)
        return result

    def get_changes_by_type(
        self, change_type: WorldStateChangeType
    ) -> list[WorldStateChange]:
        """Get all changes of a specific type.

        Args:
            change_type: The type to filter by

        Returns:
            List of changes of that type
        """
        return [c for c in self._changes if c.change_type == change_type]

    def is_location_destroyed(self, location: str) -> bool:
        """Check if a location has been destroyed.

        Args:
            location: The location name to check

        Returns:
            True if the location was destroyed
        """
        for change in self._changes:
            if (
                change.change_type == WorldStateChangeType.LOCATION_DESTROYED
                and change.target == location
            ):
                return True
        return False

    def is_npc_killed(self, npc_name: str) -> bool:
        """Check if an NPC has been killed.

        Args:
            npc_name: The NPC name to check

        Returns:
            True if the NPC was killed
        """
        for change in self._changes:
            if (
                change.change_type == WorldStateChangeType.NPC_KILLED
                and change.target == npc_name
            ):
                return True
        return False

    def is_boss_defeated(self, location: str) -> bool:
        """Check if a boss at a location has been defeated.

        Args:
            location: The location to check

        Returns:
            True if a boss was defeated at that location
        """
        for change in self._changes:
            if (
                change.change_type == WorldStateChangeType.BOSS_DEFEATED
                and change.metadata.get("location") == location
            ):
                return True
        return False

    def is_area_cleared(self, location: str) -> bool:
        """Check if an area has been cleared.

        Args:
            location: The location to check

        Returns:
            True if the area was cleared
        """
        for change in self._changes:
            if (
                change.change_type == WorldStateChangeType.AREA_CLEARED
                and change.target == location
            ):
                return True
        return False

    def to_dict(self) -> dict:
        """Serialize the manager to a dictionary.

        Returns:
            Dictionary containing all changes
        """
        return {"changes": [c.to_dict() for c in self._changes]}

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "WorldStateManager":
        """Deserialize from a dictionary.

        Args:
            data: Dictionary containing changes, or None/empty for new manager

        Returns:
            Restored WorldStateManager instance
        """
        manager = cls()
        if data and "changes" in data:
            for change_data in data["changes"]:
                manager._changes.append(WorldStateChange.from_dict(change_data))
        return manager
