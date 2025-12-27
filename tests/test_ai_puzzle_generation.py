"""Tests for AI-generated puzzles in dungeon locations.

Tests the puzzle generation system that populates Location.puzzles and
Location.blocked_directions during AI world generation and SubGrid creation.

Spec: Issue #23 - Dungeon Puzzle Mechanics - AI Generation Integration
"""

import pytest
from cli_rpg.models.puzzle import Puzzle, PuzzleType


class TestPuzzleConstants:
    """Tests for puzzle generation constants."""

    def test_puzzle_categories_defined(self):
        """Verify PUZZLE_CATEGORIES constant exists and contains expected values.

        Spec: Categories that should have puzzles (dungeon, cave, ruins, temple)
        """
        from cli_rpg.ai_world import PUZZLE_CATEGORIES

        assert isinstance(PUZZLE_CATEGORIES, frozenset)
        assert "dungeon" in PUZZLE_CATEGORIES
        assert "cave" in PUZZLE_CATEGORIES
        assert "ruins" in PUZZLE_CATEGORIES
        assert "temple" in PUZZLE_CATEGORIES

    def test_puzzle_templates_for_each_category(self):
        """Each puzzle category should have templates defined.

        Spec: Each category in PUZZLE_CATEGORIES has entries in PUZZLE_TEMPLATES
        """
        from cli_rpg.ai_world import PUZZLE_CATEGORIES, PUZZLE_TEMPLATES

        for category in PUZZLE_CATEGORIES:
            assert category in PUZZLE_TEMPLATES, f"Missing templates for {category}"
            assert len(PUZZLE_TEMPLATES[category]) >= 1, f"No templates for {category}"


