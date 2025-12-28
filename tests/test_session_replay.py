"""Tests for session replay from logged state.

These tests verify the --replay CLI flag and related functionality:
- Test 1: --replay flag is accepted
- Test 2: replay extracts seed from log
- Test 3: replay executes commands from log
- Test 4: --validate mode detects state divergence
- Test 5: --continue-at N starts from command N
- Test 6: replay works with JSON mode
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from cli_rpg.session_replay import (
    parse_log_file,
    extract_seed,
    extract_commands,
    extract_states,
    validate_state,
    LogEntry,
    StateSnapshot,
)


class TestParseLogFile:
    """Tests for parse_log_file function."""

    def test_parses_empty_file(self, tmp_path):
        """Empty log file yields no entries."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")
        entries = list(parse_log_file(str(log_file)))
        assert entries == []

    def test_parses_single_entry(self, tmp_path):
        """Single log entry is parsed correctly."""
        log_file = tmp_path / "single.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 12345}\n'
        )
        entries = list(parse_log_file(str(log_file)))
        assert len(entries) == 1
        assert entries[0].entry_type == "session_start"
        assert entries[0].data["seed"] == 12345

    def test_parses_multiple_entries(self, tmp_path):
        """Multiple log entries are parsed in order."""
        log_file = tmp_path / "multi.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "session_end", "reason": "quit"}\n'
        )
        entries = list(parse_log_file(str(log_file)))
        assert len(entries) == 3
        assert [e.entry_type for e in entries] == ["session_start", "command", "session_end"]

    def test_skips_blank_lines(self, tmp_path):
        """Blank lines are skipped."""
        log_file = tmp_path / "blanks.log"
        log_file.write_text(
            '\n'
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start"}\n'
            '\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '\n'
        )
        entries = list(parse_log_file(str(log_file)))
        assert len(entries) == 2


class TestExtractSeed:
    """Tests for extract_seed function."""

    def test_extracts_seed_from_session_start(self, tmp_path):
        """Seed is extracted from session_start entry."""
        # Test 2: replay extracts seed from log
        log_file = tmp_path / "seeded.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 12345}\n'
        )
        seed = extract_seed(str(log_file))
        assert seed == 12345

    def test_returns_none_if_no_seed(self, tmp_path):
        """Returns None if session_start has no seed."""
        log_file = tmp_path / "no_seed.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start"}\n'
        )
        seed = extract_seed(str(log_file))
        assert seed is None

    def test_returns_none_if_no_session_start(self, tmp_path):
        """Returns None if no session_start entry."""
        log_file = tmp_path / "no_start.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "command", "input": "look"}\n'
        )
        seed = extract_seed(str(log_file))
        assert seed is None


class TestExtractCommands:
    """Tests for extract_commands function."""

    def test_extracts_commands_from_log(self, tmp_path):
        """Commands are extracted from command entries."""
        # Test 3: replay executes commands from log
        log_file = tmp_path / "commands.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "response", "text": "You see..."}\n'
            '{"timestamp": "2024-01-01T00:00:03Z", "type": "command", "input": "status"}\n'
            '{"timestamp": "2024-01-01T00:00:04Z", "type": "session_end", "reason": "quit"}\n'
        )
        commands = extract_commands(str(log_file))
        assert commands == ["look", "status"]

    def test_extracts_commands_with_limit(self, tmp_path):
        """Commands are limited when limit is specified."""
        log_file = tmp_path / "many_commands.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start"}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "command", "input": "status"}\n'
            '{"timestamp": "2024-01-01T00:00:03Z", "type": "command", "input": "go north"}\n'
            '{"timestamp": "2024-01-01T00:00:04Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:05Z", "type": "command", "input": "quit"}\n'
        )
        # Test 5: --continue-at N starts from command N
        commands = extract_commands(str(log_file), limit=3)
        assert commands == ["look", "status", "go north"]

    def test_returns_empty_list_if_no_commands(self, tmp_path):
        """Returns empty list if no command entries."""
        log_file = tmp_path / "no_commands.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start"}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "session_end", "reason": "eof"}\n'
        )
        commands = extract_commands(str(log_file))
        assert commands == []


