"""Tests for agent memory system.

Tests the FailureRecord, NPCMemory, LocationMemory, and AgentMemory classes
that enable agents to learn from experience during playtesting.
"""

import pytest

from scripts.agent.memory import (
    AgentMemory,
    FailureRecord,
    LocationMemory,
    NPCMemory,
)


# ===== FailureRecord Tests =====


class TestFailureRecord:
    """Tests for FailureRecord dataclass."""

    def test_failure_record_creation(self):
        """Test creating a FailureRecord with all fields."""
        # Spec: FailureRecord tracks enemy_name, location, cause, timestamp, health_at_failure
        record = FailureRecord(
            enemy_name="Dire Wolf",
            location="Dark Forest",
            cause="death",
            timestamp="2024-01-01T12:00:00",
            health_at_failure=0,
        )

        assert record.enemy_name == "Dire Wolf"
        assert record.location == "Dark Forest"
        assert record.cause == "death"
        assert record.timestamp == "2024-01-01T12:00:00"
        assert record.health_at_failure == 0

    def test_failure_record_serialization(self):
        """Test to_dict/from_dict roundtrip for FailureRecord."""
        # Spec: FailureRecord must support to_dict() and from_dict()
        original = FailureRecord(
            enemy_name="Goblin King",
            location="Goblin Cave",
            cause="critical_damage",
            timestamp="2024-01-02T15:30:00",
            health_at_failure=5,
        )

        data = original.to_dict()
        restored = FailureRecord.from_dict(data)

        assert restored.enemy_name == original.enemy_name
        assert restored.location == original.location
        assert restored.cause == original.cause
        assert restored.timestamp == original.timestamp
        assert restored.health_at_failure == original.health_at_failure


# ===== NPCMemory Tests =====


class TestNPCMemory:
    """Tests for NPCMemory dataclass."""

    def test_npc_memory_creation(self):
        """Test creating an NPCMemory with all fields."""
        # Spec: NPCMemory tracks name, location, trust_level, interactions, has_quest, last_interaction
        memory = NPCMemory(
            name="Elara the Merchant",
            location="Town Square",
            trust_level=50,
            interactions=["talk", "buy", "accept_quest"],
            has_quest=True,
            last_interaction="2024-01-03T10:00:00",
        )

        assert memory.name == "Elara the Merchant"
        assert memory.location == "Town Square"
        assert memory.trust_level == 50
        assert memory.interactions == ["talk", "buy", "accept_quest"]
        assert memory.has_quest is True
        assert memory.last_interaction == "2024-01-03T10:00:00"

    def test_npc_memory_serialization(self):
        """Test to_dict/from_dict roundtrip for NPCMemory."""
        # Spec: NPCMemory must support to_dict() and from_dict()
        original = NPCMemory(
            name="Blacksmith",
            location="Forge",
            trust_level=-25,
            interactions=["talk", "refuse_quest"],
            has_quest=False,
            last_interaction="2024-01-04T09:00:00",
        )

        data = original.to_dict()
        restored = NPCMemory.from_dict(data)

        assert restored.name == original.name
        assert restored.location == original.location
        assert restored.trust_level == original.trust_level
        assert restored.interactions == original.interactions
        assert restored.has_quest == original.has_quest
        assert restored.last_interaction == original.last_interaction

    def test_npc_memory_trust_bounds(self):
        """Test that trust_level is clamped to -100..100 range."""
        # Spec: trust_level should be clamped to -100 to 100
        # Test upper bound clamping
        high_trust = NPCMemory(
            name="Friend",
            location="Home",
            trust_level=150,  # Above max
            interactions=[],
            has_quest=False,
            last_interaction="",
        )
        assert high_trust.trust_level == 100

        # Test lower bound clamping
        low_trust = NPCMemory(
            name="Enemy",
            location="Dungeon",
            trust_level=-200,  # Below min
            interactions=[],
            has_quest=False,
            last_interaction="",
        )
        assert low_trust.trust_level == -100


# ===== LocationMemory Tests =====


