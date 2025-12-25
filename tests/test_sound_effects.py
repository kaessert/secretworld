"""Tests for the sound_effects module - terminal bell sound effects."""
import io
import sys
from unittest.mock import patch

import pytest

from cli_rpg import sound_effects
from cli_rpg import colors


def _reset_sound_state():
    """Helper to reset sound state for each test."""
    sound_effects.set_sound_enabled(None)
    colors.set_colors_enabled(None)


class TestBellOutputsWhenEnabled:
    """Test: bell() outputs \\a when sound is enabled."""

    def test_bell_outputs_when_enabled(self):
        """bell() should output \\a character when sound is enabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(True)

        output = io.StringIO()
        sound_effects.bell(file=output)

        assert output.getvalue() == "\a"

    def test_bell_outputs_to_stdout_by_default(self):
        """bell() should write to stdout when no file provided."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(True)

        output = io.StringIO()
        with patch.object(sys, "stdout", output):
            sound_effects.bell()

        assert output.getvalue() == "\a"


class TestBellOutputsNothingWhenDisabled:
    """Test: bell() outputs nothing when sound is disabled."""

    def test_bell_outputs_nothing_when_disabled(self):
        """bell() should output nothing when sound is disabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(False)

        output = io.StringIO()
        sound_effects.bell(file=output)

        assert output.getvalue() == ""

    def test_bell_outputs_nothing_when_color_disabled(self):
        """bell() should output nothing when colors are disabled (follows color_enabled)."""
        _reset_sound_state()
        colors.set_colors_enabled(False)
        sound_effects.set_sound_enabled(None)  # Follow color setting

        output = io.StringIO()
        sound_effects.bell(file=output)

        assert output.getvalue() == ""


class TestSoundEnabledFollowsColorSetting:
    """Test: sound_enabled() follows color_enabled() when not explicitly set."""

    def test_sound_enabled_follows_color_enabled(self):
        """When sound not explicitly set, follows color_enabled()."""
        _reset_sound_state()

        # Both enabled by default
        colors.set_colors_enabled(True)
        sound_effects.set_sound_enabled(None)  # Follow colors
        assert sound_effects.sound_enabled() is True

        # Disable colors, sound should follow
        colors.set_colors_enabled(False)
        sound_effects.set_sound_enabled(None)
        assert sound_effects.sound_enabled() is False

    def test_sound_explicit_override_color_setting(self):
        """Explicit sound setting overrides color setting."""
        _reset_sound_state()

        # Disable colors but explicitly enable sound
        colors.set_colors_enabled(False)
        sound_effects.set_sound_enabled(True)
        assert sound_effects.sound_enabled() is True

        # Enable colors but explicitly disable sound
        colors.set_colors_enabled(True)
        sound_effects.set_sound_enabled(False)
        assert sound_effects.sound_enabled() is False


class TestSemanticSoundHelpers:
    """Test: semantic sound helper functions output bell when enabled."""

    def test_sound_victory_outputs_bell(self):
        """sound_victory() should output bell when enabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(True)

        output = io.StringIO()
        sound_effects.sound_victory(file=output)

        assert output.getvalue() == "\a"

    def test_sound_level_up_outputs_bell(self):
        """sound_level_up() should output bell when enabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(True)

        output = io.StringIO()
        sound_effects.sound_level_up(file=output)

        assert output.getvalue() == "\a"

    def test_sound_death_outputs_bell(self):
        """sound_death() should output bell when enabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(True)

        output = io.StringIO()
        sound_effects.sound_death(file=output)

        assert output.getvalue() == "\a"

    def test_sound_quest_complete_outputs_bell(self):
        """sound_quest_complete() should output bell when enabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(True)

        output = io.StringIO()
        sound_effects.sound_quest_complete(file=output)

        assert output.getvalue() == "\a"

    def test_semantic_helpers_output_nothing_when_disabled(self):
        """Semantic sound helpers should output nothing when sound is disabled."""
        _reset_sound_state()
        sound_effects.set_sound_enabled(False)

        output = io.StringIO()
        sound_effects.sound_victory(file=output)
        sound_effects.sound_level_up(file=output)
        sound_effects.sound_death(file=output)
        sound_effects.sound_quest_complete(file=output)

        assert output.getvalue() == ""
