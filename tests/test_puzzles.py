"""Tests for dungeon puzzle mechanics (Issue #23).

Tests cover:
1. Puzzle model creation and serialization
2. Locked door puzzles (requiring keys)
3. Lever puzzles (toggle to open passages)
4. Pressure plate puzzles (step to trigger)
5. Riddle puzzles (answer correctly)
6. Sequence puzzles (activate in order)
7. INT-based hints
8. Location puzzle integration (blocked directions)
"""

import pytest
from cli_rpg.models.puzzle import Puzzle, PuzzleType


class TestPuzzleModel:
    """Test Puzzle model creation and serialization."""

    # Spec: PuzzleType enum with 5 puzzle types
    def test_puzzle_creation_locked_door(self):
        """Verify locked door puzzle can be created with required_key."""
        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Rusted Iron Door",
            description="A heavy iron door blocks the passage.",
            required_key="Iron Key",
            target_direction="north",
        )

        assert puzzle.puzzle_type == PuzzleType.LOCKED_DOOR
        assert puzzle.name == "Rusted Iron Door"
        assert puzzle.required_key == "Iron Key"
        assert puzzle.target_direction == "north"
        assert not puzzle.solved

    # Spec: LEVER puzzle type
    def test_puzzle_creation_lever(self):
        """Verify lever puzzle can be created with target_direction."""
        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Ancient Lever",
            description="A rusted lever protrudes from the wall.",
            target_direction="east",
        )

        assert puzzle.puzzle_type == PuzzleType.LEVER
        assert puzzle.name == "Ancient Lever"
        assert puzzle.target_direction == "east"
        assert not puzzle.solved

    # Spec: RIDDLE puzzle type with riddle_text and riddle_answer
    def test_puzzle_creation_riddle(self):
        """Verify riddle puzzle stores riddle_text and riddle_answer."""
        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Sphinx Guardian",
            description="A sphinx blocks your path.",
            riddle_text="What has keys but no locks?",
            riddle_answer="piano",
            target_direction="south",
        )

        assert puzzle.puzzle_type == PuzzleType.RIDDLE
        assert puzzle.riddle_text == "What has keys but no locks?"
        assert puzzle.riddle_answer == "piano"
        assert puzzle.target_direction == "south"

    # Spec: SEQUENCE puzzle type with sequence_ids
    def test_puzzle_creation_sequence(self):
        """Verify sequence puzzle stores correct order."""
        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Sequence",
            description="Four unlit torches line the walls.",
            sequence_ids=["torch_red", "torch_blue", "torch_green"],
            target_direction="west",
        )

        assert puzzle.puzzle_type == PuzzleType.SEQUENCE
        assert puzzle.sequence_ids == ["torch_red", "torch_blue", "torch_green"]
        assert puzzle.sequence_progress == []  # Empty initially
        assert puzzle.target_direction == "west"

    # Spec: Puzzle serialization for save/load
    def test_puzzle_serialization_roundtrip(self):
        """Verify puzzle can be serialized and deserialized."""
        original = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Ancient Door",
            description="A mysterious door.",
            required_key="Golden Key",
            target_direction="north",
            hint_text="The key glimmers with gold.",
            hint_threshold=12,
            solved=False,
        )

        data = original.to_dict()
        restored = Puzzle.from_dict(data)

        assert restored.puzzle_type == original.puzzle_type
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.required_key == original.required_key
        assert restored.target_direction == original.target_direction
        assert restored.hint_text == original.hint_text
        assert restored.hint_threshold == original.hint_threshold
        assert restored.solved == original.solved


