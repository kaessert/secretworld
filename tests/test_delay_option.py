"""Tests for --delay CLI option.

Spec: Add --delay <ms> CLI option to control pacing between commands in
automated (non-interactive/JSON) runs. This is the final item under
"Additional automation features" in ISSUES.md.
"""

import subprocess
import sys
import time

import pytest


class TestDelayOption:
    """Tests for the --delay CLI flag."""

    # Spec: --delay flag is accepted without error
    def test_delay_flag_accepted(self):
        """--delay 100 is accepted without error when used with --non-interactive."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--delay", "100"],
            input="status\n",  # EOF after status, don't use quit (triggers save prompt)
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should exit successfully (0) without argparse errors
        assert result.returncode == 0
        assert "unrecognized" not in result.stderr.lower()

    # Spec: --delay requires an integer argument
    def test_delay_requires_integer(self):
        """--delay notanumber fails with argparse error."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--delay", "notanumber"],
            input="",  # Empty stdin is fine for argparse error test
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should fail with non-zero exit code
        assert result.returncode != 0
        # argparse should report an invalid int value
        assert "invalid int value" in result.stderr.lower() or "error" in result.stderr.lower()

    # Spec: --delay is accepted (warning behavior is implementation detail)
    def test_delay_parsed_with_non_interactive(self):
        """--delay with --non-interactive is parsed correctly.

        Note: We test parsing via non-interactive mode since interactive
        mode would hang waiting for input.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--delay", "0"],
            input="look\n",  # EOF after look, don't use quit (triggers save prompt)
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    # Spec: --delay slows execution measurably
    def test_delay_slows_execution(self):
        """Run with --delay 200 on 2 commands takes ~400ms longer than without."""
        # Use look and status commands - EOF ends session (no quit to avoid save prompt)
        commands = "look\nstatus\n"

        # Run without delay
        start = time.time()
        result_no_delay = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--delay", "0"],
            input=commands,
            capture_output=True,
            text=True,
            timeout=10,
        )
        time_no_delay = time.time() - start
        assert result_no_delay.returncode == 0

        # Run with 200ms delay
        start = time.time()
        result_with_delay = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--delay", "200"],
            input=commands,
            capture_output=True,
            text=True,
            timeout=10,
        )
        time_with_delay = time.time() - start
        assert result_with_delay.returncode == 0

        # With 2 commands (look, status), delay should add ~400ms
        # Allow some tolerance for process overhead
        delay_difference = time_with_delay - time_no_delay
        # At minimum, we should see ~300ms difference (2 commands * 200ms each)
        assert delay_difference >= 0.3, f"Expected ~400ms delay, got {delay_difference*1000:.0f}ms"

    # Spec: --delay works with --json mode
    def test_delay_works_with_json_mode(self):
        """--json --delay 100 works correctly."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json", "--skip-character-creation", "--delay", "100"],
            input="status\n",  # EOF ends session (no quit to avoid prompts)
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        # Should output JSON Lines
        assert "{" in result.stdout

    # Spec: default delay is zero (no delay)
    def test_delay_zero_is_default(self):
        """No delay when --delay not specified - runs quickly."""
        # EOF ends session (no quit to avoid save prompt)
        commands = "status\nstatus\nstatus\n"

        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation"],
            input=commands,
            capture_output=True,
            text=True,
            timeout=10,
        )
        elapsed = time.time() - start

        assert result.returncode == 0
        # Without delay, should complete in well under 1 second for just parsing commands
        # Allow generous time for Python startup overhead
        assert elapsed < 3.0, f"Expected quick execution, took {elapsed:.2f}s"

    # Spec: --delay validates range (implementation may clamp negative to 0)
    def test_delay_negative_value_handled(self):
        """--delay with negative value should be rejected or clamped to 0."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--delay", "-100"],
            input="look\n",  # EOF ends session (no quit to avoid save prompt)
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Implementation may either reject negative values or clamp to 0
        # Either behavior is acceptable - just verify it doesn't crash unexpectedly
        # If it returns 0, that's fine (clamped to 0)
        # If it returns non-zero with error, that's also fine (validation)
        assert result.returncode in [0, 2]  # 0 = success (clamped), 2 = argparse error