class TestLocationMemory:
    """Tests for LocationMemory dataclass."""

    def test_location_memory_creation(self):
        """Test creating a LocationMemory with all fields."""
        # Spec: LocationMemory tracks name, category, danger_level, has_secrets, has_treasure, deaths_here, visits
        memory = LocationMemory(
            name="Ancient Ruins",
            category="dungeon",
            danger_level=0.7,
            has_secrets=True,
            has_treasure=True,
            deaths_here=2,
            visits=5,
        )

        assert memory.name == "Ancient Ruins"
        assert memory.category == "dungeon"
        assert memory.danger_level == 0.7
        assert memory.has_secrets is True
        assert memory.has_treasure is True
        assert memory.deaths_here == 2
        assert memory.visits == 5

    def test_location_memory_serialization(self):
        """Test to_dict/from_dict roundtrip for LocationMemory."""
        # Spec: LocationMemory must support to_dict() and from_dict()
        original = LocationMemory(
            name="Peaceful Village",
            category="town",
            danger_level=0.1,
            has_secrets=False,
            has_treasure=False,
            deaths_here=0,
            visits=10,
        )

        data = original.to_dict()
        restored = LocationMemory.from_dict(data)

        assert restored.name == original.name
        assert restored.category == original.category
        assert restored.danger_level == original.danger_level
        assert restored.has_secrets == original.has_secrets
        assert restored.has_treasure == original.has_treasure
        assert restored.deaths_here == original.deaths_here
        assert restored.visits == original.visits

    def test_location_danger_calculation(self):
        """Test that danger level increases with deaths."""
        # Spec: danger_level should be 0.0-1.0 based on combat encounters
        # More deaths = higher danger level
        safe_location = LocationMemory(
            name="Safe Haven",
            category="town",
            danger_level=0.0,
            has_secrets=False,
            has_treasure=False,
            deaths_here=0,
            visits=10,
        )
        assert safe_location.danger_level == 0.0

        dangerous_location = LocationMemory(
            name="Dragon's Lair",
            category="dungeon",
            danger_level=1.0,
            has_secrets=True,
            has_treasure=True,
            deaths_here=5,
            visits=5,
        )
        assert dangerous_location.danger_level == 1.0


# ===== AgentMemory Tests =====


