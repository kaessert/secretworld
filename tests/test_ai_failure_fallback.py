"""Tests for AI failure graceful fallback.

Spec: When AI location generation fails, fall back gracefully without exposing
technical errors to the player.
"""

import logging
import pytest
from unittest.mock import Mock, patch
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.ai_service import AIServiceError, AIGenerationError


@pytest.fixture
def character():
    return Character(name="Hero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def world_with_coords():
    """World with coordinate-based location."""
    loc = Location(
        name="Town",
        description="A town.",
        coordinates=(0, 0)
    )
    return {"Town": loc}


class TestAIFailureFallback:
    """Test that AI failures fall back gracefully.

    Spec requirement: On ANY AI failure during move(), fall back to
    generate_fallback_location() without showing technical errors.
    """

    def test_ai_json_parse_error_uses_fallback(self, character, world_with_coords):
        """AI JSON parse errors should silently use fallback location.

        Spec: Silent fallback on ANY AI failure.
        """
        mock_ai = Mock()
        mock_ai.generate_area.side_effect = Exception(
            "Failed to parse response as JSON: Expecting value: line 52"
        )

        gs = GameState(
            character=character,
            world=world_with_coords,
            starting_location="Town",
            ai_service=mock_ai
        )

        success, message = gs.move("north")

        # Should succeed with fallback location
        assert success is True
        assert "Failed to parse" not in message
        assert gs.current_location != "Town"

    def test_ai_service_error_uses_fallback(self, character, world_with_coords):
        """AIServiceError should silently use fallback location.

        Spec: Silent fallback on ANY AI failure.
        """
        mock_ai = Mock()
        mock_ai.generate_area.side_effect = AIServiceError("API timeout")

        gs = GameState(
            character=character,
            world=world_with_coords,
            starting_location="Town",
            ai_service=mock_ai
        )

        success, message = gs.move("north")

        assert success is True
        assert "API timeout" not in message

    def test_ai_generation_error_uses_fallback(self, character, world_with_coords):
        """AIGenerationError should silently use fallback location.

        Spec: Silent fallback on ANY AI failure.
        """
        mock_ai = Mock()
        mock_ai.generate_area.side_effect = AIGenerationError("Invalid JSON")

        gs = GameState(
            character=character,
            world=world_with_coords,
            starting_location="Town",
            ai_service=mock_ai
        )

        success, message = gs.move("east")

        assert success is True
        assert "Invalid JSON" not in message

    def test_fallback_failure_shows_friendly_message(self, character, world_with_coords):
        """If fallback also fails, show friendly barrier message.

        Spec: Last resort message "The path is blocked by an impassable barrier."
        """
        mock_ai = Mock()
        mock_ai.generate_area.side_effect = Exception("AI failed")

        gs = GameState(
            character=character,
            world=world_with_coords,
            starting_location="Town",
            ai_service=mock_ai
        )

        with patch('cli_rpg.game_state.generate_fallback_location') as mock_fallback:
            mock_fallback.side_effect = Exception("Fallback also failed")

            success, message = gs.move("west")

            assert success is False
            assert "impassable barrier" in message.lower()

    def test_error_logged_but_not_shown(self, character, world_with_coords, caplog):
        """Errors should be logged for debugging but not shown to player.

        Spec: Log errors for debugging, show seamless location to player.
        """
        mock_ai = Mock()
        mock_ai.generate_area.side_effect = Exception("Detailed internal error XYZ123")

        gs = GameState(
            character=character,
            world=world_with_coords,
            starting_location="Town",
            ai_service=mock_ai
        )

        with caplog.at_level(logging.WARNING):
            success, message = gs.move("south")

        # Error should be in logs
        assert "XYZ123" in caplog.text or "Detailed internal error" in caplog.text
        # But not in player message
        assert "XYZ123" not in message
        assert "Detailed internal error" not in message
