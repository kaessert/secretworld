"""Agent package for AI-driven playtesting.

This package contains the personality system and agent logic for
human-like automated playtesting of the CLI RPG.
"""

from scripts.agent.memory import (
    AgentMemory,
    FailureRecord,
    LocationMemory,
    NPCMemory,
)
from scripts.agent.personality import (
    PersonalityType,
    PersonalityTraits,
    PERSONALITY_PRESETS,
    get_personality_traits,
)

__all__ = [
    # Memory system
    "AgentMemory",
    "FailureRecord",
    "LocationMemory",
    "NPCMemory",
    # Personality system
    "PersonalityType",
    "PersonalityTraits",
    "PERSONALITY_PRESETS",
    "get_personality_traits",
]
