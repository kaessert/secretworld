"""Tests for dialogue choice system affecting NPC relationships.

Tests dialogue choices during NPC conversations that affect NPC arc points:
- DialogueChoice dataclass
- DIALOGUE_CHOICES list with friendly/neutral/aggressive options
- format_dialogue_choices() for display
- apply_dialogue_choice() for arc modification
- DIALOGUE_CHOICE InteractionType
"""
import pytest

from cli_rpg.models.npc import NPC
from cli_rpg.models.npc_arc import NPCArc, InteractionType, NPCArcStage


# === Test DIALOGUE_CHOICE InteractionType ===
# Spec: Add DIALOGUE_CHOICE = "dialogue_choice" to InteractionType enum


class TestDialogueChoiceInteractionType:
    """Tests for DIALOGUE_CHOICE interaction type in npc_arc.py."""

    def test_dialogue_choice_interaction_type_exists(self):
        """DIALOGUE_CHOICE enum exists with value 'dialogue_choice'."""
        assert InteractionType.DIALOGUE_CHOICE.value == "dialogue_choice"


# === Test DialogueChoice dataclass ===
# Spec: DialogueChoice(label, description, arc_delta) dataclass


class TestDialogueChoice:
    """Tests for DialogueChoice dataclass in dialogue_choices.py."""

    def test_dialogue_choice_creation(self):
        """DialogueChoice stores label, description, arc_delta."""
        from cli_rpg.dialogue_choices import DialogueChoice

        choice = DialogueChoice(
            label="Friendly",
            description="Respond warmly and helpfully",
            arc_delta=3,
        )
        assert choice.label == "Friendly"
        assert choice.description == "Respond warmly and helpfully"
        assert choice.arc_delta == 3


# === Test DIALOGUE_CHOICES constant ===
# Spec: DIALOGUE_CHOICES = [Friendly (+3), Neutral (+1), Aggressive (-2)]


class TestDialogueChoicesConstant:
    """Tests for DIALOGUE_CHOICES list."""

    def test_dialogue_choices_has_three_options(self):
        """DIALOGUE_CHOICES has exactly 3 options."""
        from cli_rpg.dialogue_choices import DIALOGUE_CHOICES

        assert len(DIALOGUE_CHOICES) == 3

    def test_friendly_choice_is_first(self):
        """Friendly choice is first with +3 arc_delta."""
        from cli_rpg.dialogue_choices import DIALOGUE_CHOICES

        assert DIALOGUE_CHOICES[0].label == "Friendly"
        assert DIALOGUE_CHOICES[0].arc_delta == 3

    def test_neutral_choice_is_second(self):
        """Neutral choice is second with +1 arc_delta."""
        from cli_rpg.dialogue_choices import DIALOGUE_CHOICES

        assert DIALOGUE_CHOICES[1].label == "Neutral"
        assert DIALOGUE_CHOICES[1].arc_delta == 1

    def test_aggressive_choice_is_third(self):
        """Aggressive choice is third with -2 arc_delta."""
        from cli_rpg.dialogue_choices import DIALOGUE_CHOICES

        assert DIALOGUE_CHOICES[2].label == "Aggressive"
        assert DIALOGUE_CHOICES[2].arc_delta == -2


# === Test format_dialogue_choices() ===
# Spec: format_dialogue_choices() returns formatted string with all 3 options


class TestFormatDialogueChoices:
    """Tests for format_dialogue_choices function."""

    def test_format_dialogue_choices_includes_all_options(self):
        """format_dialogue_choices includes all 3 options with numbers."""
        from cli_rpg.dialogue_choices import format_dialogue_choices

        output = format_dialogue_choices()
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output
        assert "Friendly" in output
        assert "Neutral" in output
        assert "Aggressive" in output

    def test_format_dialogue_choices_output(self):
        """format_dialogue_choices returns expected format with descriptions."""
        from cli_rpg.dialogue_choices import format_dialogue_choices

        output = format_dialogue_choices()
        # Should include descriptions
        assert "warmly" in output.lower() or "warm" in output.lower()
        assert "polite" in output.lower() or "businesslike" in output.lower()
        assert "blunt" in output.lower() or "threatening" in output.lower()


# === Test apply_dialogue_choice() ===
# Spec: apply_dialogue_choice(npc, choice_index, timestamp) modifies arc and returns feedback


