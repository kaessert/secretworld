# Implementation Plan: Abandon Quest Command

## Spec

Add an `abandon` command that allows players to remove active quests from their journal. When abandoned:
- Quest is removed from the character's quest list
- Quest status does NOT change to `FAILED` (just removed entirely - `FAILED` status is for future use like failed timed quests)
- Can only abandon `ACTIVE` quests (not `READY_TO_TURN_IN` or `COMPLETED`)
- Works outside of combat (exploration mode only)

## Implementation Steps

### 1. Add `abandon` to known commands
**File:** `src/cli_rpg/game_state.py` (line 65-67)
- Add `"abandon"` to the `known_commands` set

### 2. Add help text for abandon command
**File:** `src/cli_rpg/main.py` (line 33-34, in HELP_TEXT)
- Add: `"  abandon <quest>    - Abandon an active quest from your journal"`

### 3. Implement `abandon_quest` method on Character
**File:** `src/cli_rpg/models/character.py`
- Add method `abandon_quest(self, quest_name: str) -> Tuple[bool, str]`:
  - Find quest by partial name match (case-insensitive), same pattern as `quest` command
  - Only allow abandoning `ACTIVE` status quests
  - Remove quest from `self.quests` list
  - Return `(True, success_message)` or `(False, error_message)`

### 4. Handle `abandon` command in exploration
**File:** `src/cli_rpg/main.py` (in `handle_exploration_command`, after `complete` command handling ~line 760)
- Add `elif command == "abandon":` block:
  - Require quest name argument
  - Call `game_state.current_character.abandon_quest(quest_name)`
  - Return result message

### 5. Block `abandon` in combat
**File:** `src/cli_rpg/main.py` (in `handle_combat_command`)
- Add `abandon` to the list of commands that return "Can't do that during combat"

## Tests

**File:** `tests/test_quest_commands.py` (add at end)

1. `test_parse_abandon_command` - parse_command recognizes "abandon"
2. `test_abandon_quest_removes_active_quest` - abandoning removes from list
3. `test_abandon_quest_not_found` - error for unknown quest
4. `test_abandon_quest_no_args` - prompts for quest name
5. `test_abandon_quest_partial_match` - finds by partial name
6. `test_abandon_cannot_abandon_completed` - error for COMPLETED status
7. `test_abandon_cannot_abandon_ready_to_turn_in` - error for READY_TO_TURN_IN status
8. `test_abandon_blocked_during_combat` - returns combat error
