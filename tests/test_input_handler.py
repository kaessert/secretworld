"""Tests for input_handler module - command history with readline integration."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestGetHistoryPath:
    """Tests for get_history_path function - Spec requirement 3: history file path."""

    def test_get_history_path_returns_home_directory(self):
        """Verify history path is ~/.cli_rpg_history."""
        from cli_rpg.input_handler import get_history_path

        expected = Path.home() / ".cli_rpg_history"
        assert get_history_path() == expected


class TestHistorySize:
    """Tests for history size configuration - Spec requirement 4: configurable size."""

    def test_history_size_constant_exists(self):
        """Verify HISTORY_SIZE constant is defined."""
        from cli_rpg.input_handler import HISTORY_SIZE

        assert isinstance(HISTORY_SIZE, int)
        assert HISTORY_SIZE == 500  # Default from spec


class TestInitReadline:
    """Tests for init_readline function - Spec requirements 1, 2, 3: readline setup."""

    def test_init_readline_loads_history_when_file_exists(self):
        """Verify readline reads history from existing file."""
        mock_readline = MagicMock()

        with patch.dict("sys.modules", {"readline": mock_readline}):
            with patch("cli_rpg.input_handler._readline_available", False):
                with patch("cli_rpg.input_handler.get_history_path") as mock_path:
                    mock_path_obj = MagicMock()
                    mock_path_obj.exists.return_value = True
                    mock_path.return_value = mock_path_obj

                    # Reset module state and reimport
                    import cli_rpg.input_handler as ih
                    ih._readline_available = False
                    ih.init_readline()

                    mock_readline.read_history_file.assert_called_once()
                    mock_readline.set_history_length.assert_called_once_with(500)

    def test_init_readline_skips_load_when_file_missing(self):
        """Verify readline doesn't try to read non-existent history file."""
        mock_readline = MagicMock()

        with patch.dict("sys.modules", {"readline": mock_readline}):
            with patch("cli_rpg.input_handler.get_history_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = False
                mock_path.return_value = mock_path_obj

                import cli_rpg.input_handler as ih
                ih._readline_available = False
                ih.init_readline()

                mock_readline.read_history_file.assert_not_called()
                mock_readline.set_history_length.assert_called_once_with(500)

    def test_init_readline_registers_atexit_handler(self):
        """Verify cleanup_readline is registered with atexit."""
        mock_readline = MagicMock()

        with patch.dict("sys.modules", {"readline": mock_readline}):
            with patch("cli_rpg.input_handler.get_history_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = False
                mock_path.return_value = mock_path_obj

                with patch("atexit.register") as mock_atexit:
                    import cli_rpg.input_handler as ih
                    ih._readline_available = False
                    ih.init_readline()

                    # Verify atexit.register was called with cleanup_readline
                    mock_atexit.assert_called_once()
                    assert mock_atexit.call_args[0][0] == ih.cleanup_readline

    def test_init_readline_handles_permission_error(self):
        """Verify PermissionError is caught gracefully in sandboxed environments."""
        mock_readline = MagicMock()
        mock_readline.read_history_file.side_effect = PermissionError("Access denied")

        with patch.dict("sys.modules", {"readline": mock_readline}):
            with patch("cli_rpg.input_handler.get_history_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path_obj.exists.return_value = True
                mock_path.return_value = mock_path_obj

                import cli_rpg.input_handler as ih
                ih._readline_available = False
                ih.init_readline()  # Should not raise

                # Verify readline was still configured despite permission error
                mock_readline.set_history_length.assert_called_once_with(500)


class TestFallbackBehavior:
    """Tests for fallback when readline unavailable - Spec requirement 5."""

    def test_get_input_works_without_readline(self):
        """Verify get_input works even if readline isn't available.

        The get_input function just wraps builtin input(), so it should
        work regardless of readline availability.
        """
        from cli_rpg.input_handler import get_input

        with patch("builtins.input", return_value="test command"):
            result = get_input("> ")
            assert result == "test command"

    def test_readline_available_flag_is_boolean(self):
        """Verify _readline_available is a boolean flag."""
        import cli_rpg.input_handler as ih

        assert isinstance(ih._readline_available, bool)


class TestCleanupReadline:
    """Tests for cleanup_readline function - Spec requirement 3: save history."""

    def test_cleanup_saves_history_when_readline_available(self):
        """Verify history is saved to file on cleanup."""
        mock_readline = MagicMock()

        with patch.dict("sys.modules", {"readline": mock_readline}):
            import cli_rpg.input_handler as ih
            ih._readline_available = True

            with patch.object(ih, "get_history_path") as mock_path:
                mock_path_obj = MagicMock()
                mock_path.return_value = mock_path_obj

                ih.cleanup_readline()

                mock_readline.write_history_file.assert_called_once()

    def test_cleanup_noop_when_readline_unavailable(self):
        """Verify cleanup does nothing when readline not available."""
        import cli_rpg.input_handler as ih
        ih._readline_available = False

        # Should not raise or do anything
        ih.cleanup_readline()  # Just verify no exception

    def test_cleanup_handles_permission_error(self):
        """Verify PermissionError is caught gracefully when writing history."""
        mock_readline = MagicMock()
        mock_readline.write_history_file.side_effect = PermissionError("Access denied")

        with patch.dict("sys.modules", {"readline": mock_readline}):
            import cli_rpg.input_handler as ih
            ih._readline_available = True

            # Should not raise
            ih.cleanup_readline()


class TestGetInput:
    """Tests for get_input function - the main input interface."""

    def test_get_input_returns_stripped_input(self):
        """Verify input is stripped of whitespace."""
        from cli_rpg.input_handler import get_input

        with patch("builtins.input", return_value="  look around  "):
            result = get_input("> ")
            assert result == "look around"

    def test_get_input_passes_prompt_to_builtin(self):
        """Verify prompt is passed to builtin input."""
        from cli_rpg.input_handler import get_input

        with patch("builtins.input", return_value="test") as mock_input:
            get_input("> ")
            mock_input.assert_called_once_with("> ")

    def test_get_input_handles_empty_prompt(self):
        """Verify empty prompt works correctly."""
        from cli_rpg.input_handler import get_input

        with patch("builtins.input", return_value="cmd") as mock_input:
            result = get_input("")
            mock_input.assert_called_once_with("")
            assert result == "cmd"


class TestMainIntegration:
    """Integration tests for input_handler in main.py."""

    def test_main_imports_input_handler(self):
        """Verify main.py imports init_readline and get_input.

        Spec requirement: main.py should integrate input_handler.
        """
        from cli_rpg import main

        assert hasattr(main, "init_readline")
        assert hasattr(main, "get_input")

    def test_run_game_loop_uses_get_input(self):
        """Verify run_game_loop uses get_input for command input."""
        import inspect
        from cli_rpg.main import run_game_loop

        source = inspect.getsource(run_game_loop)
        assert "get_input" in source
