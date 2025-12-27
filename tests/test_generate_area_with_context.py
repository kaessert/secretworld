"""Tests for generate_area_with_context layered AI generation.

Spec: Verify that generate_area_with_context() orchestrates Layers 3-4 for
named location clusters, ensuring coherence with world/region themes.
"""

import json
import pytest
from unittest.mock import Mock, patch, call

from cli_rpg.ai_service import AIService, AIConfig
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext


class TestGenerateAreaWithContext:
    """Tests for AIService.generate_area_with_context()."""

    @pytest.fixture
    def mock_openai(self):
        """Create mock OpenAI client."""
        with patch('cli_rpg.ai_service.OpenAI') as mock_class:
            mock_client = Mock()
            mock_class.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def ai_service(self, mock_openai, tmp_path):
        """Create AIService with mocked OpenAI."""
        config = AIConfig(
            api_key="test-key",
            generation_max_retries=0,
            retry_delay=0.01,
            cache_file=str(tmp_path / "test_cache.json")
        )
        return AIService(config)

    @pytest.fixture
    def world_context(self):
        """Create test WorldContext."""
        return WorldContext(
            theme="fantasy",
            theme_essence="dark medieval fantasy with ancient evils",
            naming_style="Old English with Celtic influence",
            tone="grim and foreboding"
        )

    @pytest.fixture
    def region_context(self):
        """Create test RegionContext."""
        return RegionContext(
            name="Shadowfen",
            theme="cursed marshlands with twisted trees",
            danger_level="dangerous",
            landmarks=["The Sunken Tower", "Dead Man's Crossing"],
            coordinates=(5, 5)
        )

    def _make_location_response(self, name: str, description: str, category: str = "wilderness"):
        """Helper to create mock location response."""
        return json.dumps({
            "name": name,
            "description": description,
            "category": category
        })

    def _make_npc_response(self, npcs: list[dict]):
        """Helper to create mock NPC response."""
        return json.dumps({"npcs": npcs})

    def test_generate_area_with_context_returns_list_of_locations(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: generate_area_with_context returns a list of location dicts.

        Item 4 from ISSUES.md: Area generation should return proper location dicts.
        """
        # Mock responses for location generation (Layer 3) and NPC generation (Layer 4)
        mock_responses = [
            # Location 1 (entry)
            Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                "Shadowfen Gate", "A crumbling stone archway marks the entrance."
            )))]),
            Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]),
            # Location 2
            Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                "Murky Pool", "Dark waters reflect no light."
            )))]),
            Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]),
            # Location 3
            Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                "Twisted Copse", "Gnarled trees reach like claws."
            )))]),
            Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]),
        ]
        mock_openai.chat.completions.create.side_effect = mock_responses

        result = ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=3
        )

        assert isinstance(result, list)
        assert len(result) >= 3

    def test_generate_area_with_context_includes_entry_at_origin(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: Entry location should be at relative coordinates (0, 0).

        Item 4 from ISSUES.md: Area layout must have entry at origin.
        """
        mock_responses = []
        for i in range(6):  # 3 locations * 2 calls each (location + NPC)
            if i % 2 == 0:  # Location response
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                    f"Location {i//2}", "A test location."
                )))]))
            else:  # NPC response
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]))

        mock_openai.chat.completions.create.side_effect = mock_responses

        result = ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=3
        )

        # Find the entry location (should be at 0,0)
        entry = next((loc for loc in result if loc.get("relative_coords") == [0, 0]), None)
        assert entry is not None, "Entry location at (0,0) not found"

    def test_generate_area_with_context_each_location_has_required_fields(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: Each location must have name, description, category, npcs, relative_coords.

        Item 4 from ISSUES.md: Locations must have all required fields.
        """
        mock_responses = []
        for i in range(6):  # 3 locations * 2 calls each
            if i % 2 == 0:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                    f"Test Location {i//2}", "A well-described test location.", "town"
                )))]))
            else:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_npc_response([
                    {"name": "Test NPC", "description": "A test NPC", "dialogue": "Hello", "role": "merchant"}
                ])))]))

        mock_openai.chat.completions.create.side_effect = mock_responses

        result = ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=3
        )

        required_fields = ["name", "description", "category", "npcs", "relative_coords"]
        for loc in result:
            for field in required_fields:
                assert field in loc, f"Location missing required field: {field}"

    def test_generate_area_with_context_uses_world_context_theme(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: Locations should use world context theme in generation prompts.

        Item 4 from ISSUES.md: Layered generation must use world context.
        """
        # Size 4 is the minimum, so we need 4*2=8 mock responses
        mock_responses = []
        for i in range(8):  # 4 locations * 2 calls each
            if i % 2 == 0:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                    f"Location {i//2}", "Test"
                )))]))
            else:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]))

        mock_openai.chat.completions.create.side_effect = mock_responses

        ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=4  # Minimum valid size
        )

        # Check that the prompts contain world context theme elements
        calls = mock_openai.chat.completions.create.call_args_list
        # Get first location generation call (index 0)
        first_call_messages = calls[0][1]['messages']
        prompt_content = first_call_messages[-1]['content']  # User message

        # Prompt should reference theme-related content from world context
        assert "fantasy" in prompt_content.lower() or "dark medieval" in prompt_content.lower()

    def test_generate_area_with_context_uses_region_context(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: Locations should use region context theme in generation prompts.

        Item 4 from ISSUES.md: Layered generation must use region context.
        """
        # Size 4 is the minimum, so we need 4*2=8 mock responses
        mock_responses = []
        for i in range(8):  # 4 locations * 2 calls each
            if i % 2 == 0:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                    f"Location {i//2}", "Test"
                )))]))
            else:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]))

        mock_openai.chat.completions.create.side_effect = mock_responses

        ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=4  # Minimum valid size
        )

        # Check that prompts contain region context elements
        calls = mock_openai.chat.completions.create.call_args_list
        first_call_messages = calls[0][1]['messages']
        prompt_content = first_call_messages[-1]['content']

        # Prompt should reference region name or theme
        assert "shadowfen" in prompt_content.lower() or "marshland" in prompt_content.lower()

    def test_generate_area_with_context_generates_npcs_for_each_location(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: Each location should have NPCs generated via Layer 4.

        Item 4 from ISSUES.md: Area locations must include NPC generation.
        """
        npc_data = [
            {"name": "Marsh Guide", "description": "A weathered local", "dialogue": "Careful...", "role": "guide"}
        ]
        mock_responses = []
        for i in range(6):  # 3 locations * 2 calls each
            if i % 2 == 0:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                    f"Location {i//2}", "Test location"
                )))]))
            else:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_npc_response(npc_data)))]))

        mock_openai.chat.completions.create.side_effect = mock_responses

        result = ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=3
        )

        # Each location should have npcs (may be empty list or populated)
        for loc in result:
            assert "npcs" in loc
            assert isinstance(loc["npcs"], list)

        # At least one location should have NPCs (based on our mock)
        locations_with_npcs = [loc for loc in result if len(loc["npcs"]) > 0]
        assert len(locations_with_npcs) > 0

    def test_generate_area_with_context_respects_size_parameter(
        self, ai_service, mock_openai, world_context, region_context
    ):
        """Spec: Generated area should have approximately 'size' locations.

        Item 4 from ISSUES.md: Size parameter should control area size.
        """
        target_size = 5
        mock_responses = []
        for i in range(target_size * 2):  # size locations * 2 calls each
            if i % 2 == 0:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_location_response(
                    f"Location {i//2}", "Test location"
                )))]))
            else:
                mock_responses.append(Mock(choices=[Mock(message=Mock(content=self._make_npc_response([])))]))

        mock_openai.chat.completions.create.side_effect = mock_responses

        result = ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction="north",
            size=target_size
        )

        assert len(result) == target_size


