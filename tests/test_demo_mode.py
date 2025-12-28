"""Integration tests for demo mode.

These tests verify that:
1. Demo flag skips character creation (test_demo_flag_skips_character_creation)
2. Gameplay loop works without AI (test_demo_mode_gameplay_loop)
3. AI service is not invoked in demo mode (test_demo_mode_no_ai_calls)
"""

import pytest
from unittest.mock import patch, MagicMock
import io
import sys

from cli_rpg.main import parse_args, run_demo_mode
from cli_rpg.test_world import create_demo_game_state


class TestDemoFlagParsing:
    """Tests for --demo CLI flag parsing."""

    def test_demo_flag_parsed_correctly(self):
        """--demo flag is correctly parsed."""
        args = parse_args(["--demo"])

        assert args.demo is True

    def test_demo_flag_defaults_to_false(self):
        """Demo flag defaults to False when not provided."""
        args = parse_args([])

        assert args.demo is False


class TestDemoModeCharacterCreation:
    """Tests for demo mode character creation - Spec: No prompts in demo mode."""

    def test_demo_flag_skips_character_creation(self):
        """Demo mode uses pre-generated character without prompts."""
        game_state = create_demo_game_state()

        # Character should be pre-created
        assert game_state.current_character is not None
        assert game_state.current_character.name == "Demo Hero"
        # Character should have stats already set
        assert game_state.current_character.level == 3


class TestDemoModeGameplay:
    """Tests for gameplay in demo mode - Spec: Can execute commands without AI."""

    def test_demo_mode_gameplay_loop(self, pregenerated_game_state):
        """Can execute basic commands without AI service."""
        game_state = pregenerated_game_state

        # Test look command
        look_result = game_state.look()
        assert len(look_result) > 0

        # Test movement
        success, message = game_state.move("north")
        assert success is True

        # Test status (through character)
        assert game_state.current_character.health > 0
        assert game_state.current_character.max_health > 0

    def test_demo_mode_shop_works(self, pregenerated_game_state):
        """Shop interactions work in demo mode."""
        game_state = pregenerated_game_state
        village = game_state.world["Peaceful Village"]

        # Find merchant NPC
        merchant = None
        for npc in village.npcs:
            if npc.is_merchant:
                merchant = npc
                break

        assert merchant is not None
        assert merchant.shop is not None
        assert len(merchant.shop.inventory) > 0

    def test_demo_mode_combat_can_trigger(self, pregenerated_game_state):
        """Combat system works in demo mode."""
        game_state = pregenerated_game_state

        # Move to non-safe zone (forest)
        game_state.move("north")
        assert game_state.current_location == "Whispering Forest"

        # Forest is not a safe zone
        forest = game_state.world["Whispering Forest"]
        assert forest.is_safe_zone is False


class TestDemoModeNoAI:
    """Tests for AI behavior in demo mode - Spec: AI service not invoked."""

    def test_demo_mode_no_ai_calls(self, pregenerated_game_state):
        """AI service is not invoked in demo mode."""
        game_state = pregenerated_game_state

        # AI service should be None (not initialized)
        assert game_state.ai_service is None

    def test_demo_mode_world_generation_without_ai(self, pregenerated_game_state):
        """World exists without AI generation."""
        game_state = pregenerated_game_state

        # World should be pre-populated
        assert len(game_state.world) >= 5

        # All locations should have descriptions
        for name, location in game_state.world.items():
            assert len(location.description) > 0

    def test_demo_mode_no_ai_service_attached(self, pregenerated_game_state):
        """Game state has no AI service attached."""
        game_state = pregenerated_game_state

        # Verify AI service is None
        assert game_state.ai_service is None

        # Whisper service should have None AI
        assert game_state.whisper_service.ai_service is None


