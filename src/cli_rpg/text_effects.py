"""Text effects module for typewriter-style text reveal.

This module provides functions for dramatic text display effects,
primarily used for atmospheric moments like dreams, whispers, and combat.
"""

import re
import sys
import time
from typing import Optional, TextIO

from cli_rpg.colors import color_enabled

# Default delay between characters (in seconds)
DEFAULT_TYPEWRITER_DELAY = 0.03

# Pause duration constants (in seconds)
PAUSE_SHORT = 0.5
PAUSE_MEDIUM = 1.0
PAUSE_LONG = 1.5

# ANSI escape sequence pattern - matches sequences like \x1b[31m, \x1b[0m, etc.
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")

# Global override for programmatic effects control (None means follow color_enabled())
_effects_enabled_override: Optional[bool] = None


def set_effects_enabled(enabled: Optional[bool]) -> None:
    """Enable or disable text effects globally.

    This provides programmatic control over text effects, useful for
    non-interactive mode, testing, or when effects are not desired.

    Args:
        enabled: Whether to enable effects. Pass None to follow color_enabled() setting.
    """
    global _effects_enabled_override
    _effects_enabled_override = enabled


def effects_enabled() -> bool:
    """Check if text effects are enabled.

    Effects are disabled when:
    - set_effects_enabled(False) was called, OR
    - color_enabled() returns False (when effects follow color setting)

    Returns:
        True if effects are enabled, False otherwise.
    """
    if _effects_enabled_override is not None:
        return _effects_enabled_override
    return color_enabled()


def typewriter_print(
    text: str,
    delay: float = DEFAULT_TYPEWRITER_DELAY,
    file: Optional[TextIO] = None,
    end: str = "\n",
) -> None:
    """Print text with a typewriter effect, one character at a time.

    Characters are printed with a delay between each for a dramatic reveal.
    ANSI escape sequences (color codes) are printed instantly without delay.

    If effects are disabled, the text is printed instantly.
    KeyboardInterrupt (Ctrl+C) causes remaining text to print instantly.

    Args:
        text: The text to print with typewriter effect.
        delay: Delay between characters in seconds. Defaults to DEFAULT_TYPEWRITER_DELAY.
        file: File to write to. Defaults to sys.stdout.
        end: String appended after text. Defaults to newline.
    """
    if file is None:
        file = sys.stdout

    # If effects are disabled, print instantly
    if not effects_enabled():
        print(text, file=file, end=end, flush=True)
        return

    # Split text into segments: alternating between ANSI codes and regular text
    # Using finditer to get positions of all ANSI sequences
    segments = []
    last_end = 0

    for match in ANSI_ESCAPE_PATTERN.finditer(text):
        # Add any text before this ANSI sequence
        if match.start() > last_end:
            segments.append(("text", text[last_end : match.start()]))
        # Add the ANSI sequence itself
        segments.append(("ansi", match.group()))
        last_end = match.end()

    # Add any remaining text after the last ANSI sequence
    if last_end < len(text):
        segments.append(("text", text[last_end:]))

    # Track position in text for interrupt recovery
    printed_chars = 0

    try:
        for segment_type, segment_text in segments:
            if segment_type == "ansi":
                # Print ANSI codes instantly (don't count as printed chars for recovery)
                file.write(segment_text)
                file.flush()
            else:
                # Print regular text character by character
                for char in segment_text:
                    file.write(char)
                    file.flush()
                    printed_chars += 1
                    time.sleep(delay)

        # Print the ending
        file.write(end)
        file.flush()

    except KeyboardInterrupt:
        # On interrupt, print remaining text instantly
        # Strip ANSI codes to count visible characters we've printed
        plain_text = ANSI_ESCAPE_PATTERN.sub("", text)
        remaining = plain_text[printed_chars:]
        file.write(remaining)
        file.write(end)
        file.flush()


def dramatic_pause(duration: float = PAUSE_MEDIUM) -> None:
    """Pause execution for dramatic effect.

    If effects are disabled, returns immediately.

    Args:
        duration: Pause duration in seconds. Defaults to PAUSE_MEDIUM.
    """
    if not effects_enabled():
        return
    time.sleep(duration)


def pause_short() -> None:
    """Short pause (0.5s) for minor dramatic beats."""
    dramatic_pause(PAUSE_SHORT)


def pause_medium() -> None:
    """Medium pause (1.0s) for moderate dramatic moments."""
    dramatic_pause(PAUSE_MEDIUM)


def pause_long() -> None:
    """Long pause (1.5s) for major dramatic moments."""
    dramatic_pause(PAUSE_LONG)
