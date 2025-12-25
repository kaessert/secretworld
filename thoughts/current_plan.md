# Implementation Plan: JSON Output for Non-Interactive Mode

## Spec

Add a `--json` flag to emit structured JSON Lines output that separates game state, narrative text, available actions, and valid commands. Each output is a single JSON object per line.

### JSON Output Schema

Each line is a JSON object with a `type` field indicating the message category:

```json
{"type": "state", "location": "Town Square", "health": 150, "max_health": 150, "gold": 0, "level": 1}
{"type": "narrative", "text": "A bustling town square with a fountain in the center."}
{"type": "actions", "exits": ["north", "east"], "npcs": ["Town Merchant"], "commands": ["look", "go", "status", ...]}
{"type": "error", "code": "INVALID_DIRECTION", "message": "You can't go that way."}
{"type": "combat", "enemy": "Goblin", "enemy_health": 30, "player_health": 150}
```

### Message Types

1. **state** - Emitted after each command with current game state
2. **narrative** - Human-readable text (location descriptions, action results)
3. **actions** - Available actions at current state (exits, NPCs, valid commands)
4. **error** - Error with machine-readable code and human message
5. **combat** - Combat-specific state when in battle

## Tests

File: `tests/test_json_output.py`

1. `test_json_flag_accepted` - `--json` flag parses without error
2. `test_json_implies_non_interactive` - `--json` enables non-interactive mode
3. `test_json_output_valid_lines` - Each line is valid JSON
4. `test_json_state_message` - State message contains location, health, gold, level
5. `test_json_narrative_message` - Narrative type contains text field
6. `test_json_actions_message` - Actions include exits, npcs, commands
7. `test_json_error_message` - Error includes code and message
8. `test_json_combat_state` - Combat state emitted during battle
9. `test_json_no_ansi_codes` - No ANSI escape sequences in JSON output

## Implementation

### 1. Add JSON output module (`src/cli_rpg/json_output.py`)

```python
import json
from typing import List, Optional

# Error codes for machine-readable errors
ERROR_CODES = {
    "invalid_direction": "INVALID_DIRECTION",
    "not_in_shop": "NOT_IN_SHOP",
    "item_not_found": "ITEM_NOT_FOUND",
    "unknown_command": "UNKNOWN_COMMAND",
    "not_in_combat": "NOT_IN_COMBAT",
    "in_conversation": "IN_CONVERSATION",
    "no_npc": "NO_NPC",
    "inventory_full": "INVENTORY_FULL",
    "insufficient_gold": "INSUFFICIENT_GOLD",
}

def emit_state(location: str, health: int, max_health: int, gold: int, level: int) -> None:
    print(json.dumps({
        "type": "state",
        "location": location,
        "health": health,
        "max_health": max_health,
        "gold": gold,
        "level": level
    }))

def emit_narrative(text: str) -> None:
    print(json.dumps({"type": "narrative", "text": text}))

def emit_actions(exits: List[str], npcs: List[str], commands: List[str]) -> None:
    print(json.dumps({
        "type": "actions",
        "exits": exits,
        "npcs": npcs,
        "commands": commands
    }))

def emit_error(code: str, message: str) -> None:
    print(json.dumps({"type": "error", "code": code, "message": message}))

def emit_combat(enemy: str, enemy_health: int, player_health: int) -> None:
    print(json.dumps({
        "type": "combat",
        "enemy": enemy,
        "enemy_health": enemy_health,
        "player_health": player_health
    }))
```

### 2. Add `--json` flag to argparse in `main.py` (line ~1230)

```python
parser.add_argument(
    "--json",
    action="store_true",
    help="Output structured JSON Lines (implies --non-interactive)"
)
```

### 3. Create `run_json_mode()` in `main.py`

New function that:
- Disables ANSI colors
- Creates default character and world (same as non-interactive)
- Emits initial state + actions
- Processes stdin commands
- For each command:
  - Parse and execute (reusing handle_exploration_command/handle_combat_command)
  - Parse response to determine if error or narrative
  - Emit appropriate JSON (state, narrative, error, combat, actions)

### 4. Update `main()` to route to JSON mode (after line 1237)

```python
if parsed_args.json:
    return run_json_mode()
```

### 5. Helper: classify output and extract error codes

Add function to detect error patterns and map to codes:
```python
def classify_output(message: str) -> tuple[str, Optional[str]]:
    """Classify command output as error or narrative.

    Returns: (type, error_code) where type is 'error' or 'narrative'
    """
    error_patterns = {
        "You can't go that way": "INVALID_DIRECTION",
        "Invalid direction": "INVALID_DIRECTION",
        "You're not at a shop": "NOT_IN_SHOP",
        "Unknown command": "UNKNOWN_COMMAND",
        # ...
    }
    for pattern, code in error_patterns.items():
        if pattern in message:
            return ("error", code)
    return ("narrative", None)
```

## File Changes

1. **New**: `src/cli_rpg/json_output.py` - JSON output helpers and error codes
2. **New**: `tests/test_json_output.py` - Tests for JSON output mode
3. **Modify**: `src/cli_rpg/main.py` - Add `--json` flag and `run_json_mode()` function

## Steps

1. Create `tests/test_json_output.py` with spec tests
2. Run tests (should fail - no implementation)
3. Create `src/cli_rpg/json_output.py` with emit functions
4. Add `--json` flag and `run_json_mode()` to `main.py`
5. Run tests (should pass)
6. Run full test suite to verify no regressions
