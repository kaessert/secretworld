"""Game time model for day/night cycle and seasonal system."""

from dataclasses import dataclass


# Season dread modifiers: darker seasons increase dread
SEASON_DREAD_MODIFIERS = {
    "spring": -1,
    "summer": 0,
    "autumn": 1,
    "winter": 2,
}


@dataclass
class GameTime:
    """Tracks in-game time for day/night cycle and seasons.

    Attributes:
        hour: Current hour (0-23), defaults to 6:00 AM
        total_hours: Total hours elapsed since game start (for season/day tracking)
    """

    hour: int = 6  # Start at 6:00 AM
    total_hours: int = 0  # Track total elapsed time for seasons

    def advance(self, hours: int) -> None:
        """Advance time by the specified number of hours.

        Args:
            hours: Number of hours to advance (can be any positive integer)
        """
        self.hour = (self.hour + hours) % 24
        self.total_hours += hours

    def get_day(self) -> int:
        """Get current day of the year (1-120, wrapping).

        Returns:
            Current day number (1-120)
        """
        return (self.total_hours // 24 % 120) + 1

    def get_season(self) -> str:
        """Get current season based on day.

        Seasons:
        - Spring: Days 1-30
        - Summer: Days 31-60
        - Autumn: Days 61-90
        - Winter: Days 91-120

        Returns:
            Season name ("spring", "summer", "autumn", "winter")
        """
        day = self.get_day()
        if day <= 30:
            return "spring"
        elif day <= 60:
            return "summer"
        elif day <= 90:
            return "autumn"
        else:
            return "winter"

    def get_season_display(self) -> str:
        """Get display string with day and season.

        Returns:
            Formatted string like "Day 45 (Summer)"
        """
        return f"Day {self.get_day()} ({self.get_season().capitalize()})"

    def get_season_dread_modifier(self) -> int:
        """Get dread modifier for current season.

        Returns:
            Dread modifier: Winter +2, Autumn +1, Summer 0, Spring -1
        """
        return SEASON_DREAD_MODIFIERS.get(self.get_season(), 0)

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
            Dictionary containing hour and total_hours
        """
        return {"hour": self.hour, "total_hours": self.total_hours}

    @classmethod
    def from_dict(cls, data: dict) -> "GameTime":
        """Deserialize game time from dictionary.

        Args:
            data: Dictionary containing hour and optionally total_hours

        Returns:
            GameTime instance
        """
        return cls(hour=data.get("hour", 6), total_hours=data.get("total_hours", 0))
