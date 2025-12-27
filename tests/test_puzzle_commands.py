"""Tests for puzzle command integration (Issue #23, Step 5-7).

Tests cover command handlers in main.py:
- unlock <door> <key>: Unlock locked doors with keys
- pull <lever>: Pull lever puzzles
- step <plate>: Step on pressure plates
- answer <puzzle> <text>: Answer riddles
- activate <puzzle> <id>: Activate sequence puzzle steps
- Movement blocking by puzzles
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.location import Location
from cli_rpg.models.puzzle import Puzzle, PuzzleType
from cli_rpg.game_state import GameState


def create_test_game_state_with_puzzle(puzzle: Puzzle, blocked_directions: list[str] = None) -> GameState:
    """Create a GameState with a location containing the given puzzle."""
    if blocked_directions is None:
        blocked_directions = []

    char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
    location = Location(
        name="Dungeon Hall",
        description="A dark dungeon hall.",
        puzzles=[puzzle],
        blocked_directions=blocked_directions,
    )

    game_state = GameState(
        character=char,
        world={location.name: location},
        starting_location=location.name,
    )
    return game_state


class TestUnlockCommand:
    """Test the 'unlock' command handler."""

    # Spec: unlock <door> <key> - unlock locked door with correct key
    def test_unlock_locked_door_success(self):
        """Unlock command works with correct key."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy iron door.",
            required_key="Iron Key",
            target_direction="north",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["north"])

        # Add the key to inventory
        key = Item(name="Iron Key", description="A rusty iron key", item_type=ItemType.MISC)
        game_state.current_character.inventory.add_item(key)

        continue_game, message = handle_exploration_command(game_state, "unlock", ["Iron Door", "Iron", "Key"])

        assert continue_game
        assert "unlock" in message.lower()
        assert puzzle.solved

    # Spec: unlock without key fails
    def test_unlock_missing_key_fails(self):
        """Unlock command fails when key is not in inventory."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy iron door.",
            required_key="Iron Key",
            target_direction="north",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["north"])

        continue_game, message = handle_exploration_command(game_state, "unlock", ["Iron Door", "Iron", "Key"])

        assert continue_game
        assert "don't have" in message.lower()
        assert not puzzle.solved

    # Spec: unlock with wrong key fails
    def test_unlock_wrong_key_fails(self):
        """Unlock command fails with wrong key."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy iron door.",
            required_key="Iron Key",
            target_direction="north",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["north"])

        # Add wrong key
        wrong_key = Item(name="Silver Key", description="A shiny key", item_type=ItemType.MISC)
        game_state.current_character.inventory.add_item(wrong_key)

        continue_game, message = handle_exploration_command(game_state, "unlock", ["Iron Door", "Silver", "Key"])

        assert continue_game
        assert "doesn't fit" in message.lower()
        assert not puzzle.solved

    # Spec: unlock non-locked-door puzzle fails
    def test_unlock_not_locked_door_fails(self):
        """Unlock command fails on non-locked-door puzzles."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Wall Lever",
            description="A lever on the wall.",
            target_direction="north",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["north"])

        key = Item(name="Iron Key", description="A key", item_type=ItemType.MISC)
        game_state.current_character.inventory.add_item(key)

        continue_game, message = handle_exploration_command(game_state, "unlock", ["Wall Lever", "Iron", "Key"])

        assert continue_game
        assert "not a locked door" in message.lower()


class TestPullCommand:
    """Test the 'pull' command handler."""

    # Spec: pull <lever> - pull lever puzzle successfully
    def test_pull_lever_success(self):
        """Pull command works on lever puzzles."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Stone Lever",
            description="A stone lever.",
            target_direction="east",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["east"])

        continue_game, message = handle_exploration_command(game_state, "pull", ["Stone", "Lever"])

        assert continue_game
        assert "pull" in message.lower() or "grinding" in message.lower()
        assert puzzle.solved

    # Spec: pull non-lever puzzle fails
    def test_pull_not_lever_fails(self):
        """Pull command fails on non-lever puzzles."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.PRESSURE_PLATE,
            name="Stone Plate",
            description="A pressure plate.",
            target_direction="east",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["east"])

        continue_game, message = handle_exploration_command(game_state, "pull", ["Stone", "Plate"])

        assert continue_game
        assert "not a lever" in message.lower()


class TestStepCommand:
    """Test the 'step' command handler."""

    # Spec: step <plate> - step on pressure plate successfully
    def test_step_pressure_plate_success(self):
        """Step command works on pressure plate puzzles."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.PRESSURE_PLATE,
            name="Floor Plate",
            description="A pressure plate in the floor.",
            target_direction="north",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["north"])

        continue_game, message = handle_exploration_command(game_state, "step", ["Floor", "Plate"])

        assert continue_game
        assert "step" in message.lower() or "click" in message.lower()
        assert puzzle.solved

    # Spec: step non-pressure-plate puzzle fails
    def test_step_not_plate_fails(self):
        """Step command fails on non-pressure-plate puzzles."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Wall Lever",
            description="A lever.",
            target_direction="north",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["north"])

        continue_game, message = handle_exploration_command(game_state, "step", ["Wall", "Lever"])

        assert continue_game
        assert "not a pressure plate" in message.lower()


class TestAnswerCommand:
    """Test the 'answer' command handler."""

    # Spec: answer <puzzle> <text> - correct answer solves riddle
    def test_answer_riddle_correct(self):
        """Answer command solves riddle with correct answer."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Stone Sphinx",
            description="A sphinx blocks the way.",
            riddle_text="What has keys but no locks?",
            riddle_answer="piano",
            target_direction="south",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["south"])

        continue_game, message = handle_exploration_command(game_state, "answer", ["Stone Sphinx", "piano"])

        assert continue_game
        assert "correct" in message.lower()
        assert puzzle.solved

    # Spec: answer with wrong answer fails
    def test_answer_riddle_wrong(self):
        """Answer command fails with wrong answer."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Stone Sphinx",
            description="A sphinx blocks the way.",
            riddle_text="What has keys but no locks?",
            riddle_answer="piano",
            target_direction="south",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["south"])

        continue_game, message = handle_exploration_command(game_state, "answer", ["Stone Sphinx", "door"])

        assert continue_game
        assert "wrong" in message.lower()
        assert not puzzle.solved


class TestActivateCommand:
    """Test the 'activate' command handler."""

    # Spec: activate <puzzle> <id> - activate sequence step correctly
    def test_activate_sequence_step_success(self):
        """Activate command adds correct step to sequence."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Row",
            description="Four torches on the wall.",
            sequence_ids=["torch_1", "torch_2", "torch_3"],
            target_direction="west",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["west"])

        continue_game, message = handle_exploration_command(game_state, "activate", ["Torch Row", "torch_1"])

        assert continue_game
        assert "activate" in message.lower() or "1/3" in message
        assert puzzle.sequence_progress == ["torch_1"]

    # Spec: activate wrong order resets sequence
    def test_activate_wrong_order_resets(self):
        """Activate command resets progress on wrong order."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Row",
            description="Four torches on the wall.",
            sequence_ids=["torch_1", "torch_2", "torch_3"],
            target_direction="west",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["west"])

        # Add first step correctly
        handle_exploration_command(game_state, "activate", ["Torch Row", "torch_1"])
        assert puzzle.sequence_progress == ["torch_1"]

        # Wrong step resets
        continue_game, message = handle_exploration_command(game_state, "activate", ["Torch Row", "torch_3"])

        assert continue_game
        assert "reset" in message.lower() or "wrong" in message.lower()
        assert puzzle.sequence_progress == []

    # Spec: activate completes sequence and solves puzzle
    def test_activate_completes_sequence(self):
        """Activate command completes sequence and solves puzzle."""
        from cli_rpg.main import handle_exploration_command

        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Row",
            description="Four torches on the wall.",
            sequence_ids=["torch_1", "torch_2", "torch_3"],
            target_direction="west",
        )
        game_state = create_test_game_state_with_puzzle(puzzle, ["west"])

        handle_exploration_command(game_state, "activate", ["Torch Row", "torch_1"])
        handle_exploration_command(game_state, "activate", ["Torch Row", "torch_2"])
        continue_game, message = handle_exploration_command(game_state, "activate", ["Torch Row", "torch_3"])

        assert continue_game
        assert "complete" in message.lower()
        assert puzzle.solved


class TestMovementBlocking:
    """Test that blocked_directions blocks movement."""

    # Spec: Movement in blocked direction should fail
    def test_movement_blocked_by_puzzle(self):
        """Movement is blocked when puzzle blocks direction."""
        from cli_rpg.world_grid import SubGrid

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A locked door.",
            required_key="Iron Key",
            target_direction="north",
        )

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Create locations with coordinates
        center = Location(
            name="Center Room",
            description="Center.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )
        north_room = Location(
            name="North Room",
            description="North.",
        )
        # Need a dummy overworld location for GameState
        overworld = Location(name="Overworld", description="Overworld.")

        # Create SubGrid and add locations
        sub_grid = SubGrid(bounds=(0, 2, 0, 2, 0, 0))
        sub_grid.add_location(center, x=1, y=1, z=0)
        sub_grid.add_location(north_room, x=1, y=2, z=0)

        # Create game state in sub-location mode
        game_state = GameState(
            character=char,
            world={"Overworld": overworld},
            starting_location="Overworld",
        )
        game_state.current_location = center.name
        game_state.in_sub_location = True
        game_state.current_sub_grid = sub_grid

        # Try to move north (should be blocked)
        success, message = game_state.move("north")

        assert not success
        assert "blocked" in message.lower()

    # Spec: Movement allowed after puzzle solved
    def test_movement_allowed_after_puzzle_solved(self):
        """Movement is allowed after puzzle is solved."""
        from cli_rpg.world_grid import SubGrid
        from cli_rpg.puzzles import solve_puzzle

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A locked door.",
            required_key="Iron Key",
            target_direction="north",
        )

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        center = Location(
            name="Center Room",
            description="Center.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )
        north_room = Location(
            name="North Room",
            description="North.",
        )
        # Need a dummy overworld location for GameState
        overworld = Location(name="Overworld", description="Overworld.")

        sub_grid = SubGrid(bounds=(0, 2, 0, 2, 0, 0))
        sub_grid.add_location(center, x=1, y=1, z=0)
        sub_grid.add_location(north_room, x=1, y=2, z=0)

        game_state = GameState(
            character=char,
            world={"Overworld": overworld},
            starting_location="Overworld",
        )
        game_state.current_location = center.name
        game_state.in_sub_location = True
        game_state.current_sub_grid = sub_grid

        # Solve the puzzle (removes block)
        solve_puzzle(puzzle, center)
        assert "north" not in center.blocked_directions

        # Now movement should work
        success, message = game_state.move("north")

        assert success
        assert "North Room" in message or "north" in message.lower()


class TestPuzzleCommandsKnown:
    """Test that puzzle commands are in KNOWN_COMMANDS."""

    def test_puzzle_commands_in_known_commands(self):
        """All puzzle commands should be in KNOWN_COMMANDS."""
        from cli_rpg.game_state import KNOWN_COMMANDS

        puzzle_commands = ["unlock", "pull", "step", "answer", "activate"]
        for cmd in puzzle_commands:
            assert cmd in KNOWN_COMMANDS, f"'{cmd}' should be in KNOWN_COMMANDS"
