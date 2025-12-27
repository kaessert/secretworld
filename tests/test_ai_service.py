"""Tests for AI service module."""

import json
import pytest
from unittest.mock import Mock, patch
from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import (
    AIService,
    AIServiceError,
    AIGenerationError,
    AITimeoutError
)


# Fixtures

@pytest.fixture
def basic_config(tmp_path):
    """Create a basic AIConfig for testing with isolated cache file."""
    return AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        max_retries=3,
        retry_delay=0.1,  # Short delay for tests
        cache_file=str(tmp_path / "test_cache.json")  # Isolated cache per test
    )


@pytest.fixture
def config_no_cache():
    """Create AIConfig with caching disabled."""
    return AIConfig(
        api_key="test-key-123",
        enable_caching=False,
        retry_delay=0.1
    )


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    return {
        "name": "Ancient Temple",
        "description": "A weathered stone temple with mysterious carvings on its walls.",
        "connections": {
            "south": "Town Square",
            "east": "Sacred Grove"
        }
    }


# Test: AIService initialization with API key
def test_ai_service_initialization_with_api_key(basic_config):
    """Test AIService can be initialized with an AIConfig containing API key."""
    service = AIService(basic_config)
    
    assert service.config == basic_config
    assert service.config.api_key == "test-key-123"


# Test: AIService initialization with env var (via config)
def test_ai_service_initialization_with_env_var(monkeypatch):
    """Test AIService works with config from environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key-456")
    
    config = AIConfig.from_env()
    service = AIService(config)
    
    assert service.config.api_key == "env-key-456"


# Test: Generate location returns valid structure
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_returns_valid_structure(mock_openai_class, basic_config, mock_openai_response):
    """Test generate_location returns a dict with name, description, and connections."""
    # Setup mock
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    # Create service and generate location
    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")
    
    # Verify structure (no connections - WFC handles terrain structure)
    assert "name" in result
    assert "description" in result
    assert "category" in result
    assert "npcs" in result
    assert "connections" not in result  # AI no longer generates connections
    assert isinstance(result["name"], str)
    assert isinstance(result["description"], str)


# Test: Generate location validates constraints
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_validates_constraints(mock_openai_class, basic_config):
    """Test generate_location validates name/description length limits."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # Test with name too long (>50 chars)
    invalid_response = {
        "name": "A" * 51,  # Too long
        "description": "Valid description",
        "connections": {}
    }
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(basic_config)
    
    with pytest.raises(AIGenerationError, match="name"):
        service.generate_location(theme="fantasy")


# Test: Generate location accepts context parameters
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_accepts_context_parameters(mock_openai_class, basic_config, mock_openai_response):
    """Test generate_location accepts and uses context parameters."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(basic_config)
    
    # Call with all context parameters
    result = service.generate_location(
        theme="cyberpunk",
        context_locations=["Neon District", "Data Hub"],
        source_location="Neon District",
        direction="north"
    )
    
    # Verify it returns valid result (parameters were accepted)
    assert result is not None
    assert "name" in result


# Test: API error raises exception
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_with_api_error_raises_exception(mock_openai_class, basic_config):
    """Test generate_location raises AIServiceError when API call fails."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # Simulate API error
    mock_client.chat.completions.create.side_effect = Exception("API connection failed")
    
    service = AIService(basic_config)
    
    with pytest.raises(AIServiceError):
        service.generate_location(theme="fantasy")


# Test: Timeout raises exception
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_with_timeout_raises_exception(mock_openai_class, basic_config):
    """Test generate_location raises AITimeoutError when request times out."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # Simulate timeout error
    import openai
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError(request=Mock())
    
    service = AIService(basic_config)
    
    with pytest.raises(AITimeoutError):
        service.generate_location(theme="fantasy")


# Test: Connections from AI are ignored (WFC handles terrain structure)
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_connections_ignored(mock_openai_class, basic_config):
    """Test generate_location ignores connections from AI response.

    Connections are now determined by WFC terrain adjacency, not AI suggestions.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with connections (should be ignored)
    response_with_connections = {
        "name": "Test Location",
        "description": "A test location",
        "connections": {
            "north": "Some Location",
            "south": "Another Location"
        },
        "category": "wilderness"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_with_connections)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Connections should NOT be in the result (WFC handles terrain structure)
    assert "connections" not in result
    assert result["name"] == "Test Location"
    assert result["category"] == "wilderness"


# Test: Caching enabled
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_caching_enabled(mock_openai_class, mock_openai_response, tmp_path):
    """Test generate_location uses cache when enabled."""
    # Config with caching enabled
    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )
    
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(config)
    
    # First call - should hit API
    result1 = service.generate_location(theme="fantasy", context_locations=["Town"])
    
    # Second call with same parameters - should hit cache
    result2 = service.generate_location(theme="fantasy", context_locations=["Town"])
    
    # API should only be called once
    assert mock_client.chat.completions.create.call_count == 1
    
    # Results should be the same
    assert result1 == result2


# Test: Prompt includes context
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_prompt_includes_context(mock_openai_class, basic_config, mock_openai_response):
    """Test generate_location builds prompt that includes context information."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    service.generate_location(
        theme="sci-fi",
        context_locations=["Space Station", "Docking Bay"],
        terrain_type="space"
    )

    # Get the actual call arguments
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    prompt = messages[0]["content"]

    # Verify context is in prompt (note: source/direction no longer used)
    assert "sci-fi" in prompt
    assert "Space Station" in prompt or "space station" in prompt.lower()
    assert "space" in prompt.lower()  # terrain_type


# Test: Configurable model
@patch('cli_rpg.ai_service.OpenAI')
def test_ai_service_configurable_model(mock_openai_class, mock_openai_response, tmp_path):
    """Test AIService uses the configured model."""
    config = AIConfig(
        api_key="test-key",
        model="gpt-4",
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )
    
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(config)
    service.generate_location(theme="fantasy")
    
    # Verify correct model was used
    call_args = mock_client.chat.completions.create.call_args
    assert call_args[1]["model"] == "gpt-4"


# Test: Configurable temperature
@patch('cli_rpg.ai_service.OpenAI')
def test_ai_service_configurable_temperature(mock_openai_class, mock_openai_response, tmp_path):
    """Test AIService uses the configured temperature."""
    config = AIConfig(
        api_key="test-key",
        temperature=0.9,
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )
    
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(config)
    service.generate_location(theme="fantasy")
    
    # Verify correct temperature was used
    call_args = mock_client.chat.completions.create.call_args
    assert call_args[1]["temperature"] == 0.9


# Test: Retry on transient error
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_retry_on_transient_error(mock_openai_class, basic_config, mock_openai_response):
    """Test generate_location retries on transient errors."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # First call fails, second succeeds
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    
    import openai
    mock_client.chat.completions.create.side_effect = [
        openai.APIConnectionError(request=Mock()),  # First call fails
        mock_response  # Second call succeeds
    ]
    
    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")
    
    # Should succeed after retry
    assert result is not None
    assert mock_client.chat.completions.create.call_count == 2


# Test: Max retries exceeded
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_max_retries_exceeded(mock_openai_class, basic_config):
    """Test generate_location raises error when max retries exceeded."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # All calls fail
    import openai
    mock_client.chat.completions.create.side_effect = openai.APIConnectionError(request=Mock())
    
    service = AIService(basic_config)
    
    with pytest.raises(AIServiceError):
        service.generate_location(theme="fantasy")
    
    # Should have tried max_retries + 1 times (initial + retries)
    assert mock_client.chat.completions.create.call_count == basic_config.max_retries + 1


# Test: Invalid JSON response
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_invalid_json_response(mock_openai_class, basic_config):
    """Test generate_location handles invalid JSON responses."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is not valid JSON"
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(basic_config)
    
    with pytest.raises(AIGenerationError, match="parse"):
        service.generate_location(theme="fantasy")


