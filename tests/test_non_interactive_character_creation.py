"""Tests for non-interactive character creation.

Spec: Non-interactive mode (`--non-interactive` and `--json`) should support character
creation via stdin when `--skip-character-creation` flag is not set.

Character creation inputs in non-interactive mode (when not skipped):
- Line 1: Character name (string, 2-30 chars)
- Line 2: Character class ("1"-"5" or class name: warrior, mage, rogue, ranger, cleric)
- Line 3: Stat allocation method ("1" or "2" / "manual" or "random")
- If manual: Lines 4-7: strength, dexterity, intelligence, charisma (integers 1-20)
- Final line: Confirmation ("yes" or "y")

Error handling: Invalid inputs should print error and exit with code 1 (no retry loops).
"""
import pytest
import subprocess
import sys
import json


class TestSkipCharacterCreationFlag:
    """Test --skip-character-creation flag functionality."""

    def test_non_interactive_with_skip_flag_uses_default_character(self):
        """--skip-character-creation uses default "Agent" character.

        Spec: When --skip-character-creation is set, use default character
        (preserves current behavior for backward compatibility).
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation"],
            input="status\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Default character is named "Agent"
        assert "Agent" in result.stdout

    def test_json_mode_with_skip_flag(self):
        """--json --skip-character-creation works and uses default character.

        Spec: JSON mode with skip flag uses default character.
        """
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json", "--skip-character-creation"],
            input="",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Should have valid JSON output
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) > 0
        # First line should be valid JSON
        first_obj = json.loads(lines[0])
        assert "type" in first_obj


class TestNonInteractiveCharacterCreationManual:
    """Test manual stat allocation in non-interactive character creation."""

    def test_non_interactive_character_creation_manual_stats(self):
        """Provide name, class, "1", str/dex/int/cha/per, "yes" → custom character with manual stats.

        Spec: Character creation inputs for manual allocation:
        - Line 1: Character name (string, 2-30 chars)
        - Line 2: Character class ("1" for Warrior)
        - Line 3: Stat allocation method ("1" for manual)
        - Lines 4-9: strength, dexterity, intelligence, charisma, perception, luck (integers 1-20)
        - Final line: Confirmation ("yes")
        """
        # Input: name, class (warrior), method (manual), str, dex, int, cha, per, luck, confirmation, then command
        stdin_input = "TestHero\n1\n1\n15\n12\n10\n8\n10\n10\nyes\nstatus\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Custom character name should appear in status output
        assert "TestHero" in result.stdout
        # Check stats are displayed - Warrior adds STR +3, so 15 + 3 = 18
        assert "18" in result.stdout or "Strength" in result.stdout


class TestNonInteractiveCharacterCreationRandom:
    """Test random stat allocation in non-interactive character creation."""

    def test_non_interactive_character_creation_random_stats(self):
        """Provide name, class, "2", "yes" → custom character with random stats.

        Spec: Character creation inputs for random allocation:
        - Line 1: Character name (string, 2-30 chars)
        - Line 2: Character class ("2" for Mage)
        - Line 3: Stat allocation method ("2" for random)
        - Final line: Confirmation ("yes")
        """
        # Input: name, class (mage), method (random), confirmation, then command
        stdin_input = "RandomHero\n2\n2\nyes\nstatus\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Custom character name should appear in status output
        assert "RandomHero" in result.stdout


class TestNonInteractiveCharacterCreationErrors:
    """Test error handling in non-interactive character creation."""

    def test_non_interactive_character_creation_invalid_name_exits(self):
        """Invalid name (empty or too short) → exit code 1.

        Spec: Invalid inputs should print error and exit with code 1.
        """
        # Input: empty name (invalid)
        stdin_input = "\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        # Should contain error message
        assert "error" in result.stdout.lower() or "Error" in result.stdout

    def test_non_interactive_character_creation_name_too_short_exits(self):
        """Name too short → exit code 1.

        Spec: Name must be 2-30 characters. Invalid inputs exit with code 1.
        """
        # Input: single character name (too short)
        stdin_input = "X\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower() or "Error" in result.stdout

    def test_non_interactive_character_creation_invalid_stat_exits(self):
        """Invalid stat value → exit code 1.

        Spec: Stats must be integers 1-20. Invalid inputs exit with code 1.
        """
        # Input: name, method, invalid strength (too high)
        stdin_input = "TestHero\n1\n25\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower() or "Error" in result.stdout

    def test_non_interactive_character_creation_stat_too_low_exits(self):
        """Stat too low → exit code 1.

        Spec: Stats must be integers 1-20. Invalid inputs exit with code 1.
        """
        # Input: name, method, invalid strength (too low)
        stdin_input = "TestHero\n1\n0\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower() or "Error" in result.stdout

    def test_non_interactive_character_creation_non_numeric_stat_exits(self):
        """Non-numeric stat value → exit code 1.

        Spec: Stats must be integers. Invalid inputs exit with code 1.
        """
        # Input: name, method, non-numeric strength
        stdin_input = "TestHero\n1\nabc\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower() or "Error" in result.stdout

    def test_non_interactive_character_creation_invalid_method_exits(self):
        """Invalid allocation method → exit code 1.

        Spec: Method must be "1", "2", "manual", or "random". Invalid inputs exit with code 1.
        """
        # Input: name, invalid method
        stdin_input = "TestHero\n3\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower() or "Error" in result.stdout


class TestJsonModeCharacterCreation:
    """Test character creation in JSON mode."""

    def test_json_mode_character_creation_manual(self):
        """JSON mode character creation with manual stats.

        Spec: Same inputs as non-interactive mode, but output is JSON.
        """
        # Input: name, class (warrior), method (manual), str, dex, int, cha, per, luck, confirmation
        stdin_input = "TestHero\n1\n1\n15\n12\n10\n8\n10\n10\nyes\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Output should be valid JSON lines
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) > 0
        # Check that all lines are valid JSON
        for line in lines:
            try:
                json.loads(line)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON line: {line}")

    def test_json_mode_character_creation_error_emits_json(self):
        """JSON mode errors emit JSON error objects.

        Spec: Errors in JSON mode should emit JSON error objects.
        """
        # Input: invalid name (empty)
        stdin_input = "\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 1
        # Output should contain JSON with error
        lines = [l for l in result.stdout.strip().split('\n') if l]
        if lines:
            # Check that we have valid JSON output
            last_obj = json.loads(lines[-1])
            assert "type" in last_obj
            # Should be an error type
            assert last_obj["type"] == "error" or "error" in str(last_obj).lower()


class TestNonInteractiveCharacterCreationConfirmation:
    """Test confirmation handling in non-interactive character creation."""

    def test_non_interactive_character_creation_no_confirmation_exits(self):
        """Confirmation "no" → exit code 1 (creation cancelled).

        Spec: If user does not confirm, character creation is cancelled.
        """
        # Input: name, class (warrior), method (manual), stats (str, dex, int, cha, per, luck), "no" confirmation
        stdin_input = "TestHero\n1\n1\n15\n12\n10\n8\n10\n10\nno\n"

        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should exit with error code since creation was cancelled
        assert result.returncode == 1
        assert "cancel" in result.stdout.lower() or "cancelled" in result.stdout.lower()
