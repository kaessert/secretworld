"""Agent package for AI-driven playtesting.

This package contains the personality system and agent logic for
human-like automated playtesting of the CLI RPG.
"""

from scripts.agent.personality import (
    PersonalityType,
    PersonalityTraits,
    PERSONALITY_PRESETS,
    get_personality_traits,
)

__all__ = [
    "PersonalityType",
    "PersonalityTraits",
    "PERSONALITY_PRESETS",
    "get_personality_traits",
]