# Test: Missing required fields in response
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_missing_required_fields(mock_openai_class, basic_config):
    """Test generate_location handles responses missing required fields."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    # Response missing 'description' field
    incomplete_response = {
        "name": "Test Location",
        "connections": {}
        # Missing 'description'
    }
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(incomplete_response)
    mock_client.chat.completions.create.return_value = mock_response
    
    service = AIService(basic_config)
    
    with pytest.raises(AIGenerationError, match="required field"):
        service.generate_location(theme="fantasy")


# Test: AIService initialization with Anthropic provider
@patch('cli_rpg.ai_service.Anthropic')
def test_ai_service_initialization_with_anthropic(mock_anthropic_class):
    """Test AIService creates Anthropic client when provider is 'anthropic'."""
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        retry_delay=0.1
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    service = AIService(config)

    assert service.provider == "anthropic"
    mock_anthropic_class.assert_called_once_with(api_key="anthropic-test-key")


# Test: Generate location with Anthropic provider
@patch('cli_rpg.ai_service.Anthropic')
def test_generate_location_with_anthropic(mock_anthropic_class, tmp_path):
    """Test generate_location calls Anthropic API correctly and returns valid location."""
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    # Simulate Anthropic API response structure (no connections - WFC handles terrain)
    location_data = {
        "name": "Mystic Forest",
        "description": "A dark and mysterious forest filled with ancient trees.",
        "category": "forest"
    }

    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = json.dumps(location_data)
    mock_client.messages.create.return_value = mock_response

    service = AIService(config)
    result = service.generate_location(theme="fantasy")

    # Verify result (no connections - WFC handles terrain structure)
    assert result["name"] == "Mystic Forest"
    assert result["description"] == "A dark and mysterious forest filled with ancient trees."
    assert "connections" not in result

    # Verify Anthropic API was called correctly
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-3-5-sonnet-latest"
    assert call_kwargs["max_tokens"] == 3000
    assert len(call_kwargs["messages"]) == 1
    assert call_kwargs["messages"][0]["role"] == "user"


# Test: AI connections are completely ignored (WFC handles terrain)
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_ignores_all_connections(mock_openai_class, basic_config):
    """Test generate_location ignores all connections from AI.

    WFC handles terrain structure - AI only provides content (name, description, etc).
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with connections (should be completely ignored)
    response_with_connections = {
        "name": "Neon Nexus",
        "description": "A hub of pulsing energy and data streams.",
        "connections": {
            "north": "Crystal Spire",
            "down": "Underground Lab",
            "east": "Data Center"
        },
        "category": "dungeon"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_with_connections)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="cyberpunk")

    # Connections should not be in result at all (WFC handles terrain)
    assert "connections" not in result
    assert result["name"] == "Neon Nexus"
    assert result["category"] == "dungeon"


# Test: AI returns content without connections (preferred format)
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_works_without_connections(mock_openai_class, basic_config):
    """Test generate_location works when AI doesn't include connections.

    This is the preferred response format - AI only provides content.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response without connections (correct format)
    response_without_connections = {
        "name": "Sky Tower Base",
        "description": "The base of a towering structure reaching into the clouds.",
        "category": "settlement"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_without_connections)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="sci-fi")

    # Result should have content but no connections
    assert result["name"] == "Sky Tower Base"
    assert result["category"] == "settlement"
    assert "connections" not in result


# Test: Area generation returns locations without connections - spec: coordinate-based navigation
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_area_returns_locations_without_connections(mock_openai_class, basic_config):
    """Test generate_area returns locations without connections field.

    Navigation is coordinate-based via SubGrid/WorldGrid, so connections
    are not included in the parsed response.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Area response with connections (AI still generates them, but we ignore them)
    area_response = [
        {
            "name": "Dungeon Entrance",
            "description": "A dark entrance leading into the depths below.",
            "relative_coords": [0, 0],
            "connections": {
                "south": "EXISTING_WORLD",
                "north": "First Chamber"
            }
        },
        {
            "name": "First Chamber",
            "description": "A dusty chamber with ancient markings.",
            "relative_coords": [0, 1],
            "connections": {
                "south": "Dungeon Entrance",
                "east": "Treasure Room"
            }
        },
        {
            "name": "Treasure Room",
            "description": "A room filled with glittering treasures.",
            "relative_coords": [1, 1],
            "connections": {
                "west": "First Chamber"
            }
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="dungeon",
        entry_direction="north",
        context_locations=["Village"],
        size=3
    )

    # Verify connections are not included in parsed response
    for location in result:
        assert "connections" not in location, \
            f"Found 'connections' in location '{location['name']}' but navigation is coordinate-based"
        # Verify required fields are present
        assert "name" in location
        assert "description" in location
        assert "relative_coords" in location


# ========================================================================
# Anthropic Provider Edge Case Tests (Coverage for lines 278-306)
# ========================================================================

# Test: Anthropic timeout error raises AITimeoutError - spec: timeout handling for Anthropic API
@patch('cli_rpg.ai_service.Anthropic')
@patch('cli_rpg.ai_service.anthropic_module')
def test_anthropic_timeout_error_raises_ai_timeout_error(mock_anthropic_module, mock_anthropic_class, tmp_path):
    """Test Anthropic API timeout raises AITimeoutError after retries.

    Spec: When Anthropic API times out, retry with exponential backoff and raise
    AITimeoutError if all retries exhausted (lines 281-286).
    """
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        max_retries=2,
        retry_delay=0.01,  # Fast retry for tests
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    # Create a mock APITimeoutError class
    mock_timeout_error = type('APITimeoutError', (Exception,), {})
    mock_anthropic_module.APITimeoutError = mock_timeout_error
    mock_anthropic_module.APIConnectionError = type('APIConnectionError', (Exception,), {})
    mock_anthropic_module.RateLimitError = type('RateLimitError', (Exception,), {})
    mock_anthropic_module.AuthenticationError = type('AuthenticationError', (Exception,), {})

    # Simulate timeout on all attempts
    mock_client.messages.create.side_effect = mock_timeout_error("Request timed out")

    service = AIService(config)

    with pytest.raises(AITimeoutError, match="timed out"):
        service.generate_location(theme="fantasy")

    # Should have retried (initial + max_retries attempts)
    assert mock_client.messages.create.call_count == config.max_retries + 1


# Test: Anthropic rate limit error retries and fails - spec: rate limit handling for Anthropic API
@patch('cli_rpg.ai_service.Anthropic')
@patch('cli_rpg.ai_service.anthropic_module')
def test_anthropic_rate_limit_error_retries_and_fails(mock_anthropic_module, mock_anthropic_class, tmp_path):
    """Test Anthropic rate limit error retries and raises AIServiceError when exhausted.

    Spec: When Anthropic API returns rate limit error, retry with exponential backoff
    and raise AIServiceError if all retries exhausted (lines 288-293).
    """
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        max_retries=2,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    # Create mock Anthropic error classes
    mock_anthropic_module.APITimeoutError = type('APITimeoutError', (Exception,), {})
    mock_anthropic_module.APIConnectionError = type('APIConnectionError', (Exception,), {})
    mock_rate_limit_error = type('RateLimitError', (Exception,), {})
    mock_anthropic_module.RateLimitError = mock_rate_limit_error
    mock_anthropic_module.AuthenticationError = type('AuthenticationError', (Exception,), {})

    # Simulate rate limit on all attempts
    mock_client.messages.create.side_effect = mock_rate_limit_error("Rate limit exceeded")

    service = AIService(config)

    with pytest.raises(AIServiceError, match="API call failed"):
        service.generate_location(theme="fantasy")

    # Should have retried
    assert mock_client.messages.create.call_count == config.max_retries + 1


# Test: Anthropic auth error raises immediately - spec: auth error should not retry
@patch('cli_rpg.ai_service.Anthropic')
@patch('cli_rpg.ai_service.anthropic_module')
def test_anthropic_auth_error_raises_immediately(mock_anthropic_module, mock_anthropic_class, tmp_path):
    """Test Anthropic authentication error raises immediately without retry.

    Spec: Authentication errors should not be retried - raise AIServiceError
    immediately (lines 295-296).
    """
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        max_retries=3,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    # Create mock Anthropic error classes
    mock_anthropic_module.APITimeoutError = type('APITimeoutError', (Exception,), {})
    mock_anthropic_module.APIConnectionError = type('APIConnectionError', (Exception,), {})
    mock_anthropic_module.RateLimitError = type('RateLimitError', (Exception,), {})
    mock_auth_error = type('AuthenticationError', (Exception,), {})
    mock_anthropic_module.AuthenticationError = mock_auth_error

    # Simulate auth error
    mock_client.messages.create.side_effect = mock_auth_error("Invalid API key")

    service = AIService(config)

    with pytest.raises(AIServiceError, match="Authentication failed"):
        service.generate_location(theme="fantasy")

    # Should NOT have retried - only 1 attempt
    assert mock_client.messages.create.call_count == 1


# Test: Anthropic connection error retries - spec: connection error handling
@patch('cli_rpg.ai_service.Anthropic')
@patch('cli_rpg.ai_service.anthropic_module')
def test_anthropic_connection_error_retries(mock_anthropic_module, mock_anthropic_class, tmp_path):
    """Test Anthropic connection error retries with exponential backoff.

    Spec: When Anthropic API has connection issues, retry and then succeed
    (lines 288-293 - transient error path).
    """
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        max_retries=3,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    # Create mock Anthropic error classes
    mock_anthropic_module.APITimeoutError = type('APITimeoutError', (Exception,), {})
    mock_conn_error = type('APIConnectionError', (Exception,), {})
    mock_anthropic_module.APIConnectionError = mock_conn_error
    mock_anthropic_module.RateLimitError = type('RateLimitError', (Exception,), {})
    mock_anthropic_module.AuthenticationError = type('AuthenticationError', (Exception,), {})

    # Mock successful response after retry
    location_data = {
        "name": "Test Location",
        "description": "A test location for connection retry test.",
        "connections": {"north": "Another Place"}
    }
    import json
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = json.dumps(location_data)

    # First call fails, second succeeds
    mock_client.messages.create.side_effect = [
        mock_conn_error("Connection failed"),
        mock_response
    ]

    service = AIService(config)
    result = service.generate_location(theme="fantasy")

    # Should have retried once then succeeded
    assert mock_client.messages.create.call_count == 2
    assert result["name"] == "Test Location"


# Test: Anthropic provider not available raises error - spec: graceful handling of missing package
@patch('cli_rpg.ai_service.ANTHROPIC_AVAILABLE', False)
def test_anthropic_provider_not_available_raises_error():
    """Test AIService raises AIServiceError when Anthropic package is not installed.

    Spec: When provider=anthropic but anthropic package not installed, raise
    AIServiceError with helpful message (lines 68-72).
    """
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest"
    )

    with pytest.raises(AIServiceError, match="Anthropic provider requested but 'anthropic' package is not installed"):
        AIService(config)


