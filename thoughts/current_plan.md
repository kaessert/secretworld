# Issue 23: Dungeon Puzzle Mechanics - Implementation Plan

## Overview

Add interactive puzzle mechanics to dungeons, addressing the "combat-only gameplay" gap. Puzzles include locked doors, levers/pressure plates, riddles, and sequence puzzles. INT stat provides hints.

## Acceptance Criteria (from ISSUES.md)

- [ ] Locked doors requiring keys found in other rooms
- [ ] Pressure plates/levers that open passages
- [ ] Riddle NPCs guarding boss rooms
- [ ] Sequence puzzles (light torches in order)
- [ ] INT stat provides hints for puzzle solving
- [ ] 1-2 puzzles per dungeon area

---

## Spec: Puzzle System

### PuzzleType Enum
```python
class PuzzleType(Enum):
    LOCKED_DOOR = "locked_door"      # Requires specific key item
    LEVER = "lever"                  # Toggle to open passage
    PRESSURE_PLATE = "pressure_plate" # Step on to trigger
    RIDDLE = "riddle"                # Answer correctly to pass
    SEQUENCE = "sequence"            # Activate in correct order
```

### Puzzle Dataclass
```python
@dataclass
class Puzzle:
    puzzle_type: PuzzleType
    name: str                         # e.g., "Rusted Iron Door"
    description: str                  # What player sees
    solved: bool = False
    # Type-specific fields:
    required_key: Optional[str]       # For LOCKED_DOOR
    target_direction: Optional[str]   # Direction passage opens (for lever/plate)
    riddle_text: Optional[str]        # For RIDDLE
    riddle_answer: Optional[str]      # For RIDDLE (case-insensitive)
    sequence_ids: List[str]           # For SEQUENCE - correct order
    sequence_progress: List[str]      # Current player progress
    hint_threshold: int = 14          # INT needed for hint
    hint_text: Optional[str]          # Hint shown if INT >= threshold
```

### Location Integration
- Add `puzzles: List[Puzzle]` field to Location model
- Add `blocked_directions: List[str]` field - directions blocked by unsolved puzzles
- Blocked directions removed from `get_available_directions()` until puzzle solved

### Commands
1. **`examine <puzzle>`** - View puzzle description and get INT-based hints
2. **`use <key> on <door>`** - Use key item to unlock LOCKED_DOOR
3. **`pull <lever>`** - Activate LEVER puzzle
4. **`step <plate>`** - Step on PRESSURE_PLATE
5. **`answer <text>`** - Answer current RIDDLE (when talking to riddle NPC)
6. **`activate <torch/object>`** - For SEQUENCE puzzles

---

## Tests (Write First)

### File: `tests/test_puzzles.py`

```
TestPuzzleModel:
  - test_puzzle_creation_locked_door
  - test_puzzle_creation_lever
  - test_puzzle_creation_riddle
  - test_puzzle_creation_sequence
  - test_puzzle_serialization_roundtrip

TestLockedDoorPuzzle:
  - test_unlock_with_correct_key_removes_from_inventory
  - test_unlock_without_key_fails
  - test_unlock_with_wrong_key_fails
  - test_unlock_reveals_blocked_direction
  - test_already_unlocked_door_message

TestLeverPuzzle:
  - test_pull_lever_opens_passage
  - test_lever_already_activated_message
  - test_lever_passage_direction_added

TestPressurePlatePuzzle:
  - test_step_on_plate_opens_passage
  - test_plate_stays_active_after_step

TestRiddlePuzzle:
  - test_correct_answer_opens_passage
  - test_incorrect_answer_message
  - test_riddle_answer_case_insensitive
  - test_riddle_npc_dialogue_shows_riddle

TestSequencePuzzle:
  - test_correct_sequence_solves_puzzle
  - test_wrong_sequence_resets_progress
  - test_partial_sequence_tracked

TestINTHints:
  - test_high_int_shows_hint
  - test_low_int_no_hint
  - test_hint_threshold_boundary

TestLocationPuzzleIntegration:
  - test_blocked_direction_not_in_exits
  - test_solved_puzzle_restores_direction
  - test_puzzle_serialization_in_location

TestPuzzleGeneration:
  - test_dungeon_generates_1_2_puzzles
  - test_puzzle_placement_not_in_entry_room
  - test_key_placed_in_different_room_than_door
```

---

## Implementation Steps

### Step 1: Create `src/cli_rpg/models/puzzle.py`
- PuzzleType enum
- Puzzle dataclass with all fields
- `to_dict()` / `from_dict()` serialization
- `check_solution()` method for each puzzle type
- `get_hint()` method using INT threshold

### Step 2: Modify `src/cli_rpg/models/location.py`
- Add `puzzles: List[Puzzle]` field (default empty)
- Add `blocked_directions: List[str]` field (default empty)
- Update `get_available_directions()` to filter blocked directions
- Update `to_dict()` / `from_dict()` for puzzles and blocked_directions

### Step 3: Create `src/cli_rpg/puzzles.py` (puzzle logic module)
- `examine_puzzle(char, location, puzzle_name)` - returns description + hint
- `attempt_unlock(char, location, puzzle_name, key_name)` - locked door logic
- `pull_lever(char, location, puzzle_name)` - lever logic
- `step_on_plate(char, location, puzzle_name)` - pressure plate logic
- `answer_riddle(char, location, puzzle_name, answer)` - riddle logic
- `activate_sequence(char, location, puzzle_name, object_name)` - sequence logic
- `solve_puzzle(puzzle, location)` - common solve logic (unblock direction)

### Step 4: Puzzle generation in `src/cli_rpg/ai_world.py`
- Add `_generate_dungeon_puzzles()` function
- Called during SubGrid generation for dungeon/cave/ruins categories
- Placement rules:
  - Locked doors: key in room closer to entry than door
  - Levers/plates: in side rooms, open path to deeper areas
  - Riddles: guarding boss rooms (riddle NPC)
  - Sequences: in larger dungeons (6+ rooms)
- 1-2 puzzles per dungeon (scale with size)

### Step 5: Add commands to `src/cli_rpg/main.py`
- Add to KNOWN_COMMANDS: "examine", "pull", "step", "answer", "activate"
- Add to help text
- Implement `handle_puzzle_command()` dispatcher
- Wire into `handle_exploration_command()`

### Step 6: Update `src/cli_rpg/game_state.py`
- Add puzzle commands to KNOWN_COMMANDS set
- No other changes needed (puzzle state is in Location)

### Step 7: Update `src/cli_rpg/completer.py`
- Add completers for puzzle commands:
  - `examine <tab>` -> puzzle names at location
  - `use <item> on <tab>` -> locked door puzzles
  - `pull <tab>` -> lever puzzles
  - `activate <tab>` -> sequence object names

---

## File Summary

**New Files:**
- `src/cli_rpg/models/puzzle.py` - Puzzle model and types
- `src/cli_rpg/puzzles.py` - Puzzle interaction logic
- `tests/test_puzzles.py` - Comprehensive test suite

**Modified Files:**
- `src/cli_rpg/models/location.py` - Add puzzles field
- `src/cli_rpg/ai_world.py` - Puzzle generation
- `src/cli_rpg/main.py` - Puzzle commands
- `src/cli_rpg/game_state.py` - KNOWN_COMMANDS update
- `src/cli_rpg/completer.py` - Tab completion
