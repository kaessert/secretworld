"""Tests for AI content logging functionality.

Spec: Add AI content logging to GameplayLogger so AI-generated content
(locations, NPCs, dialogue, quests, etc.) can be reviewed from session transcripts.
"""
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from cli_rpg.logging_service import GameplayLogger


class TestLogAiContent:
    """Tests for GameplayLogger.log_ai_content method."""

    # Spec: test_log_ai_content_writes_entry - Verify log_ai_content writes correct JSON structure
    def test_log_ai_content_writes_entry(self):
        """log_ai_content should write a valid JSON entry with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = GameplayLogger(str(log_path))

            content = {"name": "Dark Forest", "description": "A mysterious forest"}
            prompt_hash = "abc123def456gh78"

            logger.log_ai_content(
                generation_type="location",
                prompt_hash=prompt_hash,
                content=content
            )
            logger.close()

            # Read and parse the log entry
            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            assert len(entries) == 1
            entry = entries[0]

            # Verify structure
            assert entry["type"] == "ai_content"
            assert entry["generation_type"] == "location"
            assert entry["prompt_hash"] == prompt_hash
            assert entry["content"] == content
            assert "timestamp" in entry
            # raw_response should not be present when not provided
            assert "raw_response" not in entry

    # Spec: test_log_ai_content_includes_raw_response - raw_response is included when provided
    def test_log_ai_content_includes_raw_response(self):
        """log_ai_content should include raw_response when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = GameplayLogger(str(log_path))

            content = {"name": "Village Elder"}
            raw_response = '{"name": "Village Elder", "extra_field": true}'

            logger.log_ai_content(
                generation_type="npc",
                prompt_hash="1234567890abcdef",
                content=content,
                raw_response=raw_response
            )
            logger.close()

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            assert len(entries) == 1
            assert entries[0]["raw_response"] == raw_response

    # Spec: test_log_ai_content_various_types - Works with different generation types
    def test_log_ai_content_various_types(self):
        """log_ai_content should work with various generation types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = GameplayLogger(str(log_path))

            types_to_test = [
                ("location", {"name": "Mountain Pass"}),
                ("npc", {"name": "Merchant"}),
                ("enemy", {"name": "Goblin", "hp": 30}),
                ("quest", {"title": "Find the artifact"}),
                ("dialogue", {"text": "Hello, traveler!"}),
                ("dream", {"text": "You dream of distant lands..."}),
                ("whisper", {"text": "Shadows whisper..."}),
            ]

            for gen_type, content in types_to_test:
                logger.log_ai_content(
                    generation_type=gen_type,
                    prompt_hash=f"hash_{gen_type}",
                    content=content
                )

            logger.close()

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            assert len(entries) == len(types_to_test)

            for i, (gen_type, content) in enumerate(types_to_test):
                assert entries[i]["generation_type"] == gen_type
                assert entries[i]["content"] == content


class TestPromptHash:
    """Tests for prompt hash consistency."""

    # Spec: test_prompt_hash_is_consistent - Same prompt produces same hash
    def test_prompt_hash_is_consistent(self):
        """Same prompt should produce the same hash every time."""
        prompt = "Generate a dark forest location with mysterious atmosphere"

        # Compute hash the way AIService should
        hash1 = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        hash2 = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_different_prompts_different_hashes(self):
        """Different prompts should produce different hashes."""
        prompt1 = "Generate a dark forest"
        prompt2 = "Generate a bright meadow"

        hash1 = hashlib.sha256(prompt1.encode()).hexdigest()[:16]
        hash2 = hashlib.sha256(prompt2.encode()).hexdigest()[:16]

        assert hash1 != hash2


class TestAIServiceContentLogger:
    """Tests for AIService content logger callback."""

    # Spec: test_ai_service_calls_logger_on_generation - Verify callback invoked with correct args
    def test_ai_service_calls_logger_on_generation(self):
        """AIService should invoke content_logger callback after successful generation."""
        from cli_rpg.ai_config import AIConfig
        from cli_rpg.ai_service import AIService

        # Track callback invocations
        logged_calls: list[tuple[str, str, Any, str]] = []

        def mock_logger(
            generation_type: str,
            prompt_hash: str,
            content: Any,
            raw_response: str
        ) -> None:
            logged_calls.append((generation_type, prompt_hash, content, raw_response))

        # Disable caching to ensure we hit the LLM call
        config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)

        service = AIService(config, content_logger=mock_logger)

        # Patch at instance level (after service creation)
        with patch.object(service, '_call_llm') as mock_call:
            # Mock successful response
            mock_call.return_value = json.dumps({
                "name": "Dark Forest",
                "description": "A mysterious forest shrouded in mist",
                "category": "forest",
                "npcs": []
            })

            # Generate a location
            result = service.generate_location(theme="fantasy")

            # Verify callback was invoked
            assert len(logged_calls) == 1
            gen_type, prompt_hash, content, raw_response = logged_calls[0]

            assert gen_type == "location"
            assert len(prompt_hash) == 16  # SHA256 first 16 chars
            assert content["name"] == "Dark Forest"
            assert "Dark Forest" in raw_response

    # Spec: test_no_logging_when_callback_not_set - Verify no errors when callback is None
    def test_no_logging_when_callback_not_set(self):
        """AIService should work without errors when content_logger is None."""
        from cli_rpg.ai_config import AIConfig
        from cli_rpg.ai_service import AIService

        # Disable caching to ensure we hit the LLM call
        config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)

        # No content_logger provided (should default to None)
        service = AIService(config)

        with patch.object(service, '_call_llm') as mock_call:
            mock_call.return_value = json.dumps({
                "name": "Village",
                "description": "A peaceful village",
                "category": "village",
                "npcs": []
            })

            # Should not raise any errors
            result = service.generate_location(theme="fantasy")
            assert result["name"] == "Village"

    def test_logger_receives_raw_response(self):
        """Content logger should receive the raw LLM response for debugging."""
        from cli_rpg.ai_config import AIConfig
        from cli_rpg.ai_service import AIService

        raw_responses: list[str] = []

        def capture_raw(gen_type: str, hash: str, content: Any, raw: str) -> None:
            raw_responses.append(raw)

        # Disable caching to ensure we hit the LLM call
        config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)

        # The raw response will include extra whitespace or formatting
        raw_json = '  {"name": "Cave", "description": "Dark cave", "category": "cave", "npcs": []}  '

        service = AIService(config, content_logger=capture_raw)

        with patch.object(service, '_call_llm') as mock_call:
            mock_call.return_value = raw_json

            service.generate_location(theme="fantasy")

            assert len(raw_responses) == 1
            assert raw_responses[0] == raw_json


class TestIntegrationWithGameplayLogger:
    """Integration tests with GameplayLogger."""

    def test_ai_service_with_gameplay_logger(self):
        """AIService should work with GameplayLogger.log_ai_content as callback."""
        from cli_rpg.ai_config import AIConfig
        from cli_rpg.ai_service import AIService

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"
            gameplay_logger = GameplayLogger(str(log_path))

            # Disable caching to ensure we hit the LLM call
            config = AIConfig(api_key="test-key", provider="openai", enable_caching=False)

            # Wire up the callback
            service = AIService(
                config,
                content_logger=gameplay_logger.log_ai_content
            )

            with patch.object(service, '_call_llm') as mock_call:
                mock_call.return_value = json.dumps({
                    "name": "Haunted Tower",
                    "description": "An ancient tower",
                    "category": "tower",
                    "npcs": []
                })

                service.generate_location(theme="fantasy")

            gameplay_logger.close()

            # Verify log file content
            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            assert len(entries) == 1
            entry = entries[0]
            assert entry["type"] == "ai_content"
            assert entry["generation_type"] == "location"
            assert entry["content"]["name"] == "Haunted Tower"
