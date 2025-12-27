"""Tests for NPC character arc model (Issue 13).

Tests NPC arc progression based on player interactions:
- Arc stages (STRANGER → DEVOTED or STRANGER → ENEMY paths)
- Interaction types and recording
- Serialization/deserialization
- Integration with NPC model
"""
import pytest

from cli_rpg.models.npc_arc import (
    NPCArcStage,
    InteractionType,
    NPCInteraction,
    NPCArc,
)
from cli_rpg.models.npc import NPC


# === TestNPCArcStage ===
# Spec: NPCArcStage enum with positive (STRANGER→DEVOTED) and negative (WARY→ENEMY) paths


class TestNPCArcStage:
    """Tests for NPCArcStage enum values."""

    def test_arc_stage_stranger_exists(self):
        """STRANGER enum exists with value 'stranger'."""
        assert NPCArcStage.STRANGER.value == "stranger"

    def test_arc_stage_acquaintance_exists(self):
        """ACQUAINTANCE enum exists with value 'acquaintance'."""
        assert NPCArcStage.ACQUAINTANCE.value == "acquaintance"

    def test_arc_stage_trusted_exists(self):
        """TRUSTED enum exists with value 'trusted'."""
        assert NPCArcStage.TRUSTED.value == "trusted"

    def test_arc_stage_devoted_exists(self):
        """DEVOTED enum exists with value 'devoted'."""
        assert NPCArcStage.DEVOTED.value == "devoted"

    def test_arc_stage_wary_exists(self):
        """WARY enum exists with value 'wary'."""
        assert NPCArcStage.WARY.value == "wary"

    def test_arc_stage_hostile_exists(self):
        """HOSTILE enum exists with value 'hostile'."""
        assert NPCArcStage.HOSTILE.value == "hostile"

    def test_arc_stage_enemy_exists(self):
        """ENEMY enum exists with value 'enemy'."""
        assert NPCArcStage.ENEMY.value == "enemy"


# === TestInteractionType ===
# Spec: InteractionType enum for tracking player-NPC interaction types


class TestInteractionType:
    """Tests for InteractionType enum values."""

    def test_interaction_type_talked_exists(self):
        """TALKED enum exists with value 'talked'."""
        assert InteractionType.TALKED.value == "talked"

    def test_interaction_type_helped_quest_exists(self):
        """HELPED_QUEST enum exists with value 'helped_quest'."""
        assert InteractionType.HELPED_QUEST.value == "helped_quest"

    def test_interaction_type_failed_quest_exists(self):
        """FAILED_QUEST enum exists with value 'failed_quest'."""
        assert InteractionType.FAILED_QUEST.value == "failed_quest"

    def test_interaction_type_intimidated_exists(self):
        """INTIMIDATED enum exists with value 'intimidated'."""
        assert InteractionType.INTIMIDATED.value == "intimidated"

    def test_interaction_type_bribed_exists(self):
        """BRIBED enum exists with value 'bribed'."""
        assert InteractionType.BRIBED.value == "bribed"

    def test_interaction_type_defended_exists(self):
        """DEFENDED enum exists with value 'defended'."""
        assert InteractionType.DEFENDED.value == "defended"

    def test_interaction_type_attacked_exists(self):
        """ATTACKED enum exists with value 'attacked'."""
        assert InteractionType.ATTACKED.value == "attacked"

    def test_interaction_type_gifted_exists(self):
        """GIFTED enum exists with value 'gifted'."""
        assert InteractionType.GIFTED.value == "gifted"


# === TestNPCInteraction ===
# Spec: NPCInteraction dataclass stores type, delta, description, timestamp


class TestNPCInteraction:
    """Tests for NPCInteraction dataclass."""

    def test_interaction_creation(self):
        """NPCInteraction stores type, delta, description, timestamp."""
        interaction = NPCInteraction(
            interaction_type=InteractionType.TALKED,
            points_delta=2,
            description="Had a friendly chat",
            timestamp=100,
        )
        assert interaction.interaction_type == InteractionType.TALKED
        assert interaction.points_delta == 2
        assert interaction.description == "Had a friendly chat"
        assert interaction.timestamp == 100

    def test_interaction_to_dict(self):
        """NPCInteraction serializes correctly to dict."""
        interaction = NPCInteraction(
            interaction_type=InteractionType.HELPED_QUEST,
            points_delta=15,
            description="Completed the quest",
            timestamp=200,
        )
        data = interaction.to_dict()
        assert data["interaction_type"] == "helped_quest"
        assert data["points_delta"] == 15
        assert data["description"] == "Completed the quest"
        assert data["timestamp"] == 200

    def test_interaction_from_dict(self):
        """NPCInteraction deserializes correctly from dict."""
        data = {
            "interaction_type": "failed_quest",
            "points_delta": -10,
            "description": "Failed to save the village",
            "timestamp": 300,
        }
        interaction = NPCInteraction.from_dict(data)
        assert interaction.interaction_type == InteractionType.FAILED_QUEST
        assert interaction.points_delta == -10
        assert interaction.description == "Failed to save the village"
        assert interaction.timestamp == 300


# === TestNPCArc ===
# Spec: NPCArc tracks arc_points (-100 to 100), interactions, computes stage


