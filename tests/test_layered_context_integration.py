"""Tests for layered context integration in location generation.

Spec: Verify that game_state.move() passes WorldContext and RegionContext
to expand_area() when generating new locations via AI.
"""

import pytest
from unittest.mock import MagicMock, patch
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext


class TestLayeredContextInMove:
    """Tests that move() passes context to expand_area()."""

    @pytest.fixture
    def mock_chunk_manager(self):
        """Create mock ChunkManager that reports all terrain as passable."""
        cm = MagicMock()
        cm.get_tile_at.return_value = "plains"
        return cm

    @pytest.fixture
    def game_state_with_ai(self, mock_chunk_manager):
        """Create GameState with mock AI service."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        start = Location(name="Start", description="Test", coordinates=(0, 0))
        world = {"Start": start}
        ai_service = MagicMock()
        gs = GameState(char, world, "Start", ai_service=ai_service, theme="fantasy")
        gs.chunk_manager = mock_chunk_manager
        # Set tiles_since_named high enough to trigger named location generation
        gs.tiles_since_named = 10
        # Pre-set context to avoid AI service calls during context creation
        gs.world_context = WorldContext.default("fantasy")
        return gs

    @patch("cli_rpg.game_state.should_generate_named_location", return_value=True)
    @patch("cli_rpg.game_state.autosave")
    @patch("cli_rpg.game_state.expand_area")
    def test_move_passes_world_context_to_expand_area(
        self, mock_expand_area, mock_autosave, mock_should_gen, game_state_with_ai
    ):
        """Verify move() passes world_context when generating new location.

        Spec: When move() triggers AI location generation via expand_area(),
        it must pass the world_context parameter for layered context generation.
        """
        gs = game_state_with_ai
        # Pre-create world context
        gs.world_context = WorldContext.default("fantasy")

        # Mock expand_area to create a location (otherwise move fails)
        new_loc = Location(name="New", description="Test", coordinates=(0, 1))

        def side_effect(*args, **kwargs):
            gs.world["New"] = new_loc

        mock_expand_area.side_effect = side_effect

        gs.move("north")

        # Verify expand_area was called with world_context
        mock_expand_area.assert_called_once()
        _, kwargs = mock_expand_area.call_args
        assert "world_context" in kwargs
        assert kwargs["world_context"] is not None

    @patch("cli_rpg.game_state.should_generate_named_location", return_value=True)
    @patch("cli_rpg.game_state.autosave")
    @patch("cli_rpg.game_state.expand_area")
    def test_move_passes_region_context_to_expand_area(
        self, mock_expand_area, mock_autosave, mock_should_gen, game_state_with_ai
    ):
        """Verify move() passes region_context when generating new location.

        Spec: When move() triggers AI location generation via expand_area(),
        it must pass the region_context parameter for layered context generation.
        """
        gs = game_state_with_ai

        new_loc = Location(name="New", description="Test", coordinates=(0, 1))

        def side_effect(*args, **kwargs):
            gs.world["New"] = new_loc

        mock_expand_area.side_effect = side_effect

        gs.move("north")

        mock_expand_area.assert_called_once()
        _, kwargs = mock_expand_area.call_args
        assert "region_context" in kwargs
        assert kwargs["region_context"] is not None

    @patch("cli_rpg.game_state.should_generate_named_location", return_value=True)
    @patch("cli_rpg.game_state.autosave")
    @patch("cli_rpg.game_state.expand_area")
    def test_move_creates_world_context_if_missing(
        self, mock_expand_area, mock_autosave, mock_should_gen, game_state_with_ai
    ):
        """Verify move() creates world_context lazily if not present.

        Spec: If world_context is None, move() should create a default
        world context before calling expand_area().
        """
        gs = game_state_with_ai
        # Ensure no pre-existing world context
        gs.world_context = None
        # Mock the AI service to return a proper WorldContext
        gs.ai_service.generate_world_context.return_value = WorldContext.default("fantasy")

        new_loc = Location(name="New", description="Test", coordinates=(0, 1))

        def side_effect(*args, **kwargs):
            gs.world["New"] = new_loc

        mock_expand_area.side_effect = side_effect

        gs.move("north")

        mock_expand_area.assert_called_once()
        _, kwargs = mock_expand_area.call_args
        # Should have created world context
        assert kwargs["world_context"] is not None
        assert isinstance(kwargs["world_context"], WorldContext)

    @patch("cli_rpg.game_state.should_generate_named_location", return_value=True)
    @patch("cli_rpg.game_state.autosave")
    @patch("cli_rpg.game_state.expand_area")
    def test_move_creates_region_context_for_target_coords(
        self, mock_expand_area, mock_autosave, mock_should_gen, game_state_with_ai
    ):
        """Verify move() creates region_context for target coordinates.

        Spec: The region_context passed to expand_area() should be
        appropriate for the target coordinates being generated.
        """
        gs = game_state_with_ai
        # Mock the AI service to return a proper RegionContext
        gs.ai_service.generate_region_context.return_value = RegionContext.default(
            "Test Region", (0, 1)
        )

        new_loc = Location(name="New", description="Test", coordinates=(0, 1))

        def side_effect(*args, **kwargs):
            gs.world["New"] = new_loc

        mock_expand_area.side_effect = side_effect

        gs.move("north")

        mock_expand_area.assert_called_once()
        _, kwargs = mock_expand_area.call_args
        region_ctx = kwargs["region_context"]
        assert region_ctx is not None
        assert isinstance(region_ctx, RegionContext)
