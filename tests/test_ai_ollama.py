"""Tests for Ollama AI provider support.

These tests verify:
1. AIConfig correctly handles AI_PROVIDER=ollama
2. Ollama configuration (base_url, model) is correctly parsed
3. AIService correctly initializes OpenAI client for Ollama
4. Connection errors from Ollama provide helpful messages
5. Serialization/deserialization preserves Ollama settings
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import openai

from cli_rpg.ai_config import AIConfig, AIConfigError
from cli_rpg.ai_service import AIService, AIServiceError


# Test 1: AIConfig from_env with AI_PROVIDER=ollama
def test_ai_config_from_env_with_ollama_provider(monkeypatch):
    """Test AIConfig.from_env() correctly handles AI_PROVIDER=ollama.

    Spec: Ollama requires no API key, so api_key should be set to placeholder "ollama",
    and default model should be "llama3.2".
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "ollama")

    config = AIConfig.from_env()

    assert config.provider == "ollama"
    assert config.api_key == "ollama"  # Placeholder value
    assert config.model == "llama3.2"  # Default Ollama model


# Test 2: AIConfig from_env with custom OLLAMA_BASE_URL
def test_ai_config_from_env_ollama_with_custom_base_url(monkeypatch):
    """Test AIConfig.from_env() reads OLLAMA_BASE_URL environment variable.

    Spec: OLLAMA_BASE_URL allows custom Ollama endpoint (default: http://localhost:11434/v1).
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:8080/v1")

    config = AIConfig.from_env()

    assert config.provider == "ollama"
    assert config.ollama_base_url == "http://custom:8080/v1"


# Test 3: AIConfig from_env with custom OLLAMA_MODEL
def test_ai_config_from_env_ollama_with_custom_model(monkeypatch):
    """Test AIConfig.from_env() reads OLLAMA_MODEL environment variable.

    Spec: OLLAMA_MODEL overrides the default model (llama3.2).
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")

    config = AIConfig.from_env()

    assert config.provider == "ollama"
    assert config.model == "mistral"


# Test 4: AIService initializes OpenAI client with Ollama base_url
def test_ai_service_initialization_with_ollama():
    """Test AIService creates OpenAI client with custom base_url for Ollama.

    Spec: Ollama uses OpenAI-compatible API, so we use OpenAI client with custom base_url.
    """
    config = AIConfig(
        api_key="ollama",
        provider="ollama",
        model="llama3.2",
        ollama_base_url="http://localhost:11434/v1"
    )

    with patch("cli_rpg.ai_service.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client

        service = AIService(config)

        # Verify OpenAI client was created with Ollama base_url
        mock_openai.assert_called_once_with(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )
        assert service.provider == "ollama"
        assert service.client == mock_client


# Test 5: Generate location with Ollama (mocked)
def test_generate_location_with_ollama():
    """Test generate_location works correctly with Ollama provider.

    Spec: Ollama uses OpenAI-compatible API, so location generation should work the same.
    """
    config = AIConfig(
        api_key="ollama",
        provider="ollama",
        model="llama3.2",
        ollama_base_url="http://localhost:11434/v1",
        enable_caching=False
    )

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '''
    {
        "name": "Mystic Cave",
        "description": "A dark cave filled with glowing crystals.",
        "category": "cave"
    }
    '''

    with patch("cli_rpg.ai_service.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = AIService(config)
        result = service.generate_location(theme="fantasy", context_locations=[])

        assert result["name"] == "Mystic Cave"
        assert "dark cave" in result["description"]
        assert result["category"] == "cave"
        assert "connections" not in result  # WFC handles terrain structure


# Test 6: Ollama connection error provides helpful message
def test_ollama_connection_error_raises_service_error():
    """Test that connection errors from Ollama provide helpful error message.

    Spec: When Ollama is not running, AIServiceError should include a helpful message
    about checking if Ollama is running.
    """
    config = AIConfig(
        api_key="ollama",
        provider="ollama",
        model="llama3.2",
        ollama_base_url="http://localhost:11434/v1",
        enable_caching=False,
        max_retries=0  # Don't retry for faster test
    )

    with patch("cli_rpg.ai_service.OpenAI") as mock_openai:
        mock_client = Mock()
        # Simulate connection refused error
        mock_client.chat.completions.create.side_effect = openai.APIConnectionError(
            request=Mock()
        )
        mock_openai.return_value = mock_client

        service = AIService(config)

        with pytest.raises(AIServiceError) as exc_info:
            service.generate_location(theme="fantasy", context_locations=[])

        # Should include helpful message about Ollama not running
        error_msg = str(exc_info.value).lower()
        assert "ollama" in error_msg or "connection" in error_msg


# Test 7: AIConfig serialization includes ollama_base_url
def test_ai_config_serialization_with_ollama():
    """Test AIConfig with Ollama serializes and deserializes correctly.

    Spec: to_dict() should include ollama_base_url, from_dict() should restore it.
    """
    original_config = AIConfig(
        api_key="ollama",
        provider="ollama",
        model="llama3.2",
        ollama_base_url="http://custom:8080/v1"
    )

    config_dict = original_config.to_dict()

    assert config_dict["provider"] == "ollama"
    assert config_dict["ollama_base_url"] == "http://custom:8080/v1"

    restored_config = AIConfig.from_dict(config_dict)

    assert restored_config.provider == "ollama"
    assert restored_config.ollama_base_url == "http://custom:8080/v1"
    assert restored_config.model == "llama3.2"


# Test: Default Ollama base URL when not specified
def test_ai_service_ollama_default_base_url():
    """Test AIService uses default base_url when ollama_base_url not set.

    Spec: Default Ollama endpoint is http://localhost:11434/v1.
    """
    config = AIConfig(
        api_key="ollama",
        provider="ollama",
        model="llama3.2"
        # ollama_base_url not set, should use default
    )

    with patch("cli_rpg.ai_service.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client

        service = AIService(config)

        # Verify default base_url was used
        mock_openai.assert_called_once_with(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )


# Test: Ollama provider doesn't require external API keys in from_env
def test_ai_config_from_env_ollama_no_external_key_needed(monkeypatch):
    """Test AIConfig.from_env() with Ollama doesn't require OPENAI_API_KEY or ANTHROPIC_API_KEY.

    Spec: Ollama is local, so no external API keys are needed.
    """
    # Clear all API keys
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "ollama")

    # Should not raise - Ollama doesn't need external keys
    config = AIConfig.from_env()

    assert config.provider == "ollama"
    assert config.api_key == "ollama"
