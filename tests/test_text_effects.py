"""Tests for the text_effects module - typewriter-style text reveal."""
import io
import sys
from unittest.mock import patch, MagicMock

import pytest

from cli_rpg import text_effects
from cli_rpg import colors


def _reset_effects_state():
    """Helper to reset effects state for each test."""
    text_effects.set_effects_enabled(None)
    colors.set_colors_enabled(None)


class TestTypewriterOutputsAllText:
    """Test: typewriter_print outputs complete text."""

    def test_typewriter_outputs_all_text(self):
        """Complete text should be output regardless of typewriter effect."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        with patch("time.sleep"):  # Skip delays
            text_effects.typewriter_print("Hello World", file=output)

        assert output.getvalue() == "Hello World\n"

    def test_typewriter_outputs_all_text_without_newline(self):
        """When end='' is specified, no trailing newline."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        with patch("time.sleep"):
            text_effects.typewriter_print("Hello", file=output, end="")

        assert output.getvalue() == "Hello"


class TestRespectsDisabledEffects:
    """Test: prints instantly when effects are disabled."""

    def test_respects_disabled_effects_via_toggle(self):
        """When effects are disabled, text prints instantly (no sleep calls)."""
        _reset_effects_state()
        text_effects.set_effects_enabled(False)

        output = io.StringIO()
        with patch("time.sleep") as mock_sleep:
            text_effects.typewriter_print("Instant text", file=output)

        # Should not call sleep when effects disabled
        mock_sleep.assert_not_called()
        assert output.getvalue() == "Instant text\n"

    def test_respects_disabled_effects_via_color_disabled(self):
        """When colors are disabled (CLI_RPG_NO_COLOR), effects also disabled."""
        _reset_effects_state()
        colors.set_colors_enabled(False)  # Disable colors
        text_effects.set_effects_enabled(None)  # Let it follow color setting

        output = io.StringIO()
        with patch("time.sleep") as mock_sleep:
            text_effects.typewriter_print("Instant text", file=output)

        mock_sleep.assert_not_called()
        assert output.getvalue() == "Instant text\n"


