"""Tests for quest world effects - connecting quest completion to WorldStateManager.

Spec tested:
- WorldEffect dataclass creation and validation
- Serialization round-trip for WorldEffect
- Quest completion applies world effects to WorldStateManager
- Integration test for is_area_cleared() after quest completion
"""

import pytest
from cli_rpg.models.quest import (
    Quest,
    QuestStatus,
    ObjectiveType,
    WorldEffect,
)
from cli_rpg.models.world_state import (
    WorldStateManager,
    WorldStateChangeType,
)


class TestWorldEffectDataclass:
    """Test WorldEffect dataclass creation and validation."""

    def test_create_basic_world_effect(self):
        """Test creating a WorldEffect with required fields."""
        effect = WorldEffect(
            effect_type="area_cleared",
            target="Goblin Cave",
            description="The goblin cave has been cleared of all hostiles.",
        )
        assert effect.effect_type == "area_cleared"
        assert effect.target == "Goblin Cave"
        assert effect.description == "The goblin cave has been cleared of all hostiles."
        assert effect.metadata == {}

    def test_create_world_effect_with_metadata(self):
        """Test creating a WorldEffect with metadata."""
        effect = WorldEffect(
            effect_type="location_transformed",
            target="Haunted Tower",
            description="The tower is no longer haunted.",
            metadata={"new_category": "ruins", "cleansed_by": "holy_ritual"},
        )
        assert effect.effect_type == "location_transformed"
        assert effect.metadata["new_category"] == "ruins"
        assert effect.metadata["cleansed_by"] == "holy_ritual"

    def test_world_effect_empty_target_raises(self):
        """Test that empty target raises ValueError."""
        with pytest.raises(ValueError, match="target cannot be empty"):
            WorldEffect(
                effect_type="area_cleared",
                target="",
                description="Some description",
            )

    def test_world_effect_whitespace_target_raises(self):
        """Test that whitespace-only target raises ValueError."""
        with pytest.raises(ValueError, match="target cannot be empty"):
            WorldEffect(
                effect_type="area_cleared",
                target="   ",
                description="Some description",
            )


class TestWorldEffectSerialization:
    """Test WorldEffect serialization round-trip."""

    def test_to_dict(self):
        """Test serializing WorldEffect to dictionary."""
        effect = WorldEffect(
            effect_type="boss_defeated",
            target="Dragon's Lair",
            description="The dragon has been slain.",
            metadata={"boss_name": "Scorchwing"},
        )
        data = effect.to_dict()
        assert data == {
            "effect_type": "boss_defeated",
            "target": "Dragon's Lair",
            "description": "The dragon has been slain.",
            "metadata": {"boss_name": "Scorchwing"},
        }

    def test_from_dict(self):
        """Test deserializing WorldEffect from dictionary."""
        data = {
            "effect_type": "npc_moved",
            "target": "Merchant Guild",
            "description": "The merchants have relocated to the new market.",
            "metadata": {"new_location": "Grand Bazaar"},
        }
        effect = WorldEffect.from_dict(data)
        assert effect.effect_type == "npc_moved"
        assert effect.target == "Merchant Guild"
        assert effect.description == "The merchants have relocated to the new market."
        assert effect.metadata["new_location"] == "Grand Bazaar"

    def test_serialization_round_trip(self):
        """Test that to_dict -> from_dict preserves all data."""
        original = WorldEffect(
            effect_type="location_transformed",
            target="Cursed Swamp",
            description="The curse has been lifted.",
            metadata={"new_category": "forest", "purified": True},
        )
        restored = WorldEffect.from_dict(original.to_dict())
        assert restored.effect_type == original.effect_type
        assert restored.target == original.target
        assert restored.description == original.description
        assert restored.metadata == original.metadata


class TestQuestWithWorldEffects:
    """Test Quest with world_effects field."""

    def test_quest_with_empty_world_effects(self):
        """Test that Quest has empty world_effects by default."""
        quest = Quest(
            name="Test Quest",
            description="A test quest.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
        )
        assert quest.world_effects == []

    def test_quest_with_world_effects(self):
        """Test creating Quest with world_effects."""
        effects = [
            WorldEffect(
                effect_type="area_cleared",
                target="Goblin Cave",
                description="The cave is now safe.",
            ),
        ]
        quest = Quest(
            name="Clear the Cave",
            description="Eliminate the goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            world_effects=effects,
        )
        assert len(quest.world_effects) == 1
        assert quest.world_effects[0].target == "Goblin Cave"

    def test_quest_serialization_with_world_effects(self):
        """Test Quest serialization includes world_effects."""
        effects = [
            WorldEffect(
                effect_type="boss_defeated",
                target="Crypt",
                description="The lich has been destroyed.",
                metadata={"boss_name": "Lich King"},
            ),
        ]
        quest = Quest(
            name="Defeat the Lich",
            description="Destroy the undead menace.",
            objective_type=ObjectiveType.KILL,
            target="lich",
            world_effects=effects,
        )
        data = quest.to_dict()
        assert "world_effects" in data
        assert len(data["world_effects"]) == 1
        assert data["world_effects"][0]["effect_type"] == "boss_defeated"

    def test_quest_deserialization_with_world_effects(self):
        """Test Quest deserialization restores world_effects."""
        effects = [
            WorldEffect(
                effect_type="location_transformed",
                target="Dark Temple",
                description="Light has returned.",
                metadata={"new_category": "temple"},
            ),
        ]
        quest = Quest(
            name="Purify Temple",
            description="Cleanse the corruption.",
            objective_type=ObjectiveType.EXPLORE,
            target="altar",
            world_effects=effects,
        )
        restored = Quest.from_dict(quest.to_dict())
        assert len(restored.world_effects) == 1
        assert restored.world_effects[0].effect_type == "location_transformed"
        assert restored.world_effects[0].target == "Dark Temple"
        assert restored.world_effects[0].metadata["new_category"] == "temple"


