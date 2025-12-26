"""Tests for AI-powered quest generation.

This module tests the AI quest generation feature which creates contextual,
themed quests from NPCs with objectives and rewards scaled to player level.
"""

import json
import pytest
from unittest.mock import Mock, patch

from cli_rpg.models.quest import Quest, ObjectiveType
from cli_rpg.ai_config import AIConfig, DEFAULT_QUEST_GENERATION_PROMPT
from cli_rpg.ai_service import AIService, AIServiceError, AIGenerationError


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def basic_config():
    """Create a basic AIConfig for testing."""
    return AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        max_retries=3,
        retry_delay=0.1,  # Short delay for tests
        enable_caching=False  # Disable caching to ensure mock is called
    )


@pytest.fixture
def mock_kill_quest_response():
    """Create a valid mock AI kill quest response."""
    return {
        "name": "Goblin Slayer",
        "description": "Defeat the goblins terrorizing the village.",
        "objective_type": "kill",
        "target": "Goblin",
        "target_count": 5,
        "gold_reward": 100,
        "xp_reward": 75
    }


@pytest.fixture
def mock_collect_quest_response():
    """Create a valid mock AI collect quest response."""
    return {
        "name": "Herb Gathering",
        "description": "Collect medicinal herbs for the healer.",
        "objective_type": "collect",
        "target": "Healing Herb",
        "target_count": 3,
        "gold_reward": 50,
        "xp_reward": 40
    }


@pytest.fixture
def mock_explore_quest_response():
    """Create a valid mock AI explore quest response."""
    return {
        "name": "Scout the Ruins",
        "description": "Investigate the ancient ruins to the north.",
        "objective_type": "explore",
        "target": "Ancient Ruins",
        "target_count": 1,
        "gold_reward": 75,
        "xp_reward": 60
    }


# =============================================================================
# AIConfig Tests - Spec: quest_generation_prompt field
# =============================================================================

class TestAIConfigQuestPrompt:
    """Tests for AIConfig quest generation prompt."""

    def test_ai_config_has_quest_prompt(self):
        """Spec: quest_generation_prompt field exists in AIConfig."""
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'quest_generation_prompt')
        assert config.quest_generation_prompt != ""

    def test_ai_config_quest_prompt_serialization(self):
        """Spec: to_dict/from_dict handles quest_generation_prompt."""
        config = AIConfig(
            api_key="test-key",
            quest_generation_prompt="Custom quest prompt: {theme} {npc_name}"
        )

        # Serialize
        data = config.to_dict()
        assert "quest_generation_prompt" in data
        assert data["quest_generation_prompt"] == "Custom quest prompt: {theme} {npc_name}"

        # Deserialize
        restored = AIConfig.from_dict(data)
        assert restored.quest_generation_prompt == "Custom quest prompt: {theme} {npc_name}"

    def test_default_quest_prompt_contains_placeholders(self):
        """Spec: Default prompt contains required placeholders."""
        assert "{theme}" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "{npc_name}" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "{location_name}" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "{player_level}" in DEFAULT_QUEST_GENERATION_PROMPT

    def test_quest_prompt_includes_valid_enemy_types(self):
        """Spec: Quest prompt should list valid enemy types for kill quests.

        This ensures AI-generated kill quests reference enemy types that actually
        spawn in random encounters (defined in combat.py enemy_templates).
        """
        # Verify key enemy types from each location category are listed
        assert "Wolf" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "Goblin" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "Skeleton" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "Bandit" in DEFAULT_QUEST_GENERATION_PROMPT
        assert "Yeti" in DEFAULT_QUEST_GENERATION_PROMPT


# =============================================================================
# AIService.generate_quest() Tests
# =============================================================================

