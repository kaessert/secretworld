"""Tests for quest target validation.

Tests that KILL quest targets are validated against the set of
spawnable enemy types defined in combat.py.
"""

import pytest
from cli_rpg.combat import VALID_ENEMY_TYPES
from cli_rpg.ai_service import AIService, AIGenerationError


class TestValidEnemyTypes:
    """Tests for VALID_ENEMY_TYPES constant exported from combat.py."""

    # Tests spec: Forest enemies must be spawnable
    def test_contains_expected_forest_enemies(self):
        """Verify forest enemy types are in VALID_ENEMY_TYPES."""
        assert "wolf" in VALID_ENEMY_TYPES
        assert "bear" in VALID_ENEMY_TYPES
        assert "giant spider" in VALID_ENEMY_TYPES
        assert "wild boar" in VALID_ENEMY_TYPES

    # Tests spec: Cave enemies must be spawnable
    def test_contains_expected_cave_enemies(self):
        """Verify cave enemy types are in VALID_ENEMY_TYPES."""
        assert "goblin" in VALID_ENEMY_TYPES
        assert "troll" in VALID_ENEMY_TYPES
        assert "bat" in VALID_ENEMY_TYPES
        assert "cave dweller" in VALID_ENEMY_TYPES

    # Tests spec: Dungeon enemies must be spawnable
    def test_contains_expected_dungeon_enemies(self):
        """Verify dungeon enemy types are in VALID_ENEMY_TYPES."""
        assert "skeleton" in VALID_ENEMY_TYPES
        assert "zombie" in VALID_ENEMY_TYPES
        assert "ghost" in VALID_ENEMY_TYPES
        assert "dark knight" in VALID_ENEMY_TYPES

    # Tests spec: Mountain enemies must be spawnable
    def test_contains_expected_mountain_enemies(self):
        """Verify mountain enemy types are in VALID_ENEMY_TYPES."""
        assert "eagle" in VALID_ENEMY_TYPES
        assert "goat" in VALID_ENEMY_TYPES
        assert "mountain lion" in VALID_ENEMY_TYPES
        assert "yeti" in VALID_ENEMY_TYPES

    # Tests spec: Village enemies must be spawnable
    def test_contains_expected_village_enemies(self):
        """Verify village enemy types are in VALID_ENEMY_TYPES."""
        assert "bandit" in VALID_ENEMY_TYPES
        assert "thief" in VALID_ENEMY_TYPES
        assert "ruffian" in VALID_ENEMY_TYPES
        assert "outlaw" in VALID_ENEMY_TYPES

    # Tests spec: Default enemies must be spawnable
    def test_contains_expected_default_enemies(self):
        """Verify default enemy types are in VALID_ENEMY_TYPES."""
        assert "monster" in VALID_ENEMY_TYPES
        assert "creature" in VALID_ENEMY_TYPES
        assert "beast" in VALID_ENEMY_TYPES
        assert "fiend" in VALID_ENEMY_TYPES

    # Tests spec: All enemy types must be lowercase for case-insensitive matching
    def test_all_lowercase(self):
        """Verify all enemy types are lowercase."""
        for enemy in VALID_ENEMY_TYPES:
            assert enemy == enemy.lower(), f"Expected lowercase: {enemy}"

    def test_is_a_set(self):
        """Verify VALID_ENEMY_TYPES is a set for O(1) lookups."""
        assert isinstance(VALID_ENEMY_TYPES, (set, frozenset))


class TestKillQuestValidation:
    """Tests for KILL quest target validation in _parse_quest_response."""

    # Tests spec: Valid KILL targets from enemy_templates should be accepted
    def test_valid_kill_target_accepted(self):
        """KILL quest with valid spawnable enemy target should parse successfully."""
        response = (
            '{"name":"Hunt Wolves","description":"Kill wolves in the forest",'
            '"objective_type":"kill","target":"Wolf","target_count":3,'
            '"gold_reward":50,"xp_reward":100}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Wolf"
        assert result["objective_type"] == "kill"

    # Tests spec: Invalid KILL targets (not in enemy_templates) should be rejected
    def test_invalid_kill_target_rejected(self):
        """KILL quest with non-spawnable enemy target should raise AIGenerationError."""
        response = (
            '{"name":"Hunt Dragons","description":"Slay the mighty dragon",'
            '"objective_type":"kill","target":"Dragon","target_count":1,'
            '"gold_reward":500,"xp_reward":1000}'
        )
        service = AIService.__new__(AIService)
        with pytest.raises(AIGenerationError, match="Invalid KILL quest target"):
            service._parse_quest_response(response, "Test NPC")

    # Tests spec: Target matching should be case-insensitive
    def test_kill_target_case_insensitive(self):
        """KILL quest target validation should be case-insensitive."""
        response = (
            '{"name":"Hunt Wolves","description":"Kill wolves",'
            '"objective_type":"kill","target":"WOLF","target_count":3,'
            '"gold_reward":50,"xp_reward":100}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "WOLF"  # Original case preserved

    # Tests spec: Non-KILL quest types should not validate targets against enemy list
    def test_explore_quest_target_not_validated(self):
        """EXPLORE quest targets should not be validated against enemy types."""
        response = (
            '{"name":"Find Cave","description":"Explore the hidden cave",'
            '"objective_type":"explore","target":"Hidden Cave","target_count":1,'
            '"gold_reward":50,"xp_reward":100}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Hidden Cave"
        assert result["objective_type"] == "explore"

    # Tests spec: COLLECT quest targets should not be validated against enemy list
    def test_collect_quest_target_not_validated(self):
        """COLLECT quest targets should not be validated against enemy types."""
        response = (
            '{"name":"Gather Herbs","description":"Collect healing herbs",'
            '"objective_type":"collect","target":"Healing Herb","target_count":5,'
            '"gold_reward":30,"xp_reward":60}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Healing Herb"
        assert result["objective_type"] == "collect"

    # Tests spec: TALK quest targets should not be validated against enemy list
    def test_talk_quest_target_not_validated(self):
        """TALK quest targets should not be validated against enemy types."""
        response = (
            '{"name":"Find Elder","description":"Speak with the village elder",'
            '"objective_type":"talk","target":"Village Elder","target_count":1,'
            '"gold_reward":20,"xp_reward":40}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Village Elder"
        assert result["objective_type"] == "talk"

    def test_valid_kill_target_with_spaces_accepted(self):
        """KILL quest with multi-word enemy name should parse successfully."""
        response = (
            '{"name":"Hunt Spiders","description":"Kill giant spiders",'
            '"objective_type":"kill","target":"Giant Spider","target_count":2,'
            '"gold_reward":60,"xp_reward":120}'
        )
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Giant Spider"
