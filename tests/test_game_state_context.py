"""Tests for context caching in GameState.

Tests for:
- get_or_create_world_context
- get_or_create_region_context
- Serialization/deserialization of contexts in to_dict/from_dict
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.generation_context import GenerationContext
from cli_rpg.game_state import GameState


@pytest.fixture
def basic_character():
    """Create a basic character for testing."""
    return Character(
        name="TestHero",
        strength=10,
        dexterity=10,
        intelligence=10,
        character_class=CharacterClass.WARRIOR,
    )


@pytest.fixture
def basic_world():
    """Create a basic world for testing."""
    return {
        "Town Square": Location(
            name="Town Square",
            description="A bustling town center.",
            coordinates=(0, 0),
        ),
        "Forest Path": Location(
            name="Forest Path",
            description="A path into the dark woods.",
            coordinates=(0, 1),
        ),
    }


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock()
    service.generate_world_context.return_value = WorldContext(
        theme="fantasy",
        theme_essence="A magical realm of wonder",
        naming_style="Celtic-inspired",
        tone="adventurous",
        generated_at=datetime.now(),
    )

    def create_region_context(**kwargs):
        """Create a fresh RegionContext based on coordinates."""
        coords = kwargs.get("coordinates", (0, 0))
        return RegionContext(
            name=f"Region at {coords}",
            theme="untamed wilderness",
            danger_level="moderate",
            landmarks=["The Old Oak"],
            coordinates=coords,
            generated_at=datetime.now(),
        )

    service.generate_region_context.side_effect = create_region_context
    return service


class TestGetOrCreateWorldContext:
    """Test get_or_create_world_context method."""

    def test_returns_default_without_ai(self, basic_character, basic_world):
        """Test fallback to default when no AI service."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=None,
            theme="fantasy",
        )

        context = game_state.get_or_create_world_context()

        assert isinstance(context, WorldContext)
        assert context.theme == "fantasy"
        # Should have default values
        assert context.theme_essence != ""
        assert context.generated_at is None  # Default context not AI-generated

    def test_caches_result(self, basic_character, basic_world, mock_ai_service):
        """Test world context is cached after first call."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # First call - should generate
        context1 = game_state.get_or_create_world_context()
        # Second call - should use cache
        context2 = game_state.get_or_create_world_context()

        assert context1 is context2
        # AI service should only be called once
        assert mock_ai_service.generate_world_context.call_count == 1

    def test_uses_ai_when_available(
        self, basic_character, basic_world, mock_ai_service
    ):
        """Test uses AI service to generate context when available."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        context = game_state.get_or_create_world_context()

        assert context.theme_essence == "A magical realm of wonder"
        assert context.generated_at is not None
        mock_ai_service.generate_world_context.assert_called_once_with("fantasy")

    def test_fallback_on_ai_error(self, basic_character, basic_world, mock_ai_service):
        """Test falls back to default on AI error."""
        mock_ai_service.generate_world_context.side_effect = Exception("API error")

        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="cyberpunk",
        )

        context = game_state.get_or_create_world_context()

        # Should return default context for the theme
        assert isinstance(context, WorldContext)
        assert context.theme == "cyberpunk"


class TestGetOrCreateRegionContext:
    """Test get_or_create_region_context method."""

    def test_caches_by_region_coords(self, basic_character, basic_world, mock_ai_service):
        """Test region contexts cached by region coordinates (16x16 regions).

        World coords (0,0) and (1,1) both fall in region (0,0).
        World coords (16,0) falls in region (1,0) - a different region.
        """
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # First call for (0, 0) - region (0, 0)
        context1 = game_state.get_or_create_region_context((0, 0))
        # Second call for same region coords - should use cache
        context2 = game_state.get_or_create_region_context((0, 0))
        # Different world coords but SAME region - should still use cache
        context3 = game_state.get_or_create_region_context((1, 1))
        # Different region (1, 0) - should generate new
        context4 = game_state.get_or_create_region_context((16, 0))

        assert context1 is context2
        assert context1 is context3  # Same region (0, 0)
        assert context1 is not context4  # Different region (1, 0)
        # Should have called generate twice (once per unique region)
        assert mock_ai_service.generate_region_context.call_count == 2

    def test_returns_default_without_ai(self, basic_character, basic_world):
        """Test fallback to default when no AI service."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=None,
            theme="fantasy",
        )

        context = game_state.get_or_create_region_context((5, 5), "mountains")

        assert isinstance(context, RegionContext)
        # Context uses center of region (8, 8) for region (0, 0)
        assert context.coordinates == (8, 8)
        assert context.generated_at is None  # Default context

    def test_uses_terrain_hint(self, basic_character, basic_world, mock_ai_service):
        """Test terrain hint is passed to AI service."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # Need world context first
        game_state.get_or_create_world_context()

        game_state.get_or_create_region_context((0, 0), terrain_hint="swamp")

        # Check terrain_hint was passed
        call_args = mock_ai_service.generate_region_context.call_args
        assert call_args[1]["terrain_hint"] == "swamp"