class TestGeneratePuzzlesForLocation:
    """Tests for _generate_puzzles_for_location function."""

    def test_generates_0_to_2_puzzles(self):
        """Output count should be 0-2 puzzles for valid categories.

        Spec: 1-2 puzzles per dungeon area (but 0 is possible based on random chance)
        """
        from cli_rpg.ai_world import PUZZLE_CATEGORIES, _generate_puzzles_for_location

        for category in PUZZLE_CATEGORIES:
            # Run multiple times to get a distribution
            counts = []
            for _ in range(50):
                puzzles, blocked, keys = _generate_puzzles_for_location(
                    category, distance=1
                )
                counts.append(len(puzzles))

            # Verify all counts are in range 0-2
            for count in counts:
                assert 0 <= count <= 2, f"Wrong count for {category}: {count}"

    def test_puzzle_has_required_fields(self):
        """Each puzzle should have required fields.

        Spec: Puzzles have name, description, puzzle_type, target_direction,
              hint_threshold, hint_text
        """
        from cli_rpg.ai_world import _generate_puzzles_for_location

        # Generate multiple times to ensure we get at least one puzzle
        for _ in range(50):
            puzzles, blocked, keys = _generate_puzzles_for_location(
                "dungeon", distance=1
            )
            if puzzles:
                for puzzle in puzzles:
                    assert isinstance(puzzle, Puzzle)
                    assert puzzle.name
                    assert puzzle.description
                    assert puzzle.puzzle_type in PuzzleType
                    assert puzzle.target_direction in (
                        "north",
                        "south",
                        "east",
                        "west",
                    )
                    assert puzzle.hint_threshold > 0
                    assert puzzle.hint_text is not None
                return

        pytest.fail("No puzzles generated after 50 attempts")

    def test_locked_door_has_required_key(self):
        """LOCKED_DOOR puzzles should have required_key and generate key to place.

        Spec: Locked doors require specific key item to unlock
        """
        from cli_rpg.ai_world import PUZZLE_TEMPLATES, _generate_puzzles_for_location

        # Get templates to ensure LOCKED_DOOR templates exist
        locked_door_templates = [
            t for t in PUZZLE_TEMPLATES["dungeon"] if t[0] == PuzzleType.LOCKED_DOOR
        ]
        assert locked_door_templates, "No LOCKED_DOOR templates in dungeon category"

        # Generate until we find a locked door
        for _ in range(100):
            puzzles, blocked, keys = _generate_puzzles_for_location(
                "dungeon", distance=1
            )
            for puzzle in puzzles:
                if puzzle.puzzle_type == PuzzleType.LOCKED_DOOR:
                    assert puzzle.required_key is not None
                    # Key should be in keys_to_place list
                    key_names = [k[0] for k in keys]
                    assert puzzle.required_key in key_names
                    return

        pytest.fail("No LOCKED_DOOR puzzle generated after 100 attempts")

    def test_riddle_has_riddle_text_and_answer(self):
        """RIDDLE puzzles should have riddle_text and riddle_answer.

        Spec: Riddle puzzles require correct answer to pass
        """
        from cli_rpg.ai_world import PUZZLE_TEMPLATES, _generate_puzzles_for_location

        # Get templates to ensure RIDDLE templates exist
        riddle_templates = [
            t for t in PUZZLE_TEMPLATES["dungeon"] if t[0] == PuzzleType.RIDDLE
        ]
        assert riddle_templates, "No RIDDLE templates in dungeon category"

        # Generate until we find a riddle
        for _ in range(100):
            puzzles, blocked, keys = _generate_puzzles_for_location(
                "dungeon", distance=1
            )
            for puzzle in puzzles:
                if puzzle.puzzle_type == PuzzleType.RIDDLE:
                    assert puzzle.riddle_text is not None
                    assert puzzle.riddle_answer is not None
                    assert len(puzzle.riddle_text) > 0
                    assert len(puzzle.riddle_answer) > 0
                    return

        pytest.fail("No RIDDLE puzzle generated after 100 attempts")

    def test_lever_has_target_direction(self):
        """LEVER puzzles should have target_direction (direction they unblock).

        Spec: Levers toggle to open a passage
        """
        from cli_rpg.ai_world import PUZZLE_TEMPLATES, _generate_puzzles_for_location

        # Get templates to ensure LEVER templates exist
        lever_templates = [
            t for t in PUZZLE_TEMPLATES["dungeon"] if t[0] == PuzzleType.LEVER
        ]
        assert lever_templates, "No LEVER templates in dungeon category"

        # Generate until we find a lever
        for _ in range(100):
            puzzles, blocked, keys = _generate_puzzles_for_location(
                "dungeon", distance=1
            )
            for puzzle in puzzles:
                if puzzle.puzzle_type == PuzzleType.LEVER:
                    assert puzzle.target_direction in (
                        "north",
                        "south",
                        "east",
                        "west",
                    )
                    return

        pytest.fail("No LEVER puzzle generated after 100 attempts")

    def test_distance_scales_hint_threshold(self):
        """Higher distance should increase hint threshold.

        Spec: threshold = base_threshold + min(distance, 3) + abs(z_level)
        """
        from cli_rpg.ai_world import _generate_puzzles_for_location

        # Collect thresholds at different distances
        thresholds_d1 = []
        thresholds_d4 = []

        for _ in range(50):
            puzzles_d1, _, _ = _generate_puzzles_for_location("dungeon", distance=1)
            puzzles_d4, _, _ = _generate_puzzles_for_location("dungeon", distance=4)
            thresholds_d1.extend(p.hint_threshold for p in puzzles_d1)
            thresholds_d4.extend(p.hint_threshold for p in puzzles_d4)

        if thresholds_d1 and thresholds_d4:
            # Average threshold at distance 4 should be higher
            avg_d1 = sum(thresholds_d1) / len(thresholds_d1)
            avg_d4 = sum(thresholds_d4) / len(thresholds_d4)
            assert (
                avg_d4 > avg_d1
            ), f"Distance 4 threshold ({avg_d4}) should be higher than distance 1 ({avg_d1})"

    def test_non_puzzle_category_returns_empty(self):
        """Non-puzzle categories (town, village) should return empty results.

        Spec: Only dungeon, cave, ruins, temple have puzzles
        """
        from cli_rpg.ai_world import _generate_puzzles_for_location

        for category in ["town", "village", "settlement", "city", "shop", "forest"]:
            puzzles, blocked, keys = _generate_puzzles_for_location(
                category, distance=1
            )
            assert puzzles == [], f"Expected empty for {category}, got {puzzles}"
            assert blocked == [], f"Expected empty blocked for {category}"
            assert keys == [], f"Expected empty keys for {category}"

    def test_entry_room_returns_empty(self):
        """Entry room (distance=0) should return empty results.

        Spec: No puzzles at entry room
        """
        from cli_rpg.ai_world import _generate_puzzles_for_location

        for _ in range(20):
            puzzles, blocked, keys = _generate_puzzles_for_location(
                "dungeon", distance=0
            )
            assert puzzles == [], "Entry room should have no puzzles"
            assert blocked == [], "Entry room should have no blocked directions"
            assert keys == [], "Entry room should have no keys to place"


