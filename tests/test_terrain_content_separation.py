"""Tests for terrain/content separation - AI should only generate content, not connections.

This test file verifies that:
1. AI prompts contain NO references to exits, directions, or connections
2. AI parsing does NOT require connections in responses
3. If AI returns connections, they are ignored
4. Location data returned has no connections key
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.ai_config import (
    AIConfig,
    DEFAULT_LOCATION_PROMPT,
    DEFAULT_LOCATION_PROMPT_MINIMAL,
)
from cli_rpg.ai_service import AIService


class TestPromptNoConnections:
    """Test that prompts have no connection-related content."""

    def test_minimal_location_prompt_no_connections_field(self):
        """Minimal prompt has no 'connections' field in example JSON."""
        # The minimal prompt should NOT contain "connections" anywhere
        assert "connections" not in DEFAULT_LOCATION_PROMPT_MINIMAL.lower()

    def test_minimal_location_prompt_no_exits(self):
        """Minimal prompt contains no words 'exit' or 'direction' related to navigation."""
        prompt_lower = DEFAULT_LOCATION_PROMPT_MINIMAL.lower()
        # Should not have exit/direction in context of connections
        assert '"direction"' not in prompt_lower  # Not in JSON example
        # Note: direction may appear in Navigation context, but should be removed

    def test_minimal_location_prompt_no_connections_in_json_example(self):
        """Verify the JSON example in minimal prompt has no connections key."""
        # Find the JSON example in the prompt
        import re
        # Look for JSON block pattern
        json_match = re.search(r'\{[^{}]*"name"[^{}]*\}', DEFAULT_LOCATION_PROMPT_MINIMAL, re.DOTALL)
        if json_match:
            json_example = json_match.group(0)
            assert "connections" not in json_example

    def test_default_location_prompt_no_connections_field(self):
        """Default prompt should also have no connections field."""
        # After refactoring, the default prompt should NOT contain connections
        assert "connections" not in DEFAULT_LOCATION_PROMPT.lower()

    def test_default_location_prompt_no_requirement_about_connections(self):
        """Default prompt requirements should not mention connections."""
        # Requirements about suggesting connections should be removed
        assert "suggest" not in DEFAULT_LOCATION_PROMPT.lower() or "connection" not in DEFAULT_LOCATION_PROMPT.lower()


class TestParseLocationResponseNoConnections:
    """Test that parsing doesn't require connections and ignores them if present."""

    @pytest.fixture
    def ai_service(self):
        """Create AIService with mocked client."""
        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False
        )
        service = AIService(config)
        return service

    def test_parse_location_response_no_connections_required(self, ai_service):
        """Parsing succeeds without 'connections' in response."""
        # Response with no connections field at all
        response = '''{
            "name": "Mystic Glade",
            "description": "A peaceful clearing in the enchanted forest, where mystical energies pulse through ancient trees.",
            "category": "forest"
        }'''

        result = ai_service._parse_location_response(response)

        assert result["name"] == "Mystic Glade"
        assert "description" in result
        assert result["category"] == "forest"
        # Should NOT have connections key
        assert "connections" not in result

    def test_parse_location_response_ignores_connections(self, ai_service):
        """If AI includes connections, they are ignored and not returned."""
        # Response with connections that should be ignored
        response = '''{
            "name": "Twisted Forest",
            "description": "Dark twisted trees block out the sun, creating an eerie atmosphere.",
            "connections": {
                "north": "Mountain Pass",
                "south": "Village Square"
            },
            "category": "forest"
        }'''

        result = ai_service._parse_location_response(response)

        assert result["name"] == "Twisted Forest"
        assert "description" in result
        # Connections should NOT be in the result
        assert "connections" not in result

    def test_location_data_has_no_connections_key(self, ai_service):
        """Returned dict has no 'connections' key regardless of input."""
        response = '''{
            "name": "Ancient Ruins",
            "description": "Crumbling stone walls covered in moss, remnants of a forgotten civilization.",
            "category": "ruins"
        }'''

        result = ai_service._parse_location_response(response)

        # Verify all expected keys are present
        assert "name" in result
        assert "description" in result
        assert "category" in result
        assert "npcs" in result

        # Verify connections is NOT present
        assert "connections" not in result

    def test_parse_location_with_npcs_no_connections(self, ai_service):
        """Parsing with NPCs works and still has no connections."""
        response = '''{
            "name": "Trader's Rest",
            "description": "A small waystation where travelers can find shelter and supplies.",
            "category": "settlement",
            "npcs": [
                {
                    "name": "Old Marcus",
                    "description": "A weathered trader with knowing eyes.",
                    "dialogue": "Welcome, traveler! What can I get for you?",
                    "role": "merchant"
                }
            ]
        }'''

        result = ai_service._parse_location_response(response)

        assert result["name"] == "Trader's Rest"
        assert len(result["npcs"]) == 1
        assert result["npcs"][0]["name"] == "Old Marcus"
        # Still no connections
        assert "connections" not in result


class TestGenerateLocationWithContextNoConnections:
    """Test that generate_location_with_context returns no connections."""

    @pytest.fixture
    def ai_service(self):
        """Create AIService with mocked client."""
        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False
        )
        service = AIService(config)
        return service

    @pytest.fixture
    def mock_world_context(self):
        """Create mock WorldContext."""
        ctx = MagicMock()
        ctx.theme = "dark fantasy"
        ctx.theme_essence = "A grim world of shadows and forgotten gods."
        ctx.naming_style = "Germanic with archaic suffixes"
        ctx.tone = "Foreboding and melancholic"
        return ctx

    @pytest.fixture
    def mock_region_context(self):
        """Create mock RegionContext."""
        ctx = MagicMock()
        ctx.name = "Shadowmere"
        ctx.theme = "Haunted marshlands with will-o-wisps"
        ctx.danger_level = "high"
        return ctx

    def test_generate_location_with_context_no_connections(
        self, ai_service, mock_world_context, mock_region_context
    ):
        """Full generation returns no connections."""
        # Mock the LLM call to return a location without connections
        mock_response = '''{
            "name": "Marsh of Whispers",
            "description": "A fog-laden bog where voices of the lost echo through twisted reeds.",
            "category": "wilderness"
        }'''

        with patch.object(ai_service, '_call_llm', return_value=mock_response):
            result = ai_service.generate_location_with_context(
                world_context=mock_world_context,
                region_context=mock_region_context,
                source_location="Village Gate",
                direction="north",
                terrain_type="swamp"
            )

        assert result["name"] == "Marsh of Whispers"
        assert "description" in result
        # Must NOT have connections
        assert "connections" not in result
        # NPCs should be empty list for layered generation
        assert result["npcs"] == []

    def test_generate_location_with_context_ignores_ai_connections(
        self, ai_service, mock_world_context, mock_region_context
    ):
        """Even if AI returns connections, they are stripped out."""
        # Mock response WITH connections (should be ignored)
        mock_response = '''{
            "name": "Drowned Temple",
            "description": "A sunken shrine barely visible beneath murky waters.",
            "connections": {
                "south": "Village Gate",
                "east": "Deep Marsh"
            },
            "category": "ruins"
        }'''

        with patch.object(ai_service, '_call_llm', return_value=mock_response):
            result = ai_service.generate_location_with_context(
                world_context=mock_world_context,
                region_context=mock_region_context,
                source_location="Village Gate",
                direction="north",
                terrain_type="swamp"
            )

        assert result["name"] == "Drowned Temple"
        # Connections MUST NOT be in result
        assert "connections" not in result
