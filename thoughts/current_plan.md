# Issue 23: Dungeon Puzzle Mechanics - Command Integration

## Status
Steps 1-4 complete (Puzzle model, Location integration, puzzles.py logic, tests). This plan covers remaining command integration (Steps 5-7).

## Spec: Commands to Add
Commands from CLAUDE.md: `unlock`, `pull`, `step`, `answer`, `activate`

```python
# main.py handle_exploration_command additions:
unlock <puzzle> <key>  -> attempt_unlock()   # Unlock locked door with key
pull <puzzle>          -> pull_lever()       # Pull a lever puzzle
step <puzzle>          -> step_on_plate()    # Step on pressure plate
answer <puzzle> <text> -> answer_riddle()    # Answer riddle
activate <puzzle> <id> -> activate_sequence() # Activate sequence object
```

## Tests

### File: `tests/test_puzzle_commands.py`
```python
TestUnlockCommand:
  - test_unlock_locked_door_success
  - test_unlock_missing_key_fails
  - test_unlock_wrong_key_fails
  - test_unlock_not_locked_door_fails

TestPullCommand:
  - test_pull_lever_success
  - test_pull_not_lever_fails

TestStepCommand:
  - test_step_pressure_plate_success
  - test_step_not_plate_fails

TestAnswerCommand:
  - test_answer_riddle_correct
  - test_answer_riddle_wrong

TestActivateCommand:
  - test_activate_sequence_step_success
  - test_activate_wrong_order_resets
  - test_activate_completes_sequence
```

## Implementation Steps

### Step 1: Add commands to KNOWN_COMMANDS in game_state.py
```python
# Add to KNOWN_COMMANDS set (line ~71):
"unlock", "pull", "step", "answer", "activate"
```

### Step 2: Add command handlers in main.py
Location: `handle_exploration_command()` (after line ~2535 "elif command == 'unknown'")

```python
elif command == "unlock":
    if len(args) < 2:
        return (True, "Usage: unlock <door> <key>")
    door_name = args[0]
    key_name = " ".join(args[1:])
    from cli_rpg.puzzles import attempt_unlock
    location = game_state.get_current_location()
    success, msg = attempt_unlock(game_state.current_character, location, door_name, key_name)
    return (True, msg)

elif command == "pull":
    if not args:
        return (True, "Pull what? Usage: pull <lever>")
    lever_name = " ".join(args)
    from cli_rpg.puzzles import pull_lever
    location = game_state.get_current_location()
    success, msg = pull_lever(game_state.current_character, location, lever_name)
    return (True, msg)

elif command == "step":
    if not args:
        return (True, "Step on what? Usage: step <plate>")
    plate_name = " ".join(args)
    from cli_rpg.puzzles import step_on_plate
    location = game_state.get_current_location()
    success, msg = step_on_plate(game_state.current_character, location, plate_name)
    return (True, msg)

elif command == "answer":
    if len(args) < 2:
        return (True, "Usage: answer <puzzle> <answer text>")
    puzzle_name = args[0]
    answer_text = " ".join(args[1:])
    from cli_rpg.puzzles import answer_riddle
    location = game_state.get_current_location()
    success, msg = answer_riddle(game_state.current_character, location, puzzle_name, answer_text)
    return (True, msg)

elif command == "activate":
    if len(args) < 2:
        return (True, "Usage: activate <puzzle> <object>")
    puzzle_name = args[0]
    object_id = args[1]
    from cli_rpg.puzzles import activate_sequence
    location = game_state.get_current_location()
    success, msg = activate_sequence(game_state.current_character, location, puzzle_name, object_id)
    return (True, msg)
```

### Step 3: Add tab completion in completer.py
Add to `_complete_argument()` method:
```python
elif command == "unlock":
    return self._complete_puzzle_by_type(text_lower, PuzzleType.LOCKED_DOOR)
elif command == "pull":
    return self._complete_puzzle_by_type(text_lower, PuzzleType.LEVER)
elif command == "step":
    return self._complete_puzzle_by_type(text_lower, PuzzleType.PRESSURE_PLATE)
elif command == "answer":
    return self._complete_puzzle_by_type(text_lower, PuzzleType.RIDDLE)
elif command == "activate":
    return self._complete_puzzle_by_type(text_lower, PuzzleType.SEQUENCE)
```

Add helper method:
```python
def _complete_puzzle_by_type(self, text: str, puzzle_type: Optional["PuzzleType"] = None) -> List[str]:
    """Complete puzzle names filtered by type."""
    if self._game_state is None:
        return []
    location = self._game_state.get_current_location()
    names = []
    for puzzle in location.puzzles:
        if puzzle_type is None or puzzle.puzzle_type == puzzle_type:
            if not puzzle.solved:
                names.append(puzzle.name)
    return [n for n in names if n.lower().startswith(text)]
```

### Step 4: Integrate blocked_directions in location exit display
Modify `get_available_directions()` in location.py OR use existing `filter_blocked_directions()` in location description.

Check: `get_filtered_directions()` in location.py should call `filter_blocked_directions()`:
```python
# After getting directions, filter blocked ones:
from cli_rpg.puzzles import filter_blocked_directions
directions = filter_blocked_directions(directions, self.blocked_directions)
```

### Step 5: Block movement in game_state.py _move_in_sub_grid()
Before moving to target, check if direction is blocked:
```python
if direction in current.blocked_directions:
    return (False, f"The way {direction} is blocked by a puzzle.")
```

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/game_state.py` | Add 5 commands to KNOWN_COMMANDS, block movement on blocked_directions |
| `src/cli_rpg/main.py` | Add 5 command handlers to handle_exploration_command() |
| `src/cli_rpg/completer.py` | Add puzzle tab completion |
| `src/cli_rpg/models/location.py` | Filter blocked_directions in get_available_directions() |
| `tests/test_puzzle_commands.py` | New test file for command integration |
