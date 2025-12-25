"""Tests for non-interactive mode.

Spec: Add --non-interactive flag that reads commands from stdin when not
connected to a terminal, exiting gracefully when stdin is exhausted.
"""
import pytest
import subprocess
import sys


class TestNonInteractiveMode:
    """Test non-interactive mode functionality."""

    def test_non_interactive_flag_accepted(self):
        """--non-interactive flag is accepted without error.

        Spec: Add --non-interactive CLI flag via argparse.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="",
            capture_output=True,
            text=True,
            timeout=5
        )
        # Should exit cleanly (0) when stdin is empty
        assert result.returncode == 0

    def test_non_interactive_reads_stdin(self):
        """Non-interactive mode reads commands from stdin.

        Spec: When flag is set, game reads commands from stdin line-by-line.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Should show location description from "look" command
        assert "Town Square" in result.stdout or "location" in result.stdout.lower()

    def test_non_interactive_exits_on_eof(self):
        """Non-interactive mode exits gracefully when stdin is exhausted.

        Spec: When stdin is exhausted (EOF), game exits gracefully with exit code 0.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\nstatus\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0

    def test_non_interactive_no_ansi_codes(self):
        """Non-interactive mode disables ANSI color codes.

        Spec: Disable ANSI colors when in non-interactive mode.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        # ANSI escape codes start with \x1b[
        assert "\x1b[" not in result.stdout

    def test_non_interactive_multiple_commands(self):
        """Non-interactive mode processes multiple commands.

        Spec: Works with piped input containing multiple commands.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="look\nstatus\ninventory\nhelp\n",
            capture_output=True,
            text=True,
            timeout=15
        )
        assert result.returncode == 0
        # Should have processed help command
        assert "help" in result.stdout.lower() or "command" in result.stdout.lower()

    def test_quit_command_exits_cleanly_non_interactive(self):
        """Quit command should exit without EOFError in non-interactive mode.

        Spec: When quit command is issued in non-interactive mode, skip save prompt
        and exit directly without calling input() (which would cause EOFError).
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="quit\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "EOFError" not in result.stderr
        assert "Traceback" not in result.stderr

    def test_quit_command_exits_cleanly_json_mode(self):
        """Quit command should exit without EOFError in JSON mode.

        Spec: When quit command is issued in JSON mode, skip save prompt
        and exit directly without calling input() (which would cause EOFError).
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="quit\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "EOFError" not in result.stderr
        assert "Traceback" not in result.stderr
