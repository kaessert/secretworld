"""WorldEvent model for living world events system.

WorldEvents are timed events (plagues, caravans, invasions) that progress
with in-game time, giving players urgency and making the world feel alive.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorldEvent:
    """Tracks a world event with timed duration and consequences.

    Attributes:
        event_id: Unique identifier (e.g., "plague_millbrook_001")
        name: Display name (e.g., "The Crimson Plague")
        description: What's happening (e.g., "A deadly plague spreads through Millbrook")
        event_type: Category ("plague", "caravan", "invasion", "festival")
        affected_locations: List of location names affected by this event
        start_hour: Game hour when event started (0-23)
        duration_hours: How long event lasts before consequence
        is_active: Whether event is still ongoing
        is_resolved: Whether player addressed it
        consequence_applied: Whether negative outcome happened
    """

    event_id: str
    name: str
    description: str
    event_type: str
    affected_locations: list[str]
    start_hour: int
    duration_hours: int
    is_active: bool = True
    is_resolved: bool = False
    consequence_applied: bool = False

    def get_time_remaining(self, current_hour: int) -> int:
        """Calculate hours remaining until event expires.

        Handles midnight wrap-around for events that span across days.

        Args:
            current_hour: Current game hour (0-23)

        Returns:
            Hours remaining until event expires, minimum 0
        """
        # Calculate end hour (may wrap past midnight)
        end_hour = (self.start_hour + self.duration_hours) % 24

        # Calculate elapsed hours accounting for day wrap
        if current_hour >= self.start_hour:
            # Same day or wrapped past midnight
            elapsed = current_hour - self.start_hour
        else:
            # current_hour is after midnight, start_hour was before
            # Check if event spans midnight
            if self.start_hour + self.duration_hours > 24:
                # Event spans midnight - current_hour is still within event
                elapsed = (24 - self.start_hour) + current_hour
            else:
                # Event doesn't span midnight but we're on next day
                # Event has expired
                return 0

        remaining = self.duration_hours - elapsed
        return max(0, remaining)

    def is_expired(self, current_hour: int) -> bool:
        """Check if event has expired.

        Args:
            current_hour: Current game hour (0-23)

        Returns:
            True if time remaining is 0, False otherwise
        """
        return self.get_time_remaining(current_hour) == 0

    def to_dict(self) -> dict:
        """Serialize world event to dictionary.

        Returns:
            Dictionary containing all event fields
        """
        return {
            "event_id": self.event_id,
            "name": self.name,
            "description": self.description,
            "event_type": self.event_type,
            "affected_locations": self.affected_locations.copy(),
            "start_hour": self.start_hour,
            "duration_hours": self.duration_hours,
            "is_active": self.is_active,
            "is_resolved": self.is_resolved,
            "consequence_applied": self.consequence_applied,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldEvent":
        """Deserialize world event from dictionary.

        Args:
            data: Dictionary containing event fields

        Returns:
            WorldEvent instance
        """
        return cls(
            event_id=data["event_id"],
            name=data["name"],
            description=data["description"],
            event_type=data["event_type"],
            affected_locations=data["affected_locations"].copy(),
            start_hour=data["start_hour"],
            duration_hours=data["duration_hours"],
            is_active=data.get("is_active", True),
            is_resolved=data.get("is_resolved", False),
            consequence_applied=data.get("consequence_applied", False),
        )
