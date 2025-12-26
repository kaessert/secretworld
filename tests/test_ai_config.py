"""Tests for AI configuration module."""

import pytest
from cli_rpg.ai_config import AIConfig, AIConfigError


# Test: AIConfig initialization with direct parameters
def test_ai_config_initialization_with_parameters():
    """Test AIConfig can be initialized with direct parameters."""
    config = AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500
    )
    
    assert config.api_key == "test-key-123"
    assert config.model == "gpt-3.5-turbo"
    assert config.temperature == 0.7
    assert config.max_tokens == 500


# Test: AIConfig reads from environment variables
def test_ai_config_from_environment(monkeypatch):
    """Test AIConfig.from_env() reads configuration from environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-test-key")
    monkeypatch.setenv("AI_MODEL", "gpt-4")
    monkeypatch.setenv("AI_TEMPERATURE", "0.9")
    monkeypatch.setenv("AI_MAX_TOKENS", "1000")
    monkeypatch.setenv("AI_MAX_RETRIES", "5")
    
    config = AIConfig.from_env()
    
    assert config.api_key == "env-test-key"
    assert config.model == "gpt-4"
    assert config.temperature == 0.9
    assert config.max_tokens == 1000
    assert config.max_retries == 5


# Test: AIConfig applies defaults when env vars not set
def test_ai_config_defaults(monkeypatch):
    """Test AIConfig uses default values when environment variables not set."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    # Don't set other env vars
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("AI_TEMPERATURE", raising=False)
    
    config = AIConfig.from_env()
    
    assert config.api_key == "test-key"
    assert config.model == "gpt-3.5-turbo"  # Default
    assert config.temperature == 0.7  # Default
    assert config.max_tokens == 3000  # Default
    assert config.max_retries == 3  # Default
    assert config.enable_caching is True  # Default


# Test: AIConfig raises error for missing API key
def test_ai_config_missing_api_key_raises_error():
    """Test AIConfig raises AIConfigError when API key is missing or empty."""
    with pytest.raises(AIConfigError, match="API key cannot be empty"):
        AIConfig(api_key="")
    
    with pytest.raises(AIConfigError, match="API key cannot be empty"):
        AIConfig(api_key="   ")


