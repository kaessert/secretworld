"""Puzzle interaction logic for dungeon puzzle mechanics (Issue #23).

Provides functions for interacting with puzzles in dungeons:
- Examining puzzles (with INT-based hints)
- Unlocking locked doors with keys
- Pulling levers
- Stepping on pressure plates
- Answering riddles
- Activating sequence puzzles
"""

from typing import List, Optional, Tuple, TYPE_CHECKING

from cli_rpg.models.puzzle import Puzzle, PuzzleType

if TYPE_CHECKING:
    from cli_rpg.models.character import Character
    from cli_rpg.models.location import Location


def find_puzzle_by_name(location: "Location", puzzle_name: str) -> Optional[Puzzle]:
    """Find a puzzle by name in a location (case-insensitive).

    Args:
        location: The location to search in
        puzzle_name: Name of the puzzle to find

    Returns:
        The Puzzle if found, None otherwise
    """
    name_lower = puzzle_name.lower()
    for puzzle in location.puzzles:
        if puzzle.name.lower() == name_lower:
            return puzzle
    return None


def filter_blocked_directions(
    available_directions: List[str], blocked_directions: List[str]
) -> List[str]:
    """Filter out blocked directions from available directions.

    Args:
        available_directions: List of available direction names
        blocked_directions: List of blocked direction names

    Returns:
        List of directions that are not blocked
    """
    blocked_set = set(d.lower() for d in blocked_directions)
    return [d for d in available_directions if d.lower() not in blocked_set]


def solve_puzzle(puzzle: Puzzle, location: "Location") -> None:
    """Mark a puzzle as solved and unblock its direction.

    Args:
        puzzle: The puzzle to solve
        location: The location containing the puzzle
    """
    puzzle.solved = True
    if puzzle.target_direction and puzzle.target_direction in location.blocked_directions:
        location.blocked_directions.remove(puzzle.target_direction)


def examine_puzzle(char: "Character", puzzle: Puzzle) -> str:
    """Examine a puzzle and get description plus INT-based hints.

    Args:
        char: The character examining the puzzle
        puzzle: The puzzle to examine

    Returns:
        Description and hint (if INT is high enough)
    """
    result = f"{puzzle.name}\n{puzzle.description}"

    # Show riddle text for riddle puzzles
    if puzzle.puzzle_type == PuzzleType.RIDDLE and puzzle.riddle_text:
        result += f'\n\nThe riddle: "{puzzle.riddle_text}"'

    # Show sequence objects for sequence puzzles
    if puzzle.puzzle_type == PuzzleType.SEQUENCE and puzzle.sequence_ids:
        objects = ", ".join(puzzle.sequence_ids)
        result += f"\n\nObjects: {objects}"
        if puzzle.sequence_progress:
            progress = ", ".join(puzzle.sequence_progress)
            result += f"\nActivated: {progress}"

    # Add hint if INT is high enough
    hint = puzzle.get_hint(char.intelligence)
    if hint:
        result += f"\n\n[Insight] {hint}"

    return result


def attempt_unlock(
    char: "Character",
    location: "Location",
    puzzle_name: str,
    key_name: str,
) -> Tuple[bool, str]:
    """Attempt to unlock a locked door puzzle with a key.

    Args:
        char: The character attempting to unlock
        location: The location with the puzzle
        puzzle_name: Name of the locked door puzzle
        key_name: Name of the key to use

    Returns:
        Tuple of (success, message)
    """
    puzzle = find_puzzle_by_name(location, puzzle_name)
    if puzzle is None:
        return (False, f"There is no '{puzzle_name}' here.")

    if puzzle.puzzle_type != PuzzleType.LOCKED_DOOR:
        return (False, f"The {puzzle.name} is not a locked door.")

    if puzzle.solved:
        return (False, f"The {puzzle.name} is already unlocked.")

    # Check if player has the key
    key_item = char.inventory.find_item_by_name(key_name)
    if key_item is None:
        return (False, f"You don't have a '{key_name}'.")

    # Check if it's the correct key
    if puzzle.required_key and key_item.name.lower() != puzzle.required_key.lower():
        return (False, f"The {key_item.name} doesn't fit this lock.")

    # Unlock the door
    char.inventory.remove_item(key_item)
    solve_puzzle(puzzle, location)

    direction_msg = ""
    if puzzle.target_direction:
        direction_msg = f" The way {puzzle.target_direction} is now open."

    return (True, f"You unlock the {puzzle.name} with the {key_item.name}.{direction_msg}")


