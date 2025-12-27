"""Tests for LLM streaming support in AIService.

Spec: Add streaming support to AIService for live text display during AI generation.
When streaming is enabled, display generated text character-by-character as it arrives
from the LLM, replacing the spinner-based progress indicator with real-time content reveal.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Iterator, Optional
from unittest.mock import MagicMock, patch

import pytest

from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService


# --- Test 1: Streaming config option ---


def test_ai_config_enable_streaming_defaults_to_false():
    """Test AIConfig.enable_streaming defaults to False.

    Spec: When stream=True is passed to generation methods (or enabled via config),
    stream tokens directly to stdout.
    """
    config = AIConfig(api_key="test-key")
    assert config.enable_streaming is False


def test_ai_config_enable_streaming_can_be_set_true():
    """Test AIConfig.enable_streaming can be set to True."""
    config = AIConfig(api_key="test-key", enable_streaming=True)
    assert config.enable_streaming is True


def test_ai_config_from_env_reads_enable_streaming(monkeypatch):
    """Test AIConfig.from_env() reads AI_ENABLE_STREAMING environment variable.

    Spec: Add AI_ENABLE_STREAMING environment variable support in from_env().
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_ENABLE_STREAMING", "true")

    config = AIConfig.from_env()

    assert config.enable_streaming is True