# Test: Anthropic general exception handling - spec: fallback error handling
@patch('cli_rpg.ai_service.Anthropic')
@patch('cli_rpg.ai_service.anthropic_module')
def test_anthropic_general_exception_retries(mock_anthropic_module, mock_anthropic_class, tmp_path):
    """Test Anthropic general exceptions are retried with exponential backoff.

    Spec: Unknown exceptions should be retried and raise AIServiceError when
    exhausted (lines 298-303).
    """
    config = AIConfig(
        api_key="anthropic-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        max_retries=2,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    # Create mock Anthropic error classes (needed for isinstance checks)
    mock_anthropic_module.APITimeoutError = type('APITimeoutError', (Exception,), {})
    mock_anthropic_module.APIConnectionError = type('APIConnectionError', (Exception,), {})
    mock_anthropic_module.RateLimitError = type('RateLimitError', (Exception,), {})
    mock_anthropic_module.AuthenticationError = type('AuthenticationError', (Exception,), {})

    # Simulate a generic exception (not an Anthropic-specific error)
    mock_client.messages.create.side_effect = RuntimeError("Unexpected error")

    service = AIService(config)

    with pytest.raises(AIServiceError, match="API call failed"):
        service.generate_location(theme="fantasy")

    # Should have retried
    assert mock_client.messages.create.call_count == config.max_retries + 1


# ========================================================================
# Area Response Parsing/Validation Tests (Coverage for lines 630-631, 635, 639, etc.)
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_area_response_invalid_json(mock_openai_class, basic_config):
    """Test _parse_area_response raises on invalid JSON (line 630-631).

    Spec: When response_text is not valid JSON, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return invalid JSON
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is not valid JSON at all { bad"
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="parse"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_area_response_not_array(mock_openai_class, basic_config):
    """Test _parse_area_response raises when response is not an array (line 635).

    Spec: When response is valid JSON but not an array, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return an object instead of an array
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "name": "Location",
        "description": "A place"
    })
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="array"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_area_response_empty_array(mock_openai_class, basic_config):
    """Test _parse_area_response raises when array is empty (line 639).

    Spec: When response is an empty array, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return empty array
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "[]"
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="at least one location"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_missing_field(mock_openai_class, basic_config):
    """Test _validate_area_location raises on missing required field (line 666-668).

    Spec: When location is missing a required field, raise AIGenerationError.
    Note: connections is no longer a required field - navigation is coordinate-based.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location missing 'description' (a required field)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        # Missing 'description'
        "relative_coords": [0, 0]
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="missing required field.*description"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_name_too_short(mock_openai_class, basic_config):
    """Test _validate_area_location raises on name too short (line 672-675).

    Spec: When location name is too short, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with name too short
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "A",  # Too short (MIN_NAME_LENGTH is 2)
        "description": "A test location with adequate description length",
        "relative_coords": [0, 0],
        "connections": {}
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="name too short"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_name_too_long(mock_openai_class, basic_config):
    """Test _validate_area_location raises on name too long (line 676-679).

    Spec: When location name is too long, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with name too long (>50 chars)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "A" * 51,  # Too long
        "description": "A test location with adequate description length",
        "relative_coords": [0, 0],
        "connections": {}
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="name too long"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_description_too_short(mock_openai_class, basic_config):
    """Test _validate_area_location raises on description too short (line 683-686).

    Spec: When location description is too short, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with empty description (MIN_DESCRIPTION_LENGTH is 1)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        "description": "",  # Empty description - too short
        "relative_coords": [0, 0],
        "connections": {}
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="description too short"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_description_too_long(mock_openai_class, basic_config):
    """Test _validate_area_location raises on description too long (line 687-690).

    Spec: When location description is too long, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with description too long (>500 chars)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        "description": "A" * 501,  # Too long
        "relative_coords": [0, 0],
        "connections": {}
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="description too long"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_invalid_coords(mock_openai_class, basic_config):
    """Test _validate_area_location raises on invalid coordinates (line 694-697).

    Spec: When relative_coords is not a [x, y] array, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with invalid coords (not an array)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        "description": "A test location with adequate description length",
        "relative_coords": "invalid",  # Should be [x, y]
        "connections": {}
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="relative_coords"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_coords_wrong_length(mock_openai_class, basic_config):
    """Test _validate_area_location raises on coords with wrong length (line 694-697).

    Spec: When relative_coords has wrong number of elements, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with wrong number of coordinates
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        "description": "A test location with adequate description length",
        "relative_coords": [0, 0, 0],  # Should be [x, y], not [x, y, z]
        "connections": {}
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="relative_coords"):
        service.generate_area(
            theme="fantasy",
            sub_theme_hint="forest",
            entry_direction="north",
            context_locations=[],
            size=3
        )



# ========================================================================
# _parse_location_response Validation Edge Cases (Coverage for lines 338, 349, 353, 360)
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_location_response_name_too_short(mock_openai_class, basic_config):
    """Test _parse_location_response raises when name is too short (line 338).

    Spec: When location name has fewer than MIN_NAME_LENGTH chars, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with name too short
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "name": "A",  # Too short - Location.MIN_NAME_LENGTH is 2
        "description": "A valid description that meets the minimum length requirement for testing.",
        "connections": {}
    })
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="name too short"):
        service.generate_location(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_location_response_description_too_short(mock_openai_class, basic_config):
    """Test _parse_location_response raises when description is too short (line 349).

    Spec: When location description has fewer than MIN_DESCRIPTION_LENGTH chars, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with empty description
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "name": "Test Location",
        "description": "",  # Empty - too short
        "connections": {}
    })
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="description too short"):
        service.generate_location(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_location_response_description_too_long(mock_openai_class, basic_config):
    """Test _parse_location_response raises when description is too long (line 353).

    Spec: When location description exceeds MAX_DESCRIPTION_LENGTH chars, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with description too long (>500 chars)
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "name": "Test Location",
        "description": "A" * 501,  # Too long - Location.MAX_DESCRIPTION_LENGTH is 500
        "connections": {}
    })
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="description too long"):
        service.generate_location(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_location_response_connections_ignored_not_validated(mock_openai_class, basic_config):
    """Test _parse_location_response ignores invalid connections (no validation).

    Spec: connections field is ignored (WFC handles terrain), so invalid
    connections type should not cause an error.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with invalid connections type - should be ignored
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "name": "Test Location",
        "description": "A valid description that meets the minimum length requirement.",
        "connections": ["north", "south"],  # Invalid type - but ignored now
        "category": "wilderness"
    })
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    # Should NOT raise - connections are ignored
    result = service.generate_location(theme="fantasy")
    assert result["name"] == "Test Location"
    assert "connections" not in result


