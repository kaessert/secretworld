"""Tests for NPC relationship model.

Tests the NPCRelationship model and RelationshipType enum.
"""
import pytest
from cli_rpg.models.npc_relationship import NPCRelationship, RelationshipType


class TestRelationshipType:
    """Tests for RelationshipType enum - tests spec: NPC Relationship Types."""

    def test_relationship_type_family_exists(self):
        """RelationshipType.FAMILY exists."""
        assert RelationshipType.FAMILY.value == "family"

    def test_relationship_type_friend_exists(self):
        """RelationshipType.FRIEND exists."""
        assert RelationshipType.FRIEND.value == "friend"

    def test_relationship_type_rival_exists(self):
        """RelationshipType.RIVAL exists."""
        assert RelationshipType.RIVAL.value == "rival"

    def test_relationship_type_mentor_exists(self):
        """RelationshipType.MENTOR exists."""
        assert RelationshipType.MENTOR.value == "mentor"

    def test_relationship_type_employer_exists(self):
        """RelationshipType.EMPLOYER exists."""
        assert RelationshipType.EMPLOYER.value == "employer"

    def test_relationship_type_acquaintance_exists(self):
        """RelationshipType.ACQUAINTANCE exists."""
        assert RelationshipType.ACQUAINTANCE.value == "acquaintance"


class TestNPCRelationship:
    """Tests for NPCRelationship model - tests spec: NPC Relationship Model."""

    def test_create_relationship_basic(self):
        """NPCRelationship can be created with required fields."""
        rel = NPCRelationship(
            target_npc="Elder Mira",
            relationship_type=RelationshipType.FAMILY,
        )
        assert rel.target_npc == "Elder Mira"
        assert rel.relationship_type == RelationshipType.FAMILY
        assert rel.trust_level == 50  # Default
        assert rel.description is None  # Default

    def test_create_relationship_all_fields(self):
        """NPCRelationship can be created with all fields."""
        rel = NPCRelationship(
            target_npc="Master Chen",
            relationship_type=RelationshipType.MENTOR,
            trust_level=85,
            description="former martial arts teacher",
        )
        assert rel.target_npc == "Master Chen"
        assert rel.relationship_type == RelationshipType.MENTOR
        assert rel.trust_level == 85
        assert rel.description == "former martial arts teacher"

    def test_trust_level_clamp_above_100(self):
        """Trust level is clamped to 100 when exceeding max."""
        rel = NPCRelationship(
            target_npc="Test NPC",
            relationship_type=RelationshipType.FRIEND,
            trust_level=150,
        )
        assert rel.trust_level == 100

    def test_trust_level_clamp_below_1(self):
        """Trust level is clamped to 1 when below min."""
        rel = NPCRelationship(
            target_npc="Test NPC",
            relationship_type=RelationshipType.RIVAL,
            trust_level=0,
        )
        assert rel.trust_level == 1

    def test_trust_level_clamp_negative(self):
        """Trust level is clamped to 1 when negative."""
        rel = NPCRelationship(
            target_npc="Test NPC",
            relationship_type=RelationshipType.RIVAL,
            trust_level=-50,
        )
        assert rel.trust_level == 1

    def test_to_dict_serialization(self):
        """NPCRelationship serializes to dictionary correctly."""
        rel = NPCRelationship(
            target_npc="Elder Mira",
            relationship_type=RelationshipType.FAMILY,
            trust_level=75,
            description="sister",
        )
        data = rel.to_dict()
        assert data == {
            "target_npc": "Elder Mira",
            "relationship_type": "family",
            "trust_level": 75,
            "description": "sister",
        }

    def test_to_dict_without_description(self):
        """NPCRelationship serializes without description (None)."""
        rel = NPCRelationship(
            target_npc="Guard Bob",
            relationship_type=RelationshipType.ACQUAINTANCE,
        )
        data = rel.to_dict()
        assert data == {
            "target_npc": "Guard Bob",
            "relationship_type": "acquaintance",
            "trust_level": 50,
            "description": None,
        }

    def test_from_dict_deserialization(self):
        """NPCRelationship deserializes from dictionary correctly."""
        data = {
            "target_npc": "Master Chen",
            "relationship_type": "mentor",
            "trust_level": 90,
            "description": "former teacher",
        }
        rel = NPCRelationship.from_dict(data)
        assert rel.target_npc == "Master Chen"
        assert rel.relationship_type == RelationshipType.MENTOR
        assert rel.trust_level == 90
        assert rel.description == "former teacher"

    def test_from_dict_without_optional_fields(self):
        """NPCRelationship deserializes with missing optional fields."""
        data = {
            "target_npc": "Rival Jake",
            "relationship_type": "rival",
        }
        rel = NPCRelationship.from_dict(data)
        assert rel.target_npc == "Rival Jake"
        assert rel.relationship_type == RelationshipType.RIVAL
        assert rel.trust_level == 50  # Default
        assert rel.description is None  # Default

    def test_roundtrip_serialization(self):
        """NPCRelationship survives roundtrip serialization."""
        original = NPCRelationship(
            target_npc="Merchant Guildmaster",
            relationship_type=RelationshipType.EMPLOYER,
            trust_level=65,
            description="current employer",
        )
        data = original.to_dict()
        restored = NPCRelationship.from_dict(data)
        assert restored.target_npc == original.target_npc
        assert restored.relationship_type == original.relationship_type
        assert restored.trust_level == original.trust_level
        assert restored.description == original.description
