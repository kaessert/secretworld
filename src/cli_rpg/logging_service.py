"""Gameplay logging service for session transcripts.

This module provides the GameplayLogger class for writing session transcripts
to a log file in JSON Lines format.

Log entry types:
- session_start: Initial state when game session begins
- command: Player command input
- response: Game response text
- state: Game state snapshot (location, health, gold, level)
- session_end: Final entry when session ends
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class GameplayLogger:
    """Logger for gameplay sessions.

    Writes structured log entries in JSON Lines format to a specified file.
    Each entry includes a timestamp and type field.

    Args:
        log_path: Path to the log file to write
    """

    def __init__(self, log_path: str):
        """Initialize the logger with a file path.

        Args:
            log_path: Path to the log file to create/write
        """
        self.log_path = Path(log_path)
        self.file = open(self.log_path, "w", encoding="utf-8")

    def _write_entry(self, entry_type: str, data: dict[str, Any]) -> None:
        """Write a log entry to the file.

        Args:
            entry_type: The type of log entry (e.g., "command", "response")
            data: Additional data fields for the entry
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": entry_type,
            **data
        }
        self.file.write(json.dumps(entry) + "\n")
        self.file.flush()

    def log_session_start(self, character_name: str, location: str, theme: str) -> None:
        """Log the start of a game session.

        Args:
            character_name: Name of the player character
            location: Starting location name
            theme: World theme (e.g., "fantasy")
        """
        self._write_entry("session_start", {
            "character": character_name,
            "location": location,
            "theme": theme
        })

    def log_command(self, command: str) -> None:
        """Log a player command.

        Args:
            command: The raw command input from the player
        """
        self._write_entry("command", {"input": command})

    def log_response(self, message: str) -> None:
        """Log a game response.

        Args:
            message: The response text from the game
        """
        self._write_entry("response", {"text": message})

    def log_state(
        self,
        location: str,
        health: int,
        max_health: int,
        gold: int,
        level: int
    ) -> None:
        """Log current game state.

        Args:
            location: Current location name
            health: Current health points
            max_health: Maximum health points
            gold: Current gold amount
            level: Character level
        """
        self._write_entry("state", {
            "location": location,
            "health": health,
            "max_health": max_health,
            "gold": gold,
            "level": level
        })

    def log_session_end(self, reason: str) -> None:
        """Log the end of a game session.

        Args:
            reason: Reason for session end (e.g., "eof", "quit", "death")
        """
        self._write_entry("session_end", {"reason": reason})

    def close(self) -> None:
        """Close the log file."""
        self.file.close()