def test_ai_config_from_env_streaming_false(monkeypatch):
    """Test AI_ENABLE_STREAMING=false disables streaming."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AI_ENABLE_STREAMING", "false")

    config = AIConfig.from_env()

    assert config.enable_streaming is False


def test_ai_config_to_dict_includes_enable_streaming():
    """Test AIConfig.to_dict() includes enable_streaming.

    Spec: Include in to_dict() serialization.
    """
    config = AIConfig(api_key="test-key", enable_streaming=True)

    config_dict = config.to_dict()

    assert "enable_streaming" in config_dict
    assert config_dict["enable_streaming"] is True


def test_ai_config_from_dict_reads_enable_streaming():
    """Test AIConfig.from_dict() reads enable_streaming.

    Spec: Include in from_dict() deserialization.
    """
    config_dict = {"api_key": "test-key", "enable_streaming": True}

    config = AIConfig.from_dict(config_dict)

    assert config.enable_streaming is True


def test_ai_config_from_dict_defaults_enable_streaming_to_false():
    """Test AIConfig.from_dict() defaults enable_streaming to False when not present."""
    config_dict = {"api_key": "test-key"}

    config = AIConfig.from_dict(config_dict)

    assert config.enable_streaming is False


# --- Test 2: OpenAI streaming call ---


@dataclass
class MockDelta:
    content: str | None


@dataclass
class MockChoice:
    delta: MockDelta


@dataclass
class MockStreamChunk:
    choices: list[MockChoice]


def test_openai_streaming_call_yields_chunks():
    """Test _call_openai_streaming() streams chunks to output.

    Spec: Mock stream=True in client.chat.completions.create(), verify chunks are yielded.
    """
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    # Create mock streaming response
    mock_chunks = [
        MockStreamChunk([MockChoice(MockDelta("Hello"))]),
        MockStreamChunk([MockChoice(MockDelta(" world"))]),
        MockStreamChunk([MockChoice(MockDelta("!"))]),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter(mock_chunks)

    service = AIService(config)
    service.client = mock_client

    output = io.StringIO()
    result = service._call_openai_streaming("Test prompt", output)

    # Verify result
    assert result == "Hello world!"

    # Verify output was written
    output_text = output.getvalue()
    assert "Hello" in output_text
    assert " world" in output_text
    assert "!" in output_text

    # Verify API was called with stream=True
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["stream"] is True


def test_openai_streaming_handles_none_content():
    """Test _call_openai_streaming() handles None content in chunks gracefully."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    # Create mock streaming response with some None content
    mock_chunks = [
        MockStreamChunk([MockChoice(MockDelta("Hello"))]),
        MockStreamChunk([MockChoice(MockDelta(None))]),  # None content
        MockStreamChunk([MockChoice(MockDelta(" world"))]),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter(mock_chunks)

    service = AIService(config)
    service.client = mock_client

    output = io.StringIO()
    result = service._call_openai_streaming("Test prompt", output)

    assert result == "Hello world"


# --- Test 3: Anthropic streaming call ---


def test_anthropic_streaming_call_yields_chunks():
    """Test _call_anthropic_streaming() streams chunks to output.

    Spec: Mock streaming with client.messages.stream(), verify chunks are yielded.
    """
    config = AIConfig(api_key="test-key", provider="anthropic", enable_streaming=True)

    # Create mock streaming context manager
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
    mock_stream_ctx.__exit__ = MagicMock(return_value=False)
    mock_stream_ctx.text_stream = iter(["Hello", " world", "!"])

    mock_client = MagicMock()
    mock_client.messages.stream.return_value = mock_stream_ctx

    with patch("cli_rpg.ai_service.ANTHROPIC_AVAILABLE", True):
        service = AIService(config)
        service.client = mock_client

        output = io.StringIO()
        result = service._call_anthropic_streaming("Test prompt", output)

    assert result == "Hello world!"

    output_text = output.getvalue()
    assert "Hello" in output_text
    assert " world" in output_text
    assert "!" in output_text


# --- Test 4: Ollama streaming call ---


def test_ollama_uses_openai_streaming_interface():
    """Test Ollama uses OpenAI-compatible streaming interface.

    Spec: Verify Ollama uses OpenAI-compatible streaming interface.
    """
    config = AIConfig(
        api_key="ollama",
        provider="ollama",
        enable_streaming=True,
        ollama_base_url="http://localhost:11434/v1",
    )

    mock_chunks = [
        MockStreamChunk([MockChoice(MockDelta("Hello"))]),
        MockStreamChunk([MockChoice(MockDelta(" Ollama"))]),
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = iter(mock_chunks)

    service = AIService(config)
    service.client = mock_client

    output = io.StringIO()
    # Ollama should use the OpenAI streaming method with is_ollama=True
    result = service._call_openai_streaming("Test prompt", output, is_ollama=True)

    assert result == "Hello Ollama"


# --- Test 5: Streaming disabled for JSON methods ---


def test_generate_location_never_uses_streaming():
    """Test generate_location never uses streaming (needs JSON parsing).

    Spec: Streaming only applies to free-form text generation - NOT to JSON responses
    that require parsing.
    """
    # Disable caching to ensure _call_llm gets called
    config = AIConfig(
        api_key="test-key", provider="openai", enable_streaming=True, enable_caching=False
    )

    # Mock _call_llm to return valid JSON
    mock_response = '{"name": "Test Town", "description": "A test town.", "category": "town"}'

    service = AIService(config)
    with patch.object(service, "_call_llm", return_value=mock_response) as mock_call:
        with patch.object(service, "_call_llm_streamable") as mock_streamable:
            result = service.generate_location("fantasy")

            # Verify _call_llm was called (not streaming)
            mock_call.assert_called_once()
            # Verify _call_llm_streamable was NOT called
            mock_streamable.assert_not_called()
            assert result["name"] == "Test Town"


def test_generate_quest_never_uses_streaming():
    """Test generate_quest never uses streaming (needs JSON parsing)."""
    # Disable caching to ensure _call_llm gets called
    config = AIConfig(
        api_key="test-key", provider="openai", enable_streaming=True, enable_caching=False
    )

    # Mock _call_llm to return valid JSON
    mock_response = """{
        "name": "Test Quest",
        "description": "A test quest.",
        "objective_type": "kill",
        "target": "Wolf",
        "target_count": 3,
        "gold_reward": 100,
        "xp_reward": 50,
        "difficulty": "easy",
        "recommended_level": 1
    }"""

    service = AIService(config)
    with patch.object(service, "_call_llm", return_value=mock_response) as mock_call:
        with patch.object(service, "_call_llm_streamable") as mock_streamable:
            result = service.generate_quest("fantasy", "Old Man", 1)

            mock_call.assert_called_once()
            mock_streamable.assert_not_called()
            assert result["name"] == "Test Quest"


def test_generate_enemy_never_uses_streaming():
    """Test generate_enemy never uses streaming (needs JSON parsing)."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    # Mock _call_llm to return valid JSON
    mock_response = """{
        "name": "Goblin",
        "description": "A small green creature.",
        "attack_flavor": "The goblin swings its club!",
        "health": 30,
        "attack_power": 5,
        "defense": 2,
        "xp_reward": 25
    }"""

    service = AIService(config)
    with patch.object(service, "_call_llm", return_value=mock_response) as mock_call:
        with patch.object(service, "_call_llm_streamable") as mock_streamable:
            result = service.generate_enemy("fantasy", "Dark Forest", 1)

            mock_call.assert_called_once()
            mock_streamable.assert_not_called()
            assert result["name"] == "Goblin"


# --- Test 6: Streaming enabled for text methods ---


def test_generate_dialogue_can_stream(monkeypatch):
    """Test generate_npc_dialogue can use streaming when enabled.

    Spec: Verify generate_dialogue, generate_lore, generate_dream, generate_whisper can stream.
    """
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    # Enable effects so streaming can work
    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    # Track if _call_llm_streamable was used
    streamable_called = False
    original_result = "Welcome to my shop, traveler!"

    def mock_streamable(prompt, output=None):
        nonlocal streamable_called
        streamable_called = True
        return original_result

    with patch.object(AIService, "_call_llm_streamable", mock_streamable):
        service = AIService(config)

        result = service.generate_npc_dialogue(
            npc_name="Merchant",
            npc_description="A friendly trader",
            npc_role="merchant",
            theme="fantasy",
        )

        assert streamable_called
        assert result == original_result


def test_generate_lore_can_stream(monkeypatch):
    """Test generate_lore can use streaming when enabled."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    streamable_called = False
    original_result = "Long ago, the ancient kingdom fell to darkness. " * 3

    def mock_streamable(prompt, output=None):
        nonlocal streamable_called
        streamable_called = True
        return original_result

    with patch.object(AIService, "_call_llm_streamable", mock_streamable):
        service = AIService(config)

        result = service.generate_lore("fantasy")

        assert streamable_called


def test_generate_dream_can_stream(monkeypatch):
    """Test generate_dream can use streaming when enabled."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    streamable_called = False
    original_result = "You dream of endless corridors stretching before you."

    def mock_streamable(prompt, output=None):
        nonlocal streamable_called
        streamable_called = True
        return original_result

    with patch.object(AIService, "_call_llm_streamable", mock_streamable):
        service = AIService(config)

        result = service.generate_dream(
            theme="fantasy",
            dread=50,
            choices=None,
            location_name="Dark Cave",
            is_nightmare=True,
        )

        assert streamable_called


def test_generate_whisper_can_stream(monkeypatch):
    """Test generate_whisper can use streaming when enabled."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    streamable_called = False
    original_result = "Something watches from the shadows..."

    def mock_streamable(prompt, output=None):
        nonlocal streamable_called
        streamable_called = True
        return original_result

    with patch.object(AIService, "_call_llm_streamable", mock_streamable):
        service = AIService(config)

        result = service.generate_whisper("fantasy", "dungeon")

        assert streamable_called


# --- Test 7: Streaming respects effects_enabled() ---


def test_streaming_disabled_when_effects_disabled(monkeypatch):
    """Test streaming respects effects_enabled() - no streaming when effects disabled.

    Spec: Test streaming respects effects_enabled() - no output when effects disabled
    (--no-color, --json modes).
    """
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    # Disable effects (simulates --no-color or --json mode)
    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", False)

    # Track which method was called
    call_llm_called = False
    call_streaming_called = False

    def mock_call_llm(prompt, generation_type="default"):
        nonlocal call_llm_called
        call_llm_called = True
        return "Non-streaming response"

    def mock_call_streaming(prompt, output=None):
        nonlocal call_streaming_called
        call_streaming_called = True
        return "Streaming response"

    service = AIService(config)

    with patch.object(service, "_call_llm", mock_call_llm):
        with patch.object(service, "_call_llm_streaming", mock_call_streaming):
            result = service._call_llm_streamable("Test prompt")

            # Should use non-streaming when effects are disabled
            assert call_llm_called
            assert not call_streaming_called
            assert result == "Non-streaming response"


def test_streaming_enabled_when_effects_enabled(monkeypatch):
    """Test streaming is used when effects are enabled."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    # Enable effects
    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    call_llm_called = False
    call_streaming_called = False

    def mock_call_llm(prompt, generation_type="default"):
        nonlocal call_llm_called
        call_llm_called = True
        return "Non-streaming response"

    def mock_call_streaming(prompt, output=None):
        nonlocal call_streaming_called
        call_streaming_called = True
        return "Streaming response"

    service = AIService(config)

    with patch.object(service, "_call_llm", mock_call_llm):
        with patch.object(service, "_call_llm_streaming", mock_call_streaming):
            result = service._call_llm_streamable("Test prompt")

            # Should use streaming when effects are enabled
            assert call_streaming_called
            assert not call_llm_called
            assert result == "Streaming response"


# --- Test 8: Streaming fallback on error ---


def test_streaming_fallback_on_error(monkeypatch):
    """Test streaming falls back to non-streaming on error.

    Spec: If streaming fails, fall back to non-streaming call.
    """
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=True)

    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    def mock_call_streaming_fails(prompt, output=None):
        raise Exception("Streaming failed!")

    def mock_call_llm(prompt, generation_type="default"):
        return "Fallback non-streaming response"

    service = AIService(config)

    with patch.object(service, "_call_llm_streaming", mock_call_streaming_fails):
        with patch.object(service, "_call_llm", mock_call_llm):
            result = service._call_llm_streamable("Test prompt")

            # Should fall back to non-streaming
            assert result == "Fallback non-streaming response"


def test_streaming_config_disabled_uses_non_streaming(monkeypatch):
    """Test that streaming config disabled uses non-streaming even with effects enabled."""
    config = AIConfig(api_key="test-key", provider="openai", enable_streaming=False)

    # Effects enabled but streaming config is disabled
    monkeypatch.setattr("cli_rpg.text_effects._effects_enabled_override", True)

    call_llm_called = False

    def mock_call_llm(prompt, generation_type="default"):
        nonlocal call_llm_called
        call_llm_called = True
        return "Non-streaming response"

    service = AIService(config)

    with patch.object(service, "_call_llm", mock_call_llm):
        result = service._call_llm_streamable("Test prompt")

        assert call_llm_called
        assert result == "Non-streaming response"
