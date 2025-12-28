"""Memory system for AI agents.

Enables agents to learn from experience by tracking failures, NPC interactions,
and location knowledge during playtesting.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FailureRecord:
    """Track deaths and damage causes.

    Attributes:
        enemy_name: Enemy that caused failure
        location: Where failure occurred
        cause: Type of failure ("death", "critical_damage", "flee")
        timestamp: When it happened
        health_at_failure: HP when failure occurred
    """

    enemy_name: str
    location: str
    cause: str
    timestamp: str
    health_at_failure: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for checkpoint compatibility."""
        return {
            "enemy_name": self.enemy_name,
            "location": self.location,
            "cause": self.cause,
            "timestamp": self.timestamp,
            "health_at_failure": self.health_at_failure,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FailureRecord":
        """Deserialize from dictionary for checkpoint restoration."""
        return cls(
            enemy_name=data["enemy_name"],
            location=data["location"],
            cause=data["cause"],
            timestamp=data["timestamp"],
            health_at_failure=data["health_at_failure"],
        )


@dataclass
class NPCMemory:
    """Track NPC interactions.

    Attributes:
        name: NPC name
        location: Where first met
        trust_level: -100 to 100 (hostile to friendly), auto-clamped
        interactions: History of interaction types
        has_quest: Offered quest before
        last_interaction: Timestamp of last interaction
    """

    name: str
    location: str
    trust_level: int
    interactions: list[str]
    has_quest: bool
    last_interaction: str

    def __post_init__(self):
        """Clamp trust_level to valid range."""
        self.trust_level = max(-100, min(100, self.trust_level))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for checkpoint compatibility."""
        return {
            "name": self.name,
            "location": self.location,
            "trust_level": self.trust_level,
            "interactions": self.interactions.copy(),
            "has_quest": self.has_quest,
            "last_interaction": self.last_interaction,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NPCMemory":
        """Deserialize from dictionary for checkpoint restoration."""
        return cls(
            name=data["name"],
            location=data["location"],
            trust_level=data["trust_level"],
            interactions=data["interactions"].copy(),
            has_quest=data["has_quest"],
            last_interaction=data["last_interaction"],
        )


@dataclass
class LocationMemory:
    """Track location knowledge.

    Attributes:
        name: Location name
        category: Location type (dungeon, town, etc.)
        danger_level: 0.0-1.0 based on combat encounters
        has_secrets: Found secrets here
        has_treasure: Found treasure here
        deaths_here: Number of deaths at location
        visits: Visit count
    """

    name: str
    category: str
    danger_level: float
    has_secrets: bool
    has_treasure: bool
    deaths_here: int
    visits: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for checkpoint compatibility."""
        return {
            "name": self.name,
            "category": self.category,
            "danger_level": self.danger_level,
            "has_secrets": self.has_secrets,
            "has_treasure": self.has_treasure,
            "deaths_here": self.deaths_here,
            "visits": self.visits,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocationMemory":
        """Deserialize from dictionary for checkpoint restoration."""
        return cls(
            name=data["name"],
            category=data["category"],
            danger_level=data["danger_level"],
            has_secrets=data["has_secrets"],
            has_treasure=data["has_treasure"],
            deaths_here=data["deaths_here"],
            visits=data["visits"],
        )


@dataclass
class AgentMemory:
    """Main memory container for agent experience.

    Stores all recorded failures, NPC interactions, and location knowledge
    to enable learning from experience during playtesting.

    Attributes:
        failures: All recorded failures
        npc_memories: NPC name -> memory mapping
        location_memories: Location name -> memory mapping
        dangerous_enemies: Set of enemy types that killed the agent
    """

    failures: list[FailureRecord] = field(default_factory=list)
    npc_memories: dict[str, NPCMemory] = field(default_factory=dict)
    location_memories: dict[str, LocationMemory] = field(default_factory=dict)
    dangerous_enemies: set[str] = field(default_factory=set)

    def record_failure(
        self,
        enemy_name: str,
        location: str,
        cause: str,
        timestamp: str,
        health_at_failure: int,
    ) -> None:
        """Record a failure (death, critical damage, or flee).

        Args:
            enemy_name: Enemy that caused failure
            location: Where failure occurred
            cause: Type of failure ("death", "critical_damage", "flee")
            timestamp: When it happened
            health_at_failure: HP when failure occurred
        """
        record = FailureRecord(
            enemy_name=enemy_name,
            location=location,
            cause=cause,
            timestamp=timestamp,
            health_at_failure=health_at_failure,
        )
        self.failures.append(record)

        # Deaths mark enemy as dangerous
        if cause == "death":
            self.dangerous_enemies.add(enemy_name)

    def record_npc_interaction(
        self,
        name: str,
        location: str,
        interaction_type: str,
        trust_change: int,
        has_quest: bool,
        timestamp: str,
    ) -> None:
        """Record an interaction with an NPC.

        Creates a new NPCMemory if first interaction, otherwise updates existing.

        Args:
            name: NPC name
            location: Where interaction occurred
            interaction_type: Type of interaction (talk, buy, accept_quest, etc.)
            trust_change: Change in trust level
            has_quest: Whether NPC has/had a quest
            timestamp: When interaction occurred
        """
        if name not in self.npc_memories:
            # Create new memory
            self.npc_memories[name] = NPCMemory(
                name=name,
                location=location,
                trust_level=trust_change,
                interactions=[interaction_type],
                has_quest=has_quest,
                last_interaction=timestamp,
            )
        else:
            # Update existing memory
            memory = self.npc_memories[name]
            memory.trust_level = max(-100, min(100, memory.trust_level + trust_change))
            memory.interactions.append(interaction_type)
            memory.has_quest = memory.has_quest or has_quest
            memory.last_interaction = timestamp

    def update_location(
        self,
        name: str,
        category: str,
        had_combat: bool,
        found_secret: bool,
        found_treasure: bool,
        died: bool,
    ) -> None:
        """Update knowledge about a location.

        Creates a new LocationMemory if first visit, otherwise updates existing.

        Args:
            name: Location name
            category: Location type (dungeon, town, etc.)
            had_combat: Whether combat occurred this visit
            found_secret: Whether a secret was found
            found_treasure: Whether treasure was found
            died: Whether agent died here
        """
        if name not in self.location_memories:
            # Create new memory with initial danger based on events
            danger = 0.0
            if had_combat:
                danger += 0.2
            if died:
                danger += 0.5

            self.location_memories[name] = LocationMemory(
                name=name,
                category=category,
                danger_level=min(1.0, danger),
                has_secrets=found_secret,
                has_treasure=found_treasure,
                deaths_here=1 if died else 0,
                visits=1,
            )
        else:
            # Update existing memory
            memory = self.location_memories[name]
            memory.visits += 1

            if found_secret:
                memory.has_secrets = True
            if found_treasure:
                memory.has_treasure = True
            if died:
                memory.deaths_here += 1
                # Increase danger level on death
                memory.danger_level = min(1.0, memory.danger_level + 0.2)
            if had_combat:
                # Slight danger increase from combat
                memory.danger_level = min(1.0, memory.danger_level + 0.05)

    def is_enemy_dangerous(self, enemy_name: str) -> bool:
        """Check if an enemy has killed the agent before.

        Args:
            enemy_name: Name of enemy to check

        Returns:
            True if enemy has killed agent, False otherwise
        """
        return enemy_name in self.dangerous_enemies

    def get_location_danger(self, location_name: str) -> float:
        """Get the danger level of a location.

        Args:
            location_name: Name of location to check

        Returns:
            Danger level (0.0-1.0), or 0.0 if location unknown
        """
        if location_name not in self.location_memories:
            return 0.0
        return self.location_memories[location_name].danger_level

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for checkpoint compatibility."""
        return {
            "failures": [f.to_dict() for f in self.failures],
            "npc_memories": {k: v.to_dict() for k, v in self.npc_memories.items()},
            "location_memories": {k: v.to_dict() for k, v in self.location_memories.items()},
            "dangerous_enemies": list(self.dangerous_enemies),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMemory":
        """Deserialize from dictionary for checkpoint restoration."""
        memory = cls()
        memory.failures = [FailureRecord.from_dict(f) for f in data.get("failures", [])]
        memory.npc_memories = {
            k: NPCMemory.from_dict(v) for k, v in data.get("npc_memories", {}).items()
        }
        memory.location_memories = {
            k: LocationMemory.from_dict(v) for k, v in data.get("location_memories", {}).items()
        }
        memory.dangerous_enemies = set(data.get("dangerous_enemies", []))
        return memory
