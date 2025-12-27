"""Tests for WorldStateManager and WorldStateChange - Issue 12."""

import pytest

from cli_rpg.models.world_state import (
    WorldStateChange,
    WorldStateChangeType,
    WorldStateManager,
)


class TestWorldStateChangeType:
    """Tests for WorldStateChangeType enum."""

    def test_all_change_types_exist(self):
        """All specified change types are defined."""
        assert WorldStateChangeType.LOCATION_DESTROYED.value == "location_destroyed"
        assert WorldStateChangeType.LOCATION_TRANSFORMED.value == "location_transformed"
        assert WorldStateChangeType.NPC_KILLED.value == "npc_killed"
        assert WorldStateChangeType.NPC_MOVED.value == "npc_moved"
        assert WorldStateChangeType.FACTION_ELIMINATED.value == "faction_eliminated"
        assert WorldStateChangeType.BOSS_DEFEATED.value == "boss_defeated"
        assert WorldStateChangeType.AREA_CLEARED.value == "area_cleared"
        assert WorldStateChangeType.QUEST_WORLD_EFFECT.value == "quest_world_effect"


class TestWorldStateChange:
    """Tests for WorldStateChange dataclass."""

    def test_creation_with_required_fields(self):
        """WorldStateChange can be created with required fields."""
        change = WorldStateChange(
            change_type=WorldStateChangeType.NPC_KILLED,
            target="Goblin Chief",
            description="The Goblin Chief was slain in combat",
            timestamp=100,
            caused_by="Goblin Camp Quest",
            metadata={"location": "Goblin Camp"},
        )
        assert change.change_type == WorldStateChangeType.NPC_KILLED
        assert change.target == "Goblin Chief"
        assert change.description == "The Goblin Chief was slain in combat"
        assert change.timestamp == 100
        assert change.caused_by == "Goblin Camp Quest"
        assert change.metadata == {"location": "Goblin Camp"}

    def test_creation_with_optional_caused_by(self):
        """WorldStateChange can be created with None caused_by."""
        change = WorldStateChange(
            change_type=WorldStateChangeType.BOSS_DEFEATED,
            target="Dragon",
            description="The dragon was slain",
            timestamp=50,
            caused_by=None,
            metadata={},
        )
        assert change.caused_by is None

    def test_validation_empty_target_raises(self):
        """WorldStateChange raises ValueError for empty target."""
        with pytest.raises(ValueError, match="target cannot be empty"):
            WorldStateChange(
                change_type=WorldStateChangeType.NPC_KILLED,
                target="",
                description="Test",
                timestamp=0,
                caused_by=None,
                metadata={},
            )

    def test_to_dict_serialization(self):
        """WorldStateChange.to_dict returns correct dict."""
        change = WorldStateChange(
            change_type=WorldStateChangeType.LOCATION_TRANSFORMED,
            target="Old Mill",
            description="The mill was rebuilt",
            timestamp=200,
            caused_by="Rebuild Quest",
            metadata={"new_category": "workshop"},
        )
        result = change.to_dict()
        assert result == {
            "change_type": "location_transformed",
            "target": "Old Mill",
            "description": "The mill was rebuilt",
            "timestamp": 200,
            "caused_by": "Rebuild Quest",
            "metadata": {"new_category": "workshop"},
        }

    def test_from_dict_deserialization(self):
        """WorldStateChange.from_dict restores from dict."""
        data = {
            "change_type": "area_cleared",
            "target": "Bandit Hideout",
            "description": "All bandits eliminated",
            "timestamp": 150,
            "caused_by": "Clear the Roads",
            "metadata": {"enemy_count": 5},
        }
        change = WorldStateChange.from_dict(data)
        assert change.change_type == WorldStateChangeType.AREA_CLEARED
        assert change.target == "Bandit Hideout"
        assert change.description == "All bandits eliminated"
        assert change.timestamp == 150
        assert change.caused_by == "Clear the Roads"
        assert change.metadata == {"enemy_count": 5}

    def test_from_dict_with_none_caused_by(self):
        """WorldStateChange.from_dict handles None caused_by."""
        data = {
            "change_type": "boss_defeated",
            "target": "Lich King",
            "description": "The Lich King is no more",
            "timestamp": 300,
            "caused_by": None,
            "metadata": {},
        }
        change = WorldStateChange.from_dict(data)
        assert change.caused_by is None


