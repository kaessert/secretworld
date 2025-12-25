"""Tests for AI cache persistence.

These tests verify the spec:
- Cache AI responses to a JSON file in a configurable location (default: ~/.cli_rpg/cache/)
- Load existing cache on AIService initialization
- Write cache entries after each new API response
- Honor existing cache_ttl for expiration (both in-memory and on disk)
- Add cache_file config option to AIConfig (default: ~/.cli_rpg/cache/ai_cache.json)
- Gracefully handle file I/O errors (log warning, continue with in-memory only)
"""

import json
import os
import pytest
import tempfile
import time
from unittest.mock import Mock, patch

from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService


# Fixtures

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_cache_file(temp_cache_dir):
    """Create a temporary cache file path."""
    return os.path.join(temp_cache_dir, "ai_cache.json")


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response for location generation."""
    return {
        "name": "Ancient Temple",
        "description": "A weathered stone temple with mysterious carvings on its walls.",
        "connections": {
            "south": "Town Square",
            "east": "Sacred Grove"
        }
    }


# Test: cache_file config option works
def test_ai_config_cache_file_option():
    """Test AIConfig has cache_file field that can be configured."""
    custom_path = "/custom/path/to/cache.json"
    config = AIConfig(
        api_key="test-key",
        cache_file=custom_path
    )
    assert config.cache_file == custom_path


# Test: cache_file defaults to ~/.cli_rpg/cache/ai_cache.json when caching enabled
def test_ai_config_cache_file_default_when_caching_enabled():
    """Test cache_file defaults to ~/.cli_rpg/cache/ai_cache.json when enable_caching is True."""
    config = AIConfig(api_key="test-key", enable_caching=True)
    expected_default = os.path.expanduser("~/.cli_rpg/cache/ai_cache.json")
    assert config.cache_file == expected_default


# Test: cache_file defaults to None when caching disabled
def test_ai_config_cache_file_none_when_caching_disabled():
    """Test cache_file is None when enable_caching is False and no explicit cache_file."""
    config = AIConfig(api_key="test-key", enable_caching=False)
    assert config.cache_file is None


# Test: cache_file from environment variable
def test_ai_config_cache_file_from_env(monkeypatch):
    """Test AI_CACHE_FILE environment variable is read by from_env()."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_CACHE_FILE", "/custom/env/cache.json")

    config = AIConfig.from_env()
    assert config.cache_file == "/custom/env/cache.json"


# Test: cache_file in to_dict and from_dict
def test_ai_config_cache_file_serialization():
    """Test cache_file is included in to_dict and from_dict round-trip."""
    custom_path = "/custom/path/cache.json"
    original = AIConfig(api_key="test-key", cache_file=custom_path)

    config_dict = original.to_dict()
    assert config_dict["cache_file"] == custom_path

    restored = AIConfig.from_dict(config_dict)
    assert restored.cache_file == custom_path


# Test: cache file is created when caching enabled
@patch('cli_rpg.ai_service.OpenAI')
def test_cache_file_created_when_caching_enabled(mock_openai_class, temp_cache_file, mock_openai_response):
    """Test that a cache file is created when caching is enabled and AI call is made."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=temp_cache_file,
        retry_delay=0.1
    )

    service = AIService(config)
    service.generate_location(theme="fantasy")

    # Cache file should be created
    assert os.path.exists(temp_cache_file)

    # Cache file should contain valid JSON
    with open(temp_cache_file, 'r') as f:
        cache_data = json.load(f)

    assert isinstance(cache_data, dict)
    assert len(cache_data) > 0


# Test: cache persists across AIService instances
@patch('cli_rpg.ai_service.OpenAI')
def test_cache_persists_across_instances(mock_openai_class, temp_cache_file, mock_openai_response):
    """Test that cached data is loaded by new AIService instances."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=temp_cache_file,
        retry_delay=0.1
    )

    # First service makes API call
    service1 = AIService(config)
    result1 = service1.generate_location(theme="fantasy")

    assert mock_client.chat.completions.create.call_count == 1

    # Second service should load from persisted cache
    service2 = AIService(config)
    result2 = service2.generate_location(theme="fantasy")

    # API should NOT be called again - cache hit
    assert mock_client.chat.completions.create.call_count == 1

    # Results should match
    assert result1 == result2


