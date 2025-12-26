"""Tests for COLLECT quest target validation.

Tests that COLLECT quest targets are validated against the set of
obtainable items (shop items, loot drops, foraged items, etc.).
"""

import pytest
from cli_rpg.ai_service import AIService, AIGenerationError, OBTAINABLE_ITEMS


class TestObtainableItemsConstant:
    """Tests for OBTAINABLE_ITEMS constant exported from ai_service.py."""

    # Tests spec: Shop items must be obtainable
    def test_obtainable_items_contains_shop_items(self):
        """Verify shop items are in OBTAINABLE_ITEMS."""
        assert "health potion" in OBTAINABLE_ITEMS
        assert "iron sword" in OBTAINABLE_ITEMS
        assert "leather armor" in OBTAINABLE_ITEMS
        assert "torch" in OBTAINABLE_ITEMS
        assert "antidote" in OBTAINABLE_ITEMS
        assert "travel rations" in OBTAINABLE_ITEMS
        assert "lockpick" in OBTAINABLE_ITEMS
        assert "camping supplies" in OBTAINABLE_ITEMS
        assert "stamina potion" in OBTAINABLE_ITEMS
        assert "steel sword" in OBTAINABLE_ITEMS
        assert "chainmail" in OBTAINABLE_ITEMS
        assert "iron helmet" in OBTAINABLE_ITEMS
        assert "greater health potion" in OBTAINABLE_ITEMS
        assert "fine steel sword" in OBTAINABLE_ITEMS
        assert "plate armor" in OBTAINABLE_ITEMS

    # Tests spec: Loot drops must be obtainable
    def test_obtainable_items_contains_loot_drops(self):
        """Verify loot drop items are in OBTAINABLE_ITEMS."""
        assert "rusty sword" in OBTAINABLE_ITEMS
        assert "health potion" in OBTAINABLE_ITEMS
        assert "gold coin" in OBTAINABLE_ITEMS
        assert "iron dagger" in OBTAINABLE_ITEMS
        assert "worn armor" in OBTAINABLE_ITEMS
        assert "monster fang" in OBTAINABLE_ITEMS
        assert "strange key" in OBTAINABLE_ITEMS
        assert "gem stone" in OBTAINABLE_ITEMS

    # Tests spec: Forage items must be obtainable
    def test_obtainable_items_contains_forage_items(self):
        """Verify foraging items are in OBTAINABLE_ITEMS."""
        assert "herbs" in OBTAINABLE_ITEMS
        assert "wild berries" in OBTAINABLE_ITEMS
        assert "medicinal root" in OBTAINABLE_ITEMS
        assert "moonpetal flower" in OBTAINABLE_ITEMS

    # Tests spec: Hunt items must be obtainable
    def test_obtainable_items_contains_hunt_items(self):
        """Verify hunting items are in OBTAINABLE_ITEMS."""
        assert "raw meat" in OBTAINABLE_ITEMS
        assert "animal pelt" in OBTAINABLE_ITEMS
        assert "cooked meat" in OBTAINABLE_ITEMS

    # Tests spec: Gather items must be obtainable
    def test_obtainable_items_contains_gather_items(self):
        """Verify gathered resource items are in OBTAINABLE_ITEMS."""
        assert "wood" in OBTAINABLE_ITEMS
        assert "fiber" in OBTAINABLE_ITEMS
        assert "stone" in OBTAINABLE_ITEMS
        assert "iron ore" in OBTAINABLE_ITEMS

    # Tests spec: Crafted items must be obtainable
    def test_obtainable_items_contains_crafted_items(self):
        """Verify crafted items are in OBTAINABLE_ITEMS."""
        assert "torch" in OBTAINABLE_ITEMS
        assert "iron sword" in OBTAINABLE_ITEMS
        assert "rope" in OBTAINABLE_ITEMS
        assert "healing salve" in OBTAINABLE_ITEMS
        assert "bandage" in OBTAINABLE_ITEMS
        assert "wooden shield" in OBTAINABLE_ITEMS
        assert "stone hammer" in OBTAINABLE_ITEMS
        assert "iron armor" in OBTAINABLE_ITEMS

    # Tests spec: All items must be lowercase for case-insensitive matching
    def test_obtainable_items_all_lowercase(self):
        """Verify all items in OBTAINABLE_ITEMS are lowercase."""
        for item in OBTAINABLE_ITEMS:
            assert item == item.lower(), f"Expected lowercase: {item}"

    def test_is_a_frozenset(self):
        """Verify OBTAINABLE_ITEMS is a frozenset for O(1) lookups and immutability."""
        assert isinstance(OBTAINABLE_ITEMS, frozenset)


