"""Tests for content_request models.

Tests cover:
1. Request dataclass instantiation and field access
2. Response.from_dict() with complete data
3. Response.from_dict() with missing optional fields (defaults)
4. to_dict() serialization round-trip
"""

import pytest

from src.cli_rpg.models.content_request import (
    RoomContentRequest,
    NPCContentRequest,
    ItemContentRequest,
    QuestContentRequest,
    RoomContentResponse,
    NPCContentResponse,
    ItemContentResponse,
    QuestContentResponse,
)


class TestRoomContentRequest:
    """Tests for RoomContentRequest dataclass."""

    def test_instantiation_and_field_access(self):
        """Test creating request and accessing fields."""
        request = RoomContentRequest(
            room_type="boss_room",
            category="dungeon",
            connections=["north", "down"],
            is_entry=False,
            coordinates=(3, 2, -1),
        )

        assert request.room_type == "boss_room"
        assert request.category == "dungeon"
        assert request.connections == ["north", "down"]
        assert request.is_entry is False
        assert request.coordinates == (3, 2, -1)


class TestNPCContentRequest:
    """Tests for NPCContentRequest dataclass."""

    def test_instantiation_and_field_access(self):
        """Test creating request and accessing fields."""
        request = NPCContentRequest(
            role="merchant",
            category="cave",
            coordinates=(0, 0, 0),
        )

        assert request.role == "merchant"
        assert request.category == "cave"
        assert request.coordinates == (0, 0, 0)


class TestItemContentRequest:
    """Tests for ItemContentRequest dataclass."""

    def test_instantiation_and_field_access(self):
        """Test creating request and accessing fields."""
        request = ItemContentRequest(
            item_type="weapon",
            category="temple",
            coordinates=(5, 5, 2),
        )

        assert request.item_type == "weapon"
        assert request.category == "temple"
        assert request.coordinates == (5, 5, 2)


class TestQuestContentRequest:
    """Tests for QuestContentRequest dataclass."""

    def test_instantiation_and_field_access(self):
        """Test creating request and accessing fields."""
        request = QuestContentRequest(
            category="dungeon",
            coordinates=(1, 2, 3),
        )

        assert request.category == "dungeon"
        assert request.coordinates == (1, 2, 3)


class TestRoomContentResponse:
    """Tests for RoomContentResponse dataclass."""

    def test_from_dict_complete(self):
        """Test from_dict with all fields present."""
        data = {"name": "Obsidian Hall", "description": "Dark stone walls echo with whispers."}
        response = RoomContentResponse.from_dict(data)

        assert response.name == "Obsidian Hall"
        assert response.description == "Dark stone walls echo with whispers."

    def test_from_dict_missing_fields(self):
        """Test from_dict uses defaults for missing fields."""
        response = RoomContentResponse.from_dict({})

        assert response.name == "Unknown Chamber"
        assert response.description == "A mysterious room."

    def test_to_dict_roundtrip(self):
        """Test to_dict serialization round-trip."""
        original = RoomContentResponse(name="Crystal Cavern", description="Glittering gems.")
        data = original.to_dict()
        restored = RoomContentResponse.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description


class TestNPCContentResponse:
    """Tests for NPCContentResponse dataclass."""

    def test_from_dict_complete(self):
        """Test from_dict with all fields present."""
        data = {
            "name": "Elder Mira",
            "description": "A wise woman with silver hair.",
            "dialogue": "Welcome, traveler.",
        }
        response = NPCContentResponse.from_dict(data)

        assert response.name == "Elder Mira"
        assert response.description == "A wise woman with silver hair."
        assert response.dialogue == "Welcome, traveler."

    def test_from_dict_missing_fields(self):
        """Test from_dict uses defaults for missing fields."""
        response = NPCContentResponse.from_dict({})

        assert response.name == "Mysterious Stranger"
        assert response.description == "A person of unknown purpose."
        assert response.dialogue == "..."

    def test_to_dict_roundtrip(self):
        """Test to_dict serialization round-trip."""
        original = NPCContentResponse(
            name="Guard Thorne",
            description="Armed and vigilant.",
            dialogue="Halt! State your business.",
        )
        data = original.to_dict()
        restored = NPCContentResponse.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.dialogue == original.dialogue


