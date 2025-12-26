# Implementation Plan: Enter/Exit Commands for Hierarchical World Navigation

## Overview
Implement `enter <landmark>` and `exit/leave` commands in `game_state.py` to navigate between overworld locations and their sub-locations.

## Spec

### Enter Command
- **Trigger**: `enter <location_name>` when at an overworld location
- **Behavior**:
  1. Validate current location is overworld (`is_overworld=True`)
  2. Find sub-location matching name (case-insensitive, partial match)
  3. If location has `entry_point`, use that as default when no argument given
  4. Move player to the sub-location
  5. Return success message with `look()` at new location
- **Errors**:
  - "You're not at an overworld location" if `is_overworld=False`
  - "No such location: <name>" if sub-location not found
  - "Enter where?" if no argument and no `entry_point`

### Exit/Leave Command
- **Trigger**: `exit` or `leave` when at a sub-location
- **Behavior**:
  1. Validate current location has `parent_location` set
  2. Move player to the parent location
  3. Return success message with `look()` at parent
- **Errors**:
  - "You're not inside a landmark" if `parent_location` is None
  - "You're in a conversation. Say 'bye' to leave first." if in conversation

### Command Registration
- Add `enter`, `exit`, `leave` to `KNOWN_COMMANDS` set in `game_state.py`
- Add command handlers in `main.py`
- Update help text in `get_command_reference()`

---

## Tests (`tests/test_game_state.py`)

### Enter Command Tests
1. `test_enter_sublocation_from_overworld` - enter valid sub-location succeeds
2. `test_enter_uses_entry_point_default` - enter with no arg uses `entry_point`
3. `test_enter_partial_match` - partial name matching works (case-insensitive)
4. `test_enter_fails_when_not_overworld` - error when current location not overworld
5. `test_enter_fails_sublocation_not_found` - error when target doesn't exist
6. `test_enter_fails_no_arg_no_entrypoint` - error when no arg and no entry_point
7. `test_enter_blocked_during_conversation` - returns conversation warning

### Exit Command Tests
8. `test_exit_from_sublocation` - exit returns to parent location
9. `test_exit_fails_when_no_parent` - error when not in sub-location
10. `test_exit_blocked_during_conversation` - returns conversation warning
11. `test_leave_alias_works` - "leave" works same as "exit"

---

## Implementation Steps

### Step 1: Update `game_state.py` - Add KNOWN_COMMANDS
```python
# In KNOWN_COMMANDS set, add:
"enter", "exit", "leave"
```

### Step 2: Add `enter()` method to `GameState` class
Location: After the `move()` method (~line 580)
```python
def enter(self, target_name: Optional[str] = None) -> tuple[bool, str]:
    """Enter a sub-location within the current overworld landmark."""
```

### Step 3: Add `exit_location()` method to `GameState` class
```python
def exit_location(self) -> tuple[bool, str]:
    """Exit from a sub-location back to the parent overworld landmark."""
```

### Step 4: Update `main.py` - Add command handlers
Location: In `handle_command()` function, after "go" handler (~line 522)
```python
elif command == "enter":
    # Call game_state.enter(args[0] if args else None)

elif command in ("exit", "leave"):
    # Call game_state.exit_location()
```

### Step 5: Update `main.py` - Add help text
Location: In `get_command_reference()` (~line 30)
```python
"  enter <location>   - Enter a landmark (city, dungeon, etc.)",
"  exit / leave       - Exit back to the overworld",
```

### Step 6: Write tests first (TDD)
Create tests in `tests/test_game_state.py` in new `TestEnterExitCommands` class

---

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/game_state.py` | Add `enter`, `exit`, `leave` to KNOWN_COMMANDS; add `enter()` and `exit_location()` methods |
| `src/cli_rpg/main.py` | Add command handlers for `enter`, `exit`, `leave`; update help text |
| `tests/test_game_state.py` | Add `TestEnterExitCommands` test class with 11 tests |