class TestNPCArc:
    """Tests for NPCArc dataclass."""

    def test_arc_default_values(self):
        """NPCArc has arc_points=0, interactions=[], stage=STRANGER by default."""
        arc = NPCArc()
        assert arc.arc_points == 0
        assert arc.interactions == []
        assert arc.get_stage() == NPCArcStage.STRANGER

    def test_arc_get_stage_stranger(self):
        """0-24 points returns STRANGER stage."""
        for points in [0, 12, 24]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.STRANGER

    def test_arc_get_stage_acquaintance(self):
        """25-49 points returns ACQUAINTANCE stage."""
        for points in [25, 37, 49]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.ACQUAINTANCE

    def test_arc_get_stage_trusted(self):
        """50-74 points returns TRUSTED stage."""
        for points in [50, 62, 74]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.TRUSTED

    def test_arc_get_stage_devoted(self):
        """75-100 points returns DEVOTED stage."""
        for points in [75, 88, 100]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.DEVOTED

    def test_arc_get_stage_wary(self):
        """-1 to -24 points returns WARY stage."""
        for points in [-1, -12, -24]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.WARY

    def test_arc_get_stage_hostile(self):
        """-25 to -49 points returns HOSTILE stage."""
        for points in [-25, -37, -49]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.HOSTILE

    def test_arc_get_stage_enemy(self):
        """-50 to -100 points returns ENEMY stage."""
        for points in [-50, -75, -100]:
            arc = NPCArc(arc_points=points)
            assert arc.get_stage() == NPCArcStage.ENEMY

    def test_arc_record_interaction_adds_points(self):
        """record_interaction increases arc_points correctly."""
        arc = NPCArc()
        arc.record_interaction(InteractionType.TALKED, 5)
        assert arc.arc_points == 5
        arc.record_interaction(InteractionType.GIFTED, 10)
        assert arc.arc_points == 15

    def test_arc_record_interaction_logs_event(self):
        """record_interaction adds interaction to history."""
        arc = NPCArc()
        arc.record_interaction(
            InteractionType.DEFENDED,
            20,
            description="Saved from bandits",
            timestamp=500,
        )
        assert len(arc.interactions) == 1
        assert arc.interactions[0].interaction_type == InteractionType.DEFENDED
        assert arc.interactions[0].points_delta == 20
        assert arc.interactions[0].description == "Saved from bandits"
        assert arc.interactions[0].timestamp == 500

    def test_arc_points_clamped_max(self):
        """Arc points are capped at 100."""
        arc = NPCArc(arc_points=95)
        arc.record_interaction(InteractionType.HELPED_QUEST, 20)
        assert arc.arc_points == 100

    def test_arc_points_clamped_min(self):
        """Arc points are capped at -100."""
        arc = NPCArc(arc_points=-95)
        arc.record_interaction(InteractionType.ATTACKED, -20)
        assert arc.arc_points == -100

    def test_arc_to_dict(self):
        """NPCArc serializes arc_points and interactions correctly."""
        arc = NPCArc(arc_points=30)
        arc.record_interaction(InteractionType.TALKED, 5, "Said hello", 100)
        data = arc.to_dict()
        assert data["arc_points"] == 35  # 30 + 5
        assert len(data["interactions"]) == 1
        assert data["interactions"][0]["interaction_type"] == "talked"

    def test_arc_from_dict(self):
        """NPCArc deserializes correctly from dict."""
        data = {
            "arc_points": 45,
            "interactions": [
                {
                    "interaction_type": "gifted",
                    "points_delta": 10,
                    "description": "Gave flowers",
                    "timestamp": 200,
                }
            ],
        }
        arc = NPCArc.from_dict(data)
        assert arc.arc_points == 45
        assert len(arc.interactions) == 1
        assert arc.interactions[0].interaction_type == InteractionType.GIFTED

    def test_arc_roundtrip(self):
        """NPCArc survives save/load cycle (serialization roundtrip)."""
        original = NPCArc(arc_points=50)
        original.record_interaction(InteractionType.HELPED_QUEST, 15, "Saved them", 300)
        original.record_interaction(InteractionType.TALKED, 2, "Chatted", 400)

        data = original.to_dict()
        restored = NPCArc.from_dict(data)

        assert restored.arc_points == original.arc_points
        assert len(restored.interactions) == len(original.interactions)
        assert restored.get_stage() == original.get_stage()


# === TestNPCIntegration ===
# Spec: NPC model has optional arc field with backward compatibility


class TestNPCIntegration:
    """Tests for NPC arc field integration."""

    def test_npc_arc_field_optional(self):
        """NPC works without arc field (backward compatibility)."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC",
            dialogue="Hello there!",
        )
        assert npc.arc is None

    def test_npc_arc_serialization(self):
        """NPC with arc serializes correctly."""
        arc = NPCArc(arc_points=25)
        arc.record_interaction(InteractionType.TALKED, 5)
        npc = NPC(
            name="Friendly NPC",
            description="A friendly NPC",
            dialogue="Welcome!",
            arc=arc,
        )
        data = npc.to_dict()
        assert data["arc"] is not None
        assert data["arc"]["arc_points"] == 30  # 25 + 5

    def test_npc_arc_deserialization(self):
        """NPC with arc deserializes correctly."""
        data = {
            "name": "Arc NPC",
            "description": "NPC with arc",
            "dialogue": "I remember you!",
            "arc": {
                "arc_points": 60,
                "interactions": [],
            },
        }
        npc = NPC.from_dict(data)
        assert npc.arc is not None
        assert npc.arc.arc_points == 60
        assert npc.arc.get_stage() == NPCArcStage.TRUSTED

    def test_npc_backward_compat(self):
        """Old saves without arc field load correctly (arc is None)."""
        data = {
            "name": "Old NPC",
            "description": "From old save",
            "dialogue": "Hello from the past!",
            # No arc field - simulating old save
        }
        npc = NPC.from_dict(data)
        assert npc.arc is None