class TestItemContentResponse:
    """Tests for ItemContentResponse dataclass."""

    def test_from_dict_weapon(self):
        """Test from_dict for a weapon item."""
        data = {
            "name": "Flame Sword",
            "description": "A blade wreathed in fire.",
            "item_type": "weapon",
            "damage_bonus": 15,
        }
        response = ItemContentResponse.from_dict(data)

        assert response.name == "Flame Sword"
        assert response.description == "A blade wreathed in fire."
        assert response.item_type == "weapon"
        assert response.damage_bonus == 15
        assert response.defense_bonus is None
        assert response.heal_amount is None

    def test_from_dict_armor(self):
        """Test from_dict for an armor item."""
        data = {
            "name": "Iron Shield",
            "description": "Sturdy metal protection.",
            "item_type": "armor",
            "defense_bonus": 10,
        }
        response = ItemContentResponse.from_dict(data)

        assert response.item_type == "armor"
        assert response.defense_bonus == 10
        assert response.damage_bonus is None

    def test_from_dict_consumable(self):
        """Test from_dict for a consumable item."""
        data = {
            "name": "Health Potion",
            "description": "Restores vitality.",
            "item_type": "consumable",
            "heal_amount": 25,
        }
        response = ItemContentResponse.from_dict(data)

        assert response.item_type == "consumable"
        assert response.heal_amount == 25

    def test_from_dict_missing_fields(self):
        """Test from_dict uses defaults for missing fields."""
        response = ItemContentResponse.from_dict({})

        assert response.name == "Unknown Item"
        assert response.description == "A mysterious object."
        assert response.item_type == "misc"
        assert response.damage_bonus is None
        assert response.defense_bonus is None
        assert response.heal_amount is None

    def test_to_dict_includes_only_present_bonuses(self):
        """Test to_dict only includes non-None optional fields."""
        response = ItemContentResponse(
            name="Sword",
            description="Sharp.",
            item_type="weapon",
            damage_bonus=10,
            defense_bonus=None,
            heal_amount=None,
        )
        data = response.to_dict()

        assert data == {
            "name": "Sword",
            "description": "Sharp.",
            "item_type": "weapon",
            "damage_bonus": 10,
        }
        assert "defense_bonus" not in data
        assert "heal_amount" not in data

    def test_to_dict_roundtrip(self):
        """Test to_dict serialization round-trip."""
        original = ItemContentResponse(
            name="Staff",
            description="Magic.",
            item_type="weapon",
            damage_bonus=5,
        )
        data = original.to_dict()
        restored = ItemContentResponse.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.item_type == original.item_type
        assert restored.damage_bonus == original.damage_bonus


class TestQuestContentResponse:
    """Tests for QuestContentResponse dataclass."""

    def test_from_dict_complete(self):
        """Test from_dict with all fields present."""
        data = {
            "name": "Slay the Dragon",
            "description": "A fearsome beast terrorizes the village.",
            "objective_type": "kill",
            "target": "Red Dragon",
        }
        response = QuestContentResponse.from_dict(data)

        assert response.name == "Slay the Dragon"
        assert response.description == "A fearsome beast terrorizes the village."
        assert response.objective_type == "kill"
        assert response.target == "Red Dragon"

    def test_from_dict_missing_fields(self):
        """Test from_dict uses defaults for missing fields."""
        response = QuestContentResponse.from_dict({})

        assert response.name == "A Simple Task"
        assert response.description == "Complete an objective."
        assert response.objective_type == "explore"
        assert response.target == "Destination"

    def test_to_dict_roundtrip(self):
        """Test to_dict serialization round-trip."""
        original = QuestContentResponse(
            name="Find the Amulet",
            description="Seek the lost treasure.",
            objective_type="collect",
            target="Golden Amulet",
        )
        data = original.to_dict()
        restored = QuestContentResponse.from_dict(data)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.objective_type == original.objective_type
        assert restored.target == original.target
