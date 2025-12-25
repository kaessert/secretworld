"""DreadMeter model for psychological horror tracking.

The Darkness Meter tracks the player's Dread level (0-100%), which builds
in dangerous areas and has gameplay consequences at high levels.

Effects:
- 50%+: Paranoid whispers appear
- 75%+: -10% attack penalty
- 100%: Shadow creature attack triggered
"""

from dataclasses import dataclass
from typing import Optional

from cli_rpg import colors


# Milestone thresholds and their messages
DREAD_MILESTONES = {
    25: "A sense of unease creeps into your mind...",
    50: "Paranoid whispers echo in your thoughts. The shadows seem to watch.",
    75: "Terror grips your heart. Your hands tremble (-10% attack power).",
    100: "The darkness threatens to consume you completely!",
}


@dataclass
class DreadMeter:
    """Tracks the player's psychological dread level.

    Attributes:
        dread: Current dread level (0-100)
    """

    dread: int = 0

    def add_dread(self, amount: int) -> Optional[str]:
        """Add dread and return any milestone message.

        Args:
            amount: Amount of dread to add (positive integer)

        Returns:
            Milestone message if a threshold was crossed, None otherwise
        """
        old_dread = self.dread
        self.dread = min(100, self.dread + amount)

        # Check for milestone crossings
        for threshold, message in sorted(DREAD_MILESTONES.items()):
            if old_dread < threshold <= self.dread:
                return message

        return None

    def reduce_dread(self, amount: int) -> None:
        """Reduce dread (clamped to 0).

        Args:
            amount: Amount of dread to reduce (positive integer)
        """
        self.dread = max(0, self.dread - amount)

    def get_display(self) -> str:
        """Get a visual bar representation of the dread level.

        Returns:
            Formatted string like "DREAD: ████████░░░░░░░░ 53%"
        """
        bar_width = 16
        filled = round(bar_width * self.dread / 100)
        empty = bar_width - filled

        bar = "█" * filled + "░" * empty

        # Color based on dread level
        if self.dread >= 75:
            colored_bar = colors.damage(bar)
        elif self.dread >= 50:
            colored_bar = colors.gold(bar)
        elif self.dread >= 25:
            colored_bar = colors.warning(bar)
        else:
            colored_bar = bar

        return f"DREAD: {colored_bar} {self.dread}%"

    def get_penalty(self) -> float:
        """Get the attack power modifier based on dread level.

        Returns:
            1.0 for normal attack power, 0.9 for -10% penalty at 75%+ dread
        """
        if self.dread >= 75:
            return 0.9
        return 1.0

    def is_critical(self) -> bool:
        """Check if dread is at critical level (100%).

        Returns:
            True if dread is at 100%, False otherwise
        """
        return self.dread >= 100

    def to_dict(self) -> dict:
        """Serialize the dread meter to a dictionary.

        Returns:
            Dictionary containing dread value
        """
        return {"dread": self.dread}

    @classmethod
    def from_dict(cls, data: dict) -> "DreadMeter":
        """Deserialize dread meter from dictionary.

        Args:
            data: Dictionary containing dread value

        Returns:
            DreadMeter instance
        """
        return cls(dread=data.get("dread", 0))