class TestLockedDoorPuzzle:
    """Test locked door puzzle mechanics."""

    # Spec: Unlock with correct key removes key from inventory
    def test_unlock_with_correct_key_removes_from_inventory(self):
        """Unlocking door with correct key consumes the key."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import attempt_unlock

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        key = Item(name="Iron Key", description="A rusty iron key", item_type=ItemType.MISC)
        char.inventory.add_item(key)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
        )
        location = Location(
            name="Dungeon Hall",
            description="A dark hall.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        success, message = attempt_unlock(char, location, "Iron Door", "Iron Key")

        assert success
        assert "unlock" in message.lower()
        assert char.inventory.find_item_by_name("Iron Key") is None  # Key consumed
        assert puzzle.solved

    # Spec: Cannot unlock without key
    def test_unlock_without_key_fails(self):
        """Attempting unlock without key fails."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import attempt_unlock

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
        )
        location = Location(
            name="Dungeon Hall",
            description="A dark hall.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        success, message = attempt_unlock(char, location, "Iron Door", "Iron Key")

        assert not success
        assert "don't have" in message.lower() or "no" in message.lower()
        assert not puzzle.solved

    # Spec: Wrong key doesn't unlock
    def test_unlock_with_wrong_key_fails(self):
        """Wrong key doesn't unlock the door."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import attempt_unlock

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        wrong_key = Item(name="Silver Key", description="A shiny key", item_type=ItemType.MISC)
        char.inventory.add_item(wrong_key)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
        )
        location = Location(
            name="Dungeon Hall",
            description="A dark hall.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        success, message = attempt_unlock(char, location, "Iron Door", "Silver Key")

        assert not success
        assert "doesn't fit" in message.lower() or "wrong" in message.lower()
        assert not puzzle.solved

    # Spec: Solved puzzle reveals blocked direction
    def test_unlock_reveals_blocked_direction(self):
        """Unlocking door removes direction from blocked_directions."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import attempt_unlock

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        key = Item(name="Iron Key", description="A rusty key", item_type=ItemType.MISC)
        char.inventory.add_item(key)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
        )
        location = Location(
            name="Dungeon Hall",
            description="A dark hall.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        assert "north" in location.blocked_directions

        attempt_unlock(char, location, "Iron Door", "Iron Key")

        assert "north" not in location.blocked_directions

    # Spec: Already unlocked door shows appropriate message
    def test_already_unlocked_door_message(self):
        """Attempting to unlock already-solved puzzle shows message."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import attempt_unlock

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        key = Item(name="Iron Key", description="A rusty key", item_type=ItemType.MISC)
        char.inventory.add_item(key)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
            solved=True,  # Already solved
        )
        location = Location(
            name="Dungeon Hall",
            description="A dark hall.",
            puzzles=[puzzle],
            blocked_directions=[],
        )

        success, message = attempt_unlock(char, location, "Iron Door", "Iron Key")

        assert not success
        assert "already" in message.lower()


class TestLeverPuzzle:
    """Test lever puzzle mechanics."""

    # Spec: Pull lever opens passage
    def test_pull_lever_opens_passage(self):
        """Pulling lever solves puzzle and reveals passage."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import pull_lever

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Stone Lever",
            description="A lever set in the wall.",
            target_direction="east",
        )
        location = Location(
            name="Lever Room",
            description="A chamber with a lever.",
            puzzles=[puzzle],
            blocked_directions=["east"],
        )

        success, message = pull_lever(char, location, "Stone Lever")

        assert success
        assert puzzle.solved
        assert "east" not in location.blocked_directions

    # Spec: Already activated lever shows message
    def test_lever_already_activated_message(self):
        """Pulling already-activated lever shows message."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import pull_lever

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Stone Lever",
            description="A lever set in the wall.",
            target_direction="east",
            solved=True,
        )
        location = Location(
            name="Lever Room",
            description="A chamber with a lever.",
            puzzles=[puzzle],
            blocked_directions=[],
        )

        success, message = pull_lever(char, location, "Stone Lever")

        assert not success
        assert "already" in message.lower()

    # Spec: Lever opens correct direction
    def test_lever_passage_direction_added(self):
        """Lever opens passage in its target_direction."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import pull_lever

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Hidden Lever",
            description="A concealed lever.",
            target_direction="south",
        )
        location = Location(
            name="Secret Room",
            description="A hidden chamber.",
            puzzles=[puzzle],
            blocked_directions=["south", "west"],
        )

        pull_lever(char, location, "Hidden Lever")

        assert "south" not in location.blocked_directions
        assert "west" in location.blocked_directions  # Unaffected