class TestAgentMemory:
    """Tests for AgentMemory container class."""

    def test_record_failure_adds_to_list(self):
        """Test that record_failure adds a FailureRecord to failures list."""
        # Spec: AgentMemory.record_failure() adds failure to failures list
        memory = AgentMemory()
        assert len(memory.failures) == 0

        memory.record_failure(
            enemy_name="Skeleton",
            location="Crypt",
            cause="death",
            timestamp="2024-01-05T14:00:00",
            health_at_failure=0,
        )

        assert len(memory.failures) == 1
        assert memory.failures[0].enemy_name == "Skeleton"
        assert memory.failures[0].location == "Crypt"
        assert memory.failures[0].cause == "death"

    def test_record_failure_adds_dangerous_enemy(self):
        """Test that death adds enemy to dangerous_enemies set."""
        # Spec: Deaths add enemy to dangerous_enemies set
        memory = AgentMemory()
        assert len(memory.dangerous_enemies) == 0

        # Record a death
        memory.record_failure(
            enemy_name="Dragon",
            location="Lair",
            cause="death",
            timestamp="2024-01-05T15:00:00",
            health_at_failure=0,
        )

        assert "Dragon" in memory.dangerous_enemies

        # Non-death failures shouldn't add to dangerous_enemies
        memory.record_failure(
            enemy_name="Goblin",
            location="Forest",
            cause="flee",
            timestamp="2024-01-05T16:00:00",
            health_at_failure=10,
        )

        assert "Goblin" not in memory.dangerous_enemies

    def test_record_npc_interaction_creates_memory(self):
        """Test that interacting with new NPC creates memory entry."""
        # Spec: record_npc_interaction() creates NPCMemory for new NPCs
        memory = AgentMemory()
        assert len(memory.npc_memories) == 0

        memory.record_npc_interaction(
            name="Wizard",
            location="Tower",
            interaction_type="talk",
            trust_change=10,
            has_quest=True,
            timestamp="2024-01-06T10:00:00",
        )

        assert "Wizard" in memory.npc_memories
        npc_memory = memory.npc_memories["Wizard"]
        assert npc_memory.name == "Wizard"
        assert npc_memory.location == "Tower"
        assert npc_memory.trust_level == 10
        assert npc_memory.interactions == ["talk"]
        assert npc_memory.has_quest is True

    def test_record_npc_interaction_updates_existing(self):
        """Test that interacting with existing NPC updates memory."""
        # Spec: record_npc_interaction() updates existing NPCMemory
        memory = AgentMemory()

        # First interaction
        memory.record_npc_interaction(
            name="Guard",
            location="Gate",
            interaction_type="talk",
            trust_change=5,
            has_quest=False,
            timestamp="2024-01-06T11:00:00",
        )

        # Second interaction
        memory.record_npc_interaction(
            name="Guard",
            location="Gate",
            interaction_type="bribe",
            trust_change=20,
            has_quest=True,
            timestamp="2024-01-06T12:00:00",
        )

        assert len(memory.npc_memories) == 1
        npc_memory = memory.npc_memories["Guard"]
        assert npc_memory.trust_level == 25  # 5 + 20
        assert npc_memory.interactions == ["talk", "bribe"]
        assert npc_memory.has_quest is True  # Updated to True
        assert npc_memory.last_interaction == "2024-01-06T12:00:00"

    def test_update_location_creates_memory(self):
        """Test that visiting new location creates memory entry."""
        # Spec: update_location() creates LocationMemory for new locations
        memory = AgentMemory()
        assert len(memory.location_memories) == 0

        memory.update_location(
            name="Abandoned Mine",
            category="dungeon",
            had_combat=False,
            found_secret=True,
            found_treasure=False,
            died=False,
        )

        assert "Abandoned Mine" in memory.location_memories
        loc_memory = memory.location_memories["Abandoned Mine"]
        assert loc_memory.name == "Abandoned Mine"
        assert loc_memory.category == "dungeon"
        assert loc_memory.has_secrets is True
        assert loc_memory.visits == 1

    def test_update_location_increments_visits(self):
        """Test that visit count increases on repeated visits."""
        # Spec: update_location() increments visits counter
        memory = AgentMemory()

        # First visit
        memory.update_location(
            name="Inn",
            category="town",
            had_combat=False,
            found_secret=False,
            found_treasure=False,
            died=False,
        )
        assert memory.location_memories["Inn"].visits == 1

        # Second visit
        memory.update_location(
            name="Inn",
            category="town",
            had_combat=False,
            found_secret=False,
            found_treasure=False,
            died=False,
        )
        assert memory.location_memories["Inn"].visits == 2

        # Third visit
        memory.update_location(
            name="Inn",
            category="town",
            had_combat=False,
            found_secret=False,
            found_treasure=False,
            died=False,
        )
        assert memory.location_memories["Inn"].visits == 3

    def test_is_enemy_dangerous_returns_true(self):
        """Test is_enemy_dangerous returns True for enemies that killed agent."""
        # Spec: is_enemy_dangerous() returns true for dangerous_enemies
        memory = AgentMemory()

        memory.record_failure(
            enemy_name="Lich",
            location="Tomb",
            cause="death",
            timestamp="2024-01-07T10:00:00",
            health_at_failure=0,
        )

        assert memory.is_enemy_dangerous("Lich") is True

    def test_is_enemy_dangerous_returns_false(self):
        """Test is_enemy_dangerous returns False for unknown enemies."""
        # Spec: is_enemy_dangerous() returns false for unknown enemies
        memory = AgentMemory()

        # No failures recorded
        assert memory.is_enemy_dangerous("Slime") is False

        # Record a death from different enemy
        memory.record_failure(
            enemy_name="Orc",
            location="Camp",
            cause="death",
            timestamp="2024-01-07T11:00:00",
            health_at_failure=0,
        )

        # Still unknown
        assert memory.is_enemy_dangerous("Slime") is False

    def test_get_location_danger_returns_value(self):
        """Test get_location_danger returns correct danger level."""
        # Spec: get_location_danger() returns danger level for known locations
        memory = AgentMemory()

        # Unknown location returns 0.0
        assert memory.get_location_danger("Unknown Place") == 0.0

        # Create a location with danger
        memory.update_location(
            name="Dangerous Cave",
            category="dungeon",
            had_combat=True,
            found_secret=False,
            found_treasure=False,
            died=True,
        )

        # Should have some danger level now
        danger = memory.get_location_danger("Dangerous Cave")
        assert danger > 0.0

    def test_agent_memory_serialization(self):
        """Test full to_dict/from_dict roundtrip for AgentMemory."""
        # Spec: AgentMemory must support to_dict() and from_dict()
        memory = AgentMemory()

        # Add various data
        memory.record_failure(
            enemy_name="Boss",
            location="Throne Room",
            cause="death",
            timestamp="2024-01-08T10:00:00",
            health_at_failure=0,
        )

        memory.record_npc_interaction(
            name="King",
            location="Castle",
            interaction_type="talk",
            trust_change=50,
            has_quest=True,
            timestamp="2024-01-08T11:00:00",
        )

        memory.update_location(
            name="Castle",
            category="settlement",
            had_combat=False,
            found_secret=True,
            found_treasure=True,
            died=False,
        )

        # Serialize and restore
        data = memory.to_dict()
        restored = AgentMemory.from_dict(data)

        # Verify failures
        assert len(restored.failures) == 1
        assert restored.failures[0].enemy_name == "Boss"

        # Verify NPC memories
        assert "King" in restored.npc_memories
        assert restored.npc_memories["King"].trust_level == 50

        # Verify location memories
        assert "Castle" in restored.location_memories
        assert restored.location_memories["Castle"].has_secrets is True

        # Verify dangerous enemies
        assert "Boss" in restored.dangerous_enemies
