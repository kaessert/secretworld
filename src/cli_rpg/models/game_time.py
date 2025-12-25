"""Game time model for day/night cycle system."""

from dataclasses import dataclass


@dataclass
class GameTime:
    """Tracks in-game time for day/night cycle.

    Attributes:
        hour: Current hour (0-23), defaults to 6:00 AM
    """

    hour: int = 6  # Start at 6:00 AM

    def advance(self, hours: int) -> None:
        """Advance time by the specified number of hours.

        Args:
            hours: Number of hours to advance (can be any positive integer)
        """
        self.hour = (self.hour + hours) % 24

    def is_night(self) -> bool:
        """Check if it is currently night time.

        Night is defined as 18:00-5:59 (6 PM to 5:59 AM).

        Returns:
            True if it's night, False otherwise
        """
        return self.hour >= 18 or self.hour < 6

    def get_period(self) -> str:
        """Get the current time period as a string.

        Returns:
            "night" if it's night time, "day" otherwise
        """
        return "night" if self.is_night() else "day"

    def get_display(self) -> str:
        """Get a human-readable time display.

        Returns:
            Formatted string like "14:00 (Day)" or "22:00 (Night)"
        """
        period = self.get_period().capitalize()
        return f"{self.hour:02d}:00 ({period})"

    def to_dict(self) -> dict:
        """Serialize game time to dictionary.

        Returns:
            Dictionary containing hour
        """
        return {"hour": self.hour}

    @classmethod
    def from_dict(cls, data: dict) -> "GameTime":
        """Deserialize game time from dictionary.

        Args:
            data: Dictionary containing hour

        Returns:
            GameTime instance
        """
        return cls(hour=data.get("hour", 6))