class TestPressurePlatePuzzle:
    """Test pressure plate puzzle mechanics."""

    # Spec: Step on plate opens passage
    def test_step_on_plate_opens_passage(self):
        """Stepping on pressure plate solves puzzle."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import step_on_plate

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.PRESSURE_PLATE,
            name="Stone Plate",
            description="A pressure plate on the floor.",
            target_direction="north",
        )
        location = Location(
            name="Trap Room",
            description="A room with floor plates.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        success, message = step_on_plate(char, location, "Stone Plate")

        assert success
        assert puzzle.solved
        assert "north" not in location.blocked_directions

    # Spec: Plate stays active after stepping
    def test_plate_stays_active_after_step(self):
        """Pressure plate remains solved after activation."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import step_on_plate

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.PRESSURE_PLATE,
            name="Stone Plate",
            description="A pressure plate.",
            target_direction="north",
        )
        location = Location(
            name="Trap Room",
            description="A room with plates.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        step_on_plate(char, location, "Stone Plate")

        # Step on it again - should indicate already active
        success, message = step_on_plate(char, location, "Stone Plate")
        assert not success
        assert "already" in message.lower()


class TestRiddlePuzzle:
    """Test riddle puzzle mechanics."""

    # Spec: Correct answer opens passage
    def test_correct_answer_opens_passage(self):
        """Correct riddle answer solves puzzle."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import answer_riddle

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Stone Sphinx",
            description="A sphinx blocks the way.",
            riddle_text="What has keys but no locks?",
            riddle_answer="piano",
            target_direction="south",
        )
        location = Location(
            name="Sphinx Chamber",
            description="A chamber with a sphinx.",
            puzzles=[puzzle],
            blocked_directions=["south"],
        )

        success, message = answer_riddle(char, location, "Stone Sphinx", "piano")

        assert success
        assert puzzle.solved
        assert "south" not in location.blocked_directions

    # Spec: Incorrect answer shows failure message
    def test_incorrect_answer_message(self):
        """Incorrect riddle answer fails."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import answer_riddle

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Stone Sphinx",
            description="A sphinx blocks the way.",
            riddle_text="What has keys but no locks?",
            riddle_answer="piano",
            target_direction="south",
        )
        location = Location(
            name="Sphinx Chamber",
            description="A chamber with a sphinx.",
            puzzles=[puzzle],
            blocked_directions=["south"],
        )

        success, message = answer_riddle(char, location, "Stone Sphinx", "door")

        assert not success
        assert not puzzle.solved
        assert "wrong" in message.lower() or "incorrect" in message.lower()

    # Spec: Riddle answer is case-insensitive
    def test_riddle_answer_case_insensitive(self):
        """Riddle answer matching is case-insensitive."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import answer_riddle

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Stone Sphinx",
            description="A sphinx.",
            riddle_text="What has keys?",
            riddle_answer="Piano",
            target_direction="south",
        )
        location = Location(
            name="Chamber",
            description="A chamber.",
            puzzles=[puzzle],
            blocked_directions=["south"],
        )

        success, _ = answer_riddle(char, location, "Stone Sphinx", "PIANO")
        assert success

    # Spec: Riddle NPC shows riddle text when examined
    def test_riddle_npc_dialogue_shows_riddle(self):
        """Examining riddle puzzle shows riddle_text."""
        from cli_rpg.models.character import Character
        from cli_rpg.puzzles import examine_puzzle

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.RIDDLE,
            name="Stone Sphinx",
            description="A sphinx blocks the way.",
            riddle_text="What walks on four legs in the morning?",
            riddle_answer="man",
            target_direction="south",
        )

        result = examine_puzzle(char, puzzle)

        assert "What walks on four legs in the morning?" in result


class TestSequencePuzzle:
    """Test sequence puzzle mechanics."""

    # Spec: Correct sequence solves puzzle
    def test_correct_sequence_solves_puzzle(self):
        """Activating in correct order solves puzzle."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import activate_sequence

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Row",
            description="Four torches on the wall.",
            sequence_ids=["torch_1", "torch_2", "torch_3"],
            target_direction="west",
        )
        location = Location(
            name="Torch Chamber",
            description="A room with torches.",
            puzzles=[puzzle],
            blocked_directions=["west"],
        )

        # Activate in correct order
        activate_sequence(char, location, "Torch Row", "torch_1")
        activate_sequence(char, location, "Torch Row", "torch_2")
        success, message = activate_sequence(char, location, "Torch Row", "torch_3")

        assert success
        assert puzzle.solved
        assert "west" not in location.blocked_directions

    # Spec: Wrong sequence resets progress
    def test_wrong_sequence_resets_progress(self):
        """Wrong activation order resets sequence progress."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import activate_sequence

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Row",
            description="Four torches.",
            sequence_ids=["torch_1", "torch_2", "torch_3"],
            target_direction="west",
        )
        location = Location(
            name="Torch Chamber",
            description="A room.",
            puzzles=[puzzle],
            blocked_directions=["west"],
        )

        activate_sequence(char, location, "Torch Row", "torch_1")
        assert puzzle.sequence_progress == ["torch_1"]

        # Wrong activation
        success, message = activate_sequence(char, location, "Torch Row", "torch_3")

        assert not success
        assert puzzle.sequence_progress == []  # Reset
        assert "reset" in message.lower() or "wrong" in message.lower()

    # Spec: Partial sequence tracked
    def test_partial_sequence_tracked(self):
        """Partial sequence progress is tracked."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import activate_sequence

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.SEQUENCE,
            name="Torch Row",
            description="Four torches.",
            sequence_ids=["torch_1", "torch_2", "torch_3"],
            target_direction="west",
        )
        location = Location(
            name="Chamber",
            description="A room.",
            puzzles=[puzzle],
            blocked_directions=["west"],
        )

        activate_sequence(char, location, "Torch Row", "torch_1")
        assert puzzle.sequence_progress == ["torch_1"]

        activate_sequence(char, location, "Torch Row", "torch_2")
        assert puzzle.sequence_progress == ["torch_1", "torch_2"]