class TestAIServiceGenerateQuest:
    """Tests for AIService.generate_quest() method."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_returns_valid_structure(
        self, mock_openai_class, basic_config, mock_kill_quest_response
    ):
        """Spec: Returns dict with all required fields."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_kill_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Elder Marcus",
            player_level=3,
            location_name="Village Square"
        )

        # Verify all required fields
        assert "name" in result
        assert "description" in result
        assert "objective_type" in result
        assert "target" in result
        assert "target_count" in result
        assert "gold_reward" in result
        assert "xp_reward" in result
        assert "quest_giver" in result

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_name_length_too_short(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects names <2 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "X",  # Too short (< 2 chars)
            "description": "A quest description here.",
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="name"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_name_length_too_long(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects names >30 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "A" * 31,  # Too long (> 30 chars)
            "description": "A quest description here.",
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="name"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_description_length_too_short(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects descriptions <1 char."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Empty Quest",
            "description": "",  # Too short (< 1 char)
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="description"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_description_length_too_long(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects descriptions >200 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Long Quest",
            "description": "A" * 201,  # Too long (> 200 chars)
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="description"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_objective_type(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects invalid objective types."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Invalid Quest",
            "description": "A quest with invalid type.",
            "objective_type": "invalid_type",  # Invalid
            "target": "Something",
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="objective_type"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_target_not_empty(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects empty target."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "No Target Quest",
            "description": "A quest with no target.",
            "objective_type": "kill",
            "target": "",  # Empty target
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="target"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_target_count_positive(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects target_count < 1."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Zero Target Quest",
            "description": "A quest with zero target count.",
            "objective_type": "kill",
            "target": "Goblin",  # Valid enemy type
            "target_count": 0,  # Invalid: < 1
            "gold_reward": 50,
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="target_count"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_validates_rewards_non_negative(
        self, mock_openai_class, basic_config
    ):
        """Spec: Rejects negative rewards."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        invalid_response = {
            "name": "Bad Reward Quest",
            "description": "A quest with negative rewards.",
            "objective_type": "kill",
            "target": "Goblin",  # Valid enemy type
            "target_count": 1,
            "gold_reward": -10,  # Invalid: negative
            "xp_reward": 25
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="gold_reward"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_sets_quest_giver(
        self, mock_openai_class, basic_config, mock_kill_quest_response
    ):
        """Spec: Sets quest_giver to npc_name."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_kill_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Elder Marcus",
            player_level=3
        )

        assert result["quest_giver"] == "Elder Marcus"

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_uses_context(
        self, mock_openai_class, basic_config, mock_kill_quest_response
    ):
        """Spec: Prompt includes theme, npc, location, level."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_kill_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_quest(
            theme="steampunk",
            npc_name="Captain Brass",
            player_level=7,
            location_name="Clockwork District"
        )

        # Get the actual call arguments
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify context is in prompt
        assert "steampunk" in prompt.lower()
        assert "Captain Brass" in prompt
        assert "Clockwork District" in prompt
        assert "7" in prompt  # Player level

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_handles_api_error(
        self, mock_openai_class, basic_config
    ):
        """Spec: Raises AIServiceError on failure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Simulate API error
        mock_client.chat.completions.create.side_effect = Exception("API failure")

        service = AIService(basic_config)

        with pytest.raises(AIServiceError):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )


# =============================================================================
# Integration Tests - Quest model compatibility
# =============================================================================

class TestGenerateQuestIntegration:
    """Integration tests for generate_quest with Quest model."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_can_create_valid_quest_instance(
        self, mock_openai_class, basic_config, mock_kill_quest_response
    ):
        """Spec: Result can construct Quest model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_kill_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Elder Marcus",
            player_level=3
        )

        # Should be able to create Quest from result
        quest = Quest(
            name=result["name"],
            description=result["description"],
            objective_type=ObjectiveType(result["objective_type"]),
            target=result["target"],
            target_count=result["target_count"],
            gold_reward=result["gold_reward"],
            xp_reward=result["xp_reward"],
            quest_giver=result["quest_giver"]
        )

        assert quest.name == "Goblin Slayer"
        assert quest.objective_type == ObjectiveType.KILL
        assert quest.target == "Goblin"
        assert quest.target_count == 5
        assert quest.gold_reward == 100
        assert quest.xp_reward == 75
        assert quest.quest_giver == "Elder Marcus"

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_kill_objective_valid(
        self, mock_openai_class, basic_config, mock_kill_quest_response
    ):
        """Spec: Kill quests have valid structure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_kill_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Village Elder",
            player_level=3
        )

        assert result["objective_type"] == "kill"
        assert result["target_count"] >= 1

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_collect_objective_valid(
        self, mock_openai_class, basic_config, mock_collect_quest_response
    ):
        """Spec: Collect quests have valid structure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_collect_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Herbalist",
            player_level=2
        )

        assert result["objective_type"] == "collect"
        assert result["target_count"] >= 1

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_explore_objective_valid(
        self, mock_openai_class, basic_config, mock_explore_quest_response
    ):
        """Spec: Explore quests have valid structure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_explore_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Scout Master",
            player_level=4
        )

        assert result["objective_type"] == "explore"
        assert result["target_count"] >= 1


# =============================================================================
# Quest Response Parsing Error Tests (Coverage for lines 1281-1282, 1289, 1340)
# =============================================================================

class TestParseQuestResponseErrors:
    """Tests for _parse_quest_response error handling."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_parse_quest_response_invalid_json(self, mock_openai_class, basic_config):
        """Spec: Invalid JSON raises AIGenerationError.

        Covers lines 1281-1282: json.JSONDecodeError handling in _parse_quest_response.
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Return invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON { bad syntax"
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="parse.*JSON"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_parse_quest_response_missing_field(self, mock_openai_class, basic_config):
        """Spec: Missing required field raises AIGenerationError.

        Covers line 1289: raise AIGenerationError(f"Response missing required field: {field}")
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Response missing 'xp_reward' field
        incomplete_response = {
            "name": "Test Quest",
            "description": "A test quest description.",
            "objective_type": "kill",
            "target": "Enemy",
            "target_count": 1,
            "gold_reward": 50
            # Missing 'xp_reward'
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(incomplete_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="missing required field.*xp_reward"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )

    @patch('cli_rpg.ai_service.OpenAI')
    def test_parse_quest_response_xp_reward_negative(self, mock_openai_class, basic_config):
        """Spec: Negative xp_reward raises AIGenerationError.

        Covers lines 1339-1341: raise AIGenerationError("xp_reward must be non-negative")
        """
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # xp_reward is negative
        invalid_response = {
            "name": "Bad Reward Quest",
            "description": "A quest with negative xp reward.",
            "objective_type": "kill",
            "target": "Goblin",  # Valid enemy type
            "target_count": 1,
            "gold_reward": 50,
            "xp_reward": -10  # Invalid: negative
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="xp_reward"):
            service.generate_quest(
                theme="fantasy",
                npc_name="Test NPC",
                player_level=1
            )