class TestWorldStateManagerQuestEffects:
    """Test WorldStateManager.record_quest_world_effect() method."""

    def test_record_quest_world_effect_area_cleared(self):
        """Test recording area_cleared effect from quest completion."""
        manager = WorldStateManager()
        effect = WorldEffect(
            effect_type="area_cleared",
            target="Bandit Camp",
            description="The bandits have been driven out.",
        )
        result = manager.record_quest_world_effect(
            effect=effect,
            quest_name="Clear the Camp",
            timestamp=100,
        )
        # Should return the effect description
        assert result is not None
        assert result == "The bandits have been driven out."

        # Should be queryable (via the AREA_CLEARED change also recorded)
        assert manager.is_area_cleared("Bandit Camp")

    def test_record_quest_world_effect_location_transformed(self):
        """Test recording location_transformed effect."""
        manager = WorldStateManager()
        effect = WorldEffect(
            effect_type="location_transformed",
            target="Haunted Manor",
            description="The spirits have been laid to rest.",
            metadata={"new_category": "ruins"},
        )
        result = manager.record_quest_world_effect(
            effect=effect,
            quest_name="Ghost Hunt",
            timestamp=50,
        )
        assert result is not None

        # Should be recorded as QUEST_WORLD_EFFECT type
        changes = manager.get_changes_by_type(WorldStateChangeType.QUEST_WORLD_EFFECT)
        assert len(changes) == 1
        assert changes[0].target == "Haunted Manor"
        assert changes[0].caused_by == "Ghost Hunt"

    def test_record_quest_world_effect_preserves_metadata(self):
        """Test that metadata from WorldEffect is preserved."""
        manager = WorldStateManager()
        effect = WorldEffect(
            effect_type="boss_defeated",
            target="Dragon Cave",
            description="Scorchwing has been slain.",
            metadata={"boss_name": "Scorchwing", "loot_tier": "legendary"},
        )
        manager.record_quest_world_effect(
            effect=effect,
            quest_name="Slay the Dragon",
            timestamp=200,
        )
        changes = manager.get_changes_by_type(WorldStateChangeType.QUEST_WORLD_EFFECT)
        assert len(changes) == 1
        # Original effect metadata should be in the change
        assert changes[0].metadata.get("effect_type") == "boss_defeated"
        assert changes[0].metadata.get("boss_name") == "Scorchwing"


class TestQuestCompletionAppliesEffects:
    """Integration test: quest completion applies world effects.

    This tests the integration point in main.py where quest completion
    triggers world state changes.
    """

    def test_is_area_cleared_after_quest_effect(self):
        """Test is_area_cleared() returns True after quest world effect."""
        manager = WorldStateManager()

        # Create a quest with area_cleared effect
        effect = WorldEffect(
            effect_type="area_cleared",
            target="Goblin Stronghold",
            description="The stronghold has been purged.",
        )

        # Before recording, area is not cleared
        assert not manager.is_area_cleared("Goblin Stronghold")

        # Record the effect (simulating quest completion)
        manager.record_quest_world_effect(
            effect=effect,
            quest_name="Assault on Stronghold",
            timestamp=150,
        )

        # After recording, area should be cleared
        assert manager.is_area_cleared("Goblin Stronghold")

    def test_multiple_quest_effects_recorded(self):
        """Test that multiple effects from same quest are recorded."""
        manager = WorldStateManager()

        effects = [
            WorldEffect(
                effect_type="area_cleared",
                target="Dark Tower",
                description="The tower is cleansed.",
            ),
            WorldEffect(
                effect_type="boss_defeated",
                target="Dark Tower",
                description="The shadow lord is vanquished.",
                metadata={"boss_name": "Shadow Lord"},
            ),
        ]

        for effect in effects:
            manager.record_quest_world_effect(
                effect=effect,
                quest_name="Conquer the Tower",
                timestamp=300,
            )

        # Both should be recorded as QUEST_WORLD_EFFECT
        # (area_cleared also adds an AREA_CLEARED change for backwards compat)
        quest_effects = manager.get_changes_by_type(WorldStateChangeType.QUEST_WORLD_EFFECT)
        assert len(quest_effects) == 2

        # Area should be cleared
        assert manager.is_area_cleared("Dark Tower")