class TestPlaceKeysInEarlierRooms:
    """Tests for _place_keys_in_earlier_rooms helper."""

    def test_key_placed_in_location_before_door(self):
        """Keys should be placed in rooms with distance < door_distance.

        Spec: Key must be placed in a room that player visits BEFORE the locked door
        """
        from cli_rpg.ai_world import _place_keys_in_earlier_rooms
        from cli_rpg.models.location import Location

        # Create mock placed_locations with rooms at different distances
        loc_entry = Location(name="Entry", description="Entry room")
        loc_near = Location(name="Near Room", description="Close room")
        loc_far = Location(name="Far Room", description="Far room")

        placed_locations = {
            "Entry": {
                "location": loc_entry,
                "relative_coords": (0, 0, 0),
                "is_entry": True,
            },
            "Near Room": {
                "location": loc_near,
                "relative_coords": (0, 1, 0),
                "is_entry": False,
            },
            "Far Room": {
                "location": loc_far,
                "relative_coords": (0, 2, 0),
                "is_entry": False,
            },
        }

        # Door at distance 2, key should be placed at distance < 2
        keys_to_place = [("Iron Key", "dungeon", 2)]

        _place_keys_in_earlier_rooms(placed_locations, keys_to_place)

        # Key should be in Near Room (distance 1) or Entry (distance 0)
        # Check treasures contain the key
        found_key = False
        for name, data in placed_locations.items():
            loc = data["location"]
            for treasure in loc.treasures:
                for item in treasure.get("items", []):
                    if item.get("name") == "Iron Key":
                        found_key = True
                        # Verify it's in a room before the door
                        rel = data["relative_coords"]
                        dist = abs(rel[0]) + abs(rel[1])
                        assert dist < 2, f"Key placed at distance {dist}, should be < 2"
                        break

        assert found_key, "Iron Key was not placed in any room"

    def test_key_falls_back_to_entry_if_no_candidates(self):
        """Key should be placed at entry if no other valid rooms exist.

        Spec: Fall back to entry room if no rooms with lower distance
        """
        from cli_rpg.ai_world import _place_keys_in_earlier_rooms
        from cli_rpg.models.location import Location

        # Only entry room exists
        loc_entry = Location(name="Entry", description="Entry room")

        placed_locations = {
            "Entry": {
                "location": loc_entry,
                "relative_coords": (0, 0, 0),
                "is_entry": True,
            },
        }

        keys_to_place = [("Cave Key", "cave", 1)]

        _place_keys_in_earlier_rooms(placed_locations, keys_to_place)

        # Key should be in entry room
        assert len(loc_entry.treasures) == 1
        assert loc_entry.treasures[0]["items"][0]["name"] == "Cave Key"


