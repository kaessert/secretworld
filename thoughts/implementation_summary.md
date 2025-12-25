# Implementation Summary: `--log-file` CLI Option

## What Was Implemented

Added the `--log-file <path>` CLI argument for comprehensive gameplay logging with timestamps, commands, responses, and state changes in JSON Lines format.

### New Files Created

1. **`src/cli_rpg/logging_service.py`** - New module containing the `GameplayLogger` class with methods:
   - `log_session_start(character_name, location, theme)` - Logs session initialization
   - `log_command(command)` - Logs player commands
   - `log_response(message)` - Logs game responses
   - `log_state(location, health, max_health, gold, level)` - Logs game state snapshots
   - `log_session_end(reason)` - Logs session termination with reason (eof/quit/death)
   - `close()` - Closes the log file

2. **`tests/test_log_file.py`** - 11 comprehensive tests covering:
   - Flag parsing (`test_log_file_flag_accepted`)
   - File creation (`test_log_file_creates_file`)
   - JSON Lines format validation (`test_log_file_json_lines_format`)
   - ISO 8601 timestamps (`test_log_file_has_timestamp`)
   - Command logging (`test_log_file_logs_commands`)
   - Response logging (`test_log_file_logs_responses`)
   - State change logging (`test_log_file_logs_state_changes`)
   - Compatibility with `--non-interactive` (`test_log_file_works_with_non_interactive`)
   - Compatibility with `--json` (`test_log_file_works_with_json`)
   - Session start entry (`test_log_file_session_start_entry`)
   - Session end entry (`test_log_file_session_end_entry`)

### Modified Files

1. **`src/cli_rpg/main.py`**:
   - Added `--log-file` CLI argument (line ~1360)
   - Updated `run_non_interactive()` to accept `log_file` parameter and integrate logging
   - Updated `run_json_mode()` to accept `log_file` parameter and integrate logging
   - Updated `main()` to pass `log_file` argument to both functions

## Log File Format

Each log entry is a JSON object on a single line (JSON Lines format):

```json
{"timestamp": "2025-01-15T12:00:00.000000+00:00", "type": "session_start", "character": "Agent", "location": "Town Square", "theme": "fantasy"}
{"timestamp": "2025-01-15T12:00:01.000000+00:00", "type": "command", "input": "look"}
{"timestamp": "2025-01-15T12:00:01.100000+00:00", "type": "response", "text": "=== Town Square ===\n..."}
{"timestamp": "2025-01-15T12:00:01.100000+00:00", "type": "state", "location": "Town Square", "health": 100, "max_health": 100, "gold": 50, "level": 1}
{"timestamp": "2025-01-15T12:00:02.000000+00:00", "type": "session_end", "reason": "eof"}
```

## Entry Types

| Type | Description | Fields |
|------|-------------|--------|
| `session_start` | Session initialization | `character`, `location`, `theme` |
| `command` | Player input | `input` |
| `response` | Game output | `text` |
| `state` | Game state snapshot | `location`, `health`, `max_health`, `gold`, `level` |
| `session_end` | Session termination | `reason` (eof/quit/death) |

## Test Results

All 11 new tests pass:
```
tests/test_log_file.py ...........  [100%]
```

Full test suite: **1482 tests passed** (no regressions)

## Usage Examples

```bash
# Basic usage with non-interactive mode
cli-rpg --non-interactive --log-file session.log < commands.txt

# Combined with JSON mode (log file separate from stdout)
cli-rpg --json --log-file transcript.log < commands.txt
```

## E2E Validation

E2E tests should verify:
1. Log file is created at the specified path
2. Log entries are valid JSON Lines
3. Session start entry appears first with correct character/location/theme
4. Commands are logged in order of input
5. Responses match stdout output
6. State entries reflect actual game state changes
7. Session end entry appears last with correct reason
8. Log file works independently from stdout (both `--json` and regular output unaffected)
