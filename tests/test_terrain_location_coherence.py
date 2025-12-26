"""Tests for terrain-to-location generation coherence.

Spec: Pass WFC terrain type to AI prompts so generated locations match their terrain.
A "Desert Oasis" should only spawn on desert tiles, not forest.
"""

import pytest
from unittest.mock import Mock, patch
import json

from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext


@pytest.fixture
def basic_config(tmp_path):
    """Create basic AIConfig for testing."""
    return AIConfig(
        api_key="test-key",
        model="gpt-3.5-turbo",
        cache_file=str(tmp_path / "cache.json"),
    )


@pytest.fixture
def world_context():
    """Create a basic WorldContext for testing."""
    return WorldContext(
        theme="fantasy",
        theme_essence="A mystical fantasy realm",
        naming_style="Celtic-inspired",
        tone="adventurous",
    )


@pytest.fixture
def region_context():
    """Create a basic RegionContext for testing."""
    return RegionContext(
        name="The Sunbaked Expanse",
        theme="arid desert with ancient ruins",
        danger_level="moderate",
        landmarks=["The Obelisk"],
        coordinates=(10, 10),
    )


class TestTerrainInPrompt:
    """Test that terrain type is included in location generation prompts."""

    # Tests: terrain_type parameter is passed through to AI prompts
    @patch("cli_rpg.ai_service.OpenAI")
    def test_terrain_included_in_prompt(
        self, mock_openai_class, basic_config, world_context, region_context
    ):
        """Verify terrain_type appears in the AI prompt for location generation."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        valid_response = {
            "name": "Desert Oasis",
            "description": "A refreshing oasis amid the dunes.",
            "connections": {"south": "Caravan Route"},
            "category": "wilderness",
        }
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(valid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        service.generate_location_with_context(
            world_context=world_context,
            region_context=region_context,
            terrain_type="desert",
        )

        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args[1]["messages"][0]["content"]

        # Terrain should appear in the prompt
        assert "desert" in prompt.lower()

    # Tests: terrain_type=None should not break the prompt
    @patch("cli_rpg.ai_service.OpenAI")
    def test_terrain_none_uses_default(
        self, mock_openai_class, basic_config, world_context, region_context
    ):
        """Verify prompt works when terrain_type is None (backward compatible)."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        valid_response = {
            "name": "Mysterious Path",
            "description": "A winding path through unknown lands.",
            "connections": {},
            "category": "wilderness",
        }
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(valid_response)
        mock_client.chat.completions.create.return_value = mock_response

        service = AIService(basic_config)
        # Should not raise with terrain_type=None
        result = service.generate_location_with_context(
            world_context=world_context,
            region_context=region_context,
            terrain_type=None,
        )

        assert result["name"] == "Mysterious Path"


class TestExpandWorldTerrainPassthrough:
    """Test that terrain is passed through world expansion functions."""

    # Tests: expand_world() accepts terrain_type parameter
    def test_expand_world_accepts_terrain_type(self):
        """Verify expand_world function signature includes terrain_type."""
        from cli_rpg.ai_world import expand_world
        import inspect

        sig = inspect.signature(expand_world)
        assert "terrain_type" in sig.parameters
        param = sig.parameters["terrain_type"]
        assert param.default is None  # Optional with None default

    # Tests: expand_area() accepts terrain_type parameter
    def test_expand_area_accepts_terrain_type(self):
        """Verify expand_area function signature includes terrain_type."""
        from cli_rpg.ai_world import expand_area
        import inspect

        sig = inspect.signature(expand_area)
        assert "terrain_type" in sig.parameters
        param = sig.parameters["terrain_type"]
        assert param.default is None  # Optional with None default

    # Tests: expand_world passes terrain_type to generate_location_with_context
    @patch("cli_rpg.ai_world._generate_location_ascii_art")
    def test_expand_world_passes_terrain_to_generation(
        self, mock_art, world_context, region_context
    ):
        """Verify expand_world passes terrain_type to AI service."""
        from cli_rpg.ai_world import expand_world
        from cli_rpg.models.location import Location

        mock_art.return_value = None

        # Create mock AI service
        mock_ai = Mock()
        mock_ai.generate_location_with_context.return_value = {
            "name": "Desert Outpost",
            "description": "A dusty outpost in the desert.",
            "connections": {},
            "category": "settlement",
        }
        mock_ai.generate_npcs_for_location.return_value = []

        # Create starting location
        starting_loc = Location(
            name="Starting Town",
            description="A small town",
            coordinates=(0, 0),
        )
        world = {"Starting Town": starting_loc}

        # Call expand_world with terrain_type
        expand_world(
            world=world,
            ai_service=mock_ai,
            from_location="Starting Town",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=world_context,
            region_context=region_context,
            terrain_type="desert",
        )

        # Verify terrain_type was passed to generate_location_with_context
        mock_ai.generate_location_with_context.assert_called_once()
        call_kwargs = mock_ai.generate_location_with_context.call_args[1]
        assert call_kwargs.get("terrain_type") == "desert"


class TestPromptTemplateHasTerrain:
    """Test that prompt template includes terrain placeholder."""

    # Tests: DEFAULT_LOCATION_PROMPT_MINIMAL includes terrain_type
    def test_location_prompt_minimal_has_terrain_placeholder(self):
        """Verify the minimal location prompt template includes terrain."""
        from cli_rpg.ai_config import DEFAULT_LOCATION_PROMPT_MINIMAL

        assert "{terrain_type}" in DEFAULT_LOCATION_PROMPT_MINIMAL
        # Should mention terrain in context
        assert "terrain" in DEFAULT_LOCATION_PROMPT_MINIMAL.lower()