class TestApplyDialogueChoice:
    """Tests for apply_dialogue_choice function."""

    def _make_npc(self) -> NPC:
        """Create test NPC with arc."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC for dialogue",
            dialogue="Hello there!",
            arc=NPCArc(arc_points=0),
        )
        return npc

    def test_dialogue_choice_friendly_adds_3_points(self):
        """Friendly choice (index 0) adds +3 arc points."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        apply_dialogue_choice(npc, 0, timestamp=100)
        assert npc.arc.arc_points == 3

    def test_dialogue_choice_neutral_adds_1_point(self):
        """Neutral choice (index 1) adds +1 arc point."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        apply_dialogue_choice(npc, 1, timestamp=100)
        assert npc.arc.arc_points == 1

    def test_dialogue_choice_aggressive_subtracts_2_points(self):
        """Aggressive choice (index 2) subtracts 2 arc points."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        apply_dialogue_choice(npc, 2, timestamp=100)
        assert npc.arc.arc_points == -2

    def test_dialogue_choice_records_interaction_type(self):
        """apply_dialogue_choice uses DIALOGUE_CHOICE interaction type."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        apply_dialogue_choice(npc, 0, timestamp=100)
        assert len(npc.arc.interactions) == 1
        assert npc.arc.interactions[0].interaction_type == InteractionType.DIALOGUE_CHOICE

    def test_dialogue_choice_records_timestamp(self):
        """apply_dialogue_choice records the provided timestamp."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        apply_dialogue_choice(npc, 1, timestamp=500)
        assert npc.arc.interactions[0].timestamp == 500

    def test_dialogue_choice_returns_feedback_message(self):
        """apply_dialogue_choice returns a feedback message."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        message = apply_dialogue_choice(npc, 0, timestamp=100)
        assert isinstance(message, str)
        assert len(message) > 0

    def test_dialogue_choice_triggers_stage_change(self):
        """Stage transitions display message when arc crosses thresholds."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = self._make_npc()
        npc.arc.arc_points = 24  # Just below ACQUAINTANCE threshold (25)
        message = apply_dialogue_choice(npc, 0, timestamp=100)  # +3 -> 27
        # Should mention stage change
        assert "acquaintance" in message.lower() or "stage" in message.lower() or "relationship" in message.lower()

    def test_dialogue_choice_initializes_arc_if_none(self):
        """apply_dialogue_choice initializes NPC arc if None."""
        from cli_rpg.dialogue_choices import apply_dialogue_choice

        npc = NPC(
            name="No Arc NPC",
            description="NPC without arc",
            dialogue="Hello!",
            arc=None,
        )
        apply_dialogue_choice(npc, 0, timestamp=100)
        assert npc.arc is not None
        assert npc.arc.arc_points == 3


# === Test parse_dialogue_input() ===
# Spec: parse_dialogue_input(input_str) returns choice index or None


class TestParseDialogueInput:
    """Tests for parse_dialogue_input function."""

    def test_parse_number_1(self):
        """Input '1' returns index 0."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("1") == 0

    def test_parse_number_2(self):
        """Input '2' returns index 1."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("2") == 1

    def test_parse_number_3(self):
        """Input '3' returns index 2."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("3") == 2

    def test_parse_friendly_word(self):
        """Input 'friendly' (case insensitive) returns index 0."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("friendly") == 0
        assert parse_dialogue_input("Friendly") == 0
        assert parse_dialogue_input("FRIENDLY") == 0

    def test_parse_neutral_word(self):
        """Input 'neutral' (case insensitive) returns index 1."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("neutral") == 1
        assert parse_dialogue_input("Neutral") == 1

    def test_parse_aggressive_word(self):
        """Input 'aggressive' (case insensitive) returns index 2."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("aggressive") == 2
        assert parse_dialogue_input("Aggressive") == 2

    def test_parse_invalid_returns_none(self):
        """Invalid input returns None."""
        from cli_rpg.dialogue_choices import parse_dialogue_input

        assert parse_dialogue_input("4") is None
        assert parse_dialogue_input("hello") is None
        assert parse_dialogue_input("") is None
        assert parse_dialogue_input("0") is None


# === Test get_reaction_message() ===
# Spec: get_reaction_message(npc_name, choice_label) returns NPC reaction


class TestGetReactionMessage:
    """Tests for get_reaction_message function."""

    def test_friendly_reaction_message(self):
        """Friendly choice generates positive reaction message."""
        from cli_rpg.dialogue_choices import get_reaction_message

        msg = get_reaction_message("Elara", "Friendly")
        assert "Elara" in msg
        # Should be positive sentiment
        assert any(word in msg.lower() for word in ["smile", "appreciate", "warm", "pleased", "happy", "kindness"])

    def test_neutral_reaction_message(self):
        """Neutral choice generates neutral reaction message."""
        from cli_rpg.dialogue_choices import get_reaction_message

        msg = get_reaction_message("Marcus", "Neutral")
        assert "Marcus" in msg

    def test_aggressive_reaction_message(self):
        """Aggressive choice generates negative reaction message."""
        from cli_rpg.dialogue_choices import get_reaction_message

        msg = get_reaction_message("Thorne", "Aggressive")
        assert "Thorne" in msg
        # Should be negative sentiment
        assert any(word in msg.lower() for word in ["frown", "cold", "tense", "narrow", "displease", "upset"])
