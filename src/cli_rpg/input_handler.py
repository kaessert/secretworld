"""Input handler with readline integration for command history.

Provides enhanced input with up/down arrow history navigation
and persistent history across sessions.

Spec requirements:
1. Up arrow scrolls back through previous commands
2. Down arrow scrolls forward through history
3. History persists across sessions (saved to file)
4. Configurable history size (default: 500 commands)
5. Fallback to basic input if readline unavailable
"""
import atexit
from pathlib import Path

# Configurable history size - Spec requirement 4
HISTORY_SIZE = 500

# Module-level state for readline availability
_readline_available = False


def get_history_path() -> Path:
    """Return the path to the command history file.

    Returns:
        Path to ~/.cli_rpg_history
    """
    return Path.home() / ".cli_rpg_history"


def init_readline() -> None:
    """Initialize readline with history support.

    Loads existing history from file if it exists,
    sets history length, and registers cleanup handler.

    Spec requirements 1, 2, 3: Enable arrow key navigation
    and persistent history.
    """
    global _readline_available
    try:
        import readline

        _readline_available = True
        history_path = get_history_path()

        if history_path.exists():
            try:
                readline.read_history_file(str(history_path))
            except PermissionError:
                pass  # Gracefully handle sandboxed environments

        readline.set_history_length(HISTORY_SIZE)
        atexit.register(cleanup_readline)
    except ImportError:
        # Spec requirement 5: Fallback to basic input on Windows
        # or systems without readline
        pass


def cleanup_readline() -> None:
    """Save command history to file.

    Called automatically on exit via atexit.
    Spec requirement 3: Persist history across sessions.
    """
    if _readline_available:
        import readline

        try:
            readline.write_history_file(str(get_history_path()))
        except PermissionError:
            pass  # Gracefully handle sandboxed environments


def get_input(prompt: str = "") -> str:
    """Get user input with readline support.

    This is a drop-in replacement for input() that works
    with readline for history navigation when available.

    Args:
        prompt: The prompt to display

    Returns:
        Stripped user input
    """
    return input(prompt).strip()
