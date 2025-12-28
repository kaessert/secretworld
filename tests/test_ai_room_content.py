"""Tests for AI-generated room content for procedural interior generation.

Spec: AIService.generate_room_content() generates room name and description
for procedural interior locations. Called by ContentLayer to bridge
procedural generators with AI-generated content.

Requirements:
1. generate_room_content(room_type, category, connections, is_entry, context) -> {"name": str, "description": str}
2. Uses existing _call_llm() pattern for API calls
3. Uses progress_indicator() for generation type "location"
4. Returns None on failure (ContentLayer handles fallback via FallbackContentProvider)
"""

import pytest
from unittest.mock import Mock, patch
import json

from cli_rpg.ai_config import AIConfig, DEFAULT_ROOM_CONTENT_PROMPT
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
def mock_room_content_response():
    """Create a valid mock room content JSON response."""
    return json.dumps({
        "name": "Shadowy Antechamber",
        "description": "A dusty chamber lit by flickering torches. Cobwebs drape the corners."
    })


@pytest.fixture
def mock_generation_context():
    """Create a mock GenerationContext with world context."""
    mock_context = Mock()
    mock_context.to_prompt_context.return_value = {
        "theme": "dark fantasy",
        "theme_essence": "A world of shadow and ancient evil",
        "tone": "grim and foreboding"
    }
    mock_context.world = Mock()
    mock_context.world.theme = "dark fantasy"
    mock_context.world.theme_essence = "A world of shadow and ancient evil"
    return mock_context


# =============================================================================
# AIConfig Tests - Spec: room_content_prompt field
# =============================================================================

class TestAIConfigRoomContentPrompt:
    """Tests for AIConfig room content prompt."""

    # Spec test: AIConfig field exists
    def test_ai_config_has_room_content_prompt(self):
        """Spec: room_content_prompt field exists in AIConfig."""
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'room_content_prompt')
        assert config.room_content_prompt != ""

    # Spec test: to_dict/from_dict works
    def test_ai_config_room_content_prompt_serialization(self):
        """Spec: to_dict/from_dict handles room_content_prompt."""
        config = AIConfig(
            api_key="test-key",
            room_content_prompt="Custom room prompt: {room_type} {category}"
        )

        # Serialize
        data = config.to_dict()
        assert "room_content_prompt" in data
        assert data["room_content_prompt"] == "Custom room prompt: {room_type} {category}"

        # Deserialize
        restored = AIConfig.from_dict(data)
        assert restored.room_content_prompt == "Custom room prompt: {room_type} {category}"

    def test_ai_config_from_dict_uses_default_when_missing(self):
        """from_dict uses DEFAULT_ROOM_CONTENT_PROMPT when field is missing."""
        data = {"api_key": "test-key"}
        config = AIConfig.from_dict(data)
        assert config.room_content_prompt == DEFAULT_ROOM_CONTENT_PROMPT

    def test_default_room_content_prompt_contains_placeholders(self):
        """Spec: Default prompt contains required placeholders."""
        assert "{room_type}" in DEFAULT_ROOM_CONTENT_PROMPT
        assert "{category}" in DEFAULT_ROOM_CONTENT_PROMPT
        assert "{connections}" in DEFAULT_ROOM_CONTENT_PROMPT
        assert "{is_entry}" in DEFAULT_ROOM_CONTENT_PROMPT
        assert "{theme_essence}" in DEFAULT_ROOM_CONTENT_PROMPT


# =============================================================================
# AIService.generate_room_content() Tests
# =============================================================================

class TestAIServiceGenerateRoomContent:
    """Tests for AIService.generate_room_content() method."""

    # Spec test: Returns dict with name and description
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_returns_name_and_description(
        self, mock_openai_class, basic_config, mock_room_content_response,
        mock_generation_context
    ):
        """Spec: generate_room_content returns dict with name and description."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_room_content_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_room_content(
            room_type="chamber",
            category="dungeon",
            connections=["north", "east"],
            is_entry=False,
            context=mock_generation_context
        )

        assert isinstance(result, dict)
        assert "name" in result
        assert "description" in result
        assert result["name"] == "Shadowy Antechamber"
        mock_client.chat.completions.create.assert_called_once()

    # Spec test: Passes room_type to prompt
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_passes_room_type_to_prompt(
        self, mock_openai_class, basic_config, mock_room_content_response,
        mock_generation_context
    ):
        """Spec: room_type is included in the prompt."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_room_content_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_room_content(
            room_type="boss_room",
            category="dungeon",
            connections=["south"],
            is_entry=False,
            context=mock_generation_context
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "boss_room" in prompt

    # Spec test: Passes category to prompt
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_passes_category_to_prompt(
        self, mock_openai_class, basic_config, mock_room_content_response,
        mock_generation_context
    ):
        """Spec: category is included in the prompt."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_room_content_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_room_content(
            room_type="chamber",
            category="cave",
            connections=["north", "south"],
            is_entry=False,
            context=mock_generation_context
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        assert "cave" in prompt

    # Spec test: Returns None on invalid JSON
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_returns_none_on_invalid_json(
        self, mock_openai_class, basic_config, mock_generation_context
    ):
        """Spec: Returns None when LLM response is not valid JSON."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not JSON at all"
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_room_content(
            room_type="chamber",
            category="dungeon",
            connections=["north"],
            is_entry=False,
            context=mock_generation_context
        )

        assert result is None

    # Spec test: Returns None on missing keys
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_returns_none_on_missing_keys(
        self, mock_openai_class, basic_config, mock_generation_context
    ):
        """Spec: Returns None when response is missing required keys."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Missing "description" key
        incomplete_response = json.dumps({"name": "Some Room"})

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = incomplete_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_room_content(
            room_type="chamber",
            category="dungeon",
            connections=["north"],
            is_entry=False,
            context=mock_generation_context
        )

        assert result is None

    # Spec test: Uses context theme_essence
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_uses_context_theme(
        self, mock_openai_class, basic_config, mock_room_content_response,
        mock_generation_context
    ):
        """Spec: generation context theme_essence is used in prompt."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_room_content_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_room_content(
            room_type="chamber",
            category="dungeon",
            connections=["north"],
            is_entry=False,
            context=mock_generation_context
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Check that the theme essence from context is in the prompt
        assert "shadow" in prompt.lower() or "ancient evil" in prompt.lower()

    # Spec test: Handles None context gracefully
    @patch('cli_rpg.ai_service.OpenAI')
    def test_generate_room_content_handles_none_context(
        self, mock_openai_class, basic_config, mock_room_content_response
    ):
        """Spec: generate_room_content handles None context gracefully."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_room_content_response
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        result = service.generate_room_content(
            room_type="chamber",
            category="dungeon",
            connections=["north"],
            is_entry=False,
            context=None
        )

        # Should still work with fallback values
        assert result is not None
        assert "name" in result
        assert "description" in result
