"""Integration tests for the named location trigger system.

Tests that:
- tiles_since_named counter increments on move to unnamed location
- tiles_since_named resets to 0 when generating named location
- tiles_since_named persists through save/load
- Unnamed locations use templates (no AI call)
- Named locations trigger AI or fallback with is_named=True
"""

import pytest
import random
from unittest.mock import MagicMock, patch

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


def make_character(name="Test Hero"):
    """Helper to create a test character with required stats."""
    return Character(name=name, strength=10, dexterity=10, intelligence=10)


class TestTilesSinceNamedCounter:
    """Tests for the tiles_since_named counter tracking."""

    def test_tiles_since_named_defaults_to_zero(self):
        """GameState.tiles_since_named defaults to 0."""
        # Spec: Track tiles_since_named: int in GameState
        character = make_character()
        location = Location(
            name="Start", description="A starting location.", coordinates=(0, 0)
        )
        gs = GameState(
            character=character,
            world={"Start": location},
            starting_location="Start",
            theme="test",
        )
        assert gs.tiles_since_named == 0

    def test_tiles_since_named_increments_on_unnamed_move(self):
        """tiles_since_named increments when moving to an unnamed location."""
        # Spec: tiles_since_named increments on move to unnamed location
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=True
        )
        gs = GameState(
            character=character,
            world={"Start": start},
            starting_location="Start",
            theme="test",
        )

        # Mock chunk_manager to allow movement
        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "plains"
        gs.chunk_manager = mock_cm

        # Mock noise manager to return False (unnamed location)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = False
        mock_noise_manager.world_seed = 42
        gs.location_noise_manager = mock_noise_manager

        with patch("cli_rpg.game_state.autosave"):
            # Move north - should create unnamed location and increment counter
            success, _ = gs.move("north")
            assert success is True
            assert gs.tiles_since_named == 1

            # Move again (need to ensure terrain is passable)
            mock_cm.get_tile_at.return_value = "forest"
            success, _ = gs.move("north")
            assert success is True
            assert gs.tiles_since_named == 2

    def test_tiles_since_named_resets_on_named_location(self):
        """tiles_since_named resets to 0 when generating a named location."""
        # Spec: tiles_since_named resets to 0 when generating named location
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=True
        )
        gs = GameState(
            character=character,
            world={"Start": start},
            starting_location="Start",
            theme="test",
        )

        # Set counter to non-zero
        gs.tiles_since_named = 10

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "plains"
        gs.chunk_manager = mock_cm

        # Mock noise manager to return True (named location)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = True
        mock_noise_manager.world_seed = 42
        gs.location_noise_manager = mock_noise_manager

        with patch("cli_rpg.game_state.autosave"):
            success, _ = gs.move("north")
            assert success is True
            # Counter should reset to 0 after named location
            assert gs.tiles_since_named == 0

    def test_tiles_since_named_persists_save_load(self):
        """tiles_since_named survives to_dict/from_dict round-trip."""
        # Spec: Persist tiles_since_named in save files
        character = make_character()
        location = Location(
            name="Start", description="Starting.", coordinates=(0, 0)
        )
        gs = GameState(
            character=character,
            world={"Start": location},
            starting_location="Start",
            theme="test",
        )
        gs.tiles_since_named = 15

        # Serialize and deserialize
        data = gs.to_dict()
        assert "tiles_since_named" in data
        assert data["tiles_since_named"] == 15

        restored = GameState.from_dict(data)
        assert restored.tiles_since_named == 15

    def test_tiles_since_named_backward_compat(self):
        """Old saves without tiles_since_named default to 0."""
        # Build minimal valid data without tiles_since_named
        character = make_character()
        location = Location(name="Test", description="Test.", coordinates=(0, 0))
        gs = GameState(
            character=character,
            world={"Test": location},
            starting_location="Test",
            theme="test",
        )
        data = gs.to_dict()

        # Remove tiles_since_named to simulate old save
        if "tiles_since_named" in data:
            del data["tiles_since_named"]

        restored = GameState.from_dict(data)
        assert restored.tiles_since_named == 0


