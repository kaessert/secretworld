"""Color utilities for CLI output.

This module provides ANSI color codes and helper functions for colorizing
terminal output. Colors can be disabled via CLI_RPG_NO_COLOR environment variable.
"""

import os
from functools import lru_cache
from typing import Optional

# ANSI color codes
RESET = "\x1b[0m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
BOLD = "\x1b[1m"

# Global override for programmatic color control (None means use env var)
_colors_enabled_override: Optional[bool] = None


def set_colors_enabled(enabled: Optional[bool]) -> None:
    """Enable or disable ANSI color output globally.

    This provides programmatic control over color output, useful for
    non-interactive mode or testing.

    Args:
        enabled: Whether to enable colors. Pass None to reset to env-based behavior.
    """
    global _colors_enabled_override
    _colors_enabled_override = enabled


@lru_cache(maxsize=1)
def _check_env_color() -> bool:
    """Check environment variable for color setting.

    Returns:
        True if colors should be enabled based on env var.
    """
    value = os.environ.get("CLI_RPG_NO_COLOR", "").lower()
    return value not in ("true", "1")


def color_enabled() -> bool:
    """Check if colors are enabled.

    Colors are disabled when:
    - set_colors_enabled(False) was called, OR
    - CLI_RPG_NO_COLOR environment variable is set to 'true' or '1'.

    Returns:
        True if colors are enabled, False otherwise.
    """
    if _colors_enabled_override is not None:
        return _colors_enabled_override
    return _check_env_color()


def colorize(text: str, color: str) -> str:
    """Wrap text in color codes if colors are enabled.

    Args:
        text: The text to colorize.
        color: The ANSI color code to apply.

    Returns:
        Colored text if colors enabled, plain text otherwise.
    """
    if not color_enabled():
        return text
    return f"{color}{text}{RESET}"


def bold_colorize(text: str, color: str) -> str:
    """Wrap text in bold and color codes if colors are enabled.

    Args:
        text: The text to colorize.
        color: The ANSI color code to apply.

    Returns:
        Bold colored text if colors enabled, plain text otherwise.
    """
    if not color_enabled():
        return text
    return f"{BOLD}{color}{text}{RESET}"


# Semantic helper functions for consistent color usage across the codebase


def enemy(text: str) -> str:
    """Color text as an enemy (red).

    Args:
        text: Enemy name or related text.

    Returns:
        Red-colored text.
    """
    return colorize(text, RED)


def location(text: str) -> str:
    """Color text as a location (cyan).

    Args:
        text: Location name.

    Returns:
        Cyan-colored text.
    """
    return colorize(text, CYAN)


def npc(text: str) -> str:
    """Color text as an NPC (yellow).

    Args:
        text: NPC name.

    Returns:
        Yellow-colored text.
    """
    return colorize(text, YELLOW)


def item(text: str) -> str:
    """Color text as an item (green).

    Args:
        text: Item name.

    Returns:
        Green-colored text.
    """
    return colorize(text, GREEN)


def gold(text: str) -> str:
    """Color text as gold/currency (yellow).

    Args:
        text: Gold amount or currency text.

    Returns:
        Yellow-colored text.
    """
    return colorize(text, YELLOW)


def damage(text: str) -> str:
    """Color text as damage (red).

    Args:
        text: Damage value or related text.

    Returns:
        Red-colored text.
    """
    return colorize(text, RED)


def heal(text: str) -> str:
    """Color text as healing (green).

    Args:
        text: Heal amount or related text.

    Returns:
        Green-colored text.
    """
    return colorize(text, GREEN)


def stat_header(text: str) -> str:
    """Color text as a stat header (magenta).

    Args:
        text: Stat label or header text.

    Returns:
        Magenta-colored text.
    """
    return colorize(text, MAGENTA)


def warning(text: str) -> str:
    """Color text as a warning (yellow).

    Args:
        text: Warning message text.

    Returns:
        Yellow-colored text.
    """
    return colorize(text, YELLOW)


def companion(text: str) -> str:
    """Color text as a companion (cyan).

    Args:
        text: Companion name or banter text.

    Returns:
        Cyan-colored text.
    """
    return colorize(text, CYAN)


def dialogue(text: str) -> str:
    """Color text as dialogue/NPC speech (blue).

    Args:
        text: Dialogue text spoken by NPCs.

    Returns:
        Blue-colored text.
    """
    return colorize(text, BLUE)


def narration(text: str) -> str:
    """Return narration text unchanged (default terminal color).

    Narration uses the terminal's default color for readability.
    This function exists for semantic consistency and future styling.

    Args:
        text: Narrative/descriptive text.

    Returns:
        Unchanged text.
    """
    return text