class TestDemoModeRunFunction:
    """Tests for run_demo_mode() function."""

    @patch('cli_rpg.main.init_readline')
    @patch('cli_rpg.main.run_game_loop')
    def test_run_demo_mode_initializes_correctly(self, mock_game_loop, mock_readline, capsys):
        """run_demo_mode initializes and starts game loop."""
        # Make run_game_loop a no-op
        mock_game_loop.return_value = None

        result = run_demo_mode()

        assert result == 0
        mock_readline.assert_called_once()
        mock_game_loop.assert_called_once()

        # Check output
        captured = capsys.readouterr()
        assert "Demo Mode" in captured.out
        assert "Demo Hero" in captured.out

    @patch('cli_rpg.main.init_readline')
    @patch('cli_rpg.main.run_game_loop')
    def test_run_demo_mode_shows_welcome_message(self, mock_game_loop, mock_readline, capsys):
        """run_demo_mode shows welcome message with character info."""
        mock_game_loop.return_value = None

        run_demo_mode()

        captured = capsys.readouterr()
        assert "Welcome" in captured.out
        assert "Level 3" in captured.out
        assert "Warrior" in captured.out


class TestDemoModePregenFixture:
    """Tests using the pregenerated_game_state fixture from conftest."""

    def test_fixture_provides_fresh_state(self, pregenerated_game_state):
        """Each test gets a fresh game state."""
        game_state = pregenerated_game_state

        # Modify state
        game_state.current_character.gold = 0
        assert game_state.current_character.gold == 0

    def test_fixture_isolated_between_tests(self, pregenerated_game_state):
        """Fixture is isolated - gold should be original value."""
        game_state = pregenerated_game_state

        # Gold should be at original value (100), not 0 from previous test
        assert game_state.current_character.gold == 100

    def test_fixture_has_factions(self, pregenerated_game_state):
        """Fixture includes factions."""
        game_state = pregenerated_game_state

        assert len(game_state.factions) >= 3

    def test_fixture_has_game_time(self, pregenerated_game_state):
        """Fixture includes game time."""
        game_state = pregenerated_game_state

        assert game_state.game_time is not None
        assert game_state.game_time.hour == 8  # Morning start


class TestDemoModeWithNonInteractiveFlags:
    """Tests for demo mode combined with --non-interactive and --json flags.

    Spec: --demo should skip character creation even with --json or --non-interactive.
    """

    def test_json_mode_with_demo_uses_demo_game_state(self):
        """--demo --json should use demo game state, not stdin character creation."""
        from cli_rpg.main import run_json_mode
        from io import StringIO

        # Provide only "quit" - if character creation runs, it will fail
        with patch('sys.stdin', StringIO("quit\n")):
            result = run_json_mode(demo=True)

        # Should succeed (exit with 0) because demo mode skips character creation
        assert result == 0

    def test_non_interactive_mode_with_demo_uses_demo_game_state(self):
        """--demo --non-interactive should use demo game state, not stdin."""
        from cli_rpg.main import run_non_interactive
        from io import StringIO

        # Provide only "quit" - if character creation runs, it will fail
        with patch('sys.stdin', StringIO("quit\n")):
            result = run_non_interactive(demo=True)

        # Should succeed (exit with 0) because demo mode skips character creation
        assert result == 0

    def test_json_mode_demo_flag_in_main(self):
        """main() with --demo --json passes demo=True to run_json_mode."""
        from cli_rpg.main import parse_args

        args = parse_args(["--demo", "--json"])

        assert args.demo is True
        assert args.json is True

    def test_non_interactive_demo_flag_in_main(self):
        """main() with --demo --non-interactive passes demo=True."""
        from cli_rpg.main import parse_args

        args = parse_args(["--demo", "--non-interactive"])

        assert args.demo is True
        assert args.non_interactive is True

    @patch('cli_rpg.main.run_json_mode')
    def test_main_passes_demo_to_json_mode(self, mock_run_json):
        """main() should pass demo flag to run_json_mode when both --demo and --json."""
        from cli_rpg.main import main

        mock_run_json.return_value = 0

        result = main(["--demo", "--json"])

        assert result == 0
        mock_run_json.assert_called_once()
        # Verify demo=True was passed
        call_kwargs = mock_run_json.call_args[1]
        assert call_kwargs.get("demo") is True

    @patch('cli_rpg.main.run_non_interactive')
    def test_main_passes_demo_to_non_interactive(self, mock_run_non_interactive):
        """main() should pass demo flag to run_non_interactive when both --demo and --non-interactive."""
        from cli_rpg.main import main

        mock_run_non_interactive.return_value = 0

        result = main(["--demo", "--non-interactive"])

        assert result == 0
        mock_run_non_interactive.assert_called_once()
        # Verify demo=True was passed
        call_kwargs = mock_run_non_interactive.call_args[1]
        assert call_kwargs.get("demo") is True