class TestContextSerialization:
    """Test contexts are properly serialized/deserialized."""

    def test_world_context_in_to_dict(self, basic_character, basic_world):
        """Test world_context included in save data."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            theme="fantasy",
        )

        # Set a world context
        game_state.world_context = WorldContext(
            theme="fantasy",
            theme_essence="Test essence",
            naming_style="Test style",
            tone="Test tone",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        data = game_state.to_dict()

        assert "world_context" in data
        assert data["world_context"]["theme"] == "fantasy"
        assert data["world_context"]["theme_essence"] == "Test essence"

    def test_region_contexts_in_to_dict(self, basic_character, basic_world):
        """Test region_contexts included in save data."""
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            theme="fantasy",
        )

        # Set region contexts
        game_state.region_contexts = {
            (0, 0): RegionContext(
                name="Central Region",
                theme="peaceful meadows",
                danger_level="safe",
                landmarks=["Village"],
                coordinates=(0, 0),
            ),
            (1, 1): RegionContext(
                name="Northern Wilds",
                theme="dark forest",
                danger_level="dangerous",
                landmarks=["The Hollow"],
                coordinates=(1, 1),
            ),
        }

        data = game_state.to_dict()

        assert "region_contexts" in data
        # Check it's serialized as a list (JSON doesn't support tuple keys)
        assert isinstance(data["region_contexts"], list)
        assert len(data["region_contexts"]) == 2

    def test_contexts_restored_from_dict(self, basic_character, basic_world):
        """Test contexts properly restored on load."""
        # Create original game state with contexts
        original_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            theme="fantasy",
        )
        original_state.world_context = WorldContext(
            theme="fantasy",
            theme_essence="Restored essence",
            naming_style="Restored style",
            tone="Restored tone",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        original_state.region_contexts = {
            (0, 0): RegionContext(
                name="Restored Region",
                theme="restored theme",
                danger_level="moderate",
                landmarks=["Restored Landmark"],
                coordinates=(0, 0),
            ),
        }

        # Serialize and deserialize
        data = original_state.to_dict()
        restored_state = GameState.from_dict(data)

        # Verify world_context restored
        assert restored_state.world_context is not None
        assert restored_state.world_context.theme_essence == "Restored essence"
        assert restored_state.world_context.generated_at == datetime(2024, 1, 1, 12, 0, 0)

        # Verify region_contexts restored
        assert len(restored_state.region_contexts) == 1
        assert (0, 0) in restored_state.region_contexts
        assert restored_state.region_contexts[(0, 0)].name == "Restored Region"

    def test_backward_compatible_without_contexts(self, basic_character, basic_world):
        """Test loading old save without contexts works."""
        # Simulate old save format without contexts
        old_save_data = {
            "character": basic_character.to_dict(),
            "current_location": "Town Square",
            "world": {name: loc.to_dict() for name, loc in basic_world.items()},
            "theme": "fantasy",
            # No world_context or region_contexts
        }

        restored_state = GameState.from_dict(old_save_data)

        assert restored_state.world_context is None
        assert restored_state.region_contexts == {}


class TestGetGenerationContext:
    """Test get_generation_context method."""

    def test_returns_generation_context(self, basic_character, basic_world):
        """Test get_generation_context returns a GenerationContext instance."""
        # Spec: get_generation_context returns GenerationContext with available layers
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            theme="fantasy",
        )

        ctx = game_state.get_generation_context()

        assert isinstance(ctx, GenerationContext)
        assert ctx.world is not None
        assert ctx.world.theme == "fantasy"

    def test_uses_default_world_context(self, basic_character, basic_world):
        """Test fallback to default WorldContext when no AI service."""
        # Spec: get_generation_context gets/creates WorldContext (Layer 1)
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=None,
            theme="cyberpunk",
        )

        ctx = game_state.get_generation_context()

        assert ctx.world.theme == "cyberpunk"
        assert ctx.world.theme_essence != ""  # Should have default value

    def test_includes_region_context_with_coords(
        self, basic_character, basic_world, mock_ai_service
    ):
        """Test includes RegionContext when coordinates are available."""
        # Spec: get_generation_context includes Layer 2 when coords provided
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        # Provide explicit coords
        ctx = game_state.get_generation_context(coords=(0, 0))

        assert ctx.region is not None
        assert isinstance(ctx.region, RegionContext)

    def test_uses_current_location_coords_by_default(
        self, basic_character, basic_world, mock_ai_service
    ):
        """Test uses current location coordinates when coords not specified."""
        # Spec: get_generation_context defaults to current location coords
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        ctx = game_state.get_generation_context()

        # Should use Town Square's coords (0, 0)
        assert ctx.region is not None
        # Region coords will be center of region (8, 8) for region (0, 0)
        assert ctx.region.coordinates == (8, 8)

    def test_region_none_when_no_coords(self, basic_character):
        """Test region is None when location has no coordinates."""
        # Spec: get_generation_context handles locations without coords
        world_without_coords = {
            "Mystery Place": Location(
                name="Mystery Place",
                description="A place without coordinates.",
                coordinates=None,  # No coords
            ),
        }
        game_state = GameState(
            character=basic_character,
            world=world_without_coords,
            starting_location="Mystery Place",
            theme="fantasy",
        )

        ctx = game_state.get_generation_context()

        assert ctx.world is not None
        assert ctx.region is None

    def test_optional_layers_none_initially(self, basic_character, basic_world):
        """Test settlement and lore layers are None (not yet implemented)."""
        # Spec: Layers 5 and 6 return None until caches are implemented
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            theme="fantasy",
        )

        ctx = game_state.get_generation_context()

        # These are not yet implemented in caches
        assert ctx.settlement is None
        assert ctx.world_lore is None
        assert ctx.region_lore is None

    def test_to_prompt_context_works(self, basic_character, basic_world, mock_ai_service):
        """Test to_prompt_context produces valid output from get_generation_context."""
        # Spec: GenerationContext.to_prompt_context produces prompt-ready dict
        game_state = GameState(
            character=basic_character,
            world=basic_world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        ctx = game_state.get_generation_context()
        prompt_ctx = ctx.to_prompt_context()

        # Should have world fields
        assert "theme" in prompt_ctx
        assert "theme_essence" in prompt_ctx
        # Should have region fields
        assert "region_name" in prompt_ctx
        assert "danger_level" in prompt_ctx