# ========================================================================
# Cache Expiration Tests (Coverage for lines 399, 741)
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
@patch('cli_rpg.ai_service.time')
def test_get_cached_expired_entry_deleted(mock_time, mock_openai_class, tmp_path):
    """Test _get_cached deletes expired entries from cache (line 399).

    Spec: When a cached entry's timestamp is older than cache_ttl, delete it
    from the cache and return None.
    """
    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_ttl=3600,  # 1 hour
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Create a valid location response
    location_data = {
        "name": "Test Location",
        "description": "A valid description that meets the minimum length requirement.",
        "connections": {"north": "Another Location"}
    }
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(location_data)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(config)

    # First call - time is 0, cache gets populated
    mock_time.time.return_value = 0
    service.generate_location(theme="fantasy")
    assert mock_client.chat.completions.create.call_count == 1

    # Second call - time is beyond cache_ttl (4000 > 3600)
    # This should trigger the expired entry deletion (line 399)
    mock_time.time.return_value = 4000
    service.generate_location(theme="fantasy")

    # API should be called again because cache was expired
    assert mock_client.chat.completions.create.call_count == 2


@patch('cli_rpg.ai_service.OpenAI')
@patch('cli_rpg.ai_service.time')
def test_get_cached_list_expired_entry_deleted(mock_time, mock_openai_class, tmp_path):
    """Test _get_cached_list deletes expired entries from cache (line 741).

    Spec: When a cached list entry's timestamp is older than cache_ttl, delete it
    from the cache and return None.
    """
    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_ttl=3600,  # 1 hour
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Create a valid area response (list of locations)
    area_data = [
        {
            "name": "Test Location",
            "description": "A valid description that meets the minimum length requirement.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"}
        }
    ]
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_data)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(config)

    # First call - time is 0, cache gets populated
    mock_time.time.return_value = 0
    service.generate_area(
        theme="fantasy",
        sub_theme_hint="forest",
        entry_direction="north",
        context_locations=[],
        size=1
    )
    assert mock_client.chat.completions.create.call_count == 1

    # Second call - time is beyond cache_ttl (4000 > 3600)
    # This should trigger the expired entry deletion (line 741)
    mock_time.time.return_value = 4000
    service.generate_area(
        theme="fantasy",
        sub_theme_hint="forest",
        entry_direction="north",
        context_locations=[],
        size=1
    )

    # API should be called again because cache was expired
    assert mock_client.chat.completions.create.call_count == 2


# ========================================================================
# Cache File Configuration Tests (Coverage for lines 423, 455)
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_load_cache_no_cache_file_configured(mock_openai_class):
    """Test _load_cache_from_file returns early when no cache file (line 423).

    Spec: When config.cache_file is None/empty, return immediately without
    attempting to load from disk.
    """
    # Config with caching disabled results in cache_file being None
    config = AIConfig(
        api_key="test-key",
        enable_caching=False,  # This keeps cache_file as None
        retry_delay=0.1
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # This should not raise any file-related errors
    service = AIService(config)

    # Verify the service was created successfully with no cache file
    assert service.config.cache_file is None


@patch('cli_rpg.ai_service.OpenAI')
def test_save_cache_no_cache_file_configured(mock_openai_class):
    """Test _save_cache_to_file returns early when no cache file (line 455).

    Spec: When config.cache_file is None/empty, return immediately without
    attempting to write to disk.
    """
    config = AIConfig(
        api_key="test-key",
        enable_caching=False,  # This keeps cache_file as None
        retry_delay=0.1
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    location_data = {
        "name": "Test Location",
        "description": "A valid description that meets the minimum length requirement.",
        "connections": {}
    }
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(location_data)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(config)

    # This should work without trying to save to file
    result = service.generate_location(theme="fantasy")

    # Verify result is correct
    assert result["name"] == "Test Location"


# ========================================================================
# OpenAI RateLimitError Tests (Coverage for lines 253-257)
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_openai_rate_limit_error_retries_and_fails(mock_openai_class, basic_config):
    """Test OpenAI rate limit error retries and raises AIServiceError when exhausted.

    Spec: When OpenAI API returns rate limit error (lines 251-257), retry with
    exponential backoff and raise AIServiceError if all retries exhausted.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Simulate rate limit on all attempts
    import openai
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        message="Rate limit exceeded",
        response=Mock(),
        body=None
    )

    service = AIService(basic_config)

    with pytest.raises(AIServiceError, match="API call failed"):
        service.generate_location(theme="fantasy")

    # Should have retried (initial + max_retries attempts)
    assert mock_client.chat.completions.create.call_count == basic_config.max_retries + 1


@patch('cli_rpg.ai_service.OpenAI')
def test_openai_rate_limit_error_retries_then_succeeds(mock_openai_class, basic_config, mock_openai_response):
    """Test OpenAI rate limit error retries and succeeds on subsequent attempt.

    Spec: When OpenAI API returns rate limit error initially (lines 251-256), retry
    with exponential backoff and succeed when the API recovers.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    import openai
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)

    # First call rate limited, second succeeds
    mock_client.chat.completions.create.side_effect = [
        openai.RateLimitError(message="Rate limit", response=Mock(), body=None),
        mock_response
    ]

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    assert result is not None
    assert result["name"] == "Ancient Temple"
    assert mock_client.chat.completions.create.call_count == 2


# ========================================================================
# OpenAI AuthenticationError Tests (Coverage for line 261)
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_openai_auth_error_raises_immediately(mock_openai_class, basic_config):
    """Test OpenAI authentication error raises immediately without retry.

    Spec: When OpenAI API returns authentication error (line 261), do NOT retry -
    raise AIServiceError immediately with 'Authentication failed' message.
    Covers line 261: raise AIServiceError(f"Authentication failed: {str(e)}") from e
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    import openai
    # Simulate authentication error
    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        message="Invalid API key provided",
        response=Mock(),
        body=None
    )

    service = AIService(basic_config)

    with pytest.raises(AIServiceError, match="Authentication failed"):
        service.generate_location(theme="fantasy")

    # Should NOT have retried - only 1 attempt
    assert mock_client.chat.completions.create.call_count == 1


# ========================================================================
# NPC Generation in Location Response Tests
# Spec: AI-generated locations should include NPCs appropriate to the location
# ========================================================================


# Test: generate_location parses NPCs from response
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_parses_npcs(mock_openai_class, basic_config):
    """Test generate_location parses NPC data from AI response.

    Spec: When AI response includes 'npcs' field, parse it and include in result.
    NPCs should have name, description, dialogue, and role fields.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with NPCs
    response_with_npcs = {
        "name": "Village Square",
        "description": "A peaceful village square with a well.",
        "connections": {"north": "Forest Path"},
        "npcs": [
            {
                "name": "Elder Thomas",
                "description": "A wise old man with a long beard.",
                "dialogue": "Welcome to our village, traveler.",
                "role": "villager"
            },
            {
                "name": "Merchant Bella",
                "description": "A cheerful merchant with colorful wares.",
                "dialogue": "Looking for something special?",
                "role": "merchant"
            }
        ]
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_with_npcs)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify NPCs are parsed
    assert "npcs" in result
    assert len(result["npcs"]) == 2
    assert result["npcs"][0]["name"] == "Elder Thomas"
    assert result["npcs"][0]["role"] == "villager"
    assert result["npcs"][1]["name"] == "Merchant Bella"
    assert result["npcs"][1]["role"] == "merchant"


# Test: generate_location handles empty npcs field
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_handles_empty_npcs(mock_openai_class, basic_config):
    """Test generate_location handles empty npcs field gracefully.

    Spec: When AI response includes empty 'npcs' array, return empty list.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response_empty_npcs = {
        "name": "Abandoned Ruins",
        "description": "Ancient ruins with no sign of life.",
        "connections": {"south": "Town Square"},
        "npcs": []
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_empty_npcs)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify empty list is returned
    assert "npcs" in result
    assert result["npcs"] == []


# Test: generate_location handles missing npcs field
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_handles_missing_npcs(mock_openai_class, basic_config, mock_openai_response):
    """Test generate_location handles missing npcs field gracefully.

    Spec: When AI response does not include 'npcs' field, default to empty list.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # mock_openai_response doesn't have npcs field
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify empty list is returned when npcs field is missing
    assert "npcs" in result
    assert result["npcs"] == []


# Test: generate_location validates NPC name length
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_validates_npc_name_length(mock_openai_class, basic_config):
    """Test generate_location validates NPC name length.

    Spec: NPC names must be 2-30 characters. Invalid NPCs are logged and skipped.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response_invalid_npc = {
        "name": "Village Square",
        "description": "A peaceful village square.",
        "connections": {},
        "npcs": [
            {
                "name": "A",  # Too short - should be skipped
                "description": "An invalid NPC.",
                "dialogue": "Hello.",
                "role": "villager"
            },
            {
                "name": "Valid Villager",  # Valid - should be kept
                "description": "A friendly villager.",
                "dialogue": "Good day!",
                "role": "villager"
            }
        ]
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_invalid_npc)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Only valid NPC should be in result
    assert len(result["npcs"]) == 1
    assert result["npcs"][0]["name"] == "Valid Villager"


# Test: generate_location validates NPC description length
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_validates_npc_description_length(mock_openai_class, basic_config):
    """Test generate_location validates NPC description length.

    Spec: NPC descriptions must be 1-200 characters. Invalid NPCs are skipped.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response_invalid_desc = {
        "name": "Village Square",
        "description": "A peaceful village square.",
        "connections": {},
        "npcs": [
            {
                "name": "Empty Description NPC",
                "description": "",  # Too short - should be skipped
                "dialogue": "Hello.",
                "role": "villager"
            },
            {
                "name": "Long Description NPC",
                "description": "A" * 201,  # Too long - should be skipped
                "dialogue": "Hello.",
                "role": "villager"
            },
            {
                "name": "Valid NPC",
                "description": "A valid description.",
                "dialogue": "Hello.",
                "role": "villager"
            }
        ]
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_invalid_desc)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Only valid NPC should be in result
    assert len(result["npcs"]) == 1
    assert result["npcs"][0]["name"] == "Valid NPC"


# Test: generate_area parses NPCs from response
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_area_parses_npcs(mock_openai_class, basic_config):
    """Test generate_area parses NPC data from area locations.

    Spec: When area locations include 'npcs' field, parse it for each location.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response_with_npcs = [
        {
            "name": "Forest Entry",
            "description": "The entrance to a mystical forest.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"},
            "npcs": [
                {
                    "name": "Forest Guardian",
                    "description": "A mystical being protecting the forest.",
                    "dialogue": "State your purpose, traveler.",
                    "role": "quest_giver"
                }
            ]
        },
        {
            "name": "Deep Woods",
            "description": "Deep in the forest.",
            "relative_coords": [0, 1],
            "connections": {"south": "Forest Entry"},
            "npcs": []  # Empty NPCs
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response_with_npcs)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="forest",
        entry_direction="north",
        context_locations=[],
        size=2
    )

    # Verify NPCs are parsed for first location
    assert "npcs" in result[0]
    assert len(result[0]["npcs"]) == 1
    assert result[0]["npcs"][0]["name"] == "Forest Guardian"
    assert result[0]["npcs"][0]["role"] == "quest_giver"

    # Verify empty NPCs for second location
    assert "npcs" in result[1]
    assert result[1]["npcs"] == []


# Test: generate_area handles missing npcs field
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_area_handles_missing_npcs(mock_openai_class, basic_config):
    """Test generate_area handles missing npcs field gracefully.

    Spec: When area locations don't include 'npcs' field, default to empty list.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response_no_npcs = [
        {
            "name": "Cave Entry",
            "description": "A dark cave entrance.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"}
            # No 'npcs' field
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response_no_npcs)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="cave",
        entry_direction="north",
        context_locations=[],
        size=1
    )

    # Verify empty list is returned when npcs field is missing
    assert "npcs" in result[0]
    assert result[0]["npcs"] == []