class TestWorldStateManagerRecording:
    """Tests for WorldStateManager recording methods."""

    def test_record_change_adds_to_history(self):
        """record_change adds a WorldStateChange to the manager."""
        manager = WorldStateManager()
        change = WorldStateChange(
            change_type=WorldStateChangeType.NPC_KILLED,
            target="Goblin Scout",
            description="Killed in combat",
            timestamp=10,
            caused_by=None,
            metadata={},
        )
        manager.record_change(change)
        assert len(manager._changes) == 1
        assert manager._changes[0] == change

    def test_record_location_transformed_creates_correct_change(self):
        """record_location_transformed creates a LOCATION_TRANSFORMED change."""
        manager = WorldStateManager()
        manager.record_location_transformed(
            name="Ruined Tower",
            new_category="fortress",
            desc="The tower has been restored",
            caused_by="Restoration Quest",
            timestamp=100,
        )
        assert len(manager._changes) == 1
        change = manager._changes[0]
        assert change.change_type == WorldStateChangeType.LOCATION_TRANSFORMED
        assert change.target == "Ruined Tower"
        assert change.description == "The tower has been restored"
        assert change.caused_by == "Restoration Quest"
        assert change.metadata["new_category"] == "fortress"

    def test_record_npc_killed_creates_correct_change(self):
        """record_npc_killed creates an NPC_KILLED change."""
        manager = WorldStateManager()
        manager.record_npc_killed(
            npc_name="Evil Wizard",
            location="Dark Tower",
            caused_by="Stop the Ritual",
            timestamp=200,
        )
        assert len(manager._changes) == 1
        change = manager._changes[0]
        assert change.change_type == WorldStateChangeType.NPC_KILLED
        assert change.target == "Evil Wizard"
        assert change.metadata["location"] == "Dark Tower"
        assert change.caused_by == "Stop the Ritual"

    def test_record_boss_defeated_creates_correct_change(self):
        """record_boss_defeated creates a BOSS_DEFEATED change."""
        manager = WorldStateManager()
        manager.record_boss_defeated(
            boss_name="Dragon Lord",
            location="Dragon's Lair",
            timestamp=300,
        )
        assert len(manager._changes) == 1
        change = manager._changes[0]
        assert change.change_type == WorldStateChangeType.BOSS_DEFEATED
        assert change.target == "Dragon Lord"
        assert change.metadata["location"] == "Dragon's Lair"

    def test_record_area_cleared_creates_correct_change(self):
        """record_area_cleared creates an AREA_CLEARED change."""
        manager = WorldStateManager()
        manager.record_area_cleared(
            location="Goblin Camp",
            caused_by="Clear the Camp",
            timestamp=50,
        )
        assert len(manager._changes) == 1
        change = manager._changes[0]
        assert change.change_type == WorldStateChangeType.AREA_CLEARED
        assert change.target == "Goblin Camp"
        assert change.caused_by == "Clear the Camp"


