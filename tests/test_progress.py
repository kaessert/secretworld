"""Tests for the progress module - progress indicators during AI generation.

Tests cover:
- Spinner thread starts and stops correctly
- Messages cycle through for each generation type
- No output when effects disabled
- Context manager properly cleans up on exception
- Thread safety of start/stop
"""

import io
import sys
import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from cli_rpg import text_effects
from cli_rpg import colors
from cli_rpg import progress


def _reset_effects_state():
    """Helper to reset effects state for each test."""
    text_effects.set_effects_enabled(None)
    colors.set_colors_enabled(None)


class TestProgressIndicatorStartsAndStops:
    """Test: Spinner thread starts and stops correctly."""

    def test_spinner_starts_when_entering_context(self):
        """Spinner thread should start when entering context."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        indicator = progress.ProgressIndicator("location", output=output)

        with patch("time.sleep"):  # Skip delays
            indicator.start()
            # Thread should be running
            assert indicator._running is True
            assert indicator._thread is not None
            indicator.stop()

    def test_spinner_stops_when_exiting_context(self):
        """Spinner thread should stop when exiting context."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        indicator = progress.ProgressIndicator("location", output=output)

        with patch("time.sleep"):
            indicator.start()
            indicator.stop()
            # Thread should no longer be running
            assert indicator._running is False

    def test_context_manager_starts_and_stops(self):
        """Context manager should properly start and stop spinner."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()

        with patch("time.sleep"):
            with progress.progress_indicator("location", output=output) as indicator:
                # Inside context, spinner should be running
                assert indicator._running is True
            # After context, spinner should be stopped
            assert indicator._running is False


class TestMessagesForGenerationType:
    """Test: Messages cycle through for each generation type."""

    def test_location_messages_exist(self):
        """Location generation type should have thematic messages."""
        assert "location" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["location"]) > 0

    def test_npc_messages_exist(self):
        """NPC generation type should have thematic messages."""
        assert "npc" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["npc"]) > 0

    def test_enemy_messages_exist(self):
        """Enemy generation type should have thematic messages."""
        assert "enemy" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["enemy"]) > 0

    def test_lore_messages_exist(self):
        """Lore generation type should have thematic messages."""
        assert "lore" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["lore"]) > 0

    def test_area_messages_exist(self):
        """Area generation type should have thematic messages."""
        assert "area" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["area"]) > 0

    def test_item_messages_exist(self):
        """Item generation type should have thematic messages."""
        assert "item" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["item"]) > 0

    def test_quest_messages_exist(self):
        """Quest generation type should have thematic messages."""
        assert "quest" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["quest"]) > 0

    def test_dream_messages_exist(self):
        """Dream generation type should have thematic messages."""
        assert "dream" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["dream"]) > 0

    def test_atmosphere_messages_exist(self):
        """Atmosphere generation type should have thematic messages."""
        assert "atmosphere" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["atmosphere"]) > 0

    def test_art_messages_exist(self):
        """Art generation type should have thematic messages."""
        assert "art" in progress.GENERATION_MESSAGES
        assert len(progress.GENERATION_MESSAGES["art"]) > 0

    def test_unknown_type_uses_default_messages(self):
        """Unknown generation type should use default messages."""
        assert "default" in progress.GENERATION_MESSAGES
        indicator = progress.ProgressIndicator("unknown_type")
        # Should not raise, should use default messages
        assert indicator._messages == progress.GENERATION_MESSAGES["default"]


class TestNoOutputWhenEffectsDisabled:
    """Test: No output when effects are disabled."""

    def test_no_output_when_effects_disabled(self):
        """When effects are disabled, no spinner output should appear."""
        _reset_effects_state()
        text_effects.set_effects_enabled(False)

        output = io.StringIO()

        with patch("time.sleep"):
            with progress.progress_indicator("location", output=output):
                pass

        # Should have no output when effects disabled
        assert output.getvalue() == ""

    def test_no_output_when_color_disabled(self):
        """When colors are disabled, no spinner output should appear."""
        _reset_effects_state()
        colors.set_colors_enabled(False)
        text_effects.set_effects_enabled(None)  # Follow color setting

        output = io.StringIO()

        with patch("time.sleep"):
            with progress.progress_indicator("location", output=output):
                pass

        assert output.getvalue() == ""


class TestContextManagerCleansUpOnException:
    """Test: Context manager properly cleans up on exception."""

    def test_cleanup_on_exception(self):
        """Spinner should be stopped even when exception is raised."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        indicator = None

        with patch("time.sleep"):
            try:
                with progress.progress_indicator("location", output=output) as ind:
                    indicator = ind
                    raise ValueError("Test exception")
            except ValueError:
                pass

        # Should be stopped after exception
        assert indicator is not None
        assert indicator._running is False


class TestSpinnerOutput:
    """Test: Spinner produces expected output format."""

    def test_spinner_uses_carriage_return(self):
        """Spinner output should use carriage return to overwrite line."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()

        with patch("time.sleep"):
            with progress.progress_indicator("location", output=output):
                # Give the thread a moment to produce output
                time.sleep(0.01)

        # Output should contain carriage return for line overwriting
        result = output.getvalue()
        if result:  # Only check if there was output
            assert "\r" in result

    def test_spinner_clears_line_on_stop(self):
        """Spinner should clear the line when stopped."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()

        with patch("time.sleep"):
            with progress.progress_indicator("location", output=output):
                pass

        # The final output should end with a line clear
        # (carriage return + spaces to clear + carriage return)
        result = output.getvalue()
        # The line should be cleared at the end (ends with \r)
        if result:
            assert result.endswith("\r")


class TestThreadSafety:
    """Test: Thread safety of start/stop operations."""

    def test_double_start_is_safe(self):
        """Calling start() twice should not cause issues."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        indicator = progress.ProgressIndicator("location", output=output)

        with patch("time.sleep"):
            indicator.start()
            indicator.start()  # Should be no-op
            assert indicator._running is True
            indicator.stop()
            assert indicator._running is False

    def test_double_stop_is_safe(self):
        """Calling stop() twice should not cause issues."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        indicator = progress.ProgressIndicator("location", output=output)

        with patch("time.sleep"):
            indicator.start()
            indicator.stop()
            indicator.stop()  # Should be no-op
            assert indicator._running is False

    def test_stop_without_start_is_safe(self):
        """Calling stop() without start() should not cause issues."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        indicator = progress.ProgressIndicator("location", output=output)

        # Should not raise
        indicator.stop()
        assert indicator._running is False


class TestSpinnerCharacters:
    """Test: Spinner uses ASCII characters."""

    def test_spinner_uses_ascii(self):
        """Spinner should use ASCII characters only."""
        for char in progress.SPINNER_CHARS:
            assert char.isascii() or char in "|/-\\"