class TestHandlesAnsiCodes:
    """Test: ANSI color codes are printed instantly without delays."""

    def test_handles_ansi_codes_no_extra_delay(self):
        """ANSI escape sequences should not add character delays."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)
        colors.set_colors_enabled(True)

        # Text with color codes: "Hi" in red
        colored_text = f"{colors.RED}Hi{colors.RESET}"

        output = io.StringIO()
        sleep_calls = []

        def track_sleep(duration):
            sleep_calls.append(duration)

        with patch("time.sleep", side_effect=track_sleep):
            text_effects.typewriter_print(colored_text, file=output, delay=0.03)

        # Should only delay for visible characters "H" and "i", not for escape sequences
        # 2 visible characters = 2 sleep calls
        assert len(sleep_calls) == 2
        assert output.getvalue() == colored_text + "\n"


class TestEmptyString:
    """Test: empty input produces no crash."""

    def test_empty_string_no_crash(self):
        """Empty string should produce no output (except optional newline)."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        with patch("time.sleep") as mock_sleep:
            text_effects.typewriter_print("", file=output)

        # No characters to delay for
        mock_sleep.assert_not_called()
        # Just the newline from print
        assert output.getvalue() == "\n"

    def test_empty_string_no_newline(self):
        """Empty string with end='' produces empty output."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        text_effects.typewriter_print("", file=output, end="")

        assert output.getvalue() == ""


class TestMultiline:
    """Test: newlines are respected in output."""

    def test_multiline_preserves_newlines(self):
        """Newlines in text should be preserved in output."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        text = "Line 1\nLine 2\nLine 3"
        output = io.StringIO()

        with patch("time.sleep"):
            text_effects.typewriter_print(text, file=output)

        assert output.getvalue() == "Line 1\nLine 2\nLine 3\n"

    def test_multiline_newlines_delayed_like_chars(self):
        """Newlines should also trigger delay like visible chars."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        text = "A\nB"  # 3 chars: A, \n, B
        sleep_calls = []

        def track_sleep(duration):
            sleep_calls.append(duration)

        output = io.StringIO()
        with patch("time.sleep", side_effect=track_sleep):
            text_effects.typewriter_print(text, file=output, delay=0.03)

        # All 3 characters should trigger delay
        assert len(sleep_calls) == 3


class TestCustomDelay:
    """Test: custom delay parameter works."""

    def test_custom_delay_value(self):
        """Custom delay should be used instead of default."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        custom_delay = 0.05
        sleep_calls = []

        def track_sleep(duration):
            sleep_calls.append(duration)

        output = io.StringIO()
        with patch("time.sleep", side_effect=track_sleep):
            text_effects.typewriter_print("AB", file=output, delay=custom_delay)

        assert all(d == custom_delay for d in sleep_calls)
        assert len(sleep_calls) == 2

    def test_default_delay(self):
        """Default delay should be used when not specified."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        sleep_calls = []

        def track_sleep(duration):
            sleep_calls.append(duration)

        output = io.StringIO()
        with patch("time.sleep", side_effect=track_sleep):
            text_effects.typewriter_print("X", file=output)

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == text_effects.DEFAULT_TYPEWRITER_DELAY


class TestEffectsEnabledRespectsColorSetting:
    """Test: effects_enabled() follows color_enabled() when not explicitly set."""

    def test_effects_enabled_follows_color_enabled(self):
        """When effects not explicitly set, follows color_enabled()."""
        _reset_effects_state()

        # Both enabled by default
        colors.set_colors_enabled(True)
        text_effects.set_effects_enabled(None)  # Follow colors
        assert text_effects.effects_enabled() is True

        # Disable colors, effects should follow
        colors.set_colors_enabled(False)
        text_effects.set_effects_enabled(None)
        assert text_effects.effects_enabled() is False

    def test_effects_explicit_override_color_setting(self):
        """Explicit effects setting overrides color setting."""
        _reset_effects_state()

        # Disable colors but explicitly enable effects
        colors.set_colors_enabled(False)
        text_effects.set_effects_enabled(True)
        assert text_effects.effects_enabled() is True

        # Enable colors but explicitly disable effects
        colors.set_colors_enabled(True)
        text_effects.set_effects_enabled(False)
        assert text_effects.effects_enabled() is False


class TestKeyboardInterrupt:
    """Test: Ctrl+C interrupt prints remaining text instantly."""

    def test_keyboard_interrupt_prints_remaining(self):
        """KeyboardInterrupt during typewriter should print remaining text."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        output = io.StringIO()
        call_count = 0

        def interrupt_after_two(duration):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise KeyboardInterrupt()

        with patch("time.sleep", side_effect=interrupt_after_two):
            text_effects.typewriter_print("ABCDE", file=output, end="")

        # All text should still be output despite interrupt
        assert output.getvalue() == "ABCDE"


class TestDramaticPause:
    """Test: dramatic_pause() creates timed delays."""

    def test_dramatic_pause_sleeps_when_enabled(self):
        """dramatic_pause() should sleep for specified duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.dramatic_pause(0.75)

        mock_sleep.assert_called_once_with(0.75)

    def test_dramatic_pause_skips_when_disabled(self):
        """dramatic_pause() should skip sleep when effects disabled."""
        _reset_effects_state()
        text_effects.set_effects_enabled(False)

        with patch("time.sleep") as mock_sleep:
            text_effects.dramatic_pause(1.0)

        mock_sleep.assert_not_called()

    def test_pause_short_uses_correct_duration(self):
        """pause_short() should use PAUSE_SHORT duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_short()

        mock_sleep.assert_called_once_with(text_effects.PAUSE_SHORT)

    def test_pause_medium_uses_correct_duration(self):
        """pause_medium() should use PAUSE_MEDIUM duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_medium()

        mock_sleep.assert_called_once_with(text_effects.PAUSE_MEDIUM)

    def test_pause_long_uses_correct_duration(self):
        """pause_long() should use PAUSE_LONG duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_long()

        mock_sleep.assert_called_once_with(text_effects.PAUSE_LONG)

    def test_pause_respects_color_disabled(self):
        """Pause functions should skip when colors are disabled."""
        _reset_effects_state()
        colors.set_colors_enabled(False)
        text_effects.set_effects_enabled(None)  # Follow color setting

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_short()
            text_effects.pause_medium()
            text_effects.pause_long()

        mock_sleep.assert_not_called()
