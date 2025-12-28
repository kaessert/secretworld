# Implementation Plan: Session Replay from Logged State

## Feature Spec

Add `--replay <log_file>` CLI flag that re-executes commands from a previously logged session, enabling:
1. Deterministic replay using the original RNG seed
2. Validation that game responses match (for debugging regressions)
3. Option to continue interactively from any point in the log

**Entry:** `cli-rpg --replay session.log [--validate] [--continue-at N]`

## Tests First (TDD)

### File: `tests/test_session_replay.py`

```python
# Test 1: --replay flag is accepted
def test_replay_flag_accepted(tmp_path):
    """--replay flag should parse without error."""
    # Create minimal log file with session_start and session_end
    # Run: cli-rpg --replay log_path
    # Assert: exit code 0

# Test 2: replay extracts seed from log
def test_replay_uses_seed_from_log(tmp_path):
    """Replay should use the RNG seed from session_start."""
    # Create log with seed=12345 in session_start
    # Assert: random state is seeded with 12345

# Test 3: replay executes commands from log
def test_replay_executes_commands(tmp_path):
    """Replay should execute commands from log entries."""
    # Create log with: session_start, command("look"), command("status"), session_end
    # Run replay
    # Assert: both commands were executed (via stdout or JSON output)

# Test 4: --validate mode detects state divergence
def test_validate_detects_state_mismatch(tmp_path):
    """--validate should report when replay state differs from log."""
    # Create log with state entry that won't match (e.g., wrong gold value)
    # Run: cli-rpg --replay log --validate
    # Assert: warning/error about state divergence

# Test 5: --continue-at N starts from command N
def test_continue_at_skips_to_command(tmp_path):
    """--continue-at N should skip to command N and continue interactively."""
    # Create log with 5 commands
    # Run: cli-rpg --replay log --continue-at 3
    # Feed additional input after command 3
    # Assert: commands 1-2 were replayed, then interactive mode

# Test 6: replay works with JSON mode
def test_replay_with_json_mode(tmp_path):
    """Replay should work with --json for structured output."""
    # Run: cli-rpg --replay log --json
    # Assert: JSON output emitted for replayed commands
```

## Implementation Steps

### 1. Add CLI argument (`main.py` ~ line 3531)
```python
parser.add_argument(
    "--replay",
    type=str,
    metavar="LOG_FILE",
    help="Replay session from a log file"
)
parser.add_argument(
    "--validate",
    action="store_true",
    help="Validate replay state matches logged state (use with --replay)"
)
parser.add_argument(
    "--continue-at",
    type=int,
    metavar="N",
    help="Continue interactively after replaying N commands (use with --replay)"
)
```

### 2. Create `src/cli_rpg/session_replay.py`

```python
"""Session replay from logged state.

Provides functionality to replay game sessions from JSON Lines log files.
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
```

### 3. Add `run_replay_mode()` function to `main.py`

Location: After `run_json_mode()` function (~ line 3250)