class TestINTHints:
    """Test INT stat providing hints for puzzles."""

    # Spec: High INT shows hint
    def test_high_int_shows_hint(self):
        """Character with high INT sees puzzle hints."""
        from cli_rpg.models.character import Character
        from cli_rpg.puzzles import examine_puzzle

        # High INT character
        char = Character(name="Wizard", strength=10, dexterity=10, intelligence=16)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
            hint_threshold=14,
            hint_text="The key bears a mark of rusted iron.",
        )

        result = examine_puzzle(char, puzzle)

        assert "rusted iron" in result.lower()

    # Spec: Low INT doesn't show hint
    def test_low_int_no_hint(self):
        """Character with low INT does not see hints."""
        from cli_rpg.models.character import Character
        from cli_rpg.puzzles import examine_puzzle

        # Low INT character
        char = Character(name="Brute", strength=16, dexterity=10, intelligence=8)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
            hint_threshold=14,
            hint_text="The key bears a mark of rusted iron.",
        )

        result = examine_puzzle(char, puzzle)

        assert "rusted iron" not in result.lower()

    # Spec: Hint threshold boundary
    def test_hint_threshold_boundary(self):
        """INT exactly at threshold shows hint."""
        from cli_rpg.models.character import Character
        from cli_rpg.puzzles import examine_puzzle

        char = Character(name="Scholar", strength=10, dexterity=10, intelligence=14)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A heavy door.",
            required_key="Iron Key",
            target_direction="north",
            hint_threshold=14,
            hint_text="The key bears a mark.",
        )

        result = examine_puzzle(char, puzzle)

        assert "key bears a mark" in result.lower()