class TestCollectQuestValidation:
    """Tests for COLLECT quest target validation in _parse_quest_response."""

    # Tests spec: Valid COLLECT targets (obtainable items) should be accepted
    def test_valid_collect_target_accepted(self):
        """COLLECT quest with obtainable item target should parse successfully."""
        response = (
            '{"name":"Gather Potions","description":"Collect health potions",'
            '"objective_type":"collect","target":"Health Potion","target_count":3,'
            '"gold_reward":50,"xp_reward":100}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Health Potion"
        assert result["objective_type"] == "collect"

    # Tests spec: Invalid COLLECT targets (not obtainable) should be rejected
    def test_invalid_collect_target_rejected(self):
        """COLLECT quest with non-obtainable item target should raise AIGenerationError."""
        response = (
            '{"name":"Collect Scales","description":"Gather dragon scales",'
            '"objective_type":"collect","target":"Dragon Scales","target_count":5,'
            '"gold_reward":500,"xp_reward":1000}'
        )
        service = AIService.__new__(AIService)
        with pytest.raises(AIGenerationError, match="Invalid COLLECT quest target"):
            service._parse_quest_response(response, "Test NPC")

    # Tests spec: Target matching should be case-insensitive
    def test_collect_target_case_insensitive(self):
        """COLLECT quest target validation should be case-insensitive."""
        response = (
            '{"name":"Gather Herbs","description":"Collect healing herbs",'
            '"objective_type":"collect","target":"HEALTH POTION","target_count":2,'
            '"gold_reward":30,"xp_reward":60}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "HEALTH POTION"  # Original case preserved

    # Tests spec: KILL quests should still validate against VALID_ENEMY_TYPES
    def test_kill_quest_unchanged(self):
        """KILL quests should still validate against VALID_ENEMY_TYPES."""
        # Valid KILL quest should work
        valid_response = (
            '{"name":"Hunt Wolves","description":"Kill wolves",'
            '"objective_type":"kill","target":"Wolf","target_count":3,'
            '"gold_reward":50,"xp_reward":100}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(valid_response, "Test NPC")
        assert result["target"] == "Wolf"

        # Invalid KILL quest should fail
        invalid_response = (
            '{"name":"Hunt Dragons","description":"Slay dragon",'
            '"objective_type":"kill","target":"Dragon","target_count":1,'
            '"gold_reward":500,"xp_reward":1000}'
        )
        with pytest.raises(AIGenerationError, match="Invalid KILL quest target"):
            service._parse_quest_response(invalid_response, "Test NPC")

    # Tests spec: EXPLORE quests should still validate against valid_locations
    def test_explore_quest_unchanged(self):
        """EXPLORE quests should still validate against valid_locations when provided."""
        valid_locations = {"hidden cave", "ancient ruins", "dark forest"}

        # Valid EXPLORE quest should work
        valid_response = (
            '{"name":"Find Cave","description":"Explore the hidden cave",'
            '"objective_type":"explore","target":"Hidden Cave","target_count":1,'
            '"gold_reward":50,"xp_reward":100}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(valid_response, "Test NPC", valid_locations)
        assert result["target"] == "Hidden Cave"

        # Invalid EXPLORE quest should fail when valid_locations provided
        invalid_response = (
            '{"name":"Find Castle","description":"Explore the castle",'
            '"objective_type":"explore","target":"Unknown Castle","target_count":1,'
            '"gold_reward":50,"xp_reward":100}'
        )
        with pytest.raises(AIGenerationError, match="Invalid EXPLORE quest target"):
            service._parse_quest_response(invalid_response, "Test NPC", valid_locations)

    def test_collect_foraged_item_accepted(self):
        """COLLECT quest with foraged item should parse successfully."""
        response = (
            '{"name":"Gather Herbs","description":"Collect herbs from the wild",'
            '"objective_type":"collect","target":"Herbs","target_count":5,'
            '"gold_reward":25,"xp_reward":50}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Herbs"
        assert result["objective_type"] == "collect"

    def test_collect_crafted_item_accepted(self):
        """COLLECT quest with crafted item should parse successfully."""
        response = (
            '{"name":"Get Torches","description":"Bring me some torches",'
            '"objective_type":"collect","target":"Torch","target_count":3,'
            '"gold_reward":40,"xp_reward":80}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Torch"
        assert result["objective_type"] == "collect"

    def test_collect_loot_drop_accepted(self):
        """COLLECT quest with loot drop item should parse successfully."""
        response = (
            '{"name":"Find Coin","description":"Find gold coins",'
            '"objective_type":"collect","target":"Gold Coin","target_count":10,'
            '"gold_reward":100,"xp_reward":150}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Gold Coin"
        assert result["objective_type"] == "collect"
