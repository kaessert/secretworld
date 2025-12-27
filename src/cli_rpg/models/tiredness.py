"""Tiredness model for tracking player fatigue.

The Tiredness stat tracks player fatigue (0-100), replacing random sleep/dream
triggers with behavior-driven mechanics. High tiredness causes gameplay penalties;
rest reduces tiredness based on sleep quality.

Core Mechanics:
- Range: 0-100 (0 = fully rested, 100 = exhausted)
- Tiredness < 30: Cannot sleep (too alert), no dreams
- Tiredness 30-60: May sleep (low chance), light rest
- Tiredness 60-80: Normal sleep, standard recovery
- Tiredness 80+: Deep sleep guaranteed, vivid dreams more likely

Gameplay Effects at High Tiredness (80+):
- -10% attack power (mirrors dread penalty pattern)
- -10% perception (miss secrets more often)
- Movement warning messages at 60+/80+/100
"""

from dataclasses import dataclass
from typing import Optional

from cli_rpg import colors


# Milestone thresholds and their warning messages
TIREDNESS_THRESHOLDS = {
    60: "You're feeling tired...",
    80: "You're exhausted and should rest soon.",
    100: "You can barely keep your eyes open!",
}


@dataclass
class Tiredness:
    """Tracks the player's fatigue level (0-100).

    Attributes:
        current: Current tiredness level (0 = rested, 100 = exhausted)
    """

    current: int = 0

    def increase(self, amount: int) -> Optional[str]:
        """Increase tiredness and return any threshold warning.

        Args:
            amount: Amount of tiredness to add (positive integer)

        Returns:
            Warning message if a threshold was crossed, None otherwise
        """
        old = self.current
        self.current = min(100, self.current + amount)

        # Check for threshold crossings
        for threshold, message in sorted(TIREDNESS_THRESHOLDS.items()):
            if old < threshold <= self.current:
                return message

        return None

    def decrease(self, amount: int) -> None:
        """Decrease tiredness (clamped to 0).

        Args:
            amount: Amount of tiredness to reduce (positive integer)
        """
        self.current = max(0, self.current - amount)

    def can_sleep(self) -> bool:
        """Check if tired enough to sleep (30+).

        Returns:
            True if tiredness >= 30, False otherwise
        """
        return self.current >= 30

    def sleep_quality(self) -> str:
        """Get sleep quality based on tiredness level.

        Returns:
            "deep" if tiredness >= 80
            "normal" if tiredness 60-79
            "light" if tiredness < 60
        """
        if self.current >= 80:
            return "deep"
        elif self.current >= 60:
            return "normal"
        return "light"

    def get_attack_penalty(self) -> float:
        """Get attack power modifier based on tiredness.

        Returns:
            1.0 for normal attack power, 0.9 for -10% penalty at 80+ tiredness
        """
        return 0.9 if self.current >= 80 else 1.0

    def get_perception_penalty(self) -> float:
        """Get perception modifier based on tiredness.

        Returns:
            1.0 for normal perception, 0.9 for -10% penalty at 80+ tiredness
        """
        return 0.9 if self.current >= 80 else 1.0

    def get_display(self) -> str:
        """Get a visual bar representation of tiredness level.

        Returns:
            Formatted string like "TIREDNESS: ████████░░░░░░░░ 53%"
        """
        bar_width = 16
        filled = round(bar_width * self.current / 100)
        empty = bar_width - filled

        bar = "█" * filled + "░" * empty

        # Color based on tiredness level
        if self.current >= 80:
            colored_bar = colors.damage(bar)
        elif self.current >= 60:
            colored_bar = colors.gold(bar)
        else:
            colored_bar = bar

        return f"TIREDNESS: {colored_bar} {self.current}%"

    def to_dict(self) -> dict:
        """Serialize tiredness to dictionary.

        Returns:
            Dictionary containing current tiredness value
        """
        return {"current": self.current}

    @classmethod
    def from_dict(cls, data: dict) -> "Tiredness":
        """Deserialize tiredness from dictionary.

        Args:
            data: Dictionary containing tiredness value

        Returns:
            Tiredness instance
        """
        return cls(current=data.get("current", 0))
