"""Tests for dump-state command.

Spec: dump-state outputs complete game state as valid JSON including
player stats, inventory, location, quest progress, and world state.
"""
import json
import subprocess
import sys
import pytest
from cli_rpg.game_state import GameState, KNOWN_COMMANDS
from cli_rpg.models.character import Character
from cli_rpg.world import create_world


class TestDumpStateCommand:
    """Test dump-state command functionality."""

    def test_dump_state_in_known_commands(self):
        """dump-state should be a recognized command."""
        # Spec: dump-state is a valid exploration command
        assert "dump-state" in KNOWN_COMMANDS

    def test_dump_state_outputs_valid_json(self):
        """dump-state should output valid JSON."""
        # Spec: dump-state outputs complete game state as valid JSON
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="dump-state\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Find JSON in output (skip any narrative text)
        lines = result.stdout.strip().split("\n")
        # Look for line starting with '{' (JSON object start)
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break
        assert json_start is not None, "Should contain JSON output"
        json_text = "\n".join(lines[json_start:])
        # Parse should not raise
        state = json.loads(json_text)
        assert isinstance(state, dict)

    def test_dump_state_contains_character(self):
        """dump-state should include character data."""
        # Spec: dump-state includes player stats, inventory
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="dump-state\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = result.stdout.strip().split("\n")
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
        state = json.loads("\n".join(lines[json_start:]))

        assert "character" in state
        char = state["character"]
        assert "name" in char
        assert "strength" in char
        assert "dexterity" in char
        assert "intelligence" in char
        assert "health" in char
        assert "gold" in char
        assert "inventory" in char
        assert "quests" in char

    def test_dump_state_contains_world(self):
        """dump-state should include world data."""
        # Spec: dump-state includes location and world state
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="dump-state\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = result.stdout.strip().split("\n")
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
        state = json.loads("\n".join(lines[json_start:]))

        assert "world" in state
        assert "current_location" in state
        assert isinstance(state["world"], dict)
        assert len(state["world"]) > 0

    def test_dump_state_contains_theme(self):
        """dump-state should include theme."""
        # Spec: dump-state includes complete game state (theme is part of it)
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive"],
            input="dump-state\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = result.stdout.strip().split("\n")
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
        state = json.loads("\n".join(lines[json_start:]))

        assert "theme" in state


class TestDumpStateJsonMode:
    """Test dump-state in JSON mode."""

    def test_dump_state_json_mode_emits_dump_state_type(self):
        """In JSON mode, dump-state should emit dump_state type message."""
        # Spec: dump-state works in JSON mode (--json) with proper type field
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json"],
            input="dump-state\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]

        # Find dump_state message
        dump_messages = [json.loads(line) for line in lines
                        if json.loads(line).get("type") == "dump_state"]

        assert len(dump_messages) == 1, "Should have exactly one dump_state message"
        dump = dump_messages[0]
        assert "character" in dump
        assert "world" in dump
        assert "current_location" in dump
