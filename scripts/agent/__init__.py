"""Agent package for AI-driven playtesting.

This package contains the personality system and agent logic for
human-like automated playtesting of the CLI RPG.
"""

from scripts.agent.class_behaviors import (
    CharacterClassName,
    ClassBehavior,
    ClassBehaviorConfig,
    WarriorBehavior,
    MageBehavior,
    RogueBehavior,
    RangerBehavior,
    ClericBehavior,
    BEHAVIOR_REGISTRY,
    get_class_behavior,
)
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
    # Class behavior system
    "CharacterClassName",
    "ClassBehavior",
    "ClassBehaviorConfig",
    "WarriorBehavior",
    "MageBehavior",
    "RogueBehavior",
    "RangerBehavior",
    "ClericBehavior",
    "BEHAVIOR_REGISTRY",
    "get_class_behavior",
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