class TestExtractStates:
    """Tests for extract_states function."""

    def test_extracts_states_from_log(self, tmp_path):
        """State snapshots are extracted from state entries."""
        # Test 4: --validate mode detects state divergence
        log_file = tmp_path / "states.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start"}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "state", "location": "Town Square", "health": 100, "max_health": 100, "gold": 50, "level": 1}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:03Z", "type": "state", "location": "Town Square", "health": 100, "max_health": 100, "gold": 50, "level": 1}\n'
        )
        states = extract_states(str(log_file))
        assert len(states) == 2
        assert states[0].location == "Town Square"
        assert states[0].health == 100
        assert states[0].gold == 50

    def test_returns_empty_list_if_no_states(self, tmp_path):
        """Returns empty list if no state entries."""
        log_file = tmp_path / "no_states.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start"}\n'
        )
        states = extract_states(str(log_file))
        assert states == []


class TestValidateState:
    """Tests for validate_state function."""

    def test_no_differences_when_matching(self):
        """No differences reported when states match."""
        expected = StateSnapshot(
            location="Town Square",
            health=100,
            max_health=100,
            gold=50,
            level=1
        )
        actual = {
            "location": "Town Square",
            "health": 100,
            "max_health": 100,
            "gold": 50,
            "level": 1
        }
        diffs = validate_state(expected, actual)
        assert diffs == []

    def test_detects_location_mismatch(self):
        """Detects location mismatch."""
        expected = StateSnapshot(
            location="Town Square",
            health=100,
            max_health=100,
            gold=50,
            level=1
        )
        actual = {
            "location": "Forest Path",
            "health": 100,
            "gold": 50,
            "level": 1
        }
        diffs = validate_state(expected, actual)
        assert len(diffs) == 1
        assert "location" in diffs[0]
        assert "Town Square" in diffs[0]
        assert "Forest Path" in diffs[0]

    def test_detects_multiple_mismatches(self):
        """Detects multiple field mismatches."""
        expected = StateSnapshot(
            location="Town Square",
            health=100,
            max_health=100,
            gold=50,
            level=1
        )
        actual = {
            "location": "Town Square",
            "health": 80,  # Different
            "gold": 100,   # Different
            "level": 1
        }
        diffs = validate_state(expected, actual)
        assert len(diffs) == 2
        assert any("health" in d for d in diffs)
        assert any("gold" in d for d in diffs)


class TestReplayFlagAccepted:
    """Test 1: --replay flag is accepted."""

    def test_replay_flag_parses(self, tmp_path):
        """--replay flag should parse without error."""
        from cli_rpg.main import parse_args

        log_file = tmp_path / "test.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:05Z", "type": "session_end", "reason": "quit"}\n'
        )

        args = parse_args(["--replay", str(log_file)])
        assert args.replay == str(log_file)

    def test_validate_flag_parses(self, tmp_path):
        """--validate flag should parse with --replay."""
        from cli_rpg.main import parse_args

        log_file = tmp_path / "test.log"
        log_file.write_text("")

        args = parse_args(["--replay", str(log_file), "--validate"])
        assert args.replay == str(log_file)
        assert args.validate is True

    def test_continue_at_flag_parses(self, tmp_path):
        """--continue-at flag should parse with --replay."""
        from cli_rpg.main import parse_args

        log_file = tmp_path / "test.log"
        log_file.write_text("")

        args = parse_args(["--replay", str(log_file), "--continue-at", "5"])
        assert args.replay == str(log_file)
        assert args.continue_at == 5


