"""Gameplay logging service for session transcripts.

This module provides the GameplayLogger class for writing session transcripts
to a log file in JSON Lines format.

Log entry types:
- session_start: Initial state when game session begins
- command: Player command input
- response: Game response text
- state: Game state snapshot (location, health, gold, level)
- ai_content: AI-generated content (location, npc, enemy, quest, dialogue, etc.)
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

    def log_session_start(
        self,
        character_name: str,
        location: str,
        theme: str,
        seed: Optional[int] = None
    ) -> None:
        """Log the start of a game session.

        Args:
            character_name: Name of the player character
            location: Starting location name
            theme: World theme (e.g., "fantasy")
            seed: Optional RNG seed used for reproducibility
        """
        data = {
            "character": character_name,
            "location": location,
            "theme": theme
        }
        if seed is not None:
            data["seed"] = seed
        self._write_entry("session_start", data)

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

    def log_ai_content(
        self,
        generation_type: str,
        prompt_hash: str,
        content: Any,
        raw_response: Optional[str] = None
    ) -> None:
        """Log AI-generated content for review.

        Args:
            generation_type: Type of content generated (e.g., "location", "npc", "quest")
            prompt_hash: SHA256 hash prefix of the prompt (first 16 chars)
            content: The parsed generated content (dict, list, or other serializable object)
            raw_response: Optional raw LLM response for debugging
        """
        data: dict[str, Any] = {
            "generation_type": generation_type,
            "prompt_hash": prompt_hash,
            "content": content,
        }
        if raw_response is not None:
            data["raw_response"] = raw_response
        self._write_entry("ai_content", data)

    def close(self) -> None:
        """Close the log file."""
        self.file.close()