# Test: expired entries are pruned on load
@patch('cli_rpg.ai_service.OpenAI')
def test_expired_entries_pruned_on_load(mock_openai_class, temp_cache_file, mock_openai_response):
    """Test that expired cache entries are removed when loading from disk."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    # Create a cache file with an expired entry (timestamp in the past)
    expired_timestamp = time.time() - 10000  # 10000 seconds ago
    cache_key = "test_key"
    cache_data = {
        cache_key: {
            "data": {"name": "Old Location", "description": "Old desc", "connections": {}},
            "timestamp": expired_timestamp
        }
    }

    # Create cache directory and write expired cache
    os.makedirs(os.path.dirname(temp_cache_file), exist_ok=True)
    with open(temp_cache_file, 'w') as f:
        json.dump(cache_data, f)

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=temp_cache_file,
        cache_ttl=3600,  # 1 hour TTL - entry is definitely expired
        retry_delay=0.1
    )

    # Service should prune expired entries on load
    service = AIService(config)

    # The in-memory cache should not contain the expired entry
    assert cache_key not in service._cache


# Test: graceful fallback when cache file is unreadable
@patch('cli_rpg.ai_service.OpenAI')
def test_graceful_fallback_when_cache_unreadable(mock_openai_class, temp_cache_file, mock_openai_response, caplog):
    """Test that AIService gracefully handles unreadable cache files."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    # Create an invalid/corrupt cache file
    os.makedirs(os.path.dirname(temp_cache_file), exist_ok=True)
    with open(temp_cache_file, 'w') as f:
        f.write("{ this is not valid json }")

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=temp_cache_file,
        retry_delay=0.1
    )

    # Service should initialize without crashing
    import logging
    with caplog.at_level(logging.WARNING):
        service = AIService(config)

    # Should still be able to generate locations (in-memory cache works)
    result = service.generate_location(theme="fantasy")
    assert result is not None
    assert "name" in result


# Test: graceful fallback when cache file is not writable
@patch('cli_rpg.ai_service.OpenAI')
def test_graceful_fallback_when_cache_not_writable(mock_openai_class, temp_cache_dir, mock_openai_response, caplog):
    """Test that AIService gracefully handles unwritable cache locations."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    # Use a path that cannot be written (directory doesn't exist and can't be created)
    unwritable_cache_file = "/nonexistent_root_dir/cache/ai_cache.json"

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=unwritable_cache_file,
        retry_delay=0.1
    )

    # Service should initialize without crashing
    import logging
    with caplog.at_level(logging.WARNING):
        service = AIService(config)

    # Should still be able to generate locations (in-memory cache works)
    result = service.generate_location(theme="fantasy")
    assert result is not None


# Test: cache file directory is created automatically
@patch('cli_rpg.ai_service.OpenAI')
def test_cache_directory_created_automatically(mock_openai_class, temp_cache_dir, mock_openai_response):
    """Test that the cache directory is created automatically if it doesn't exist."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)
    mock_client.chat.completions.create.return_value = mock_response

    # Use a cache file in a nested directory that doesn't exist yet
    nested_cache_file = os.path.join(temp_cache_dir, "nested", "deep", "cache.json")

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=nested_cache_file,
        retry_delay=0.1
    )

    service = AIService(config)
    service.generate_location(theme="fantasy")

    # Cache file should be created, including parent directories
    assert os.path.exists(nested_cache_file)


# Test: cache is saved after each new API response
@patch('cli_rpg.ai_service.OpenAI')
def test_cache_saved_after_each_response(mock_openai_class, temp_cache_file, mock_openai_response):
    """Test that cache is persisted to disk after each new API response."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Create two different responses
    response1 = mock_openai_response.copy()
    response1["name"] = "Location One"

    response2 = {
        "name": "Location Two",
        "description": "Another location for testing.",
        "connections": {"north": "Location One"}
    }

    mock_response1 = Mock()
    mock_response1.choices = [Mock()]
    mock_response1.choices[0].message.content = json.dumps(response1)

    mock_response2 = Mock()
    mock_response2.choices = [Mock()]
    mock_response2.choices[0].message.content = json.dumps(response2)

    mock_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=temp_cache_file,
        retry_delay=0.1
    )

    service = AIService(config)

    # First call
    service.generate_location(theme="fantasy")

    # Check file has 1 entry
    with open(temp_cache_file, 'r') as f:
        cache_data = json.load(f)
    assert len(cache_data) == 1

    # Second call with different parameters
    service.generate_location(theme="sci-fi")

    # Check file has 2 entries
    with open(temp_cache_file, 'r') as f:
        cache_data = json.load(f)
    assert len(cache_data) == 2


# Test: list caching (for generate_area) persists to disk
@patch('cli_rpg.ai_service.OpenAI')
def test_list_cache_persists_to_disk(mock_openai_class, temp_cache_file):
    """Test that list caching (used by generate_area) also persists to disk."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response = [
        {
            "name": "Dungeon Entrance",
            "description": "A dark entrance leading into the depths below.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD", "north": "First Chamber"}
        },
        {
            "name": "First Chamber",
            "description": "A dusty chamber with ancient markings.",
            "relative_coords": [0, 1],
            "connections": {"south": "Dungeon Entrance"}
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    config = AIConfig(
        api_key="test-key",
        enable_caching=True,
        cache_file=temp_cache_file,
        retry_delay=0.1
    )

    # First service generates area
    service1 = AIService(config)
    result1 = service1.generate_area(
        theme="fantasy",
        sub_theme_hint="dungeon",
        entry_direction="north",
        context_locations=[],
        size=2
    )

    assert mock_client.chat.completions.create.call_count == 1

    # Second service should load from disk cache
    service2 = AIService(config)
    result2 = service2.generate_area(
        theme="fantasy",
        sub_theme_hint="dungeon",
        entry_direction="north",
        context_locations=[],
        size=2
    )

    # API should NOT be called again
    assert mock_client.chat.completions.create.call_count == 1
    assert result1 == result2