# Test: AIConfig from_env raises error when no API key in environment
def test_ai_config_from_env_missing_api_key(monkeypatch):
    """Test AIConfig.from_env() raises error when no API key is set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(AIConfigError, match="No API key found"):
        AIConfig.from_env()


# Test: AIConfig validates temperature range
def test_ai_config_validates_temperature():
    """Test AIConfig validates temperature is within valid range [0.0, 2.0]."""
    # Valid temperatures
    config = AIConfig(api_key="test-key", temperature=0.0)
    assert config.temperature == 0.0
    
    config = AIConfig(api_key="test-key", temperature=2.0)
    assert config.temperature == 2.0
    
    # Invalid temperatures
    with pytest.raises(AIConfigError, match="Temperature must be between 0.0 and 2.0"):
        AIConfig(api_key="test-key", temperature=-0.1)
    
    with pytest.raises(AIConfigError, match="Temperature must be between 0.0 and 2.0"):
        AIConfig(api_key="test-key", temperature=2.1)


# Test: AIConfig validates max_tokens is positive
def test_ai_config_validates_max_tokens():
    """Test AIConfig validates max_tokens is positive."""
    config = AIConfig(api_key="test-key", max_tokens=1)
    assert config.max_tokens == 1
    
    with pytest.raises(AIConfigError, match="max_tokens must be positive"):
        AIConfig(api_key="test-key", max_tokens=0)
    
    with pytest.raises(AIConfigError, match="max_tokens must be positive"):
        AIConfig(api_key="test-key", max_tokens=-100)


# Test: AIConfig validates max_retries is non-negative
def test_ai_config_validates_max_retries():
    """Test AIConfig validates max_retries is non-negative."""
    config = AIConfig(api_key="test-key", max_retries=0)
    assert config.max_retries == 0
    
    with pytest.raises(AIConfigError, match="max_retries must be non-negative"):
        AIConfig(api_key="test-key", max_retries=-1)


# Test: AIConfig validates retry_delay is positive
def test_ai_config_validates_retry_delay():
    """Test AIConfig validates retry_delay is positive."""
    config = AIConfig(api_key="test-key", retry_delay=0.1)
    assert config.retry_delay == 0.1
    
    with pytest.raises(AIConfigError, match="retry_delay must be positive"):
        AIConfig(api_key="test-key", retry_delay=0.0)
    
    with pytest.raises(AIConfigError, match="retry_delay must be positive"):
        AIConfig(api_key="test-key", retry_delay=-1.0)


# Test: AIConfig to_dict and from_dict round-trip
def test_ai_config_serialization():
    """Test AIConfig can be serialized to dict and deserialized back."""
    original_config = AIConfig(
        api_key="test-key",
        model="gpt-4",
        temperature=0.8,
        max_tokens=1000,
        max_retries=5,
        retry_delay=2.0,
        enable_caching=False,
        cache_ttl=7200
    )
    
    # Serialize to dict
    config_dict = original_config.to_dict()
    
    assert config_dict["api_key"] == "test-key"
    assert config_dict["model"] == "gpt-4"
    assert config_dict["temperature"] == 0.8
    
    # Deserialize from dict
    restored_config = AIConfig.from_dict(config_dict)
    
    assert restored_config.api_key == original_config.api_key
    assert restored_config.model == original_config.model
    assert restored_config.temperature == original_config.temperature
    assert restored_config.max_tokens == original_config.max_tokens
    assert restored_config.max_retries == original_config.max_retries
    assert restored_config.retry_delay == original_config.retry_delay
    assert restored_config.enable_caching == original_config.enable_caching
    assert restored_config.cache_ttl == original_config.cache_ttl


# Test: AIConfig custom prompt template
def test_ai_config_custom_prompts():
    """Test AIConfig allows custom prompt templates."""
    custom_prompt = "Custom prompt: {theme}, {direction}"
    
    config = AIConfig(
        api_key="test-key",
        location_generation_prompt=custom_prompt
    )
    
    assert config.location_generation_prompt == custom_prompt


# Test: AIConfig default prompt template is not empty
def test_ai_config_default_prompt_not_empty():
    """Test AIConfig has a non-empty default prompt template."""
    config = AIConfig(api_key="test-key")
    
    assert config.location_generation_prompt
    assert len(config.location_generation_prompt) > 0
    assert "{theme}" in config.location_generation_prompt


# Test: AIConfig from_dict with missing fields uses defaults
def test_ai_config_from_dict_with_defaults():
    """Test AIConfig.from_dict() uses defaults for missing optional fields."""
    minimal_dict = {
        "api_key": "test-key"
    }

    config = AIConfig.from_dict(minimal_dict)

    assert config.api_key == "test-key"
    assert config.model == "gpt-3.5-turbo"  # Default
    assert config.temperature == 0.7  # Default
    assert config.max_tokens == 3000  # Default


# Test: AIConfig from_env with ANTHROPIC_API_KEY sets provider to "anthropic"
def test_ai_config_from_env_with_anthropic_key(monkeypatch):
    """Test AIConfig.from_env() detects ANTHROPIC_API_KEY and sets provider to 'anthropic'."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")

    config = AIConfig.from_env()

    assert config.api_key == "anthropic-test-key"
    assert config.provider == "anthropic"
    assert config.model == "claude-3-5-sonnet-latest"  # Default Anthropic model


# Test: AIConfig prefers Anthropic when both keys are set
def test_ai_config_from_env_prefers_anthropic_over_openai(monkeypatch):
    """Test AIConfig.from_env() prefers Anthropic when both API keys are set."""
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    config = AIConfig.from_env()

    assert config.api_key == "anthropic-test-key"
    assert config.provider == "anthropic"


# Test: AI_PROVIDER env var allows explicit provider selection
def test_ai_config_from_env_explicit_provider_selection(monkeypatch):
    """Test AI_PROVIDER=openai overrides preference when both keys are set."""
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("AI_PROVIDER", "openai")

    config = AIConfig.from_env()

    assert config.api_key == "openai-test-key"
    assert config.provider == "openai"
    assert config.model == "gpt-3.5-turbo"


