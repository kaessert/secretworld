"""Color utilities for CLI output.

This module provides ANSI color codes and helper functions for colorizing
terminal output. Colors can be disabled via CLI_RPG_NO_COLOR environment variable.
"""

import os
from functools import lru_cache

# ANSI color codes
RESET = "\x1b[0m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
BOLD = "\x1b[1m"


@lru_cache(maxsize=1)
def color_enabled() -> bool:
    """Check if colors are enabled.

    Colors are disabled when CLI_RPG_NO_COLOR environment variable is set
    to 'true' or '1'.

    Returns:
        True if colors are enabled, False otherwise.
    """
    value = os.environ.get("CLI_RPG_NO_COLOR", "").lower()
    return value not in ("true", "1")


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