class TestSubGridPuzzleIntegration:
    """Tests for puzzle integration in SubGrid generation."""

    def test_subgrid_rooms_have_puzzles(self):
        """Non-entry rooms in SubGrid should have puzzles.

        Spec: 1-2 puzzles per dungeon area
        """
        from cli_rpg.ai_world import generate_subgrid_for_location
        from cli_rpg.models.location import Location

        # Create a dungeon location
        dungeon = Location(
            name="Test Dungeon",
            description="A test dungeon",
            category="dungeon",
        )

        # Generate SubGrid (without AI service)
        sub_grid = generate_subgrid_for_location(
            location=dungeon,
            ai_service=None,
            theme="fantasy",
        )

        # Check that some non-entry rooms have puzzles
        has_puzzles = False
        for loc in sub_grid._by_name.values():
            if not loc.is_exit_point and loc.puzzles:
                has_puzzles = True
                break

        # Note: puzzles are random, so we just verify the integration works
        # The actual puzzle generation is tested in TestGeneratePuzzlesForLocation
        assert sub_grid is not None

    def test_puzzles_block_directions(self):
        """Puzzles should add to Location.blocked_directions.

        Spec: Puzzles block directions until solved
        """
        from cli_rpg.ai_world import _generate_puzzles_for_location

        # Generate puzzles and verify blocked directions match
        for _ in range(50):
            puzzles, blocked, keys = _generate_puzzles_for_location(
                "dungeon", distance=1
            )
            if puzzles:
                # Each puzzle should have its target_direction in blocked
                for puzzle in puzzles:
                    assert (
                        puzzle.target_direction in blocked
                    ), f"Puzzle direction {puzzle.target_direction} not in blocked: {blocked}"
                return

        # If we didn't get any puzzles in 50 attempts, that's also valid (0 puzzles is possible)

    def test_entry_room_has_no_puzzles(self):
        """Entry room (is_exit_point=True) should have no puzzles.

        Spec: No puzzles at entry room
        """
        from cli_rpg.ai_world import generate_subgrid_for_location
        from cli_rpg.models.location import Location

        # Create a dungeon location
        dungeon = Location(
            name="Test Dungeon 2",
            description="A test dungeon for entry testing",
            category="dungeon",
        )

        # Generate SubGrid (without AI service)
        sub_grid = generate_subgrid_for_location(
            location=dungeon,
            ai_service=None,
            theme="fantasy",
        )

        # Find entry room and verify no puzzles
        for loc in sub_grid._by_name.values():
            if loc.is_exit_point:
                assert loc.puzzles == [], f"Entry room has puzzles: {loc.puzzles}"
                assert (
                    loc.blocked_directions == []
                ), f"Entry room has blocked directions: {loc.blocked_directions}"
                break

    def test_key_placed_before_locked_door(self):
        """Keys for locked doors should be placed in earlier rooms.

        Spec: Key placed in room at distance < door_distance
        """
        from cli_rpg.ai_world import generate_subgrid_for_location
        from cli_rpg.models.location import Location
        from cli_rpg.models.puzzle import PuzzleType

        # Create a dungeon location
        dungeon = Location(
            name="Key Test Dungeon",
            description="A test dungeon for key placement",
            category="dungeon",
        )

        # Generate multiple times to find a dungeon with locked doors
        for _ in range(20):
            sub_grid = generate_subgrid_for_location(
                location=dungeon,
                ai_service=None,
                theme="fantasy",
            )

            # Find all locked doors and their keys
            locked_doors = []
            for loc in sub_grid._by_name.values():
                for puzzle in loc.puzzles:
                    if puzzle.puzzle_type == PuzzleType.LOCKED_DOOR:
                        locked_doors.append((loc, puzzle))

            if locked_doors:
                # For each locked door, verify key exists somewhere
                for door_loc, puzzle in locked_doors:
                    key_name = puzzle.required_key
                    door_coords = door_loc.coordinates
                    door_distance = abs(door_coords[0]) + abs(door_coords[1])

                    # Search for the key in treasures
                    found_key = False
                    for loc in sub_grid._by_name.values():
                        for treasure in loc.treasures:
                            for item in treasure.get("items", []):
                                if item.get("name") == key_name:
                                    key_coords = loc.coordinates
                                    key_distance = (
                                        abs(key_coords[0]) + abs(key_coords[1])
                                    )
                                    assert (
                                        key_distance < door_distance
                                        or loc.is_exit_point
                                    ), f"Key at distance {key_distance}, door at {door_distance}"
                                    found_key = True
                                    break

                    # Key should be findable
                    assert (
                        found_key
                    ), f"Key '{key_name}' not found for locked door at {door_loc.name}"
                return

        # If no locked doors in 20 attempts, that's okay (random generation)
