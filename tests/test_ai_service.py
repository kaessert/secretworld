"""Tests for AI service module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
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
    
    # Verify structure
    assert "name" in result
    assert "description" in result
    assert "connections" in result
    assert isinstance(result["name"], str)
    assert isinstance(result["description"], str)
    assert isinstance(result["connections"], dict)


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


# Test: Connection directions are filtered to cardinal only
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_connection_directions_filtered(mock_openai_class, basic_config):
    """Test generate_location filters out non-cardinal directions like 'northeast'.

    Only north, south, east, west are valid for grid-based movement.
    Invalid directions like 'northeast' are silently filtered.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with invalid direction
    invalid_response = {
        "name": "Test Location",
        "description": "A test location",
        "connections": {
            "northeast": "Invalid Direction Location",  # Invalid - will be filtered
            "south": "Valid Location"  # Valid - will be kept
        }
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    # Verify 'northeast' was filtered out, but valid 'south' remains
    assert "northeast" not in result["connections"]
    assert result["connections"] == {"south": "Valid Location"}


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
        source_location="Space Station",
        direction="north"
    )
    
    # Get the actual call arguments
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    prompt = messages[0]["content"]
    
    # Verify context is in prompt
    assert "sci-fi" in prompt
    assert "Space Station" in prompt or "space station" in prompt.lower()
    assert "north" in prompt.lower()


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

    # Simulate Anthropic API response structure
    location_data = {
        "name": "Mystic Forest",
        "description": "A dark and mysterious forest filled with ancient trees.",
        "connections": {
            "north": "Village Square",
            "east": "River Bank"
        }
    }

    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = json.dumps(location_data)
    mock_client.messages.create.return_value = mock_response

    service = AIService(config)
    result = service.generate_location(theme="fantasy")

    # Verify result
    assert result["name"] == "Mystic Forest"
    assert result["description"] == "A dark and mysterious forest filled with ancient trees."
    assert result["connections"]["north"] == "Village Square"

    # Verify Anthropic API was called correctly
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-3-5-sonnet-latest"
    assert call_kwargs["max_tokens"] == 500
    assert len(call_kwargs["messages"]) == 1
    assert call_kwargs["messages"][0]["role"] == "user"


# Test: Filter non-cardinal directions (down) - spec: grid-based movement only supports cardinal directions
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_filters_non_cardinal_directions(mock_openai_class, basic_config):
    """Test generate_location filters out non-cardinal directions like 'down'.

    The grid-based movement system only supports north, south, east, west.
    AI may generate 'up' or 'down' connections which should be filtered out.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with both valid and invalid directions
    response_with_down = {
        "name": "Neon Nexus",
        "description": "A hub of pulsing energy and data streams.",
        "connections": {
            "north": "Crystal Spire",
            "down": "Underground Lab",  # Invalid - should be filtered
            "east": "Data Center"
        }
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_with_down)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="cyberpunk")

    # Verify 'down' was filtered out
    assert "down" not in result["connections"]
    assert result["connections"] == {"north": "Crystal Spire", "east": "Data Center"}


# Test: Filter 'up' direction - spec: grid-based movement only supports cardinal directions
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_filters_up_direction(mock_openai_class, basic_config):
    """Test generate_location filters out 'up' direction.

    The grid-based movement system only supports north, south, east, west.
    AI may generate 'up' connections which should be filtered out.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Response with 'up' direction
    response_with_up = {
        "name": "Sky Tower Base",
        "description": "The base of a towering structure reaching into the clouds.",
        "connections": {
            "up": "Sky Tower Observation Deck",  # Invalid - should be filtered
            "south": "Ground Floor Lobby"
        }
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_with_up)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="sci-fi")

    # Verify 'up' was filtered out
    assert "up" not in result["connections"]
    assert result["connections"] == {"south": "Ground Floor Lobby"}


# Test: Area generation filters non-cardinal directions - spec: grid-based movement
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_area_filters_non_cardinal_directions(mock_openai_class, basic_config):
    """Test generate_area filters out non-cardinal directions from all locations.

    The grid-based movement system only supports north, south, east, west.
    AI-generated areas may include 'up'/'down' connections which should be filtered.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Area response with non-cardinal directions in multiple locations
    area_response = [
        {
            "name": "Dungeon Entrance",
            "description": "A dark entrance leading into the depths below.",
            "relative_coords": [0, 0],
            "connections": {
                "south": "EXISTING_WORLD",
                "north": "First Chamber",
                "down": "Deep Pit"  # Invalid - should be filtered
            }
        },
        {
            "name": "First Chamber",
            "description": "A dusty chamber with ancient markings.",
            "relative_coords": [0, 1],
            "connections": {
                "south": "Dungeon Entrance",
                "up": "Ceiling Passage",  # Invalid - should be filtered
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

    # Verify all non-cardinal directions were filtered from all locations
    for location in result:
        for direction in location["connections"].keys():
            assert direction in {"north", "south", "east", "west"}, \
                f"Found non-cardinal direction '{direction}' in location '{location['name']}'"

    # Verify specific filtering
    assert "down" not in result[0]["connections"]
    assert "up" not in result[1]["connections"]
    assert result[0]["connections"] == {"south": "EXISTING_WORLD", "north": "First Chamber"}
    assert result[1]["connections"] == {"south": "Dungeon Entrance", "east": "Treasure Room"}


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
