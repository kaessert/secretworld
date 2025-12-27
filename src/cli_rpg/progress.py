"""Progress indicator module for AI content generation.

This module provides visual progress indicators with thematic messages
during AI generation calls to improve user experience when waiting.
"""

import sys
import threading
import time
from contextlib import contextmanager
from typing import Iterator, Optional, TextIO

from cli_rpg.text_effects import effects_enabled

# ASCII spinner characters (no external dependencies)
SPINNER_CHARS = ["|", "/", "-", "\\"]

# Thematic messages by generation type
GENERATION_MESSAGES = {
    "location": [
        "Weaving ancient tales...",
        "Charting unexplored lands...",
        "Discovering hidden places...",
        "Mapping the unknown...",
        "Unearthing forgotten ruins...",
    ],
    "npc": [
        "Summoning wanderers...",
        "Awakening souls...",
        "Gathering travelers...",
        "Calling forth denizens...",
        "Breathing life into shadows...",
    ],
    "enemy": [
        "Summoning creatures...",
        "Awakening ancient foes...",
        "Stirring darkness...",
        "Conjuring adversaries...",
        "Unleashing beasts...",
    ],
    "lore": [
        "Weaving ancient tales...",
        "Unraveling mysteries...",
        "Consulting the archives...",
        "Deciphering old texts...",
        "Recalling forgotten legends...",
    ],
    "area": [
        "Expanding horizons...",
        "Revealing new lands...",
        "Unveiling territories...",
        "Charting the wilderness...",
        "Discovering new regions...",
    ],
    "item": [
        "Forging treasures...",
        "Crafting artifacts...",
        "Discovering relics...",
        "Unearthing valuables...",
        "Shaping materials...",
    ],
    "quest": [
        "Weaving destinies...",
        "Unfolding adventures...",
        "Charting journeys...",
        "Summoning challenges...",
        "Preparing trials...",
    ],
    "dream": [
        "Drifting into slumber...",
        "Wandering dreamscapes...",
        "Weaving visions...",
        "Entering the ethereal...",
        "Summoning phantasms...",
    ],
    "atmosphere": [
        "Sensing the unseen...",
        "Listening to whispers...",
        "Feeling presences...",
        "Attuning to spirits...",
        "Perceiving echoes...",
    ],
    "art": [
        "Sketching visions...",
        "Rendering forms...",
        "Shaping images...",
        "Drawing essence...",
        "Capturing likeness...",
    ],
    "default": [
        "Generating content...",
        "Processing...",
        "Creating...",
        "Building...",
        "Preparing...",
    ],
}


class ProgressIndicator:
    """Non-blocking progress indicator with spinner and thematic messages.

    Uses threading to display a spinner without blocking the main thread.
    Respects the effects_enabled() setting.

    Usage:
        with progress_indicator("location") as indicator:
            # Do AI generation work
            pass
    """

    def __init__(
        self,
        generation_type: str,
        output: Optional[TextIO] = None,
        spin_delay: float = 0.1,
        message_delay: float = 2.0,
    ):
        """Initialize the progress indicator.

        Args:
            generation_type: Type of generation (location, npc, enemy, lore, area)
            output: Output stream (defaults to sys.stdout)
            spin_delay: Delay between spinner updates in seconds
            message_delay: Delay between message changes in seconds
        """
        self._generation_type = generation_type
        self._output = output if output is not None else sys.stdout
        self._spin_delay = spin_delay
        self._message_delay = message_delay
        self._messages = GENERATION_MESSAGES.get(
            generation_type, GENERATION_MESSAGES["default"]
        )

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the progress indicator thread."""
        with self._lock:
            if self._running:
                return  # Already running, no-op

            # Don't start if effects are disabled
            if not effects_enabled():
                return

            self._running = True
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop the progress indicator and clear the line."""
        with self._lock:
            if not self._running:
                return  # Already stopped, no-op

            self._running = False

        # Wait for thread to finish (outside lock to avoid deadlock)
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        # Clear the progress line if effects were enabled
        if effects_enabled():
            self._clear_line()

    def _spin(self) -> None:
        """Spinner thread loop."""
        spinner_idx = 0
        message_idx = 0
        message_time = time.time()

        while self._running:
            # Get current spinner and message
            spinner = SPINNER_CHARS[spinner_idx % len(SPINNER_CHARS)]
            message = self._messages[message_idx % len(self._messages)]

            # Update display
            line = f"\r{spinner} {message}"
            self._output.write(line)
            self._output.flush()

            # Update indices
            spinner_idx += 1

            # Change message periodically
            if time.time() - message_time >= self._message_delay:
                message_idx += 1
                message_time = time.time()

            # Sleep before next update
            time.sleep(self._spin_delay)

    def _clear_line(self) -> None:
        """Clear the current line."""
        # Write enough spaces to cover any previous message, then return to start
        max_msg_len = max(len(m) for m in self._messages) + 3  # +3 for spinner and spaces
        self._output.write("\r" + " " * max_msg_len + "\r")
        self._output.flush()


@contextmanager
def progress_indicator(
    generation_type: str,
    output: Optional[TextIO] = None,
) -> Iterator[ProgressIndicator]:
    """Context manager for progress indication during AI generation.

    Usage:
        with progress_indicator("location"):
            # Do AI generation work
            pass

    Args:
        generation_type: Type of generation (location, npc, enemy, lore, area)
        output: Output stream (defaults to sys.stdout)

    Yields:
        The ProgressIndicator instance
    """
    indicator = ProgressIndicator(generation_type, output=output)
    indicator.start()
    try:
        yield indicator
    finally:
        indicator.stop()
