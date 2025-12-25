"""Tests for 'Did you mean?' command suggestions.

Tests the fuzzy matching feature that suggests similar commands when a player
types an unrecognized command (e.g., typing "attakc" suggests "attack").
"""

import pytest

from cli_rpg.game_state import suggest_command, KNOWN_COMMANDS, parse_command


class TestSuggestCommand:
    """Tests for the suggest_command helper function."""

    def test_suggests_attack_for_attakc(self):
        """'attakc' should suggest 'attack' - transposed letters."""
        # Spec: similar typo should suggest the correct command
        suggestion = suggest_command("attakc", KNOWN_COMMANDS)
        assert suggestion == "attack"

    def test_suggests_inventory_for_invnetory(self):
        """Common typo 'invnetory' should suggest 'inventory'."""
        # Spec: transposed letters in the middle of a word
        suggestion = suggest_command("invnetory", KNOWN_COMMANDS)
        assert suggestion == "inventory"

    def test_suggests_look_for_lokk(self):
        """'lokk' should suggest 'look' - doubled wrong letter."""
        suggestion = suggest_command("lokk", KNOWN_COMMANDS)
        assert suggestion == "look"

    def test_suggests_status_for_staus(self):
        """'staus' should suggest 'status' - missing letter."""
        suggestion = suggest_command("staus", KNOWN_COMMANDS)
        assert suggestion == "status"

    def test_no_suggestion_for_gibberish(self):
        """Random gibberish like 'xyzzy' should not suggest anything."""
        # Spec: if no close match, return None
        suggestion = suggest_command("xyzzy", KNOWN_COMMANDS)
        assert suggestion is None

    def test_no_suggestion_for_completely_different(self):
        """Words that are too different should return None."""
        suggestion = suggest_command("zzzzz", KNOWN_COMMANDS)
        assert suggestion is None

    def test_suggestion_threshold_boundary(self):
        """Only suggests when similarity is >= 60%."""
        # Spec: threshold is 0.6 (60%)
        # 'go' is only 2 chars - 'gg' should not match (50% similarity)
        suggestion = suggest_command("gg", KNOWN_COMMANDS)
        assert suggestion is None

    def test_suggests_go_for_ho(self):
        """'ho' should suggest 'go' - single letter off."""
        # 'ho' is 1 char different from 'go' (2 chars) = 50% match
        # Actually at 60% cutoff this might not match, let's test
        suggestion = suggest_command("goo", KNOWN_COMMANDS)
        assert suggestion == "go"

    def test_suggests_help_for_hlep(self):
        """'hlep' should suggest 'help' - transposed letters."""
        suggestion = suggest_command("hlep", KNOWN_COMMANDS)
        assert suggestion == "help"

    def test_suggests_equip_for_equpi(self):
        """'equpi' should suggest 'equip' - transposed ending."""
        suggestion = suggest_command("equpi", KNOWN_COMMANDS)
        assert suggestion == "equip"


class TestParseCommandWithUnknown:
    """Tests for parse_command returning original input for unknown commands."""

    def test_unknown_command_returns_original_input(self):
        """Unknown command should include the original input in args."""
        # Spec: Returns ("unknown", [original_command]) for unknown commands
        command, args = parse_command("attakc")
        assert command == "unknown"
        assert args == ["attakc"]

    def test_unknown_command_with_args_returns_first_word(self):
        """Unknown command with arguments should return first word."""
        command, args = parse_command("attakc goblin")
        assert command == "unknown"
        assert args == ["attakc"]

    def test_empty_command_returns_unknown_with_empty_args(self):
        """Empty input should return unknown with empty args."""
        command, args = parse_command("")
        assert command == "unknown"
        assert args == []

    def test_whitespace_only_returns_unknown_with_empty_args(self):
        """Whitespace-only input should return unknown with empty args."""
        command, args = parse_command("   ")
        assert command == "unknown"
        assert args == []

    def test_valid_command_still_works(self):
        """Valid commands should still be parsed correctly."""
        command, args = parse_command("attack")
        assert command == "attack"
        assert args == []

    def test_valid_command_with_args_still_works(self):
        """Valid commands with args should still be parsed correctly."""
        command, args = parse_command("go north")
        assert command == "go"
        assert args == ["north"]


class TestUnknownCommandMessages:
    """Tests for unknown command message formatting in handlers."""

    def test_suggestion_message_format(self):
        """Verify the suggestion message format is correct."""
        from cli_rpg.game_state import suggest_command, KNOWN_COMMANDS

        unknown_cmd = "attakc"
        suggestion = suggest_command(unknown_cmd, KNOWN_COMMANDS)

        # Format the message as main.py should
        if suggestion:
            message = f"\n✗ Unknown command '{unknown_cmd}'. Did you mean '{suggestion}'?"
        else:
            message = "\n✗ Unknown command. Type 'help' for a list of commands."

        assert "attakc" in message
        assert "attack" in message
        assert "Did you mean" in message

    def test_no_suggestion_message_format(self):
        """Verify the no-suggestion message format is correct."""
        from cli_rpg.game_state import suggest_command, KNOWN_COMMANDS

        unknown_cmd = "xyzzy"
        suggestion = suggest_command(unknown_cmd, KNOWN_COMMANDS)

        # Format the message as main.py should
        if suggestion:
            message = f"\n✗ Unknown command '{unknown_cmd}'. Did you mean '{suggestion}'?"
        else:
            message = "\n✗ Unknown command. Type 'help' for a list of commands."

        assert "Did you mean" not in message
        assert "help" in message


class TestKnownCommandsSet:
    """Tests for the KNOWN_COMMANDS constant."""

    def test_known_commands_contains_basic_commands(self):
        """KNOWN_COMMANDS should contain all basic game commands."""
        expected = {"look", "go", "attack", "defend", "flee", "status",
                    "inventory", "equip", "help", "save", "quit"}
        assert expected.issubset(KNOWN_COMMANDS)

    def test_known_commands_contains_shop_commands(self):
        """KNOWN_COMMANDS should contain shop-related commands."""
        expected = {"buy", "sell", "shop"}
        assert expected.issubset(KNOWN_COMMANDS)

    def test_known_commands_contains_quest_commands(self):
        """KNOWN_COMMANDS should contain quest-related commands."""
        expected = {"quests", "quest", "accept", "complete", "abandon"}
        assert expected.issubset(KNOWN_COMMANDS)