class TestTemplateUsageForUnnamed:
    """Tests that unnamed locations use templates without AI."""

    def test_unnamed_location_uses_template(self):
        """When noise manager returns False, template is used for unnamed location."""
        # Spec: If FALSE → use get_unnamed_location_template(terrain) for instant generation
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=True
        )
        gs = GameState(
            character=character,
            world={"Start": start},
            starting_location="Start",
            theme="test",
        )

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "forest"
        gs.chunk_manager = mock_cm

        # Track if AI was called
        ai_called = False

        def mock_expand_area(*args, **kwargs):
            nonlocal ai_called
            ai_called = True
            raise Exception("AI should not be called for unnamed locations")

        # Mock noise manager to return False (unnamed location)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = False
        mock_noise_manager.world_seed = 42
        gs.location_noise_manager = mock_noise_manager

        with patch("cli_rpg.game_state.expand_area", mock_expand_area):
            with patch("cli_rpg.game_state.autosave"):
                success, _ = gs.move("north")
                assert success is True
                assert not ai_called

                # New location should be unnamed
                new_loc = gs.get_current_location()
                assert new_loc.is_named is False

    def test_unnamed_location_has_correct_terrain(self):
        """Unnamed locations have correct terrain type."""
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0)
        )
        gs = GameState(
            character=character,
            world={"Start": start},
            starting_location="Start",
            theme="test",
        )

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "mountain"
        gs.chunk_manager = mock_cm

        # Mock noise manager to return False (unnamed location)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = False
        mock_noise_manager.world_seed = 42
        gs.location_noise_manager = mock_noise_manager

        with patch("cli_rpg.game_state.autosave"):
            success, _ = gs.move("north")
            assert success is True

            new_loc = gs.get_current_location()
            assert new_loc.terrain == "mountain"


class TestAIUsageForNamed:
    """Tests that named locations trigger AI generation."""

    def test_named_location_triggers_ai_or_fallback(self):
        """When noise manager returns True, AI or fallback generates named location."""
        # Spec: If TRUE → generate named location via AI (current behavior)
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=True
        )
        gs = GameState(
            character=character,
            world={"Start": start},
            starting_location="Start",
            theme="test",
        )

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "plains"
        gs.chunk_manager = mock_cm

        # Mock noise manager to return True (named location)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = True
        mock_noise_manager.world_seed = 42
        gs.location_noise_manager = mock_noise_manager

        # When noise manager returns True, the existing AI/fallback path runs
        # AI is not available in tests, so fallback is used
        # But for named locations, the fallback should now set is_named=True
        with patch("cli_rpg.game_state.autosave"):
            success, _ = gs.move("north")
            assert success is True

            # Counter should reset
            assert gs.tiles_since_named == 0

            new_loc = gs.get_current_location()
            # Named location should have is_named=True
            assert new_loc.is_named is True

    def test_named_location_counter_resets_after_ai_fallback(self):
        """Counter resets whether AI succeeds or fallback is used."""
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=True
        )
        gs = GameState(
            character=character,
            world={"Start": start},
            starting_location="Start",
            theme="test",
        )
        gs.tiles_since_named = 20

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "forest"
        gs.chunk_manager = mock_cm

        # Mock noise manager to return True (named location)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = True
        mock_noise_manager.world_seed = 42
        gs.location_noise_manager = mock_noise_manager

        with patch("cli_rpg.game_state.autosave"):
            success, _ = gs.move("north")
            assert success is True
            # Counter reset regardless of AI or fallback
            assert gs.tiles_since_named == 0


class TestMoveToExistingLocation:
    """Tests that moving to existing locations doesn't change counter."""

    def test_move_to_existing_location_increments_counter(self):
        """Moving to an existing unnamed location increments the counter."""
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=True
        )
        north = Location(
            name="North Loc", description="Northern.", coordinates=(0, 1), is_named=False
        )
        gs = GameState(
            character=character,
            world={"Start": start, "North Loc": north},
            starting_location="Start",
            theme="test",
        )

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "plains"
        gs.chunk_manager = mock_cm

        # Move to existing unnamed location
        with patch("cli_rpg.game_state.autosave"):
            success, _ = gs.move("north")
            assert success is True
            # Counter should increment for existing unnamed
            assert gs.tiles_since_named == 1

    def test_move_to_existing_named_location_resets_counter(self):
        """Moving to an existing named location resets the counter."""
        character = make_character()
        start = Location(
            name="Start", description="Starting.", coordinates=(0, 0), is_named=False
        )
        named_north = Location(
            name="Town", description="A town.", coordinates=(0, 1), is_named=True
        )
        gs = GameState(
            character=character,
            world={"Start": start, "Town": named_north},
            starting_location="Start",
            theme="test",
        )
        gs.tiles_since_named = 5

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "plains"
        gs.chunk_manager = mock_cm

        # Move to existing named location
        with patch("cli_rpg.game_state.autosave"):
            success, _ = gs.move("north")
            assert success is True
            # Counter should reset for existing named
            assert gs.tiles_since_named == 0
