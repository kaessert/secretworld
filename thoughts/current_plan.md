# Implementation Plan: `--log-file` CLI Option

## Summary
Add `--log-file <path>` CLI argument for comprehensive gameplay logging with timestamps, commands, responses, and state changes.

## Spec

The `--log-file <path>` option writes a complete session transcript to the specified file:
- Timestamps (ISO 8601) for each entry
- Commands issued by player
- Game responses (narrative, errors)
- State changes (location, health, gold, level, combat start/end)
- AI-generated content (if applicable)
- RNG seed (for reproducibility, when deterministic mode is added later)

Format: JSON Lines (one JSON object per line), consistent with `--json` mode structure.

Works in both interactive and non-interactive modes.

## Tests

Create `tests/test_log_file.py`:

1. `test_log_file_flag_accepted` - `--log-file path.log` parses without error
2. `test_log_file_creates_file` - Running with `--log-file` creates the log file
3. `test_log_file_json_lines_format` - Each line in log file is valid JSON
4. `test_log_file_has_timestamp` - Each log entry has ISO 8601 timestamp
5. `test_log_file_logs_commands` - Commands appear in log with type "command"
6. `test_log_file_logs_responses` - Game responses appear in log with type "response"
7. `test_log_file_logs_state_changes` - State changes appear in log with type "state"
8. `test_log_file_works_with_non_interactive` - `--log-file` + `--non-interactive` both work together
9. `test_log_file_works_with_json` - `--log-file` + `--json` both work together (log file separate from stdout JSON)
10. `test_log_file_session_start_entry` - Log includes session_start entry with initial state
11. `test_log_file_session_end_entry` - Log includes session_end entry when game exits

## Implementation

### 1. Create `src/cli_rpg/logging_service.py`

New module for gameplay logging:

```python
"""Gameplay logging service for session transcripts."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

class GameplayLogger:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.file = open(self.log_path, 'w', encoding='utf-8')

    def _write_entry(self, entry_type: str, data: dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": entry_type,
            **data
        }
        self.file.write(json.dumps(entry) + "\n")
        self.file.flush()

    def log_session_start(self, character_name: str, location: str, theme: str) -> None:
        self._write_entry("session_start", {
            "character": character_name,
            "location": location,
            "theme": theme
        })

    def log_command(self, command: str) -> None:
        self._write_entry("command", {"input": command})

    def log_response(self, message: str) -> None:
        self._write_entry("response", {"text": message})

    def log_state(self, location: str, health: int, max_health: int, gold: int, level: int) -> None:
        self._write_entry("state", {
            "location": location,
            "health": health,
            "max_health": max_health,
            "gold": gold,
            "level": level
        })

    def log_session_end(self, reason: str) -> None:
        self._write_entry("session_end", {"reason": reason})

    def close(self) -> None:
        self.file.close()
```

### 2. Update `src/cli_rpg/main.py`

Add CLI argument (after `--json` argument, around line 1358):
```python
parser.add_argument(
    "--log-file",
    type=str,
    metavar="PATH",
    help="Write session transcript to file (JSON Lines format)"
)
```

Pass logger through game loops:
- `run_non_interactive()`: Create logger if `--log-file` specified, pass to game loop
- `run_json_mode()`: Same treatment
- `run_game_loop()`: Accept optional `GameplayLogger`, log commands/responses
- `handle_exploration_command()` / `handle_combat_command()`: No changes needed (return messages, loop logs them)

Key integration points in `run_non_interactive()` and `run_json_mode()`:
1. At function start: Create logger if `log_file` path provided
2. Before stdin loop: `logger.log_session_start(...)`
3. After `parse_command()`: `logger.log_command(command_input)`
4. After getting response: `logger.log_response(message)` and `logger.log_state(...)`
5. At function end: `logger.log_session_end(reason)` and `logger.close()`

### 3. Files to modify

- `src/cli_rpg/main.py`: Add `--log-file` arg, integrate logger into `run_non_interactive()` and `run_json_mode()`
- `src/cli_rpg/logging_service.py`: New file (gameplay logger class)
- `tests/test_log_file.py`: New file (all tests for the feature)
