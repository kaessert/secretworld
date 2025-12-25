# Implementation Summary: JSON Output for Non-Interactive Mode

## What Was Implemented

Added a `--json` flag to the CLI RPG that outputs structured JSON Lines for programmatic consumption.

### New Files
- `src/cli_rpg/json_output.py` - JSON output module with emit functions for each message type

### Modified Files
- `src/cli_rpg/main.py` - Added `--json` argument and `run_json_mode()` function

### New Test File
- `tests/test_json_output.py` - 9 tests covering all spec requirements

## Features

### JSON Message Types
1. **state** - Current game state with location, health, max_health, gold, level
2. **narrative** - Human-readable text (descriptions, action results)
3. **actions** - Available exits, NPCs, and valid commands
4. **error** - Machine-readable error code + human message
5. **combat** - Combat state with enemy name, enemy health, player health

### Key Behaviors
- `--json` implies non-interactive mode (reads commands from stdin)
- ANSI colors are disabled for clean JSON output
- Each line is a valid JSON object
- Errors are classified automatically using pattern matching

### Error Codes
- INVALID_DIRECTION - Moving in invalid direction
- NOT_IN_SHOP - Shop command when not at shop
- ITEM_NOT_FOUND - Item not in inventory
- UNKNOWN_COMMAND - Unrecognized command
- NOT_IN_COMBAT - Combat command outside combat
- IN_CONVERSATION - Movement blocked by conversation
- NO_NPC - Talk command with no NPCs
- INVENTORY_FULL - Inventory capacity reached
- INSUFFICIENT_GOLD - Can't afford purchase

## Test Results

All 9 JSON output tests pass:
- test_json_flag_accepted
- test_json_implies_non_interactive
- test_json_output_valid_lines
- test_json_state_message
- test_json_narrative_message
- test_json_actions_message
- test_json_error_message
- test_json_no_ansi_codes
- test_json_combat_state

Full test suite: 1471 passed, 0 failures

## Usage Example

```bash
echo -e "look\ngo north\nstatus" | cli-rpg --json
```

Output:
```json
{"type": "state", "location": "Town Square", "health": 150, "max_health": 150, "gold": 0, "level": 1}
{"type": "narrative", "text": "=== Town Square ===\nA bustling town square..."}
{"type": "actions", "exits": ["north", "east"], "npcs": ["Town Merchant"], "commands": ["look", "go", ...]}
...
```

## E2E Validation

To validate in production:
1. Run `cli-rpg --json` with piped commands
2. Verify each line parses as valid JSON
3. Check that state/narrative/actions appear after commands
4. Confirm no ANSI codes in output