class TestWorldStateManagerQuerying:
    """Tests for WorldStateManager query methods."""

    @pytest.fixture
    def populated_manager(self):
        """Create a manager with various changes for testing."""
        manager = WorldStateManager()
        manager.record_npc_killed("Guard", "Castle", "Heist Quest", timestamp=10)
        manager.record_boss_defeated("Dark Knight", "Castle", timestamp=20)
        manager.record_area_cleared("Dungeon", "Clear Quest", timestamp=30)
        manager.record_npc_killed("Merchant", "Town Square", "Robbery", timestamp=40)
        manager.record_location_transformed("Old Mill", "workshop", "Rebuilt", "Build", timestamp=50)
        return manager

    def test_get_changes_for_location_filters_correctly(self, populated_manager):
        """get_changes_for_location returns only changes for that location."""
        castle_changes = populated_manager.get_changes_for_location("Castle")
        assert len(castle_changes) == 2
        targets = {c.target for c in castle_changes}
        assert "Guard" in targets
        assert "Dark Knight" in targets

    def test_get_changes_for_location_empty_when_no_matches(self, populated_manager):
        """get_changes_for_location returns empty list when no matches."""
        changes = populated_manager.get_changes_for_location("Unknown Place")
        assert changes == []

    def test_get_changes_by_type_filters_correctly(self, populated_manager):
        """get_changes_by_type returns only changes of that type."""
        npc_killed_changes = populated_manager.get_changes_by_type(WorldStateChangeType.NPC_KILLED)
        assert len(npc_killed_changes) == 2
        assert all(c.change_type == WorldStateChangeType.NPC_KILLED for c in npc_killed_changes)

    def test_is_location_destroyed_returns_true(self):
        """is_location_destroyed returns True when location was destroyed."""
        manager = WorldStateManager()
        change = WorldStateChange(
            change_type=WorldStateChangeType.LOCATION_DESTROYED,
            target="Cursed Village",
            description="The village was consumed by darkness",
            timestamp=100,
            caused_by="Dark Ritual",
            metadata={},
        )
        manager.record_change(change)
        assert manager.is_location_destroyed("Cursed Village") is True

    def test_is_location_destroyed_returns_false(self, populated_manager):
        """is_location_destroyed returns False when location not destroyed."""
        assert populated_manager.is_location_destroyed("Castle") is False

    def test_is_npc_killed_returns_true(self, populated_manager):
        """is_npc_killed returns True when NPC was killed."""
        assert populated_manager.is_npc_killed("Guard") is True
        assert populated_manager.is_npc_killed("Merchant") is True

    def test_is_npc_killed_returns_false(self, populated_manager):
        """is_npc_killed returns False when NPC not killed."""
        assert populated_manager.is_npc_killed("Alive NPC") is False

    def test_is_boss_defeated_returns_true(self, populated_manager):
        """is_boss_defeated returns True when boss at location was defeated."""
        assert populated_manager.is_boss_defeated("Castle") is True

    def test_is_boss_defeated_returns_false(self, populated_manager):
        """is_boss_defeated returns False when no boss defeated at location."""
        assert populated_manager.is_boss_defeated("Dungeon") is False

    def test_is_area_cleared_returns_true(self, populated_manager):
        """is_area_cleared returns True when area was cleared."""
        assert populated_manager.is_area_cleared("Dungeon") is True

    def test_is_area_cleared_returns_false(self, populated_manager):
        """is_area_cleared returns False when area not cleared."""
        assert populated_manager.is_area_cleared("Castle") is False


class TestWorldStateManagerSerialization:
    """Tests for WorldStateManager serialization."""

    def test_to_dict_includes_all_changes(self):
        """to_dict includes all recorded changes."""
        manager = WorldStateManager()
        manager.record_npc_killed("Goblin", "Forest", "Hunt", timestamp=10)
        manager.record_boss_defeated("Troll", "Cave", timestamp=20)

        result = manager.to_dict()
        assert "changes" in result
        assert len(result["changes"]) == 2

    def test_from_dict_restores_all_changes(self):
        """from_dict restores all changes correctly."""
        data = {
            "changes": [
                {
                    "change_type": "npc_killed",
                    "target": "Goblin",
                    "description": "Goblin was killed",
                    "timestamp": 10,
                    "caused_by": "Hunt",
                    "metadata": {"location": "Forest"},
                },
                {
                    "change_type": "boss_defeated",
                    "target": "Troll",
                    "description": "Troll was defeated at Cave",
                    "timestamp": 20,
                    "caused_by": None,
                    "metadata": {"location": "Cave"},
                },
            ]
        }
        manager = WorldStateManager.from_dict(data)
        assert len(manager._changes) == 2
        assert manager.is_npc_killed("Goblin")
        assert manager.is_boss_defeated("Cave")

    def test_from_dict_backward_compatibility_empty(self):
        """from_dict handles empty/missing data gracefully."""
        # Empty dict
        manager = WorldStateManager.from_dict({})
        assert len(manager._changes) == 0

        # None
        manager = WorldStateManager.from_dict(None)
        assert len(manager._changes) == 0

    def test_round_trip_serialization(self):
        """Changes survive serialization round-trip."""
        original = WorldStateManager()
        original.record_npc_killed("Guard", "Castle", "Quest", timestamp=100)
        original.record_area_cleared("Dungeon", "Clear", timestamp=200)

        data = original.to_dict()
        restored = WorldStateManager.from_dict(data)

        assert restored.is_npc_killed("Guard")
        assert restored.is_area_cleared("Dungeon")
        assert len(restored._changes) == len(original._changes)
