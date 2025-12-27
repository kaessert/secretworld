"""Tests for enhanced NPC generation with shop inventory and faction support."""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.ai_config import DEFAULT_NPC_PROMPT_MINIMAL
from cli_rpg.ai_service import AIService
from cli_rpg.ai_world import _create_npcs_from_data
from cli_rpg.models.npc import NPC
from cli_rpg.models.item import ItemType


def create_mock_ai_service():
    """Create a mock AIService for testing _parse_npcs."""
    # Mock the service and its config to avoid initialization issues
    service = MagicMock(spec=AIService)
    # Bind the real methods to our mock
    service._parse_npcs = AIService._parse_npcs.__get__(service, AIService)
    service._parse_shop_inventory = AIService._parse_shop_inventory.__get__(service, AIService)
    return service


class TestPromptEnhancements:
    """Tests for verifying the NPC prompt requests correct count and roles."""

    def test_prompt_requests_three_to_five_npcs(self):
        """Verify prompt requests 3-5 NPCs instead of 1-2."""
        # The plan specifies expanding from 1-2 to 3-5 NPCs
        assert "3-5 NPCs" in DEFAULT_NPC_PROMPT_MINIMAL or "3 to 5 NPCs" in DEFAULT_NPC_PROMPT_MINIMAL
        # Ensure we're not still using the old 1-2 count for NPCs (not in other contexts like "1-200 chars")
        assert "1-2 NPCs" not in DEFAULT_NPC_PROMPT_MINIMAL

    def test_prompt_includes_all_six_roles(self):
        """Verify prompt includes all 6 roles: villager, merchant, quest_giver, guard, traveler, innkeeper."""
        expected_roles = ["villager", "merchant", "quest_giver", "guard", "traveler", "innkeeper"]
        for role in expected_roles:
            assert role in DEFAULT_NPC_PROMPT_MINIMAL, f"Role '{role}' not found in prompt"


class TestNPCParsing:
    """Tests for parsing shop_inventory and faction from AI responses."""

    def test_parse_npc_with_shop_inventory(self):
        """Verify shop inventory with valid items is parsed correctly."""
        service = create_mock_ai_service()

        npcs_data = [{
            "name": "Marcus the Armorer",
            "description": "A burly blacksmith",
            "dialogue": "Looking for something sturdy?",
            "role": "merchant",
            "shop_inventory": [
                {"name": "Iron Sword", "price": 80},
                {"name": "Steel Shield", "price": 120}
            ]
        }]

        result = service._parse_npcs(npcs_data, "Test Town")

        assert len(result) == 1
        assert result[0]["name"] == "Marcus the Armorer"
        assert "shop_inventory" in result[0]
        assert len(result[0]["shop_inventory"]) == 2
        assert result[0]["shop_inventory"][0]["name"] == "Iron Sword"
        assert result[0]["shop_inventory"][0]["price"] == 80

    def test_parse_npc_with_empty_shop_inventory(self):
        """Verify empty shop inventory is handled gracefully."""
        service = create_mock_ai_service()

        npcs_data = [{
            "name": "Empty Merchant",
            "description": "A merchant with nothing to sell",
            "dialogue": "Hello",
            "role": "merchant",
            "shop_inventory": []
        }]

        result = service._parse_npcs(npcs_data, "Test Town")

        assert len(result) == 1
        # Empty inventory should be passed through (creation handles fallback)
        assert result[0]["shop_inventory"] == []

    def test_parse_npc_with_invalid_shop_item(self):
        """Verify malformed shop items are skipped."""
        service = create_mock_ai_service()

        npcs_data = [{
            "name": "Bad Merchant",
            "description": "A merchant with bad inventory",
            "dialogue": "Hello",
            "role": "merchant",
            "shop_inventory": [
                {"name": "Valid Item", "price": 50},
                {"name": "No Price Item"},  # Missing price
                {"price": 100},  # Missing name
                {"name": "", "price": 50},  # Empty name
                {"name": "Negative Price", "price": -10},  # Negative price
            ]
        }]

        result = service._parse_npcs(npcs_data, "Test Town")

        assert len(result) == 1
        # Only the valid item should remain
        assert len(result[0]["shop_inventory"]) == 1
        assert result[0]["shop_inventory"][0]["name"] == "Valid Item"

    def test_parse_npc_with_faction(self):
        """Verify faction field is parsed correctly."""
        service = create_mock_ai_service()

        npcs_data = [{
            "name": "Guild Guard",
            "description": "A stern-looking guard",
            "dialogue": "Move along",
            "role": "guard",
            "faction": "Merchant Guild"
        }]

        result = service._parse_npcs(npcs_data, "Test Town")

        assert len(result) == 1
        assert result[0]["faction"] == "Merchant Guild"

    def test_parse_npc_without_faction(self):
        """Verify NPC without faction defaults to None."""
        service = create_mock_ai_service()

        npcs_data = [{
            "name": "Simple Villager",
            "description": "A humble villager",
            "dialogue": "Hello",
            "role": "villager"
        }]

        result = service._parse_npcs(npcs_data, "Test Town")

        assert len(result) == 1
        assert result[0].get("faction") is None

    def test_parse_npc_with_new_roles(self):
        """Verify new roles (guard, traveler, innkeeper) are accepted."""
        service = create_mock_ai_service()

        npcs_data = [
            {"name": "Town Guard", "description": "A vigilant guard", "dialogue": "Halt!", "role": "guard"},
            {"name": "Weary Traveler", "description": "A dusty traveler", "dialogue": "Hello", "role": "traveler"},
            {"name": "Jolly Innkeeper", "description": "A friendly innkeeper", "dialogue": "Welcome!", "role": "innkeeper"},
        ]

        result = service._parse_npcs(npcs_data, "Test Town")

        assert len(result) == 3
        assert result[0]["role"] == "guard"
        assert result[1]["role"] == "traveler"
        assert result[2]["role"] == "innkeeper"


