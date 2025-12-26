"""Tests for TALK quest target validation.

Tests spec: TALK quest targets must match an existing NPC name (case-insensitive)
when valid_npcs is provided. When valid_npcs is None, validation is skipped.
"""

import pytest
from cli_rpg.ai_service import AIService, AIGenerationError


class TestTalkQuestValidation:
    """Tests for TALK quest target validation in _parse_quest_response."""

    # Tests spec: TALK quest targets must match an existing NPC name
    def test_valid_talk_target_accepted(self):
        """TALK quest with existing NPC name parses successfully."""
        response = (
            '{"name":"Seek Counsel","description":"Talk to the merchant",'
            '"objective_type":"talk","target":"Merchant","target_count":1,'
            '"gold_reward":25,"xp_reward":50}'
        )
        valid_npcs = {"merchant", "village elder", "blacksmith"}
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(
            response, "Test NPC", valid_npcs=valid_npcs
        )
        assert result["target"] == "Merchant"
        assert result["objective_type"] == "talk"

    # Tests spec: Invalid TALK targets (not in valid_npcs) should be rejected
    def test_invalid_talk_target_rejected(self):
        """TALK quest with non-existent NPC raises AIGenerationError."""
        response = (
            '{"name":"Seek Wisdom","description":"Talk to the ancient mage",'
            '"objective_type":"talk","target":"Elder Mage Aldous","target_count":1,'
            '"gold_reward":100,"xp_reward":200}'
        )
        valid_npcs = {"merchant", "village elder", "blacksmith"}
        service = AIService.__new__(AIService)
        with pytest.raises(AIGenerationError, match="Invalid TALK quest target"):
            service._parse_quest_response(
                response, "Test NPC", valid_npcs=valid_npcs
            )

    # Tests spec: Target matching should be case-insensitive
    def test_talk_target_case_insensitive(self):
        """TALK quest target validation should be case-insensitive."""
        response = (
            '{"name":"Meet the Elder","description":"Speak with the village elder",'
            '"objective_type":"talk","target":"Village Elder","target_count":1,'
            '"gold_reward":30,"xp_reward":60}'
        )
        # Valid NPCs stored in lowercase (as spec says)
        valid_npcs = {"merchant", "village elder", "blacksmith"}
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(
            response, "Test NPC", valid_npcs=valid_npcs
        )
        assert result["target"] == "Village Elder"  # Original case preserved

    # Tests spec: Validation skipped when valid_npcs=None (backward compat)
    def test_talk_validation_skipped_when_no_npcs(self):
        """No validation when valid_npcs=None (backward compatibility)."""
        response = (
            '{"name":"Seek Wisdom","description":"Talk to the ancient mage",'
            '"objective_type":"talk","target":"Elder Mage Aldous","target_count":1,'
            '"gold_reward":100,"xp_reward":200}'
        )
        service = AIService.__new__(AIService)
        # Should not raise even though "Elder Mage Aldous" doesn't exist
        result = service._parse_quest_response(response, "Test NPC", valid_npcs=None)
        assert result["target"] == "Elder Mage Aldous"
        assert result["objective_type"] == "talk"

    # Tests spec: KILL quests still validate against VALID_ENEMY_TYPES
    def test_kill_quest_unchanged(self):
        """KILL quests still validate against VALID_ENEMY_TYPES."""
        response = (
            '{"name":"Hunt Dragons","description":"Slay the mighty dragon",'
            '"objective_type":"kill","target":"Dragon","target_count":1,'
            '"gold_reward":500,"xp_reward":1000}'
        )
        valid_npcs = {"merchant", "village elder"}
        service = AIService.__new__(AIService)
        # Should reject Dragon (not in VALID_ENEMY_TYPES) regardless of valid_npcs
        with pytest.raises(AIGenerationError, match="Invalid KILL quest target"):
            service._parse_quest_response(
                response, "Test NPC", valid_npcs=valid_npcs
            )

    # Tests spec: EXPLORE quests still validate against valid_locations
    def test_explore_quest_unchanged(self):
        """EXPLORE quests still validate against valid_locations."""
        response = (
            '{"name":"Find Cave","description":"Explore the hidden cave",'
            '"objective_type":"explore","target":"Hidden Cave","target_count":1,'
            '"gold_reward":50,"xp_reward":100}'
        )
        valid_npcs = {"merchant", "village elder"}
        valid_locations = {"hidden cave", "town square"}
        service = AIService.__new__(AIService)
        # Should pass - EXPLORE uses valid_locations, not valid_npcs
        result = service._parse_quest_response(
            response, "Test NPC", valid_locations=valid_locations, valid_npcs=valid_npcs
        )
        assert result["target"] == "Hidden Cave"
        assert result["objective_type"] == "explore"

    # Tests spec: COLLECT quests validated against OBTAINABLE_ITEMS
    def test_collect_quest_unchanged(self):
        """COLLECT quests validated against OBTAINABLE_ITEMS, not NPCs.

        Note: COLLECT quests are validated against OBTAINABLE_ITEMS,
        so this test uses a valid obtainable item (Herbs).
        """
        response = (
            '{"name":"Gather Herbs","description":"Collect healing herbs",'
            '"objective_type":"collect","target":"Herbs","target_count":5,'
            '"gold_reward":30,"xp_reward":60}'
        )
        valid_npcs = {"merchant", "village elder"}
        service = AIService.__new__(AIService)
        # Should pass - COLLECT targets validated against OBTAINABLE_ITEMS
        result = service._parse_quest_response(
            response, "Test NPC", valid_npcs=valid_npcs
        )
        assert result["target"] == "Herbs"
        assert result["objective_type"] == "collect"


class TestGenerateQuestWithValidNpcs:
    """Tests for generate_quest passing valid_npcs to _parse_quest_response."""

    # Tests spec: valid_npcs parameter flows through generate_quest
    def test_generate_quest_accepts_valid_npcs_param(self):
        """generate_quest accepts valid_npcs parameter."""
        # Verify the parameter exists in the function signature
        import inspect
        sig = inspect.signature(AIService.generate_quest)
        assert "valid_npcs" in sig.parameters
        # Should have default of None
        assert sig.parameters["valid_npcs"].default is None
