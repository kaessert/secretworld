"""Personality system for AI agents.

Provides personality presets that influence agent decision-making,
establishing the foundation for human-like behavior in playtesting.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PersonalityType(Enum):
    """Five personality presets with distinct play styles.

    Each personality type maps to a set of traits that influence
    how the agent makes decisions during gameplay.
    """

    CAUTIOUS_EXPLORER = "cautious_explorer"  # Prioritizes safety and thorough exploration
    AGGRESSIVE_FIGHTER = "aggressive_fighter"  # Seeks combat, takes risks
    COMPLETIONIST = "completionist"  # Does everything, talks to everyone
    SPEEDRUNNER = "speedrunner"  # Minimal interaction, efficient pathing
    ROLEPLAYER = "roleplayer"  # Balanced with focus on NPC interaction


@dataclass
class PersonalityTraits:
    """Float traits (0.0-1.0) that influence agent decisions.

    Attributes:
        risk_tolerance: Willingness to fight at low HP, enter dangerous areas
        exploration_drive: Priority on visiting new locations vs returning to known
        social_engagement: Likelihood of talking to NPCs, accepting quests
        combat_aggression: Preference for fighting vs fleeing
        resource_conservation: Tendency to use potions sparingly, rest often
    """

    risk_tolerance: float
    exploration_drive: float
    social_engagement: float
    combat_aggression: float
    resource_conservation: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize traits to dictionary for checkpoint compatibility."""
        return {
            "risk_tolerance": self.risk_tolerance,
            "exploration_drive": self.exploration_drive,
            "social_engagement": self.social_engagement,
            "combat_aggression": self.combat_aggression,
            "resource_conservation": self.resource_conservation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonalityTraits":
        """Deserialize traits from dictionary for checkpoint restoration."""
        return cls(
            risk_tolerance=data["risk_tolerance"],
            exploration_drive=data["exploration_drive"],
            social_engagement=data["social_engagement"],
            combat_aggression=data["combat_aggression"],
            resource_conservation=data["resource_conservation"],
        )


# Preset values matching the specification from ISSUES.md
PERSONALITY_PRESETS: dict[PersonalityType, PersonalityTraits] = {
    PersonalityType.CAUTIOUS_EXPLORER: PersonalityTraits(
        risk_tolerance=0.2,
        exploration_drive=0.9,
        social_engagement=0.7,
        combat_aggression=0.3,
        resource_conservation=0.7,
    ),
    PersonalityType.AGGRESSIVE_FIGHTER: PersonalityTraits(
        risk_tolerance=0.9,
        exploration_drive=0.4,
        social_engagement=0.3,
        combat_aggression=0.9,
        resource_conservation=0.2,
    ),
    PersonalityType.COMPLETIONIST: PersonalityTraits(
        risk_tolerance=0.5,
        exploration_drive=1.0,
        social_engagement=1.0,
        combat_aggression=0.5,
        resource_conservation=0.4,
    ),
    PersonalityType.SPEEDRUNNER: PersonalityTraits(
        risk_tolerance=0.7,
        exploration_drive=0.1,
        social_engagement=0.1,
        combat_aggression=0.4,
        resource_conservation=0.3,
    ),
    PersonalityType.ROLEPLAYER: PersonalityTraits(
        risk_tolerance=0.5,
        exploration_drive=0.7,
        social_engagement=0.9,
        combat_aggression=0.5,
        resource_conservation=0.5,
    ),
}


def get_personality_traits(preset: PersonalityType) -> PersonalityTraits:
    """Get the personality traits for a given preset type.

    Args:
        preset: The personality type to get traits for

    Returns:
        PersonalityTraits instance with the preset's values
    """
    return PERSONALITY_PRESETS[preset]
