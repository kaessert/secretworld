"""Status effect model for CLI RPG."""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class StatusEffect:
    """Represents a status effect (buff, debuff, DOT, etc.) on a character.

    Attributes:
        name: Display name of the effect (e.g., "Poison", "Burn")
        effect_type: Type of effect - "dot" (damage over time), "buff", "debuff"
        damage_per_turn: Damage dealt each tick for DOT effects
        duration: Number of turns remaining
    """

    name: str
    effect_type: str  # "dot", "buff", "debuff"
    damage_per_turn: int
    duration: int

    def tick(self) -> Tuple[int, bool]:
        """Process one turn of the status effect.

        Decrements duration and returns the damage dealt this tick.

        Returns:
            Tuple of (damage_dealt, is_expired)
            - damage_dealt: Amount of damage dealt this tick (for DOT effects)
            - is_expired: True if effect has expired (duration reached 0)
        """
        damage = self.damage_per_turn if self.effect_type == "dot" else 0
        self.duration -= 1
        expired = self.duration <= 0
        return damage, expired

    def to_dict(self) -> Dict:
        """Serialize status effect to dictionary for persistence.

        Returns:
            Dictionary containing all status effect attributes
        """
        return {
            "name": self.name,
            "effect_type": self.effect_type,
            "damage_per_turn": self.damage_per_turn,
            "duration": self.duration,
        }

    @staticmethod
    def from_dict(data: Dict) -> "StatusEffect":
        """Deserialize status effect from dictionary.

        Args:
            data: Dictionary containing status effect data

        Returns:
            StatusEffect instance
        """
        return StatusEffect(
            name=data["name"],
            effect_type=data["effect_type"],
            damage_per_turn=data["damage_per_turn"],
            duration=data["duration"],
        )