# Test: NPC role defaults to villager when missing
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_npc_role_defaults_to_villager(mock_openai_class, basic_config):
    """Test NPC role defaults to 'villager' when not specified.

    Spec: If role is missing or invalid, default to 'villager'.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response_no_role = {
        "name": "Village Square",
        "description": "A peaceful village square.",
        "connections": {},
        "npcs": [
            {
                "name": "Simple Farmer",
                "description": "A hardworking farmer.",
                "dialogue": "Fine day for farming!"
                # No 'role' field
            }
        ]
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_no_role)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify role defaults to villager
    assert result["npcs"][0]["role"] == "villager"


# ========================================================================
# JSON Extraction from Markdown Code Blocks Tests
# Spec: Extract JSON from markdown ```json...``` or ```...``` code blocks
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_extract_json_from_markdown_code_block(mock_openai_class, basic_config):
    """Test _extract_json_from_response extracts JSON from ```json...``` block.

    Spec: When response contains a markdown code block with json language tag,
    extract the JSON content from inside the block.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Test with markdown-wrapped JSON
    markdown_response = '''Here is the location data:

```json
{
    "name": "Test Location",
    "description": "A test location",
    "connections": {}
}
```

That's the location.'''

    result = service._extract_json_from_response(markdown_response)
    expected = '''{
    "name": "Test Location",
    "description": "A test location",
    "connections": {}
}'''
    assert result == expected


@patch('cli_rpg.ai_service.OpenAI')
def test_extract_json_from_plain_code_block(mock_openai_class, basic_config):
    """Test _extract_json_from_response extracts JSON from plain ``` block.

    Spec: When response contains a markdown code block without language tag,
    extract the content from inside the block.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Test with plain code block (no language tag)
    plain_block_response = '''```
{"name": "Plain Location", "description": "A plain test", "connections": {"north": "Town"}}
```'''

    result = service._extract_json_from_response(plain_block_response)
    assert result == '{"name": "Plain Location", "description": "A plain test", "connections": {"north": "Town"}}'


@patch('cli_rpg.ai_service.OpenAI')
def test_extract_json_returns_original_when_no_block(mock_openai_class, basic_config):
    """Test _extract_json_from_response returns original when no code block.

    Spec: When response does not contain a markdown code block, return the
    original text stripped of whitespace.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Test without code block
    plain_json = '{"name": "Direct JSON", "description": "No wrapper", "connections": {}}'

    result = service._extract_json_from_response(plain_json)
    assert result == plain_json


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_handles_markdown_wrapped_json(mock_openai_class, basic_config):
    """Test generate_location handles markdown-wrapped JSON responses.

    Spec: When AI returns JSON wrapped in markdown code blocks, extract the
    JSON and parse it successfully. This is an integration test for the
    full flow from API response to parsed location.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response wrapped in markdown code block (no connections - WFC handles terrain)
    markdown_wrapped = '''Sure! Here's a location for your fantasy world:

```json
{
    "name": "Enchanted Grove",
    "description": "A mystical grove where ancient trees whisper secrets.",
    "category": "forest"
}
```

Hope this helps!'''

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = markdown_wrapped
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify the location was parsed correctly (no connections)
    assert result["name"] == "Enchanted Grove"
    assert result["description"] == "A mystical grove where ancient trees whisper secrets."
    assert result["category"] == "forest"
    assert "connections" not in result


# ========================================================================
# JSON Repair for Truncated AI Responses Tests
# Spec: Attempt to repair truncated JSON by closing unclosed brackets
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_repair_truncated_json_unclosed_object(mock_openai_class, basic_config):
    """Test _repair_truncated_json repairs unclosed object braces.

    Spec: When JSON has unclosed `{`, append matching `}` to fix it.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Truncated JSON with unclosed object
    truncated = '{"name": "Test"'
    repaired = service._repair_truncated_json(truncated)

    # Verify it can be parsed as valid JSON
    data = json.loads(repaired)
    assert data["name"] == "Test"


@patch('cli_rpg.ai_service.OpenAI')
def test_repair_truncated_json_unclosed_array(mock_openai_class, basic_config):
    """Test _repair_truncated_json repairs unclosed arrays.

    Spec: When JSON has unclosed `[`, append matching `]` to fix it.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Truncated JSON with unclosed array
    truncated = '[{"name": "A"}'
    repaired = service._repair_truncated_json(truncated)

    # Verify it can be parsed as valid JSON
    data = json.loads(repaired)
    assert len(data) == 1
    assert data[0]["name"] == "A"


@patch('cli_rpg.ai_service.OpenAI')
def test_repair_truncated_json_nested_brackets(mock_openai_class, basic_config):
    """Test _repair_truncated_json repairs nested unclosed brackets.

    Spec: When JSON has multiple unclosed brackets, close them in correct order.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Truncated JSON with nested unclosed brackets
    truncated = '{"items": [{"a": 1}'
    repaired = service._repair_truncated_json(truncated)

    # Verify it can be parsed as valid JSON
    data = json.loads(repaired)
    assert data["items"][0]["a"] == 1