def pull_lever(
    char: "Character",
    location: "Location",
    puzzle_name: str,
) -> Tuple[bool, str]:
    """Pull a lever puzzle.

    Args:
        char: The character pulling the lever
        location: The location with the puzzle
        puzzle_name: Name of the lever puzzle

    Returns:
        Tuple of (success, message)
    """
    puzzle = find_puzzle_by_name(location, puzzle_name)
    if puzzle is None:
        return (False, f"There is no '{puzzle_name}' here.")

    if puzzle.puzzle_type != PuzzleType.LEVER:
        return (False, f"The {puzzle.name} is not a lever.")

    if puzzle.solved:
        return (False, f"The {puzzle.name} has already been activated.")

    # Pull the lever
    solve_puzzle(puzzle, location)

    direction_msg = ""
    if puzzle.target_direction:
        direction_msg = f" A passage opens to the {puzzle.target_direction}!"

    return (True, f"You pull the {puzzle.name}. You hear a grinding of stone.{direction_msg}")


def step_on_plate(
    char: "Character",
    location: "Location",
    puzzle_name: str,
) -> Tuple[bool, str]:
    """Step on a pressure plate puzzle.

    Args:
        char: The character stepping on the plate
        location: The location with the puzzle
        puzzle_name: Name of the pressure plate puzzle

    Returns:
        Tuple of (success, message)
    """
    puzzle = find_puzzle_by_name(location, puzzle_name)
    if puzzle is None:
        return (False, f"There is no '{puzzle_name}' here.")

    if puzzle.puzzle_type != PuzzleType.PRESSURE_PLATE:
        return (False, f"The {puzzle.name} is not a pressure plate.")

    if puzzle.solved:
        return (False, f"The {puzzle.name} has already been activated.")

    # Step on the plate
    solve_puzzle(puzzle, location)

    direction_msg = ""
    if puzzle.target_direction:
        direction_msg = f" A passage opens to the {puzzle.target_direction}!"

    return (
        True,
        f"You step on the {puzzle.name}. It clicks and sinks into the floor.{direction_msg}",
    )


def answer_riddle(
    char: "Character",
    location: "Location",
    puzzle_name: str,
    answer: str,
) -> Tuple[bool, str]:
    """Answer a riddle puzzle.

    Args:
        char: The character answering the riddle
        location: The location with the puzzle
        puzzle_name: Name of the riddle puzzle
        answer: The answer to the riddle

    Returns:
        Tuple of (success, message)
    """
    puzzle = find_puzzle_by_name(location, puzzle_name)
    if puzzle is None:
        return (False, f"There is no '{puzzle_name}' here.")

    if puzzle.puzzle_type != PuzzleType.RIDDLE:
        return (False, f"The {puzzle.name} doesn't pose riddles.")

    if puzzle.solved:
        return (False, f"You have already solved the {puzzle.name}'s riddle.")

    # Check the answer
    if puzzle.check_riddle_answer(answer):
        solve_puzzle(puzzle, location)
        direction_msg = ""
        if puzzle.target_direction:
            direction_msg = f" The way {puzzle.target_direction} is now open."
        return (True, f'"Correct," says the {puzzle.name}.{direction_msg}')
    else:
        return (False, f'"Wrong," says the {puzzle.name}. "That is not the answer."')


def activate_sequence(
    char: "Character",
    location: "Location",
    puzzle_name: str,
    object_id: str,
) -> Tuple[bool, str]:
    """Activate an object in a sequence puzzle.

    Args:
        char: The character activating the object
        location: The location with the puzzle
        puzzle_name: Name of the sequence puzzle
        object_id: ID of the object to activate

    Returns:
        Tuple of (success, message)
    """
    puzzle = find_puzzle_by_name(location, puzzle_name)
    if puzzle is None:
        return (False, f"There is no '{puzzle_name}' here.")

    if puzzle.puzzle_type != PuzzleType.SEQUENCE:
        return (False, f"The {puzzle.name} is not a sequence puzzle.")

    if puzzle.solved:
        return (False, f"The {puzzle.name} has already been solved.")

    # Check if object is valid
    if object_id not in puzzle.sequence_ids:
        return (False, f"There is no '{object_id}' in this puzzle.")

    # Try to add the step
    if puzzle.add_sequence_step(object_id):
        # Check if sequence is complete
        if puzzle.is_sequence_complete():
            solve_puzzle(puzzle, location)
            direction_msg = ""
            if puzzle.target_direction:
                direction_msg = f" A passage opens to the {puzzle.target_direction}!"
            return (
                True,
                f"You activate {object_id}. The sequence is complete!{direction_msg}",
            )
        else:
            progress = len(puzzle.sequence_progress)
            total = len(puzzle.sequence_ids)
            return (True, f"You activate {object_id}. ({progress}/{total})")
    else:
        return (
            False,
            f"You activate {object_id}, but something resets! The sequence was wrong.",
        )
