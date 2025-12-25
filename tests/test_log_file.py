"""Tests for --log-file CLI option.

Spec: Add `--log-file <path>` CLI argument for comprehensive gameplay logging
with timestamps, commands, responses, and state changes in JSON Lines format.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestLogFileFlagParsing:
    """Test --log-file flag parsing."""

    # Spec: test_log_file_flag_accepted - --log-file path.log parses without error
    def test_log_file_flag_accepted(self):
        """--log-file flag should be accepted without error."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", log_path],
                input="",
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should exit cleanly (exit code 0)
            assert result.returncode == 0
        finally:
            Path(log_path).unlink(missing_ok=True)


class TestLogFileCreation:
    """Test log file creation."""

    # Spec: test_log_file_creates_file - Running with --log-file creates the log file
    def test_log_file_creates_file(self):
        """--log-file should create the specified log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0
            assert log_path.exists(), "Log file should be created"
            assert log_path.stat().st_size > 0, "Log file should not be empty"


class TestLogFileFormat:
    """Test log file format - JSON Lines."""

    # Spec: test_log_file_json_lines_format - Each line in log file is valid JSON
    def test_log_file_json_lines_format(self):
        """Each line in log file should be valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\nstatus\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0
            assert log_path.exists()

            with open(log_path) as f:
                lines = [line for line in f if line.strip()]

            assert len(lines) > 0, "Should have at least one line of log output"

            for i, line in enumerate(lines):
                try:
                    parsed = json.loads(line)
                    assert isinstance(parsed, dict), f"Line {i+1} should be a JSON object"
                    assert "type" in parsed, f"Line {i+1} should have a 'type' field"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON on line {i+1}: {line!r}")


class TestLogFileTimestamps:
    """Test log file timestamps."""

    # Spec: test_log_file_has_timestamp - Each log entry has ISO 8601 timestamp
    def test_log_file_has_timestamp(self):
        """Each log entry should have an ISO 8601 timestamp."""
        import re
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0

            with open(log_path) as f:
                lines = [line for line in f if line.strip()]

            for line in lines:
                entry = json.loads(line)
                assert "timestamp" in entry, "Each entry should have a timestamp"

                # Verify ISO 8601 format (YYYY-MM-DDTHH:MM:SS.microseconds+00:00)
                ts = entry["timestamp"]
                # Should be parseable as ISO 8601 datetime
                try:
                    # Python 3.11+ supports fromisoformat with 'Z' suffix
                    # For earlier versions, replace Z with +00:00
                    ts_normalized = ts.replace("Z", "+00:00")
                    datetime.fromisoformat(ts_normalized)
                except ValueError:
                    pytest.fail(f"Timestamp not valid ISO 8601: {ts}")


class TestLogFileContent:
    """Test log file content - commands, responses, state."""

    # Spec: test_log_file_logs_commands - Commands appear in log with type "command"
    def test_log_file_logs_commands(self):
        """Commands should be logged with type 'command'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\nstatus\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            command_entries = [e for e in entries if e.get("type") == "command"]
            assert len(command_entries) >= 2, "Should have logged at least 2 commands"

            # Verify command input is captured
            inputs = [e.get("input") for e in command_entries]
            assert "look" in inputs, "Should have logged 'look' command"
            assert "status" in inputs, "Should have logged 'status' command"

    # Spec: test_log_file_logs_responses - Game responses appear in log with type "response"
    def test_log_file_logs_responses(self):
        """Game responses should be logged with type 'response'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            response_entries = [e for e in entries if e.get("type") == "response"]
            assert len(response_entries) >= 1, "Should have at least one response"

            # Verify response has text field
            for resp in response_entries:
                assert "text" in resp, "Response entry should have 'text' field"

    # Spec: test_log_file_logs_state_changes - State changes appear in log with type "state"
    def test_log_file_logs_state_changes(self):
        """State changes should be logged with type 'state'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="status\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            state_entries = [e for e in entries if e.get("type") == "state"]
            assert len(state_entries) >= 1, "Should have at least one state entry"

            # Verify state entry has required fields
            state = state_entries[0]
            assert "location" in state, "State should have location"
            assert "health" in state, "State should have health"
            assert "max_health" in state, "State should have max_health"
            assert "gold" in state, "State should have gold"
            assert "level" in state, "State should have level"


class TestLogFileCompatibility:
    """Test log file works with other modes."""

    # Spec: test_log_file_works_with_non_interactive - --log-file + --non-interactive both work
    def test_log_file_works_with_non_interactive(self):
        """--log-file should work with --non-interactive mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\nstatus\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0
            assert log_path.exists()

            # Verify stdout still has normal output
            assert "Town Square" in result.stdout or "look" in result.stdout.lower()

            # Verify log file has content
            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]
            assert len(entries) > 0

    # Spec: test_log_file_works_with_json - --log-file + --json both work (log file separate from stdout JSON)
    def test_log_file_works_with_json(self):
        """--log-file should work with --json mode (separate from stdout JSON)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--json", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0
            assert log_path.exists()

            # Verify stdout has JSON output
            stdout_lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
            assert len(stdout_lines) > 0
            for line in stdout_lines:
                parsed = json.loads(line)  # Should be valid JSON
                assert "type" in parsed

            # Verify log file also has content (separate from stdout)
            with open(log_path) as f:
                log_entries = [json.loads(line) for line in f if line.strip()]
            assert len(log_entries) > 0


class TestLogFileSessionMarkers:
    """Test log file session start and end markers."""

    # Spec: test_log_file_session_start_entry - Log includes session_start entry with initial state
    def test_log_file_session_start_entry(self):
        """Log should include session_start entry with initial state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            # First entry should be session_start
            session_starts = [e for e in entries if e.get("type") == "session_start"]
            assert len(session_starts) == 1, "Should have exactly one session_start"

            start = session_starts[0]
            assert "character" in start, "session_start should have character name"
            assert "location" in start, "session_start should have location"
            assert "theme" in start, "session_start should have theme"

    # Spec: test_log_file_session_end_entry - Log includes session_end entry when game exits
    def test_log_file_session_end_entry(self):
        """Log should include session_end entry when game exits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.log"

            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--log-file", str(log_path)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0

            with open(log_path) as f:
                entries = [json.loads(line) for line in f if line.strip()]

            # Last entry should be session_end
            session_ends = [e for e in entries if e.get("type") == "session_end"]
            assert len(session_ends) == 1, "Should have exactly one session_end"

            end = session_ends[0]
            assert "reason" in end, "session_end should have a reason"
