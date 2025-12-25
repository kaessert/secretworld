"""Tests for JSON output mode.

Spec:
- Add a --json flag to emit structured JSON Lines output
- Each line is a valid JSON object with a 'type' field
- Message types: state, narrative, actions, error, combat
- ANSI escape codes should not appear in JSON output
"""
import json
import subprocess
import sys
from io import StringIO


class TestJsonFlag:
    """Test --json flag parsing and basic behavior."""

    # Spec: test_json_flag_accepted - --json flag parses without error
    def test_json_flag_accepted(self):
        """--json flag should be accepted without error."""
        # Run with --json flag and empty stdin, should not error
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="",
            capture_output=True,
            text=True,
            timeout=5
        )
        # Should exit cleanly (exit code 0)
        assert result.returncode == 0

    # Spec: test_json_implies_non_interactive - --json enables non-interactive mode
    def test_json_implies_non_interactive(self):
        """--json should run non-interactively (no prompts, read from stdin)."""
        # Run with --json and a simple command
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        # Should exit cleanly without waiting for interactive input
        assert result.returncode == 0
        # Should have produced JSON output
        assert len(result.stdout.strip()) > 0


class TestJsonOutputFormat:
    """Test JSON output format and validity."""

    # Spec: test_json_output_valid_lines - Each line is valid JSON
    def test_json_output_valid_lines(self):
        """Each non-empty line in output should be valid JSON."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="look\nstatus\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
        assert len(lines) > 0, "Should have at least one line of output"

        for line in lines:
            try:
                parsed = json.loads(line)
                assert isinstance(parsed, dict), f"Each line should be a JSON object: {line}"
                assert "type" in parsed, f"Each object should have a 'type' field: {line}"
            except json.JSONDecodeError as e:
                raise AssertionError(f"Invalid JSON line: {line!r}") from e

    # Spec: test_json_state_message - State message contains location, health, gold, level
    def test_json_state_message(self):
        """State messages should contain required fields."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="status\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

        # Find state message
        state_messages = [json.loads(line) for line in lines
                         if json.loads(line).get("type") == "state"]

        assert len(state_messages) > 0, "Should have at least one state message"
        state = state_messages[0]

        # Verify required fields
        assert "location" in state, "state should have location"
        assert "health" in state, "state should have health"
        assert "max_health" in state, "state should have max_health"
        assert "gold" in state, "state should have gold"
        assert "level" in state, "state should have level"

    # Spec: test_json_narrative_message - Narrative type contains text field
    def test_json_narrative_message(self):
        """Narrative messages should have a text field."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

        # Find narrative messages
        narrative_messages = [json.loads(line) for line in lines
                             if json.loads(line).get("type") == "narrative"]

        assert len(narrative_messages) > 0, "Should have at least one narrative message"
        narrative = narrative_messages[0]

        assert "text" in narrative, "narrative should have text field"
        assert isinstance(narrative["text"], str), "narrative text should be a string"

    # Spec: test_json_actions_message - Actions include exits, npcs, commands
    def test_json_actions_message(self):
        """Actions messages should have exits, npcs, and commands."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

        # Find actions messages
        actions_messages = [json.loads(line) for line in lines
                           if json.loads(line).get("type") == "actions"]

        assert len(actions_messages) > 0, "Should have at least one actions message"
        actions = actions_messages[0]

        assert "exits" in actions, "actions should have exits"
        assert "npcs" in actions, "actions should have npcs"
        assert "commands" in actions, "actions should have commands"
        assert isinstance(actions["exits"], list), "exits should be a list"
        assert isinstance(actions["npcs"], list), "npcs should be a list"
        assert isinstance(actions["commands"], list), "commands should be a list"

    # Spec: test_json_error_message - Error includes code and message
    def test_json_error_message(self):
        """Error messages should have code and message fields."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="go nowhere\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

        # Find error messages
        error_messages = [json.loads(line) for line in lines
                         if json.loads(line).get("type") == "error"]

        assert len(error_messages) > 0, "Should have at least one error message for invalid direction"
        error = error_messages[0]

        assert "code" in error, "error should have code field"
        assert "message" in error, "error should have message field"
        assert isinstance(error["code"], str), "error code should be a string"
        assert isinstance(error["message"], str), "error message should be a string"

    # Spec: test_json_no_ansi_codes - No ANSI escape sequences in JSON output
    def test_json_no_ansi_codes(self):
        """JSON output should not contain ANSI escape sequences."""
        import re

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="look\nstatus\ngo north\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

        # ANSI escape sequence pattern
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')

        # Check entire output for ANSI codes
        assert not ansi_pattern.search(result.stdout), \
            f"Output should not contain ANSI codes: {result.stdout!r}"


class TestJsonCombatState:
    """Test JSON output during combat."""

    # Spec: test_json_combat_state - Combat state emitted during battle
    def test_json_combat_state(self):
        """Combat messages should be emitted when in battle.

        Note: This test is probabilistic since combat is triggered randomly.
        We test that IF combat is triggered, proper JSON is emitted.
        For deterministic testing, we would need to mock the random encounter.
        """
        # The combat test is tricky since encounters are random.
        # We'll test the json_output module directly for combat emission
        from cli_rpg.json_output import emit_combat
        from io import StringIO
        import sys

        # Capture stdout
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        try:
            emit_combat("Test Enemy", 50, 100)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue().strip()
        combat_msg = json.loads(output)

        assert combat_msg["type"] == "combat"
        assert "enemy" in combat_msg
        assert "enemy_health" in combat_msg
        assert "player_health" in combat_msg
        assert combat_msg["enemy"] == "Test Enemy"
        assert combat_msg["enemy_health"] == 50
        assert combat_msg["player_health"] == 100