class TestNPCCreation:
    """Tests for creating NPC objects with AI shop inventory and faction."""

    def test_merchant_gets_ai_shop_inventory(self):
        """Verify merchant NPC gets AI-generated shop items when valid."""
        npc_data = [{
            "name": "Marcus the Armorer",
            "description": "A burly blacksmith",
            "dialogue": "Looking for something sturdy?",
            "role": "merchant",
            "shop_inventory": [
                {"name": "Iron Sword", "price": 80},
                {"name": "Steel Shield", "price": 120}
            ]
        }]

        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        merchant = npcs[0]
        assert merchant.is_merchant
        assert merchant.shop is not None
        # Verify AI items were used
        item_names = [si.item.name for si in merchant.shop.inventory]
        assert "Iron Sword" in item_names
        assert "Steel Shield" in item_names
        # Verify prices
        iron_sword = merchant.shop.find_item_by_name("Iron Sword")
        assert iron_sword is not None
        assert iron_sword.buy_price == 80

    def test_merchant_falls_back_to_default_shop(self):
        """Verify merchant falls back to default shop when AI inventory is empty/invalid."""
        npc_data = [{
            "name": "Empty Merchant",
            "description": "A merchant with no wares",
            "dialogue": "Sorry, nothing in stock",
            "role": "merchant",
            "shop_inventory": []  # Empty inventory
        }]

        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        merchant = npcs[0]
        assert merchant.is_merchant
        assert merchant.shop is not None
        # Should have default items
        assert len(merchant.shop.inventory) >= 1
        # Default shop includes Health Potion
        item_names = [si.item.name for si in merchant.shop.inventory]
        assert "Health Potion" in item_names

    def test_npc_faction_assignment(self):
        """Verify faction is passed to NPC object."""
        npc_data = [{
            "name": "Guild Guard",
            "description": "A stern-looking guard",
            "dialogue": "Move along",
            "role": "guard",
            "faction": "Merchant Guild"
        }]

        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        guard = npcs[0]
        assert guard.faction == "Merchant Guild"

    def test_npc_without_faction_defaults_to_none(self):
        """Verify NPC without faction field defaults to None."""
        npc_data = [{
            "name": "Simple Villager",
            "description": "A humble villager",
            "dialogue": "Hello",
            "role": "villager"
        }]

        npcs = _create_npcs_from_data(npc_data)

        assert len(npcs) == 1
        villager = npcs[0]
        assert villager.faction is None


class TestNPCFactionSerialization:
    """Tests for NPC faction serialization (to_dict/from_dict)."""

    def test_npc_faction_serialization_roundtrip(self):
        """Verify faction field survives to_dict/from_dict roundtrip."""
        original = NPC(
            name="Guild Guard",
            description="A stern-looking guard",
            dialogue="Move along",
            faction="Merchant Guild"
        )

        data = original.to_dict()
        assert data["faction"] == "Merchant Guild"

        restored = NPC.from_dict(data)
        assert restored.faction == "Merchant Guild"

    def test_npc_without_faction_serialization(self):
        """Verify NPC without faction serializes as None and restores correctly."""
        original = NPC(
            name="Simple Villager",
            description="A humble villager",
            dialogue="Hello"
        )

        data = original.to_dict()
        assert data.get("faction") is None

        restored = NPC.from_dict(data)
        assert restored.faction is None

    def test_backward_compatibility_missing_faction(self):
        """Verify old saved data without faction field loads correctly."""
        # Simulate old save data without faction field
        old_data = {
            "name": "Old NPC",
            "description": "From old save",
            "dialogue": "Hello"
        }

        npc = NPC.from_dict(old_data)
        assert npc.faction is None
