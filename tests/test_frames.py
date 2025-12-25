"""Tests for the frames module.

Tests cover:
- FrameStyle enum character sets
- frame_text() function with various parameters
- Convenience functions (frame_announcement, frame_dream, frame_combat_intro)
- Color integration
"""

import pytest
from cli_rpg import colors
from cli_rpg.frames import (
    FrameStyle,
    frame_text,
    frame_announcement,
    frame_dream,
    frame_combat_intro,
)


class TestFrameStyle:
    """Tests for FrameStyle enum - spec: Frame character sets."""

    def test_frame_styles_have_required_characters(self):
        """Each style has top/bottom/left/right/corners characters."""
        for style in FrameStyle:
            chars = style.value
            # Verify required keys exist
            assert "top" in chars, f"{style.name} missing 'top'"
            assert "bottom" in chars, f"{style.name} missing 'bottom'"
            assert "left" in chars, f"{style.name} missing 'left'"
            assert "right" in chars, f"{style.name} missing 'right'"
            assert "top_left" in chars, f"{style.name} missing 'top_left'"
            assert "top_right" in chars, f"{style.name} missing 'top_right'"
            assert "bottom_left" in chars, f"{style.name} missing 'bottom_left'"
            assert "bottom_right" in chars, f"{style.name} missing 'bottom_right'"


class TestFrameText:
    """Tests for frame_text() function - spec: Main framing utility."""

    def test_frame_text_wraps_single_line(self):
        """Short text fits in frame."""
        result = frame_text("Hello", style=FrameStyle.SINGLE)
        assert "Hello" in result
        # Should have frame characters
        assert "┌" in result
        assert "┐" in result
        assert "└" in result
        assert "┘" in result
        assert "│" in result

    def test_frame_text_wraps_multiline(self):
        """Long text wraps correctly within frame."""
        long_text = "This is a very long text that should wrap to multiple lines when framed"
        result = frame_text(long_text, style=FrameStyle.SINGLE, width=30)
        lines = result.split("\n")
        # Should have multiple content lines due to wrapping
        content_lines = [l for l in lines if "│" in l and "─" not in l]
        assert len(content_lines) > 1, "Text should wrap to multiple lines"

    def test_frame_text_with_title(self):
        """Title appears in top border."""
        result = frame_text("Content", style=FrameStyle.DOUBLE, title="My Title")
        lines = result.split("\n")
        top_border = lines[0]
        assert "My Title" in top_border

    def test_frame_text_with_custom_width(self):
        """Respects width parameter."""
        result = frame_text("Hi", style=FrameStyle.SINGLE, width=50)
        lines = result.split("\n")
        # Top border should be close to 50 chars (accounting for corners)
        top_border = lines[0]
        assert len(top_border) == 50

    def test_frame_text_with_color(self):
        """Color codes applied to frame chars."""
        colors.set_colors_enabled(True)
        try:
            result = frame_text("Text", style=FrameStyle.SINGLE, color=colors.RED)
            # Should contain ANSI color codes
            assert colors.RED in result
            assert colors.RESET in result
        finally:
            colors.set_colors_enabled(None)

    def test_frame_text_without_color(self):
        """Works when colors disabled."""
        colors.set_colors_enabled(False)
        try:
            result = frame_text("Text", style=FrameStyle.SINGLE, color=colors.RED)
            # Should NOT contain ANSI color codes when disabled
            assert colors.RED not in result
            assert "Text" in result
            # Frame chars should still be present
            assert "┌" in result
        finally:
            colors.set_colors_enabled(None)

    def test_frame_text_double_style(self):
        """Uses double-line box chars ╔═╗║╚╝."""
        result = frame_text("Hello", style=FrameStyle.DOUBLE)
        assert "╔" in result
        assert "╗" in result
        assert "╚" in result
        assert "╝" in result
        assert "║" in result
        assert "═" in result

    def test_frame_text_single_style(self):
        """Uses single-line box chars ┌─┐│└┘."""
        result = frame_text("Hello", style=FrameStyle.SINGLE)
        assert "┌" in result
        assert "┐" in result
        assert "└" in result
        assert "┘" in result
        assert "│" in result
        assert "─" in result

    def test_frame_text_simple_style(self):
        """Uses simple horizontal lines only with ═."""
        result = frame_text("Hello", style=FrameStyle.SIMPLE)
        lines = result.split("\n")
        # Simple style uses ═ for top/bottom borders
        assert "═" in lines[0]
        assert "═" in lines[-1]
        # Content line should NOT have side borders (simple has no sides)
        # The middle line should contain the text without vertical borders
        content_lines = [l for l in lines if "Hello" in l]
        assert len(content_lines) == 1


class TestConvenienceFunctions:
    """Tests for convenience functions - spec: Common patterns."""

    def test_frame_announcement_uses_double_gold(self):
        """frame_announcement uses Double style with gold color."""
        colors.set_colors_enabled(True)
        try:
            result = frame_announcement("World event!", title="EVENT")
            # Should use double frame characters
            assert "╔" in result
            assert "║" in result
            # Should use YELLOW (gold) color
            assert colors.YELLOW in result
            # Title should appear
            assert "EVENT" in result
        finally:
            colors.set_colors_enabled(None)

    def test_frame_dream_uses_simple_magenta(self):
        """frame_dream uses Simple style with magenta color."""
        colors.set_colors_enabled(True)
        try:
            result = frame_dream("You drift into dreams...")
            # Should use simple frame characters (═ only for borders)
            assert "═" in result
            # Should use MAGENTA color
            assert colors.MAGENTA in result
        finally:
            colors.set_colors_enabled(None)

    def test_frame_combat_intro_uses_double_red(self):
        """frame_combat_intro uses Double style with red color."""
        colors.set_colors_enabled(True)
        try:
            result = frame_combat_intro("The darkness takes form!")
            # Should use double frame characters
            assert "╔" in result
            assert "║" in result
            # Should use RED color
            assert colors.RED in result
        finally:
            colors.set_colors_enabled(None)


class TestIntegration:
    """Integration tests for edge cases."""

    def test_frame_with_ansi_color_in_text(self):
        """Colored text inside frame aligns correctly."""
        colors.set_colors_enabled(True)
        try:
            colored_text = colors.colorize("Important", colors.RED)
            result = frame_text(colored_text, style=FrameStyle.SINGLE, width=30)
            # Should contain the text
            assert "Important" in result
            # Frame should still be properly formed
            assert "┌" in result
            assert "┘" in result
        finally:
            colors.set_colors_enabled(None)

    def test_frame_empty_text(self):
        """Empty text produces valid frame."""
        result = frame_text("", style=FrameStyle.SINGLE, width=20)
        # Should still have frame structure
        assert "┌" in result
        assert "┘" in result

    def test_frame_text_preserves_newlines(self):
        """Multi-line input text is handled correctly."""
        text = "Line 1\nLine 2\nLine 3"
        result = frame_text(text, style=FrameStyle.SINGLE)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