class TestLocationPuzzleIntegration:
    """Test puzzle integration with Location model."""

    # Spec: Blocked directions not shown in exits
    def test_blocked_direction_not_in_exits(self):
        """Blocked directions are not available as exits."""
        from cli_rpg.models.location import Location
        from cli_rpg.world_grid import SubGrid

        # Create a SubGrid with adjacent locations
        sub_grid = SubGrid(bounds=(0, 2, 0, 2, 0, 0))

        center = Location(
            name="Center Room",
            description="A room.",
            puzzles=[],
            blocked_directions=["north"],
        )
        north_room = Location(
            name="North Room",
            description="North.",
        )
        south_room = Location(
            name="South Room",
            description="South.",
        )

        sub_grid.add_location(center, x=1, y=1, z=0)
        sub_grid.add_location(north_room, x=1, y=2, z=0)
        sub_grid.add_location(south_room, x=1, y=0, z=0)

        # Get available directions
        available = center.get_available_directions(sub_grid=sub_grid)

        # Filter blocked directions
        from cli_rpg.puzzles import filter_blocked_directions
        filtered = filter_blocked_directions(available, center.blocked_directions)

        assert "south" in filtered
        assert "north" not in filtered

    # Spec: Solved puzzle restores direction
    def test_solved_puzzle_restores_direction(self):
        """Solving puzzle removes direction from blocked_directions."""
        from cli_rpg.models.location import Location
        from cli_rpg.models.character import Character
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.puzzles import attempt_unlock

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        key = Item(name="Iron Key", description="A key", item_type=ItemType.MISC)
        char.inventory.add_item(key)

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A door.",
            required_key="Iron Key",
            target_direction="north",
        )
        location = Location(
            name="Hall",
            description="A hall.",
            puzzles=[puzzle],
            blocked_directions=["north"],
        )

        assert "north" in location.blocked_directions

        attempt_unlock(char, location, "Iron Door", "Iron Key")

        assert "north" not in location.blocked_directions

    # Spec: Puzzle serialization in location
    def test_puzzle_serialization_in_location(self):
        """Location puzzles are serialized correctly."""
        from cli_rpg.models.location import Location

        puzzle = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Wall Lever",
            description="A lever.",
            target_direction="east",
        )
        location = Location(
            name="Lever Room",
            description="A room.",
            puzzles=[puzzle],
            blocked_directions=["east"],
        )

        data = location.to_dict()
        restored = Location.from_dict(data)

        assert len(restored.puzzles) == 1
        assert restored.puzzles[0].name == "Wall Lever"
        assert restored.puzzles[0].puzzle_type == PuzzleType.LEVER
        assert restored.blocked_directions == ["east"]


class TestPuzzleHelpers:
    """Test puzzle helper functions."""

    def test_find_puzzle_by_name(self):
        """find_puzzle_by_name locates puzzle by case-insensitive name."""
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import find_puzzle_by_name

        puzzle1 = Puzzle(
            puzzle_type=PuzzleType.LEVER,
            name="Ancient Lever",
            description="A lever.",
            target_direction="north",
        )
        puzzle2 = Puzzle(
            puzzle_type=PuzzleType.LOCKED_DOOR,
            name="Iron Door",
            description="A door.",
            required_key="Key",
            target_direction="south",
        )
        location = Location(
            name="Room",
            description="A room.",
            puzzles=[puzzle1, puzzle2],
        )

        found = find_puzzle_by_name(location, "ancient lever")
        assert found is puzzle1

        found = find_puzzle_by_name(location, "IRON DOOR")
        assert found is puzzle2

        found = find_puzzle_by_name(location, "nonexistent")
        assert found is None

    def test_puzzle_not_found_error(self):
        """Attempting action on nonexistent puzzle fails gracefully."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.puzzles import pull_lever

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        location = Location(
            name="Empty Room",
            description="Nothing here.",
            puzzles=[],
        )

        success, message = pull_lever(char, location, "Nonexistent Lever")

        assert not success
        assert "not found" in message.lower() or "no" in message.lower()
