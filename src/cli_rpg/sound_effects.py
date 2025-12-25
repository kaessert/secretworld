"""Sound effects module for terminal bell alerts.

This module provides functions for playing terminal bell sounds (\a)
on important game events like combat victory, level up, death, and quest completion.
"""

import sys
from typing import Optional, TextIO

from cli_rpg.colors import color_enabled

# Global override for programmatic sound control (None means follow color_enabled())
_sound_enabled_override: Optional[bool] = None


def set_sound_enabled(enabled: Optional[bool]) -> None:
    """Enable or disable sound effects globally.

    This provides programmatic control over sound effects, useful for
    non-interactive mode, JSON mode, testing, or when sounds are not desired.

    Args:
        enabled: Whether to enable sounds. Pass None to follow color_enabled() setting.
    """
    global _sound_enabled_override
    _sound_enabled_override = enabled


def sound_enabled() -> bool:
    """Check if sound effects are enabled.

    Sound effects are disabled when:
    - set_sound_enabled(False) was called, OR
    - color_enabled() returns False (when sounds follow color setting)

    Returns:
        True if sounds are enabled, False otherwise.
    """
    if _sound_enabled_override is not None:
        return _sound_enabled_override
    return color_enabled()


def bell(file: Optional[TextIO] = None) -> None:
    """Output terminal bell character if sounds are enabled.

    Args:
        file: File to write to. Defaults to sys.stdout.
    """
    if not sound_enabled():
        return

    if file is None:
        file = sys.stdout

    file.write("\a")
    file.flush()


# Semantic helper functions for consistent sound usage across the codebase


def sound_victory(file: Optional[TextIO] = None) -> None:
    """Play sound for combat victory.

    Args:
        file: File to write to. Defaults to sys.stdout.
    """
    bell(file=file)


def sound_level_up(file: Optional[TextIO] = None) -> None:
    """Play sound for level up.

    Args:
        file: File to write to. Defaults to sys.stdout.
    """
    bell(file=file)


def sound_death(file: Optional[TextIO] = None) -> None:
    """Play sound for player death.

    Args:
        file: File to write to. Defaults to sys.stdout.
    """
    bell(file=file)


def sound_quest_complete(file: Optional[TextIO] = None) -> None:
    """Play sound for quest completion.

    Args:
        file: File to write to. Defaults to sys.stdout.
    """
    bell(file=file)
