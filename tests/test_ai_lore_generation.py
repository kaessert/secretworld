"""Tests for AI-generated lore and world history.

Spec: AIService.generate_lore() generates world history/lore snippets appropriate
to the theme and location context. Returns a lore text string (50-500 chars)
following existing patterns for NPC dialogue, enemy, and item generation.
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.ai_config import AIConfig, DEFAULT_LORE_GENERATION_PROMPT
from cli_rpg.ai_service import AIService, AIGenerationError


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
        retry_delay=0.1  # Short delay for tests
    )


@pytest.fixture
def mock_lore_response():
    """Create a valid mock lore response (50-500 chars)."""
    return (
        "In ancient times, the Kingdom of Aeloria was founded by the legendary warrior "
        "Theron the Brave, who united the warring clans under one banner."
    )


# =============================================================================
# AIConfig Tests - Spec: lore_generation_prompt field
# =============================================================================

class TestAIConfigLorePrompt:
    """Tests for AIConfig lore generation prompt."""

    # Spec test: AIConfig field exists
    def test_ai_config_has_lore_prompt(self):
        """Spec: lore_generation_prompt field exists in AIConfig."""
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'lore_generation_prompt')
        assert config.lore_generation_prompt != ""

    # Spec test: to_dict/from_dict works
    def test_ai_config_lore_prompt_serialization(self):
        """Spec: to_dict/from_dict handles lore_generation_prompt."""
        config = AIConfig(
            api_key="test-key",
            lore_generation_prompt="Custom lore prompt: {theme} {location_name}"
        )

        # Serialize
        data = config.to_dict()
        assert "lore_generation_prompt" in data
        assert data["lore_generation_prompt"] == "Custom lore prompt: {theme} {location_name}"

        # Deserialize
        restored = AIConfig.from_dict(data)
        assert restored.lore_generation_prompt == "Custom lore prompt: {theme} {location_name}"

    def test_ai_config_from_dict_uses_default_when_missing(self):
        """from_dict uses DEFAULT_LORE_GENERATION_PROMPT when field is missing."""
        data = {"api_key": "test-key"}
        config = AIConfig.from_dict(data)
        assert config.lore_generation_prompt == DEFAULT_LORE_GENERATION_PROMPT

    def test_default_lore_prompt_contains_placeholders(self):
        """Spec: Default prompt contains required placeholders."""
        assert "{theme}" in DEFAULT_LORE_GENERATION_PROMPT
        assert "{location_name}" in DEFAULT_LORE_GENERATION_PROMPT
        assert "{lore_category}" in DEFAULT_LORE_GENERATION_PROMPT


# =============================================================================
# AIService.generate_lore() Tests
# =============================================================================

class TestAIServiceGenerateLore:
    """Tests for AIService.generate_lore() method."""

    # Spec test: Returns non-empty string
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_returns_string(
        self, mock_openai_class, basic_config, mock_lore_response
    ):
        """Spec: generate_lore returns a non-empty string."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_lore_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_lore(
            theme="fantasy",
            location_name="Ancient Temple"
        )

        assert isinstance(result, str)
        assert len(result) >= 50
        mock_client.chat.completions.create.assert_called_once()

    # Spec test: Prompt includes theme
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_uses_theme_in_prompt(
        self, mock_openai_class, basic_config, mock_lore_response
    ):
        """Spec: Prompt includes theme."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_lore_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_lore(
            theme="sci-fi",
            location_name="Space Station"
        )

        # Get the actual call arguments
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "sci-fi" in prompt.lower()

    # Spec test: Prompt includes location
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_uses_location_in_prompt(
        self, mock_openai_class, basic_config, mock_lore_response
    ):
        """Spec: Prompt includes location name."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_lore_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_lore(
            theme="fantasy",
            location_name="Haunted Graveyard"
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "Haunted Graveyard" in prompt or "haunted graveyard" in prompt.lower()

    # Spec test: Category (history/legend/secret) in prompt
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_respects_category(
        self, mock_openai_class, basic_config, mock_lore_response
    ):
        """Spec: Category (history/legend/secret) appears in prompt."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_lore_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_lore(
            theme="fantasy",
            location_name="Temple",
            lore_category="legend"
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "legend" in prompt.lower()

    # Spec test: Raises AIGenerationError if < 50 chars
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_validates_min_length(
        self, mock_openai_class, basic_config
    ):
        """Spec: Raises AIGenerationError if response < 50 chars."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        short_response = "Too short lore text."  # Less than 50 chars

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = short_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        with pytest.raises(AIGenerationError, match="too short"):
            service.generate_lore(
                theme="fantasy",
                location_name="Temple"
            )

    # Spec test: Truncates to 500 chars with "..."
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_truncates_long_responses(
        self, mock_openai_class, basic_config
    ):
        """Spec: Truncates responses longer than 500 chars with '...'."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        long_response = "A" * 600  # Way too long

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = long_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_lore(
            theme="fantasy",
            location_name="Temple"
        )

        assert len(result) == 500
        assert result.endswith("...")

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_strips_quotes(
        self, mock_openai_class, basic_config
    ):
        """Lore generation strips surrounding quotes from response."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # LLM might return quoted text - make sure it's 50+ chars
        quoted_lore = (
            '"Long ago, the ancient kingdom fell to darkness. '
            'The legends speak of a prophecy that one day a hero shall rise."'
        )
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = quoted_lore
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_lore(
            theme="fantasy",
            location_name="Temple"
        )

        assert not result.startswith('"')
        assert not result.endswith('"')

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_default_category_is_history(
        self, mock_openai_class, basic_config, mock_lore_response
    ):
        """Default lore_category is 'history'."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_lore_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_lore(
            theme="fantasy"
            # No location_name or lore_category specified
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "history" in prompt.lower()

    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_lore_handles_empty_location(
        self, mock_openai_class, basic_config, mock_lore_response
    ):
        """Lore generation handles empty location name gracefully."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_lore_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)

        # Should not raise an error
        result = service.generate_lore(
            theme="fantasy",
            location_name=""  # Empty location
        )

        assert isinstance(result, str)
        assert len(result) >= 50