class TestExpandAreaWithLayeredGeneration:
    """Integration tests for expand_area() using layered generation."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service with both generation methods."""
        ai_service = Mock()
        return ai_service

    @pytest.fixture
    def sample_world(self):
        """Create sample world with start location."""
        from cli_rpg.models.location import Location
        start = Location(name="Start", description="Starting point", coordinates=(0, 0))
        return {"Start": start}

    @pytest.fixture
    def world_context(self):
        """Create test WorldContext."""
        return WorldContext.default("fantasy")

    @pytest.fixture
    def region_context(self):
        """Create test RegionContext."""
        return RegionContext.default("Test Region", (0, 1))

    def test_expand_area_uses_layered_generation_when_contexts_provided(
        self, mock_ai_service, sample_world, world_context, region_context
    ):
        """Spec: expand_area should use generate_area_with_context when contexts provided.

        Item 4 from ISSUES.md: expand_area must use layered generation for coherence.
        """
        from cli_rpg.ai_world import expand_area

        # Setup mock to return valid area data
        mock_ai_service.generate_area_with_context.return_value = [
            {
                "name": "New Location",
                "description": "A new location",
                "category": "wilderness",
                "npcs": [],
                "relative_coords": [0, 0]
            }
        ]

        expand_area(
            world=sample_world,
            ai_service=mock_ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=world_context,
            region_context=region_context
        )

        # Verify layered generation was called
        mock_ai_service.generate_area_with_context.assert_called_once()
        call_kwargs = mock_ai_service.generate_area_with_context.call_args[1]
        assert call_kwargs["world_context"] == world_context
        assert call_kwargs["region_context"] == region_context

    def test_expand_area_falls_back_to_monolithic_without_contexts(
        self, mock_ai_service, sample_world
    ):
        """Spec: expand_area should use generate_area when contexts are None.

        Item 4 from ISSUES.md: Backward compatibility with monolithic generation.
        """
        from cli_rpg.ai_world import expand_area

        # Setup mock to return valid area data
        mock_ai_service.generate_area.return_value = [
            {
                "name": "New Location",
                "description": "A new location",
                "category": "wilderness",
                "npcs": [],
                "relative_coords": [0, 0]
            }
        ]

        expand_area(
            world=sample_world,
            ai_service=mock_ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
            world_context=None,
            region_context=None
        )

        # Verify monolithic generation was called (not layered)
        mock_ai_service.generate_area.assert_called_once()
        mock_ai_service.generate_area_with_context.assert_not_called()
