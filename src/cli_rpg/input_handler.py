"""Input handler with readline integration for command history and tab completion.

Provides enhanced input with up/down arrow history navigation,
persistent history across sessions, and tab auto-completion.

Spec requirements:
1. Up arrow scrolls back through previous commands
2. Down arrow scrolls forward through history
3. History persists across sessions (saved to file)
4. Configurable history size (default: 500 commands)
5. Fallback to basic input if readline unavailable
6. Tab completion for commands and contextual arguments
"""
import atexit
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from cli_rpg.completer import completer

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState

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
    """Initialize readline with history support and tab completion.

    Loads existing history from file if it exists,
    sets history length, configures tab completion,
    and registers cleanup handler.

    Spec requirements 1, 2, 3: Enable arrow key navigation
    and persistent history.
    Spec requirement 6: Enable tab completion.
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

        # Set up tab completion - Spec requirement 6
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
        # Set word delimiters for proper completion of multi-word arguments
        readline.set_completer_delims(" \t\n")

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


def set_completer_context(game_state: Optional["GameState"]) -> None:
    """Update completer with current game state for contextual completions.

    Call this when game state is created or changes, and with None
    when exiting the game loop.

    Args:
        game_state: The current GameState, or None to disable contextual completion
    """
    completer.set_game_state(game_state)
