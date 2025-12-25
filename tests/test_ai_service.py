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
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location missing 'connections'
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        "description": "A test location with adequate description length",
        "relative_coords": [0, 0]
        # Missing 'connections'
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="missing required field.*connections"):
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


@patch('cli_rpg.ai_service.OpenAI')
def test_validate_area_location_invalid_connections(mock_openai_class, basic_config):
    """Test _validate_area_location raises on invalid connections type (line 701-702).

    Spec: When connections is not a dictionary, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with invalid connections type
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([{
        "name": "Test Location",
        "description": "A test location with adequate description length",
        "relative_coords": [0, 0],
        "connections": ["north", "south"]  # Should be a dict
    }])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="connections must be a dictionary"):
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
def test_parse_location_response_connections_not_dict(mock_openai_class, basic_config):
    """Test _parse_location_response raises when connections is not a dictionary (line 360).

    Spec: When connections field is not a dict, raise AIGenerationError.
    """
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Return location with invalid connections type
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "name": "Test Location",
        "description": "A valid description that meets the minimum length requirement.",
        "connections": ["north", "south"]  # Should be a dict, not a list
    })
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)

    with pytest.raises(AIGenerationError, match="Connections must be a dictionary"):
        service.generate_location(theme="fantasy")


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
    result1 = service.generate_location(theme="fantasy")
    assert mock_client.chat.completions.create.call_count == 1

    # Second call - time is beyond cache_ttl (4000 > 3600)
    # This should trigger the expired entry deletion (line 399)
    mock_time.time.return_value = 4000
    result2 = service.generate_location(theme="fantasy")

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
    result1 = service.generate_area(
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
    result2 = service.generate_area(
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