```python
def run_replay_mode(
    log_file: str,
    validate: bool = False,
    continue_at: Optional[int] = None,
    json_output: bool = False
) -> int:
    """Replay a session from a log file.

    Args:
        log_file: Path to the log file to replay
        validate: If True, validate state matches at each step
        continue_at: If set, switch to interactive after N commands
        json_output: If True, emit JSON output instead of text

    Returns:
        Exit code (0 for success, 1 for validation failure)
    """
    from cli_rpg.session_replay import (
        extract_seed, extract_commands, extract_states, validate_state
    )
    from cli_rpg.colors import set_colors_enabled

    # Disable colors for replay (like non-interactive mode)
    set_colors_enabled(False)
    set_effects_enabled(False)
    set_sound_enabled(False)

    # Extract seed and commands from log
    seed = extract_seed(log_file)
    commands = extract_commands(log_file, limit=continue_at)
    states = extract_states(log_file) if validate else []

    # Seed RNG for reproducibility
    import random
    if seed is not None:
        random.seed(seed)

    # Initialize game state (reuse non-interactive setup logic)
    from cli_rpg.models.character import Character, CharacterClass
    character = Character(
        name="Hero",
        character_class=CharacterClass.WARRIOR,
        strength=14, dexterity=10, intelligence=8,
        charisma=10, wisdom=10, perception=10
    )

    # Create world and game state
    ai_config = load_ai_config()
    ai_service = None
    if ai_config:
        try:
            ai_service = AIService(ai_config)
        except Exception:
            pass

    world, starting_location = create_world(ai_service=ai_service, strict=False)
    game_state = GameState(character, world, starting_location=starting_location, ai_service=ai_service)

    # Initialize factions
    from cli_rpg.world import get_default_factions
    game_state.factions = get_default_factions()

    # Replay commands
    state_index = 0
    validation_failures = []

    for i, command_input in enumerate(commands):
        command, args = parse_command(command_input)

        if game_state.is_in_combat():
            continue_game, message = handle_combat_command(game_state, command, args, non_interactive=True)
        else:
            continue_game, message = handle_exploration_command(game_state, command, args, non_interactive=True)

        # Output (JSON or text)
        if json_output:
            emit_narrative(message.strip())
            emit_state(
                location=game_state.current_location,
                health=game_state.current_character.health,
                max_health=game_state.current_character.max_health,
                gold=game_state.current_character.gold,
                level=game_state.current_character.level
            )
        else:
            print(f"[{i+1}/{len(commands)}] > {command_input}")
            print(message.strip())

        # Validate state if enabled
        if validate and state_index < len(states):
            expected = states[state_index]
            actual = {
                "location": game_state.current_location,
                "health": game_state.current_character.health,
                "gold": game_state.current_character.gold,
                "level": game_state.current_character.level
            }
            diffs = validate_state(expected, actual)
            if diffs:
                validation_failures.append((i+1, diffs))
                if json_output:
                    emit_error(code="STATE_MISMATCH", message="; ".join(diffs))
                else:
                    print(f"⚠️  State mismatch at command {i+1}: {'; '.join(diffs)}")
            state_index += 1

        if not continue_game:
            break

    # Continue interactively if requested
    if continue_at and continue_at <= len(commands):
        print(f"\n--- Replay complete. Continuing interactively from command {continue_at} ---\n")
        # Switch to interactive input loop
        for line in sys.stdin:
            command_input = line.strip()
            if not command_input:
                continue
            command, args = parse_command(command_input)
            if game_state.is_in_combat():
                continue_game, message = handle_combat_command(game_state, command, args)
            else:
                continue_game, message = handle_exploration_command(game_state, command, args)
            print(message.strip())
            if not continue_game:
                break

    # Report validation summary
    if validate and validation_failures:
        print(f"\n❌ Validation failed: {len(validation_failures)} state mismatches")
        return 1
    elif validate:
        print(f"\n✓ Validation passed: all states matched")

    return 0
```

### 4. Wire up in `main()` function (~ line 3577)

Add after the `--demo` check:

```python
if parsed_args.replay:
    return run_replay_mode(
        log_file=parsed_args.replay,
        validate=parsed_args.validate,
        continue_at=parsed_args.continue_at,
        json_output=parsed_args.json
    )
```

### 5. Update ISSUES.md

Mark "Enable session replay from logged state" as COMPLETED under Non-interactive mode enhancements.

## Verification

Run tests:
```bash
pytest tests/test_session_replay.py -v
```

Manual verification:
```bash
# Create a session log
echo -e "look\nstatus\ngo north" | cli-rpg --json --skip-character-creation --log-file test.log --seed 42

# Replay it
cli-rpg --replay test.log

# Replay with validation
cli-rpg --replay test.log --validate

# Replay and continue interactively
cli-rpg --replay test.log --continue-at 2
```
