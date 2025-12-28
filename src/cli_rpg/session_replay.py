"""Session replay from logged state.

Provides functionality to replay game sessions from JSON Lines log files.
This enables:
1. Deterministic replay using the original RNG seed
2. Validation that game responses match (for debugging regressions)
3. Option to continue interactively from any point in the log
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Any


@dataclass
class LogEntry:
    """A single log entry from a session log."""
    timestamp: str
    entry_type: str
    data: dict[str, Any]


def parse_log_file(log_path: str) -> Iterator[LogEntry]:
    """Parse a JSON Lines log file into LogEntry objects.

    Args:
        log_path: Path to the log file

    Yields:
        LogEntry for each line in the log
    """
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            yield LogEntry(
                timestamp=entry.get("timestamp", ""),
                entry_type=entry.get("type", ""),
                data=entry
            )


def extract_seed(log_path: str) -> Optional[int]:
    """Extract RNG seed from log file's session_start entry.

    Args:
        log_path: Path to the log file

    Returns:
        The seed if present, None otherwise
    """
    for entry in parse_log_file(log_path):
        if entry.entry_type == "session_start":
            return entry.data.get("seed")
    return None


def extract_commands(log_path: str, limit: Optional[int] = None) -> list[str]:
    """Extract command inputs from log file.

    Args:
        log_path: Path to the log file
        limit: Maximum number of commands to extract (None = all)

    Returns:
        List of command strings
    """
    commands = []
    for entry in parse_log_file(log_path):
        if entry.entry_type == "command":
            commands.append(entry.data.get("input", ""))
            if limit and len(commands) >= limit:
                break
    return commands


@dataclass
class StateSnapshot:
    """Game state snapshot from log for validation."""
    location: str
    health: int
    max_health: int
    gold: int
    level: int


def extract_states(log_path: str) -> list[StateSnapshot]:
    """Extract state snapshots from log file.

    Args:
        log_path: Path to the log file

    Returns:
        List of StateSnapshot objects in log order
    """
    states = []
    for entry in parse_log_file(log_path):
        if entry.entry_type == "state":
            states.append(StateSnapshot(
                location=entry.data.get("location", ""),
                health=entry.data.get("health", 0),
                max_health=entry.data.get("max_health", 0),
                gold=entry.data.get("gold", 0),
                level=entry.data.get("level", 1)
            ))
    return states


def validate_state(expected: StateSnapshot, actual_state: dict) -> list[str]:
    """Compare expected state to actual state and return differences.

    Args:
        expected: StateSnapshot from log
        actual_state: Current game state dict

    Returns:
        List of difference descriptions (empty if match)
    """
    diffs = []
    if expected.location != actual_state.get("location"):
        diffs.append(f"location: expected '{expected.location}', got '{actual_state.get('location')}'")
    if expected.health != actual_state.get("health"):
        diffs.append(f"health: expected {expected.health}, got {actual_state.get('health')}")
    if expected.gold != actual_state.get("gold"):
        diffs.append(f"gold: expected {expected.gold}, got {actual_state.get('gold')}")
    if expected.level != actual_state.get("level"):
        diffs.append(f"level: expected {expected.level}, got {actual_state.get('level')}")
    return diffs
