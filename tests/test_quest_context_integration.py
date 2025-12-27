"""Tests for quest world/region context integration.

This module tests that generate_quest() accepts and uses WorldContext and
RegionContext to produce more cohesive, world-aware quests.

Spec: Pass world_context and region_context to quest generation. The prompt includes:
- Theme essence (e.g., "dark supernatural horror with creeping dread")
- Region theme (e.g., "crumbling stone, forgotten history, decay")
- Region danger level (for reward scaling hints)
"""

import json
import pytest
from unittest.mock import Mock, patch

from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext


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
        retry_delay=0.1,
        enable_caching=False
    )


@pytest.fixture
def world_context():
    """Create a WorldContext for testing."""
    return WorldContext(
        theme="horror",
        theme_essence="dark supernatural horror with creeping dread",
        naming_style="archaic, unsettling names with dark undertones",
        tone="tense, atmospheric, psychologically unsettling"
    )


@pytest.fixture
def region_context():
    """Create a RegionContext for testing."""
    return RegionContext(
        name="The Rotting Hollow",
        theme="crumbling stone, forgotten history, decay",
        danger_level="dangerous",
        landmarks=["Abandoned Cathedral", "The Bone Pit"],
        coordinates=(5, 7)
    )


@pytest.fixture
def mock_quest_response():
    """Create a valid mock AI quest response."""
    return {
        "name": "Cleanse the Hollow",
        "description": "Purge the undead from the cathedral.",
        "objective_type": "kill",
        "target": "Skeleton",
        "target_count": 5,
        "gold_reward": 100,
        "xp_reward": 75
    }


# =============================================================================
# Test: generate_quest() accepts world_context parameter
# Spec: generate_quest() accepts optional world_context param
# =============================================================================

class TestGenerateQuestAcceptsWorldContext:
    """Tests that generate_quest() accepts world_context parameter."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_accepts_world_context(
        self, mock_openai_class, basic_config, world_context, mock_quest_response
    ):
        """Spec: generate_quest() accepts optional world_context param."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        # Should not raise - world_context is accepted
        result = service.generate_quest(
            theme="horror",
            npc_name="Dark Priest",
            player_level=5,
            location_name="Cathedral",
            world_context=world_context
        )

        assert result["name"] == "Cleanse the Hollow"


# =============================================================================
# Test: generate_quest() accepts region_context parameter
# Spec: generate_quest() accepts optional region_context param
# =============================================================================

class TestGenerateQuestAcceptsRegionContext:
    """Tests that generate_quest() accepts region_context parameter."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_quest_accepts_region_context(
        self, mock_openai_class, basic_config, region_context, mock_quest_response
    ):
        """Spec: generate_quest() accepts optional region_context param."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        # Should not raise - region_context is accepted
        result = service.generate_quest(
            theme="horror",
            npc_name="Dark Priest",
            player_level=5,
            location_name="Cathedral",
            region_context=region_context
        )

        assert result["name"] == "Cleanse the Hollow"


# =============================================================================
# Test: prompt includes theme_essence when world_context provided
# Spec: When world_context provided, prompt contains theme_essence
# =============================================================================

class TestPromptIncludesThemeEssence:
    """Tests that prompt includes theme_essence from world_context."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_prompt_includes_theme_essence(
        self, mock_openai_class, basic_config, world_context, mock_quest_response
    ):
        """Spec: When world_context provided, prompt contains theme_essence."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_quest(
            theme="horror",
            npc_name="Dark Priest",
            player_level=5,
            location_name="Cathedral",
            world_context=world_context
        )

        # Get the actual prompt sent to the LLM
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify theme_essence is in prompt
        assert "dark supernatural horror with creeping dread" in prompt


# =============================================================================
# Test: prompt includes region theme when region_context provided
# Spec: When region_context provided, prompt contains region theme
# =============================================================================

class TestPromptIncludesRegionTheme:
    """Tests that prompt includes region theme from region_context."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_prompt_includes_region_theme(
        self, mock_openai_class, basic_config, region_context, mock_quest_response
    ):
        """Spec: When region_context provided, prompt contains region theme."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_quest(
            theme="horror",
            npc_name="Dark Priest",
            player_level=5,
            location_name="Cathedral",
            region_context=region_context
        )

        # Get the actual prompt sent to the LLM
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify region theme is in prompt
        assert "crumbling stone, forgotten history, decay" in prompt


# =============================================================================
# Test: prompt includes danger_level when region_context provided
# Spec: When region_context provided, prompt contains danger_level
# =============================================================================

class TestPromptIncludesDangerLevel:
    """Tests that prompt includes danger_level from region_context."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_prompt_includes_danger_level(
        self, mock_openai_class, basic_config, region_context, mock_quest_response
    ):
        """Spec: When region_context provided, prompt contains danger_level."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_quest(
            theme="horror",
            npc_name="Dark Priest",
            player_level=5,
            location_name="Cathedral",
            region_context=region_context
        )

        # Get the actual prompt sent to the LLM
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify danger_level is in prompt
        assert "dangerous" in prompt.lower()


# =============================================================================
# Test: context params are optional (backward compatibility)
# Spec: Quest generation works without context (backward compatible)
# =============================================================================

class TestContextParamsOptional:
    """Tests that context parameters are optional for backward compatibility."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_context_params_are_optional(
        self, mock_openai_class, basic_config, mock_quest_response
    ):
        """Spec: Quest generation works without context (backward compatible)."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        # Should work without world_context or region_context
        result = service.generate_quest(
            theme="fantasy",
            npc_name="Village Elder",
            player_level=3,
            location_name="Village Square"
        )

        assert result["name"] == "Cleanse the Hollow"
        assert result["quest_giver"] == "Village Elder"


# =============================================================================
# Test: both contexts can be passed together
# Spec: Full context integration with both world and region
# =============================================================================

class TestBothContextsTogether:
    """Tests that both world_context and region_context can be passed together."""

    @patch('cli_rpg.ai_service.OpenAI')
    def test_both_contexts_together(
        self, mock_openai_class, basic_config, world_context, region_context, mock_quest_response
    ):
        """Spec: Both world_context and region_context can be used together."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_quest_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_quest(
            theme="horror",
            npc_name="Dark Priest",
            player_level=5,
            location_name="Cathedral",
            world_context=world_context,
            region_context=region_context
        )

        # Get the actual prompt sent to the LLM
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify both contexts are in prompt
        assert "dark supernatural horror with creeping dread" in prompt
        assert "crumbling stone, forgotten history, decay" in prompt
        assert "dangerous" in prompt.lower()