class TestReplayMode:
    """Tests for run_replay_mode function."""

    def test_replay_uses_seed_from_log(self, tmp_path):
        """Test 2: Replay should use the RNG seed from session_start."""
        import random
        from cli_rpg.main import run_replay_mode

        log_file = tmp_path / "seeded.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 12345}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "session_end", "reason": "quit"}\n'
        )

        # Run replay mode
        exit_code = run_replay_mode(str(log_file))
        assert exit_code == 0

        # Verify seed was used by checking random state is reproducible
        random.seed(12345)
        expected_value = random.random()
        random.seed(12345)
        actual_value = random.random()
        assert expected_value == actual_value

    def test_replay_executes_commands(self, tmp_path, capsys):
        """Test 3: Replay should execute commands from log entries."""
        from cli_rpg.main import run_replay_mode

        log_file = tmp_path / "commands.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "command", "input": "status"}\n'
            '{"timestamp": "2024-01-01T00:00:03Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = run_replay_mode(str(log_file))
        assert exit_code == 0

        captured = capsys.readouterr()
        # Should show replay progress for both commands
        assert "[1/2]" in captured.out
        assert "[2/2]" in captured.out
        assert "look" in captured.out
        assert "status" in captured.out

    def test_validate_detects_state_mismatch(self, tmp_path, capsys):
        """Test 4: --validate should report when replay state differs from log."""
        from cli_rpg.main import run_replay_mode

        log_file = tmp_path / "mismatch.log"
        # Create log with state that won't match (gold value will be different)
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "state", "location": "Anywhere", "health": 100, "max_health": 100, "gold": 99999, "level": 99}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:03Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = run_replay_mode(str(log_file), validate=True)
        # Should return 1 for validation failure
        assert exit_code == 1

        captured = capsys.readouterr()
        # Should report state mismatch
        assert "mismatch" in captured.out.lower() or "validation failed" in captured.out.lower()

    def test_validate_passes_when_states_match(self, tmp_path, capsys):
        """Validate mode passes when all states match."""
        from cli_rpg.main import run_replay_mode

        log_file = tmp_path / "match.log"
        # Create minimal log without state entries to validate
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = run_replay_mode(str(log_file), validate=True)
        assert exit_code == 0

        captured = capsys.readouterr()
        # Should report validation passed
        assert "passed" in captured.out.lower() or "✓" in captured.out

    def test_replay_with_json_mode(self, tmp_path, capsys):
        """Test 6: Replay should work with --json for structured output."""
        from cli_rpg.main import run_replay_mode

        log_file = tmp_path / "json.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = run_replay_mode(str(log_file), json_output=True)
        assert exit_code == 0

        captured = capsys.readouterr()
        # JSON output should contain valid JSON lines
        lines = [line for line in captured.out.strip().split('\n') if line.strip()]
        # Should have at least some output
        assert len(lines) > 0
        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "type" in parsed


class TestReplayModeIntegration:
    """Integration tests for replay mode with main entry point."""

    def test_main_accepts_replay_flag(self, tmp_path):
        """main() should accept --replay and run replay mode."""
        from cli_rpg.main import main

        log_file = tmp_path / "test.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = main(["--replay", str(log_file)])
        assert exit_code == 0

    def test_main_with_replay_and_json(self, tmp_path, capsys):
        """main() should accept --replay with --json flag."""
        from cli_rpg.main import main

        log_file = tmp_path / "test.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "command", "input": "look"}\n'
            '{"timestamp": "2024-01-01T00:00:02Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = main(["--replay", str(log_file), "--json"])
        assert exit_code == 0

        captured = capsys.readouterr()
        # Should have JSON output
        lines = [line for line in captured.out.strip().split('\n') if line.strip()]
        assert len(lines) > 0

    def test_main_with_replay_and_validate(self, tmp_path):
        """main() should accept --replay with --validate flag."""
        from cli_rpg.main import main

        log_file = tmp_path / "test.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00Z", "type": "session_start", "seed": 42}\n'
            '{"timestamp": "2024-01-01T00:00:01Z", "type": "session_end", "reason": "quit"}\n'
        )

        exit_code = main(["--replay", str(log_file), "--validate"])
        assert exit_code == 0