# Test: AIConfig raises error when neither API key is set
def test_ai_config_from_env_no_api_key_raises_error(monkeypatch):
    """Test AIConfig.from_env() raises error when neither API key is set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(AIConfigError, match="No API key found"):
        AIConfig.from_env()


# Test: AIConfig provider field serializes correctly
def test_ai_config_serialization_with_provider():
    """Test AIConfig with provider serializes and deserializes correctly."""
    original_config = AIConfig(
        api_key="test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest"
    )

    config_dict = original_config.to_dict()

    assert config_dict["provider"] == "anthropic"

    restored_config = AIConfig.from_dict(config_dict)

    assert restored_config.provider == "anthropic"


# Test: AIConfig defaults to openai provider
def test_ai_config_defaults_to_openai_provider():
    """Test AIConfig defaults to 'openai' provider when not specified."""
    config = AIConfig(api_key="test-key")

    assert config.provider == "openai"


# Test: AI_PROVIDER=anthropic explicit selection (coverage for ai_config.py:301-302)
def test_ai_config_from_env_explicit_anthropic_provider_selection(monkeypatch):
    """Test AI_PROVIDER=anthropic selects Anthropic when both keys are set.

    Spec: Covers lines 301-302 in ai_config.py where AI_PROVIDER=anthropic
    explicitly selects the Anthropic provider.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("AI_PROVIDER", "anthropic")

    config = AIConfig.from_env()

    assert config.api_key == "anthropic-test-key"
    assert config.provider == "anthropic"
    assert config.model == "claude-3-5-sonnet-latest"


# --- Tests for Split Generation Prompts (Step 5 of Layered Query Architecture) ---


# Test: WORLD_CONTEXT_PROMPT exists and contains {theme}
def test_ai_config_world_context_prompt_exists():
    """Test AIConfig has world_context_prompt with {theme} placeholder.

    Spec: WORLD_CONTEXT_PROMPT generates Layer 1 context (once per world)
    with input {theme} and outputs theme_essence, naming_style, tone.
    """
    config = AIConfig(api_key="test-key")

    assert config.world_context_prompt
    assert len(config.world_context_prompt) > 0
    assert "{theme}" in config.world_context_prompt


# Test: REGION_CONTEXT_PROMPT exists and contains {theme_essence}
def test_ai_config_region_context_prompt_exists():
    """Test AIConfig has region_context_prompt with {theme_essence} placeholder.

    Spec: REGION_CONTEXT_PROMPT generates Layer 2 context (per region)
    with inputs including theme_essence and outputs region metadata.
    """
    config = AIConfig(api_key="test-key")

    assert config.region_context_prompt
    assert len(config.region_context_prompt) > 0
    assert "{theme_essence}" in config.region_context_prompt


# Test: LOCATION_PROMPT_MINIMAL exists and contains {region_theme}
def test_ai_config_location_prompt_minimal_exists():
    """Test AIConfig has location_prompt_minimal with {region_theme} placeholder.

    Spec: LOCATION_PROMPT_MINIMAL generates Layer 3 location (per location, no NPCs)
    with inputs including region_theme and outputs location metadata.
    """
    config = AIConfig(api_key="test-key")

    assert config.location_prompt_minimal
    assert len(config.location_prompt_minimal) > 0
    assert "{region_theme}" in config.location_prompt_minimal


# Test: NPC_PROMPT_MINIMAL exists and contains {location_name}
def test_ai_config_npc_prompt_minimal_exists():
    """Test AIConfig has npc_prompt_minimal with {location_name} placeholder.

    Spec: NPC_PROMPT_MINIMAL generates Layer 4 NPCs (optional, per location)
    with inputs including location_name and outputs NPC data.
    """
    config = AIConfig(api_key="test-key")

    assert config.npc_prompt_minimal
    assert len(config.npc_prompt_minimal) > 0
    assert "{location_name}" in config.npc_prompt_minimal


# Test: Serialization includes all 4 new prompts
def test_ai_config_serialization_includes_new_prompts():
    """Test AIConfig serialization round-trip includes all 4 new prompts.

    Spec: to_dict() and from_dict() serialize/deserialize new prompts.
    """
    custom_world = "Custom world context: {theme}"
    custom_region = "Custom region context: {theme_essence}"
    custom_location = "Custom location: {region_theme}"
    custom_npc = "Custom npc: {location_name}"

    original_config = AIConfig(
        api_key="test-key",
        world_context_prompt=custom_world,
        region_context_prompt=custom_region,
        location_prompt_minimal=custom_location,
        npc_prompt_minimal=custom_npc,
    )

    # Serialize to dict
    config_dict = original_config.to_dict()

    assert config_dict["world_context_prompt"] == custom_world
    assert config_dict["region_context_prompt"] == custom_region
    assert config_dict["location_prompt_minimal"] == custom_location
    assert config_dict["npc_prompt_minimal"] == custom_npc

    # Deserialize from dict
    restored_config = AIConfig.from_dict(config_dict)

    assert restored_config.world_context_prompt == custom_world
    assert restored_config.region_context_prompt == custom_region
    assert restored_config.location_prompt_minimal == custom_location
    assert restored_config.npc_prompt_minimal == custom_npc
