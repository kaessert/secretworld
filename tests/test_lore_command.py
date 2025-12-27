"""Tests for the lore command functionality."""
import pytest
from unittest.mock import Mock, patch

from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.main import handle_exploration_command, get_command_reference


class TestLoreCommandParsing:
    """Tests that the lore command is recognized by parse_command."""

    # Test: parse_command recognizes "lore" as valid
    def test_lore_command_is_recognized(self):
        """Lore command should be recognized and parsed correctly."""
        command, args = parse_command("lore")
        assert command == "lore"
        assert args == []


class TestLoreCommandExecution:
    """Tests for lore command execution in handle_exploration_command."""

    @pytest.fixture
    def basic_game_state(self):
        """Create a basic game state for testing."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            gold=50,
        )
        location = Location(
            name="Mystic Forest",
            description="A dark and mysterious forest.",
            coordinates=(0, 0),
        )
        world = {"Mystic Forest": location}
        game_state = GameState(
            character=character,
            world=world,
            starting_location="Mystic Forest",
            theme="fantasy",
        )
        return game_state

    # Test: Returns fallback message when no AI service is available
    def test_lore_command_without_ai_shows_fallback(self, basic_game_state):
        """Lore command should show fallback when AI service is unavailable."""
        basic_game_state.ai_service = None

        continue_game, output = handle_exploration_command(basic_game_state, "lore", [])

        assert continue_game is True
        assert "=== Ancient Lore ===" in output
        assert "No mystical knowledge is available" in output

    # Test: Calls AIService.generate_lore with correct arguments
    def test_lore_command_with_ai_calls_generate_lore(self, basic_game_state):
        """Lore command should call generate_lore with theme, location, and category."""
        mock_ai = Mock()
        mock_ai.generate_lore.return_value = "Long ago, the Mystic Forest was home to ancient elves."
        basic_game_state.ai_service = mock_ai

        with patch("random.choice", return_value="history"):
            continue_game, output = handle_exploration_command(basic_game_state, "lore", [])

        mock_ai.generate_lore.assert_called_once_with(
            theme="fantasy",
            location_name="Mystic Forest",
            lore_category="history"
        )
        assert continue_game is True

    # Test: Output includes header and lore text
    def test_lore_command_displays_lore_with_header(self, basic_game_state):
        """Lore command output should include a thematic header and the lore text."""
        mock_ai = Mock()
        mock_ai.generate_lore.return_value = "The ancient wizards built this tower centuries ago."
        basic_game_state.ai_service = mock_ai

        with patch("random.choice", return_value="legend"):
            continue_game, output = handle_exploration_command(basic_game_state, "lore", [])

        assert "=== Local Legend ===" in output
        assert "The ancient wizards built this tower centuries ago." in output

    # Test: Handles AI errors gracefully with fallback
    def test_lore_command_handles_ai_error_gracefully(self, basic_game_state):
        """Lore command should catch AI exceptions and show fallback message."""
        mock_ai = Mock()
        mock_ai.generate_lore.side_effect = Exception("API error")
        basic_game_state.ai_service = mock_ai

        continue_game, output = handle_exploration_command(basic_game_state, "lore", [])

        assert continue_game is True
        assert "=== Ancient Lore ===" in output
        assert "mysteries of this place remain hidden" in output


class TestLoreInHelp:
    """Tests that lore command appears in help text."""

    # Test: lore command is listed in help text
    def test_lore_command_in_help_text(self):
        """The lore command should appear in the command reference."""
        help_text = get_command_reference()
        assert "lore" in help_text
        assert "lore" in help_text.lower()
