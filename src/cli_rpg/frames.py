"""Frame and border utilities for CLI output.

Provides centralized, reusable border/frame utilities for consistent UI
presentation across the codebase. Used for dream sequences, world events,
combat announcements, and other dramatic moments.
"""

import textwrap
from enum import Enum
from typing import Optional

from cli_rpg import colors


class FrameStyle(Enum):
    """Frame character sets for different UI contexts.

    DOUBLE: Double-line box for major announcements (world events, boss encounters)
    SINGLE: Single-line box for standard UI (maps, dialogs)
    SIMPLE: Horizontal lines only for subtle framing (dreams)
    """

    DOUBLE = {
        "top_left": "╔",
        "top_right": "╗",
        "bottom_left": "╚",
        "bottom_right": "╝",
        "top": "═",
        "bottom": "═",
        "left": "║",
        "right": "║",
    }
    SINGLE = {
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "top": "─",
        "bottom": "─",
        "left": "│",
        "right": "│",
    }
    SIMPLE = {
        "top_left": "",
        "top_right": "",
        "bottom_left": "",
        "bottom_right": "",
        "top": "═",
        "bottom": "═",
        "left": "",
        "right": "",
    }


def _strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text to get visual length.

    Args:
        text: Text potentially containing ANSI codes.

    Returns:
        Text with ANSI codes removed.
    """
    import re

    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def _visible_len(text: str) -> int:
    """Get the visible length of text (excluding ANSI codes).

    Args:
        text: Text potentially containing ANSI codes.

    Returns:
        Visual length of text.
    """
    return len(_strip_ansi(text))


def frame_text(
    text: str,
    style: FrameStyle,
    width: Optional[int] = None,
    title: Optional[str] = None,
    color: Optional[str] = None,
) -> str:
    """Create a framed text block.

    Args:
        text: The text to frame. May contain newlines for multi-line content.
        style: The FrameStyle to use (DOUBLE, SINGLE, SIMPLE).
        width: Total frame width. If None, auto-calculated from content.
        title: Optional title to display in top border.
        color: Optional ANSI color code to apply to frame characters.

    Returns:
        Framed text string ready for display.
    """
    chars = style.value
    is_simple = style == FrameStyle.SIMPLE

    # Default width if not specified
    if width is None:
        # Calculate based on content, with reasonable min/max
        max_line_len = max(
            (_visible_len(line) for line in text.split("\n")),
            default=0,
        )
        # Add padding for borders and internal spacing
        if is_simple:
            width = max(max_line_len + 8, 40)  # Padding for indent
        else:
            width = max(max_line_len + 4, 40)  # 2 for borders + 2 padding

    # Calculate inner width (content area)
    if is_simple:
        inner_width = width
    else:
        inner_width = width - 2  # Account for left/right borders

    # Helper to colorize frame chars
    def colorize_frame(char: str) -> str:
        if color and char:
            return colors.colorize(char, color)
        return char

    lines = []

    # Build top border
    if is_simple:
        top_border = chars["top"] * width
        lines.append(colorize_frame(top_border))
    else:
        if title:
            # Title centered in top border
            title_padded = f" {title} "
            remaining = width - 2 - len(title_padded)  # -2 for corners
            left_pad = remaining // 2
            right_pad = remaining - left_pad
            top_line = (
                colorize_frame(chars["top_left"])
                + colorize_frame(chars["top"] * left_pad)
                + title_padded
                + colorize_frame(chars["top"] * right_pad)
                + colorize_frame(chars["top_right"])
            )
        else:
            top_line = (
                colorize_frame(chars["top_left"])
                + colorize_frame(chars["top"] * (width - 2))
                + colorize_frame(chars["top_right"])
            )
        lines.append(top_line)

    # Process content - handle existing newlines and wrap long lines
    content_lines = []
    for paragraph in text.split("\n"):
        if paragraph:
            # Wrap long lines
            wrapped = textwrap.wrap(paragraph, width=inner_width - 2)  # -2 for padding
            content_lines.extend(wrapped if wrapped else [""])
        else:
            content_lines.append("")

    # Ensure at least one content line
    if not content_lines:
        content_lines = [""]

    # Build content lines
    for content in content_lines:
        visible_content_len = _visible_len(content)
        padding_needed = inner_width - visible_content_len - 2  # -2 for spaces around content

        if is_simple:
            # Simple style: just indent content, no side borders
            line = "    " + content  # 4-space indent
        else:
            # Regular styles: add side borders
            line = (
                colorize_frame(chars["left"])
                + " "
                + content
                + " " * (padding_needed + 1)
                + colorize_frame(chars["right"])
            )
        lines.append(line)

    # Build bottom border
    if is_simple:
        bottom_border = chars["bottom"] * width
        lines.append(colorize_frame(bottom_border))
    else:
        bottom_line = (
            colorize_frame(chars["bottom_left"])
            + colorize_frame(chars["bottom"] * (width - 2))
            + colorize_frame(chars["bottom_right"])
        )
        lines.append(bottom_line)

    return "\n".join(lines)


def frame_announcement(text: str, title: Optional[str] = None) -> str:
    """Frame text as a major announcement (world events).

    Uses Double frame style with gold (yellow) color.

    Args:
        text: The announcement content.
        title: Optional title for the announcement.

    Returns:
        Framed announcement string.
    """
    return frame_text(
        text,
        style=FrameStyle.DOUBLE,
        title=title,
        color=colors.YELLOW,
    )


def frame_dream(text: str) -> str:
    """Frame text as a dream sequence.

    Uses Simple frame style with magenta color.

    Args:
        text: The dream content.

    Returns:
        Framed dream string.
    """
    return frame_text(
        text,
        style=FrameStyle.SIMPLE,
        color=colors.MAGENTA,
    )


def frame_combat_intro(text: str, title: Optional[str] = None) -> str:
    """Frame text as a combat introduction (boss fights, shadow creature).

    Uses Double frame style with red color.

    Args:
        text: The combat intro content.
        title: Optional title for the intro.

    Returns:
        Framed combat intro string.
    """
    return frame_text(
        text,
        style=FrameStyle.DOUBLE,
        title=title,
        color=colors.RED,
    )
