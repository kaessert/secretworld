"""Class-specific behavior system for AI agents.

Provides class-specific combat and exploration strategies for all 5 character classes
(Warrior, Mage, Rogue, Ranger, Cleric) to make the AI agent behave differently
based on character class.
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Protocol

from scripts.state_parser import AgentState
from scripts.agent.memory import AgentMemory


class CharacterClassName(Enum):
    """Mirror of CharacterClass from game for agent use."""

    WARRIOR = "Warrior"
    MAGE = "Mage"
    ROGUE = "Rogue"
    RANGER = "Ranger"
    CLERIC = "Cleric"


@dataclass
class ClassBehaviorConfig:
    """Configuration for class-specific behavior thresholds.

    Attributes:
        flee_health_threshold: HP% to consider fleeing (0.0-1.0)
        heal_health_threshold: HP% to heal self (0.0-1.0)
        mana_conservation_threshold: Mana% to conserve (0.0-1.0)
        special_ability_cooldown: Moves between special abilities
    """

    flee_health_threshold: float
    heal_health_threshold: float
    mana_conservation_threshold: float
    special_ability_cooldown: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for checkpoint compatibility."""
        return {
            "flee_health_threshold": self.flee_health_threshold,
            "heal_health_threshold": self.heal_health_threshold,
            "mana_conservation_threshold": self.mana_conservation_threshold,
            "special_ability_cooldown": self.special_ability_cooldown,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassBehaviorConfig":
        """Deserialize from dictionary for checkpoint restoration."""
        return cls(
            flee_health_threshold=data["flee_health_threshold"],
            heal_health_threshold=data["heal_health_threshold"],
            mana_conservation_threshold=data["mana_conservation_threshold"],
            special_ability_cooldown=data["special_ability_cooldown"],
        )


class ClassBehavior(Protocol):
    """Protocol defining class-specific agent behaviors."""

    def get_combat_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Return class-specific combat command, or None to use default attack.

        Args:
            state: Current agent state
            memory: Agent memory for context

        Returns:
            Command string or None for default attack
        """
        ...

    def get_exploration_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Return class-specific exploration command, or None for default behavior.

        Args:
            state: Current agent state
            memory: Agent memory for context

        Returns:
            Command string or None for default behavior
        """
        ...

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Return True if class strategy suggests fleeing.

        Args:
            state: Current agent state
            memory: Agent memory for context

        Returns:
            True if should flee, False otherwise
        """
        ...


class WarriorBehavior:
    """Warrior behavior: bash, stance switching, brave fighter.

    Combat: Use bash when available. Switch stances based on health.
    - Health > 50%: aggressive stance
    - Health < 30%: berserker stance (all-in)
    Flee threshold: 15% (lower - warriors are brave)
    Exploration: Direct approach, no special commands
    """

    def __init__(self):
        """Initialize warrior behavior with default config."""
        self.config = ClassBehaviorConfig(
            flee_health_threshold=0.15,
            heal_health_threshold=0.3,
            mana_conservation_threshold=0.0,  # Warriors don't use mana
            special_ability_cooldown=2,
        )
        self._last_bash_turn = -10
        self._current_stance = "normal"

    def get_combat_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Get warrior combat command - prioritize bash and stance switching."""
        health_percent = state.health_percent

        # Priority 1: Use bash if available (and not on cooldown in our mind)
        if "bash" in state.commands:
            return "bash"

        # Priority 2: Stance management
        if "stance" in state.commands:
            if health_percent < 0.30 and self._current_stance != "berserker":
                self._current_stance = "berserker"
                return "stance berserker"
            elif health_percent > 0.50 and self._current_stance != "aggressive":
                self._current_stance = "aggressive"
                return "stance aggressive"

        # Default: use normal attack
        return None

    def get_exploration_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Warriors use direct approach - no special exploration commands."""
        return None

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Warriors are brave - flee only at very low health (15%)."""
        return state.health_percent < self.config.flee_health_threshold


class MageBehavior:
    """Mage behavior: spells, self-heal, mana conservation.

    Combat: Cast fireball/ice_bolt when mana > 30%. Heal self when hurt.
    Fall back to attack when mana < 20%.
    Flee threshold: 25% (higher - mages are fragile)
    Exploration: Rest more often to conserve mana
    """

    def __init__(self):
        """Initialize mage behavior with default config."""
        self.config = ClassBehaviorConfig(
            flee_health_threshold=0.25,
            heal_health_threshold=0.50,
            mana_conservation_threshold=0.20,
            special_ability_cooldown=1,
        )
        # Internal mana tracking (set externally or estimated)
        self._mana_percent = 1.0

    def get_combat_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Get mage combat command - spells, healing, mana management."""
        health_percent = state.health_percent

        # Check if we have enough mana to cast
        if self._mana_percent < self.config.mana_conservation_threshold:
            # Conserve mana - use default attack
            return None

        # Priority 1: Heal self when hurt and mana available
        if health_percent < self.config.heal_health_threshold:
            if "cast" in state.commands and self._mana_percent >= 0.20:
                return "cast heal"

        # Priority 2: Offensive spells when mana > 30%
        if self._mana_percent >= 0.30 and "cast" in state.commands:
            # Randomly choose between fireball and ice_bolt
            spell = random.choice(["fireball", "ice_bolt"])
            return f"cast {spell}"

        # Default: use normal attack
        return None

    def get_exploration_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Mages might rest more to conserve mana - no special command."""
        return None

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Mages are fragile - flee at 25% health."""
        return state.health_percent < self.config.flee_health_threshold


class RogueBehavior:
    """Rogue behavior: sneak attacks, hide, secret searching.

    Combat: Hide first turn, then sneak attack. Repeat cycle.
    Flee threshold: 20% (default)
    Exploration: Search for secrets in dungeons (30% chance per room)
    """

    def __init__(self):
        """Initialize rogue behavior with default config."""
        self.config = ClassBehaviorConfig(
            flee_health_threshold=0.20,
            heal_health_threshold=0.40,
            mana_conservation_threshold=0.0,  # Rogues don't use mana
            special_ability_cooldown=1,
        )
        self._is_hidden = False
        self._combat_turns = 0

    def get_combat_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Get rogue combat command - stealth and sneak attacks."""
        # Priority 1: Sneak attack if hidden
        if self._is_hidden and "sneak" in state.commands:
            self._is_hidden = False  # Attacking reveals us
            return "sneak"

        # Priority 2: Hide at combat start if not hidden
        if not self._is_hidden and self._combat_turns == 0 and "hide" in state.commands:
            self._is_hidden = True
            self._combat_turns += 1
            return "hide"

        # Increment turn counter
        self._combat_turns += 1

        # Default: use normal attack
        return None

    def get_exploration_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Rogues search for secrets in dungeons (30% chance)."""
        # Only search in dungeon-type locations
        dungeon_categories = {"dungeon", "cave", "ruins", "crypt", "tomb"}
        if state.location_category.lower() in dungeon_categories:
            if "search" in state.commands and random.random() < 0.30:
                return "search"

        return None

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Default flee threshold (20%)."""
        return state.health_percent < self.config.flee_health_threshold


class RangerBehavior:
    """Ranger behavior: companion, tracking, wilderness comfort.

    Combat: Normal attacks (companion fights alongside)
    Flee threshold: 20% (default), slightly lower in wilderness
    Exploration: Summon companion if not present. Track in wilderness.
                Feed companion when hurt.
    """

    def __init__(self):
        """Initialize ranger behavior with default config."""
        self.config = ClassBehaviorConfig(
            flee_health_threshold=0.20,
            heal_health_threshold=0.40,
            mana_conservation_threshold=0.0,  # Rangers don't use mana
            special_ability_cooldown=5,
        )
        self._has_companion = False
        self._companion_health_low = False

    def get_combat_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Rangers rely on companion - default attacks in combat."""
        # Rangers fight alongside their companion - no special combat commands
        return None

    def get_exploration_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Rangers summon companions, track, and care for their animal."""
        # Priority 1: Feed companion if health is low
        if self._has_companion and self._companion_health_low:
            if "feed" in state.commands and state.inventory:
                # Find food item in inventory
                food_items = ["meat", "berries", "fish", "ration"]
                for item in state.inventory:
                    if any(food in item.lower() for food in food_items):
                        return f"feed {item}"

        # Priority 2: Summon companion if not present
        if not self._has_companion and "summon" in state.commands:
            self._has_companion = True
            return "summon"

        # Priority 3: Track in wilderness
        wilderness_categories = {"forest", "plains", "mountains", "swamp", "wilderness"}
        if state.location_category.lower() in wilderness_categories:
            if "track" in state.commands and random.random() < 0.20:
                return "track"

        return None

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Default flee threshold, slightly braver in wilderness."""
        threshold = self.config.flee_health_threshold

        # Rangers are more comfortable in wilderness
        wilderness_categories = {"forest", "plains", "mountains", "swamp", "wilderness"}
        if state.location_category.lower() in wilderness_categories:
            threshold -= 0.05  # Slightly braver in wilderness

        return state.health_percent < threshold


class ClericBehavior:
    """Cleric behavior: smite undead, bless, heal, holy symbol.

    Combat: Smite undead enemies. Bless at start of combat. Heal when hurt.
    Flee threshold: 20% (default)
    Exploration: Ensure holy symbol is equipped
    """

    UNDEAD_KEYWORDS = {"skeleton", "zombie", "ghost", "wraith", "vampire", "lich",
                       "ghoul", "specter", "wight", "mummy", "revenant", "undead"}

    def __init__(self):
        """Initialize cleric behavior with default config."""
        self.config = ClassBehaviorConfig(
            flee_health_threshold=0.20,
            heal_health_threshold=0.50,
            mana_conservation_threshold=0.20,
            special_ability_cooldown=2,
        )
        self._is_blessed = False
        self._combat_turns = 0
        self._has_holy_symbol_equipped = False

    def _is_undead(self, enemy_name: str) -> bool:
        """Check if enemy is undead based on name."""
        enemy_lower = enemy_name.lower()
        return any(keyword in enemy_lower for keyword in self.UNDEAD_KEYWORDS)

    def get_combat_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Get cleric combat command - smite, bless, heal."""
        health_percent = state.health_percent

        # Priority 1: Smite undead enemies
        if self._is_undead(state.enemy) and "smite" in state.commands:
            return "smite"

        # Priority 2: Bless at start of combat
        if not self._is_blessed and self._combat_turns == 0 and "bless" in state.commands:
            self._is_blessed = True
            self._combat_turns += 1
            return "bless"

        # Priority 3: Heal when hurt
        if health_percent < self.config.heal_health_threshold:
            if "cast" in state.commands:
                return "cast heal"

        # Increment turn counter
        self._combat_turns += 1

        # Default: use normal attack
        return None

    def get_exploration_command(
        self, state: AgentState, memory: AgentMemory
    ) -> Optional[str]:
        """Clerics ensure holy symbol is equipped."""
        if not self._has_holy_symbol_equipped and "equip" in state.commands:
            # Look for holy symbol in inventory
            for item in state.inventory:
                if "holy" in item.lower() and "symbol" in item.lower():
                    self._has_holy_symbol_equipped = True
                    return f"equip {item}"

        return None

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Default flee threshold (20%)."""
        return state.health_percent < self.config.flee_health_threshold


# Registry mapping class names to behavior instances
BEHAVIOR_REGISTRY: dict[CharacterClassName, ClassBehavior] = {
    CharacterClassName.WARRIOR: WarriorBehavior(),
    CharacterClassName.MAGE: MageBehavior(),
    CharacterClassName.ROGUE: RogueBehavior(),
    CharacterClassName.RANGER: RangerBehavior(),
    CharacterClassName.CLERIC: ClericBehavior(),
}


def get_class_behavior(class_name: CharacterClassName) -> ClassBehavior:
    """Get the behavior instance for a character class.

    Args:
        class_name: The character class to get behavior for

    Returns:
        ClassBehavior instance for the class
    """
    return BEHAVIOR_REGISTRY[class_name]
