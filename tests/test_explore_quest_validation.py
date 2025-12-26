"""Tests for EXPLORE quest target validation.

Tests spec: EXPLORE quest targets must match an existing location name (case-insensitive)
when valid_locations is provided. When valid_locations is None, validation is skipped.
"""

import pytest
from cli_rpg.ai_service import AIService, AIGenerationError


class TestExploreQuestValidation:
    """Tests for EXPLORE quest target validation in _parse_quest_response."""

    # Tests spec: EXPLORE quest targets must match an existing location name
    def test_valid_explore_target_accepted(self):
        """EXPLORE quest with existing location name parses successfully."""
        response = (
            '{"name":"Find Cave","description":"Explore the hidden cave",'
            '"objective_type":"explore","target":"Hidden Cave","target_count":1,'
            '"gold_reward":50,"xp_reward":100}'
        )
        valid_locations = {"hidden cave", "town square", "forest clearing"}
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(
            response, "Test NPC", valid_locations=valid_locations
        )
        assert result["target"] == "Hidden Cave"
        assert result["objective_type"] == "explore"

    # Tests spec: Invalid EXPLORE targets (not in locations) should be rejected
    def test_invalid_explore_target_rejected(self):
        """EXPLORE quest with non-existent location raises AIGenerationError."""
        response = (
            '{"name":"Find Dragon Lair","description":"Explore the dragon lair",'
            '"objective_type":"explore","target":"Dragon Lair","target_count":1,'
            '"gold_reward":100,"xp_reward":200}'
        )
        valid_locations = {"hidden cave", "town square", "forest clearing"}
        service = AIService.__new__(AIService)
        with pytest.raises(AIGenerationError, match="Invalid EXPLORE quest target"):
            service._parse_quest_response(
                response, "Test NPC", valid_locations=valid_locations
            )

    # Tests spec: Target matching should be case-insensitive
    def test_explore_target_case_insensitive(self):
        """EXPLORE quest target validation should be case-insensitive."""
        response = (
            '{"name":"Visit Town","description":"Explore the town square",'
            '"objective_type":"explore","target":"town square","target_count":1,'
            '"gold_reward":30,"xp_reward":60}'
        )
        # Valid locations stored in lowercase (as spec says)
        valid_locations = {"hidden cave", "town square", "forest clearing"}
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(
            response, "Test NPC", valid_locations=valid_locations
        )
        assert result["target"] == "town square"  # Original case preserved

    # Tests spec: Validation skipped when valid_locations=None (backward compat)
    def test_explore_validation_skipped_when_no_locations(self):
        """No validation when valid_locations=None (backward compatibility)."""
        response = (
            '{"name":"Find Dragon Lair","description":"Explore the dragon lair",'
            '"objective_type":"explore","target":"Dragon Lair","target_count":1,'
            '"gold_reward":100,"xp_reward":200}'
        )
        service = AIService.__new__(AIService)
        # Should not raise even though "Dragon Lair" doesn't exist
        result = service._parse_quest_response(response, "Test NPC", valid_locations=None)
        assert result["target"] == "Dragon Lair"
        assert result["objective_type"] == "explore"

    # Tests spec: KILL quests still validate against VALID_ENEMY_TYPES
    def test_kill_quest_unchanged(self):
        """KILL quests still validate against VALID_ENEMY_TYPES."""
        response = (
            '{"name":"Hunt Dragons","description":"Slay the mighty dragon",'
            '"objective_type":"kill","target":"Dragon","target_count":1,'
            '"gold_reward":500,"xp_reward":1000}'
        )
        valid_locations = {"hidden cave", "town square"}
        service = AIService.__new__(AIService)
        # Should reject Dragon (not in VALID_ENEMY_TYPES) regardless of valid_locations
        with pytest.raises(AIGenerationError, match="Invalid KILL quest target"):
            service._parse_quest_response(
                response, "Test NPC", valid_locations=valid_locations
            )

    # Tests spec: COLLECT quests not validated against locations
    def test_collect_quest_unchanged(self):
        """COLLECT quests not validated against locations."""
        response = (
            '{"name":"Gather Herbs","description":"Collect healing herbs",'
            '"objective_type":"collect","target":"Healing Herb","target_count":5,'
            '"gold_reward":30,"xp_reward":60}'
        )
        valid_locations = {"hidden cave", "town square"}
        service = AIService.__new__(AIService)
        # Should pass - COLLECT targets don't need to match locations
        result = service._parse_quest_response(
            response, "Test NPC", valid_locations=valid_locations
        )
        assert result["target"] == "Healing Herb"
        assert result["objective_type"] == "collect"


class TestGenerateQuestWithValidLocations:
    """Tests for generate_quest passing valid_locations to _parse_quest_response."""

    # Tests spec: valid_locations parameter flows through generate_quest
    def test_generate_quest_accepts_valid_locations_param(self):
        """generate_quest accepts valid_locations parameter."""
        # Verify the parameter exists in the function signature
        import inspect
        sig = inspect.signature(AIService.generate_quest)
        assert "valid_locations" in sig.parameters
        # Should have default of None
        assert sig.parameters["valid_locations"].default is None