@patch('cli_rpg.ai_service.OpenAI')
def test_repair_truncated_string_value(mock_openai_class, basic_config):
    """Test _repair_truncated_json repairs truncated string values.

    Spec: When JSON has unclosed string (odd number of unescaped quotes),
    close the string before closing brackets.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Truncated JSON with unclosed string
    truncated = '{"name": "Trunc'
    repaired = service._repair_truncated_json(truncated)

    # Verify it can be parsed as valid JSON
    data = json.loads(repaired)
    assert data["name"] == "Trunc"


@patch('cli_rpg.ai_service.OpenAI')
def test_repair_json_fails_gracefully(mock_openai_class, basic_config):
    """Test unrepairable JSON still raises AIGenerationError.

    Spec: When JSON cannot be repaired (e.g., completely invalid syntax),
    the original JSONDecodeError should be wrapped in AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return completely invalid JSON that can't be repaired
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is {not} valid JSON: at all"
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="parse"):
        service.generate_location(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_with_truncated_response(mock_openai_class, basic_config):
    """Test generate_location handles truncated JSON responses via repair.

    Spec: When AI returns truncated JSON (e.g., due to max_tokens limit),
    the repair mechanism should fix it and return valid location data.
    This is an integration test for the full flow from truncated API response
    to successfully parsed location.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Simulating a truncated response (missing closing brace)
    truncated_response = '{"name": "Mystic Cave", "description": "A dark and mysterious cave with ancient runes.", "category": "cave"'

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = truncated_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify the location was parsed correctly after repair (no connections)
    assert result["name"] == "Mystic Cave"
    assert result["description"] == "A dark and mysterious cave with ancient runes."
    assert result["category"] == "cave"
    assert "connections" not in result


@patch('cli_rpg.ai_service.OpenAI')
def test_repair_truncated_json_returns_original_when_balanced(mock_openai_class, basic_config):
    """Test _repair_truncated_json returns original text when brackets are balanced.

    Spec: When JSON already has balanced brackets, return it unchanged.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    service = AIService(basic_config)

    # Already valid JSON
    valid = '{"name": "Test"}'
    repaired = service._repair_truncated_json(valid)

    # Should be unchanged
    assert repaired == valid


# ========================================================================
# Parse Failure Logging Tests
# Spec: When JSON parsing fails, log the full response at DEBUG level for debugging
# ========================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_failure_logs_full_response(mock_openai_class, basic_config, caplog):
    """Test parse failures log the full AI response at DEBUG level.

    Spec: When JSON parsing fails, log the full response for debugging.
    """
    import logging

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return invalid JSON
    invalid_response = "This is not valid JSON { broken"
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = invalid_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(AIGenerationError):
            service.generate_location(theme="fantasy")

    # Verify the full response was logged
    assert "This is not valid JSON { broken" in caplog.text
    assert "parse failure" in caplog.text.lower()
    assert "(location)" in caplog.text


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_area_failure_logs_full_response(mock_openai_class, basic_config, caplog):
    """Test area parse failures log the full AI response at DEBUG level.

    Spec: When area JSON parsing fails, log the full response for debugging.
    """
    import logging

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    invalid_response = "Not a valid JSON array at all { }"
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = invalid_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(AIGenerationError):
            service.generate_area(
                theme="fantasy",
                sub_theme_hint="forest",
                entry_direction="north",
                context_locations=[],
                size=3
            )

    assert "Not a valid JSON array at all" in caplog.text
    assert "(area)" in caplog.text


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_enemy_failure_logs_full_response(mock_openai_class, basic_config, caplog):
    """Test enemy parse failures log the full AI response at DEBUG level.

    Spec: When enemy JSON parsing fails, log the full response for debugging.
    """
    import logging

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    invalid_response = "Enemy data: { invalid json structure"
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = invalid_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(AIGenerationError):
            service.generate_enemy(
                theme="fantasy",
                location_name="Dark Forest",
                player_level=5
            )

    assert "Enemy data: { invalid json structure" in caplog.text
    assert "(enemy)" in caplog.text


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_item_failure_logs_full_response(mock_openai_class, basic_config, caplog):
    """Test item parse failures log the full AI response at DEBUG level.

    Spec: When item JSON parsing fails, log the full response for debugging.
    """
    import logging

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    invalid_response = "Here's an item: {broken json"
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = invalid_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(AIGenerationError):
            service.generate_item(
                theme="fantasy",
                location_name="Castle",
                player_level=3
            )

    assert "Here's an item: {broken json" in caplog.text
    assert "(item)" in caplog.text


@patch('cli_rpg.ai_service.OpenAI')
def test_parse_quest_failure_logs_full_response(mock_openai_class, basic_config, caplog):
    """Test quest parse failures log the full AI response at DEBUG level.

    Spec: When quest JSON parsing fails, log the full response for debugging.
    """
    import logging

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    invalid_response = "Quest details: malformed {json content"
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = invalid_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(AIGenerationError):
            service.generate_quest(
                theme="fantasy",
                npc_name="Elder Thomas",
                player_level=5,
                location_name="Village"
            )

    assert "Quest details: malformed {json content" in caplog.text
    assert "(quest)" in caplog.text


# ============================================================================
# Tests: generate_world_context() (Layer 1 World Context Generation)
# ============================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_world_context_returns_valid_world_context(mock_openai_class, basic_config):
    """Test generate_world_context returns a valid WorldContext.

    Spec: Method returns WorldContext with AI-generated theme_essence, naming_style, tone.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Valid JSON response with all required fields
    valid_response = {
        "theme_essence": "A dark and mysterious medieval world shrouded in shadow.",
        "naming_style": "Old English with Gothic influence",
        "tone": "grim, foreboding, with flickers of hope"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(valid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_world_context(theme="fantasy")

    # Verify result is WorldContext with correct fields
    assert isinstance(result, WorldContext)
    assert result.theme == "fantasy"
    assert result.theme_essence == valid_response["theme_essence"]
    assert result.naming_style == valid_response["naming_style"]
    assert result.tone == valid_response["tone"]
    assert result.generated_at is not None


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_world_context_validates_required_fields(mock_openai_class, basic_config):
    """Test generate_world_context raises AIGenerationError for missing fields.

    Spec: Missing required fields (theme_essence, naming_style, tone) raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response missing 'naming_style' field
    invalid_response = {
        "theme_essence": "A dark world.",
        "tone": "grim"
        # Missing: "naming_style"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="naming_style"):
        service.generate_world_context(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_world_context_validates_field_lengths(mock_openai_class, basic_config):
    """Test generate_world_context validates field length constraints.

    Spec: theme_essence: 1-200 chars, naming_style: 1-100 chars, tone: 1-100 chars.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with theme_essence too long (>200 chars)
    invalid_response = {
        "theme_essence": "A" * 201,  # Too long
        "naming_style": "Gothic",
        "tone": "dark"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="theme_essence"):
        service.generate_world_context(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_world_context_validates_empty_fields(mock_openai_class, basic_config):
    """Test generate_world_context raises AIGenerationError for empty fields.

    Spec: All fields must be non-empty strings.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with empty naming_style
    invalid_response = {
        "theme_essence": "A dark world.",
        "naming_style": "",  # Empty
        "tone": "grim"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="naming_style"):
        service.generate_world_context(theme="fantasy")


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_world_context_handles_json_in_code_block(mock_openai_class, basic_config):
    """Test generate_world_context extracts JSON from markdown code blocks.

    Spec: Response may be wrapped in ```json...``` and should be extracted.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response wrapped in markdown code block
    valid_json = {
        "theme_essence": "A neon-lit dystopia.",
        "naming_style": "Japanese-English hybrid",
        "tone": "noir, cynical"
    }
    wrapped_response = f"```json\n{json.dumps(valid_json)}\n```"

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = wrapped_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_world_context(theme="cyberpunk")

    assert isinstance(result, WorldContext)
    assert result.theme_essence == valid_json["theme_essence"]


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_world_context_repairs_truncated_json(mock_openai_class, basic_config):
    """Test generate_world_context repairs truncated JSON responses.

    Spec: Truncated JSON (unclosed braces) should be repaired.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Truncated JSON (missing closing brace)
    truncated_response = '{"theme_essence": "A dark world.", "naming_style": "Gothic", "tone": "grim"'

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = truncated_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_world_context(theme="horror")

    assert isinstance(result, WorldContext)
    assert result.theme_essence == "A dark world."
    assert result.naming_style == "Gothic"
    assert result.tone == "grim"


# Tests: generate_region_context() (Layer 2 Region Context Generation)
# ============================================================================


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_returns_valid_region_context(mock_openai_class, basic_config):
    """Test generate_region_context returns a valid RegionContext.

    Spec: Method returns RegionContext with AI-generated name, theme, danger_level, landmarks.
    """
    from cli_rpg.models.region_context import RegionContext
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Valid JSON response with all required fields
    valid_response = {
        "name": "The Shadowed Vale",
        "theme": "A mist-shrouded valley haunted by ancient spirits.",
        "danger_level": "high",
        "landmarks": ["The Hollow Oak", "Wraithstone Bridge", "Ruins of Aldrath"]
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(valid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    # Create a WorldContext for input
    world_context = WorldContext(
        theme="fantasy",
        theme_essence="A dark medieval world shrouded in shadow.",
        naming_style="Old English with Gothic influence",
        tone="grim, foreboding"
    )

    result = service.generate_region_context(
        theme="fantasy",
        world_context=world_context,
        coordinates=(5, 10),
        terrain_hint="forest"
    )

    # Verify result is RegionContext with correct fields
    assert isinstance(result, RegionContext)
    assert result.name == valid_response["name"]
    assert result.theme == valid_response["theme"]
    # danger_level 'high' should map to 'dangerous'
    assert result.danger_level == "dangerous"
    assert result.landmarks == valid_response["landmarks"]
    assert result.coordinates == (5, 10)
    assert result.generated_at is not None


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_validates_required_fields(mock_openai_class, basic_config):
    """Test generate_region_context raises AIGenerationError for missing fields.

    Spec: Missing required fields (name, theme, danger_level) raise AIGenerationError.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response missing 'danger_level' field
    invalid_response = {
        "name": "The Vale",
        "theme": "A misty valley."
        # Missing: "danger_level", "landmarks"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    world_context = WorldContext.default("fantasy")

    with pytest.raises(AIGenerationError, match="danger_level"):
        service.generate_region_context(
            theme="fantasy",
            world_context=world_context,
            coordinates=(0, 0)
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_validates_danger_level(mock_openai_class, basic_config):
    """Test generate_region_context raises AIGenerationError for invalid danger_level.

    Spec: danger_level must be one of 'low', 'medium', 'high', 'deadly'.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with invalid danger_level
    invalid_response = {
        "name": "The Vale",
        "theme": "A misty valley.",
        "danger_level": "extreme",  # Invalid value
        "landmarks": []
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    world_context = WorldContext.default("fantasy")

    with pytest.raises(AIGenerationError, match="danger_level"):
        service.generate_region_context(
            theme="fantasy",
            world_context=world_context,
            coordinates=(0, 0)
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_validates_field_lengths(mock_openai_class, basic_config):
    """Test generate_region_context validates field length constraints.

    Spec: name: 1-50 chars, theme: 1-200 chars, landmarks: 0-5 items, each 1-50 chars.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with name too long (>50 chars)
    invalid_response = {
        "name": "A" * 51,  # Too long
        "theme": "A misty valley.",
        "danger_level": "low",
        "landmarks": []
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    world_context = WorldContext.default("fantasy")

    with pytest.raises(AIGenerationError, match="name"):
        service.generate_region_context(
            theme="fantasy",
            world_context=world_context,
            coordinates=(0, 0)
        )


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_handles_json_in_code_block(mock_openai_class, basic_config):
    """Test generate_region_context extracts JSON from markdown code blocks.

    Spec: Response may be wrapped in ```json...``` and should be extracted.
    """
    from cli_rpg.models.region_context import RegionContext
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response wrapped in markdown code block
    valid_json = {
        "name": "Neon District",
        "theme": "A rain-slicked urban sprawl of corporate towers and neon signs.",
        "danger_level": "medium",
        "landmarks": ["MegaCorp Tower", "The Undercity"]
    }
    wrapped_response = f"```json\n{json.dumps(valid_json)}\n```"

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = wrapped_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    world_context = WorldContext.default("cyberpunk")

    result = service.generate_region_context(
        theme="cyberpunk",
        world_context=world_context,
        coordinates=(0, 0)
    )

    assert isinstance(result, RegionContext)
    assert result.name == valid_json["name"]
    assert result.theme == valid_json["theme"]


@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_repairs_truncated_json(mock_openai_class, basic_config):
    """Test generate_region_context repairs truncated JSON responses.

    Spec: Truncated JSON (unclosed braces) should be repaired.
    """
    from cli_rpg.models.region_context import RegionContext
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Truncated JSON (missing closing brace)
    truncated_response = '{"name": "The Vale", "theme": "A misty valley.", "danger_level": "low", "landmarks": []'

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = truncated_response
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    world_context = WorldContext.default("fantasy")

    result = service.generate_region_context(
        theme="fantasy",
        world_context=world_context,
        coordinates=(3, 7)
    )

    assert isinstance(result, RegionContext)
    assert result.name == "The Vale"
    assert result.theme == "A misty valley."
    assert result.danger_level == "safe"  # 'low' maps to 'safe'
    assert result.coordinates == (3, 7)


# ========================================================================
# Generation Retry Tests - spec: retry on parse/validation failures
# ========================================================================

# Test: generate_location retries on parse failure (AIGenerationError)
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_retries_on_parse_failure(mock_openai_class, tmp_path):
    """Test generate_location retries when first response fails to parse.

    Spec: When AI returns invalid JSON, retry up to generation_max_retries times
    before raising AIGenerationError.
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=2,
        retry_delay=0.01,  # Fast retry for tests
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Valid response to return on retry
    valid_response = {
        "name": "Test Location",
        "description": "A test location that works.",
        "connections": {"north": "Other Place"}
    }

    mock_response_invalid = Mock()
    mock_response_invalid.choices = [Mock()]
    mock_response_invalid.choices[0].message.content = "invalid json garbage"

    mock_response_valid = Mock()
    mock_response_valid.choices = [Mock()]
    mock_response_valid.choices[0].message.content = json.dumps(valid_response)

    # First call fails with invalid JSON, second succeeds
    mock_client.chat.completions.create.side_effect = [
        mock_response_invalid,
        mock_response_valid
    ]

    service = AIService(config)
    result = service.generate_location(theme="fantasy")

    # Should succeed after retry
    assert result["name"] == "Test Location"
    assert mock_client.chat.completions.create.call_count == 2


# Test: generate_location respects generation_max_retries limit
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_respects_retry_limit(mock_openai_class, tmp_path):
    """Test generate_location raises AIGenerationError after retry limit exhausted.

    Spec: After generation_max_retries + 1 attempts (1 initial + N retries),
    raise AIGenerationError if all attempts fail to parse.
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=2,  # 1 initial + 2 retries = 3 total attempts
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "invalid json"
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(config)

    with pytest.raises(AIGenerationError, match="parse"):
        service.generate_location(theme="fantasy")

    # Should have tried 1 + generation_max_retries times
    assert mock_client.chat.completions.create.call_count == 3  # 1 + 2 retries


# Test: generate_location does NOT retry on API errors (AIServiceError)
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_does_not_retry_api_errors(mock_openai_class, tmp_path):
    """Test that AIServiceError (API failures) are NOT retried at generation level.

    Spec: API-level errors like authentication failures should be passed through
    without generation-level retry (they already have API-level retry).
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=3,  # Would allow 3 generation retries
        max_retries=0,  # No API retries to speed up test
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Simulate authentication error (not retried)
    import openai
    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        "Invalid API key", response=Mock(), body=None
    )

    service = AIService(config)

    with pytest.raises(AIServiceError, match="Authentication failed"):
        service.generate_location(theme="fantasy")

    # Should only be called once (no generation-level retry for API errors)
    assert mock_client.chat.completions.create.call_count == 1


# Test: generate_area retries on parse failure
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_area_retries_on_parse_failure(mock_openai_class, tmp_path):
    """Test generate_area retries when first response fails to parse.

    Spec: When AI returns invalid JSON for area generation, retry up to
    generation_max_retries times before raising AIGenerationError.
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=2,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Valid area response
    valid_area_response = [
        {
            "name": "Entry Point",
            "description": "The entrance to the area.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD", "north": "Inner Area"}
        },
        {
            "name": "Inner Area",
            "description": "Deep within the area.",
            "relative_coords": [0, 1],
            "connections": {"south": "Entry Point"}
        },
        {
            "name": "Hidden Spot",
            "description": "A hidden location.",
            "relative_coords": [1, 0],
            "connections": {"west": "Entry Point"}
        },
        {
            "name": "Final Room",
            "description": "The final destination.",
            "relative_coords": [1, 1],
            "connections": {"west": "Inner Area"}
        }
    ]

    mock_response_invalid = Mock()
    mock_response_invalid.choices = [Mock()]
    mock_response_invalid.choices[0].message.content = "not valid json at all"

    mock_response_valid = Mock()
    mock_response_valid.choices = [Mock()]
    mock_response_valid.choices[0].message.content = json.dumps(valid_area_response)

    # First call fails, second succeeds
    mock_client.chat.completions.create.side_effect = [
        mock_response_invalid,
        mock_response_valid
    ]

    service = AIService(config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="ruins",
        entry_direction="north",
        context_locations=["Town"],
        size=4
    )

    assert len(result) == 4
    assert result[0]["name"] == "Entry Point"
    assert mock_client.chat.completions.create.call_count == 2


# Test: generate_location_with_context retries on parse failure
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_with_context_retries_on_parse_failure(mock_openai_class, tmp_path):
    """Test generate_location_with_context retries on parse failure.

    Spec: Layered generation (Layer 3) should also retry on parse failures.
    """
    from cli_rpg.models.world_context import WorldContext
    from cli_rpg.models.region_context import RegionContext

    config = AIConfig(
        api_key="test-key",
        generation_max_retries=2,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    valid_response = {
        "name": "Contextual Location",
        "description": "A location generated with context.",
        "connections": {"west": "Origin"},
        "category": "wilderness"
    }

    mock_response_invalid = Mock()
    mock_response_invalid.choices = [Mock()]
    mock_response_invalid.choices[0].message.content = "{broken json..."

    mock_response_valid = Mock()
    mock_response_valid.choices = [Mock()]
    mock_response_valid.choices[0].message.content = json.dumps(valid_response)

    # First fails, second succeeds
    mock_client.chat.completions.create.side_effect = [
        mock_response_invalid,
        mock_response_valid
    ]

    service = AIService(config)
    world_context = WorldContext.default("fantasy")
    region_context = RegionContext(
        name="Test Region",
        theme="A test region",
        danger_level="safe",
        landmarks=[],
        coordinates=(0, 0)
    )

    result = service.generate_location_with_context(
        world_context=world_context,
        region_context=region_context,
        source_location="Origin",
        direction="east"
    )

    assert result["name"] == "Contextual Location"
    assert result["npcs"] == []  # Layer 3 doesn't generate NPCs
    assert mock_client.chat.completions.create.call_count == 2


# Test: generation_max_retries=0 disables generation-level retry
@patch('cli_rpg.ai_service.OpenAI')
def test_generation_max_retries_zero_disables_retry(mock_openai_class, tmp_path):
    """Test that setting generation_max_retries=0 disables generation retry.

    Spec: With generation_max_retries=0, parse failures should immediately raise
    AIGenerationError without any retry.
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=0,  # No generation retries
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "invalid json"
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(config)

    with pytest.raises(AIGenerationError):
        service.generate_location(theme="fantasy")

    # Should only be called once (no retry)
    assert mock_client.chat.completions.create.call_count == 1


# Test: Retry on validation failure (name too short)
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_retries_on_validation_failure(mock_openai_class, tmp_path):
    """Test generate_location retries when response fails validation.

    Spec: When AI returns valid JSON but validation fails (e.g., name too short),
    retry up to generation_max_retries times.
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=2,
        retry_delay=0.01,
        cache_file=str(tmp_path / "test_cache.json")
    )

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Invalid response (name too short - must be >= 2 chars)
    invalid_response = {
        "name": "X",  # Too short
        "description": "A valid description here.",
        "connections": {}
    }

    # Valid response
    valid_response = {
        "name": "Valid Location",
        "description": "A valid description here.",
        "connections": {}
    }

    mock_response_invalid = Mock()
    mock_response_invalid.choices = [Mock()]
    mock_response_invalid.choices[0].message.content = json.dumps(invalid_response)

    mock_response_valid = Mock()
    mock_response_valid.choices = [Mock()]
    mock_response_valid.choices[0].message.content = json.dumps(valid_response)

    mock_client.chat.completions.create.side_effect = [
        mock_response_invalid,
        mock_response_valid
    ]

    service = AIService(config)
    result = service.generate_location(theme="fantasy")

    assert result["name"] == "Valid Location"
    assert mock_client.chat.completions.create.call_count == 2


# Test: AIConfig generation_max_retries serialization
def test_ai_config_generation_max_retries_serialization():
    """Test generation_max_retries is serialized and deserialized correctly.

    Spec: The new generation_max_retries field should be included in to_dict()
    and restored from from_dict().
    """
    config = AIConfig(
        api_key="test-key",
        generation_max_retries=5
    )

    # Serialize
    config_dict = config.to_dict()
    assert config_dict["generation_max_retries"] == 5

    # Deserialize
    restored_config = AIConfig.from_dict(config_dict)
    assert restored_config.generation_max_retries == 5


# Test: AIConfig generation_max_retries from environment
def test_ai_config_generation_max_retries_from_env(monkeypatch):
    """Test generation_max_retries can be set via environment variable.

    Spec: AI_GENERATION_MAX_RETRIES environment variable should set the config value.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_GENERATION_MAX_RETRIES", "4")

    config = AIConfig.from_env()

    assert config.generation_max_retries == 4


# --- Tests for theme_essence in generate_location prompts ---


# Test: generate_location includes theme_essence in prompt when WorldContext provided
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_includes_theme_essence_with_world_context(
    mock_openai_class, basic_config, mock_openai_response
):
    """Test generate_location includes theme_essence in prompt when WorldContext provided.

    Spec: When a WorldContext is passed to generate_location(), the prompt should
    include the theme_essence from that context.
    """
    from cli_rpg.models.world_context import WorldContext

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    # Create a WorldContext with a specific theme_essence
    world_context = WorldContext(
        theme="fantasy",
        theme_essence="A mystical realm of ancient dragons and forgotten magic",
        naming_style="Old English with Celtic influence",
        tone="heroic, adventurous"
    )

    service.generate_location(
        theme="fantasy",
        context_locations=["Town Square"],
        world_context=world_context
    )

    # Get the actual call arguments
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    prompt = messages[0]["content"]

    # Verify theme_essence from WorldContext is in the prompt
    assert "mystical realm of ancient dragons" in prompt


# Test: generate_location uses default theme_essence when no WorldContext
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_uses_default_theme_essence_without_world_context(
    mock_openai_class, basic_config, mock_openai_response
):
    """Test generate_location uses default theme_essence when no WorldContext.

    Spec: When no WorldContext is passed, generate_location() should use the
    default theme_essence from DEFAULT_THEME_ESSENCES based on the theme.
    """
    from cli_rpg.models.world_context import DEFAULT_THEME_ESSENCES

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    service.generate_location(
        theme="fantasy",
        context_locations=["Town Square"]
    )

    # Get the actual call arguments
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    prompt = messages[0]["content"]

    # Verify default theme_essence for fantasy is in the prompt
    expected_essence = DEFAULT_THEME_ESSENCES["fantasy"]
    assert expected_essence in prompt


# Test: generate_location uses empty string for unknown theme without WorldContext
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_uses_empty_theme_essence_for_unknown_theme(
    mock_openai_class, basic_config, mock_openai_response
):
    """Test generate_location uses empty theme_essence for unknown themes.

    Spec: When no WorldContext is passed and the theme is not in DEFAULT_THEME_ESSENCES,
    the theme_essence should be an empty string.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    service.generate_location(
        theme="unknown-custom-theme",
        context_locations=["Town Square"]
    )

    # Get the actual call arguments
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    prompt = messages[0]["content"]

    # Verify the prompt was formatted correctly (no KeyError)
    # The Theme Essence line should have an empty value for unknown themes
    assert "Theme Essence:" in prompt
    assert "unknown-custom-theme" in prompt