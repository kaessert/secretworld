"""Tests for exploration tracking in SubGrids.

Tests the visited_rooms tracking, exploration percentage calculation,
and bonus rewards when a SubGrid is fully explored.
"""

import pytest
from cli_rpg.world_grid import SubGrid
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character


class TestSubGridVisitedRooms:
    """Tests for SubGrid visited room tracking."""

    def test_subgrid_visited_rooms_starts_empty(self):
        """New SubGrid has empty visited_rooms set."""
        # Spec: Track visited rooms in SubGrid
        sub_grid = SubGrid()
        assert sub_grid.visited_rooms == set()

    def test_subgrid_mark_visited(self):
        """mark_visited adds coordinates to visited set."""
        # Spec: Track visited rooms in SubGrid
        sub_grid = SubGrid()
        sub_grid.mark_visited(0, 0, 0)
        assert (0, 0, 0) in sub_grid.visited_rooms

    def test_subgrid_mark_visited_idempotent(self):
        """Marking same room twice doesn't duplicate."""
        # Spec: Track visited rooms in SubGrid
        sub_grid = SubGrid()
        sub_grid.mark_visited(1, 2, 0)
        sub_grid.mark_visited(1, 2, 0)
        assert sub_grid.visited_rooms == {(1, 2, 0)}

    def test_subgrid_get_exploration_stats(self):
        """get_exploration_stats returns correct (visited, total, percentage)."""
        # Spec: Exploration percentage visible in map command
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0))
        # Add 4 rooms (of possible 9 coords in 3x3 grid)
        loc1 = Location(name="Room1", description="test")
        loc2 = Location(name="Room2", description="test")
        loc3 = Location(name="Room3", description="test")
        loc4 = Location(name="Room4", description="test")
        sub_grid.add_location(loc1, 0, 0, 0)
        sub_grid.add_location(loc2, 1, 0, 0)
        sub_grid.add_location(loc3, 0, 1, 0)
        sub_grid.add_location(loc4, -1, 0, 0)

        # Mark 2 as visited
        sub_grid.mark_visited(0, 0, 0)
        sub_grid.mark_visited(1, 0, 0)

        visited, total, percentage = sub_grid.get_exploration_stats()
        assert visited == 2
        assert total == 4  # Only counts actual locations, not all coords
        assert percentage == 50.0

    def test_subgrid_is_fully_explored_false(self):
        """is_fully_explored returns False when rooms remain unvisited."""
        # Spec: "Fully explored" bonus when all rooms visited
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0))
        loc1 = Location(name="Room1", description="test")
        loc2 = Location(name="Room2", description="test")
        sub_grid.add_location(loc1, 0, 0, 0)
        sub_grid.add_location(loc2, 1, 0, 0)

        sub_grid.mark_visited(0, 0, 0)

        assert sub_grid.is_fully_explored() is False

    def test_subgrid_is_fully_explored_true(self):
        """is_fully_explored returns True when all rooms visited."""
        # Spec: "Fully explored" bonus when all rooms visited
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0))
        loc1 = Location(name="Room1", description="test")
        loc2 = Location(name="Room2", description="test")
        sub_grid.add_location(loc1, 0, 0, 0)
        sub_grid.add_location(loc2, 1, 0, 0)

        sub_grid.mark_visited(0, 0, 0)
        sub_grid.mark_visited(1, 0, 0)

        assert sub_grid.is_fully_explored() is True

    def test_subgrid_is_fully_explored_empty_grid(self):
        """is_fully_explored returns True for empty SubGrid (vacuously true)."""
        sub_grid = SubGrid()
        assert sub_grid.is_fully_explored() is True


class TestSubGridSerialization:
    """Tests for visited_rooms serialization."""

    def test_subgrid_serialization_with_visited_rooms(self):
        """to_dict/from_dict preserves visited_rooms."""
        # Spec: Track visited rooms in SubGrid (persisted in save)
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0), parent_name="Test Parent")
        loc1 = Location(name="Room1", description="test")
        sub_grid.add_location(loc1, 0, 0, 0)
        sub_grid.mark_visited(0, 0, 0)

        # Serialize
        data = sub_grid.to_dict()
        assert "visited_rooms" in data
        assert [0, 0, 0] in data["visited_rooms"]

        # Deserialize
        restored = SubGrid.from_dict(data)
        assert (0, 0, 0) in restored.visited_rooms

    def test_subgrid_deserialization_backward_compat(self):
        """Old saves without visited_rooms load with empty set."""
        # Spec: Track visited rooms in SubGrid (persisted in save)
        data = {
            "locations": [],
            "bounds": [-1, 1, -1, 1, 0, 0],
            "parent_name": "Test Parent",
            "secret_passages": [],
            "districts": [],
            # No visited_rooms key - simulating old save
        }
        restored = SubGrid.from_dict(data)
        assert restored.visited_rooms == set()


class TestGameStateMovementTracking:
    """Tests for tracking visits during movement."""

    def _create_subgrid_game_state(self):
        """Helper to create a GameState with an active SubGrid."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import CharacterClass

        # Create character (health/max_health calculated from strength in __post_init__)
        character = Character(
            name="Test",
            character_class=CharacterClass.WARRIOR,
            strength=10,
            dexterity=10,
            intelligence=10,
            perception=10,
            charisma=10,
        )

        # Create overworld with a location that has a SubGrid
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0), parent_name="Dungeon")

        # Add rooms to SubGrid
        entrance = Location(
            name="Entrance",
            description="The dungeon entrance",
            coordinates=(0, 0, 0),
            is_exit_point=True,
        )
        hall = Location(
            name="Hall",
            description="A long hall",
            coordinates=(0, 1, 0),
        )
        chamber = Location(
            name="Chamber",
            description="A dark chamber",
            coordinates=(1, 0, 0),
        )
        sub_grid.add_location(entrance, 0, 0, 0)
        sub_grid.add_location(hall, 0, 1, 0)
        sub_grid.add_location(chamber, 1, 0, 0)

        # Create overworld location with the SubGrid
        dungeon = Location(
            name="Dungeon",
            description="A dark dungeon",
            coordinates=(0, 0),
            is_overworld=True,
            sub_grid=sub_grid,
            entry_point="Entrance",
        )

        world = {"Dungeon": dungeon}
        game_state = GameState(character, world, "Dungeon")

        return game_state, sub_grid

    def test_enter_marks_initial_room_visited(self):
        """Entering SubGrid marks entry point as visited."""
        # Spec: Track visited rooms in SubGrid
        game_state, sub_grid = self._create_subgrid_game_state()

        # Enter the dungeon
        success, message = game_state.enter()
        assert success

        # Check that entry room is marked visited
        assert (0, 0, 0) in sub_grid.visited_rooms

    def test_move_in_sub_grid_marks_visited(self):
        """Movement marks destination as visited."""
        # Spec: Track visited rooms in SubGrid
        game_state, sub_grid = self._create_subgrid_game_state()

        # Enter the dungeon first
        game_state.enter()

        # Move north to Hall
        success, message = game_state.move("north")
        assert success
        assert game_state.current_location == "Hall"

        # Both entrance and hall should be visited
        assert (0, 0, 0) in sub_grid.visited_rooms  # Entrance
        assert (0, 1, 0) in sub_grid.visited_rooms  # Hall

    def test_fully_explored_awards_xp_and_gold(self):
        """Completing exploration gives XP and gold bonus."""
        # Spec: "Fully explored" bonus (XP + gold) when all rooms visited
        game_state, sub_grid = self._create_subgrid_game_state()

        # Enter (marks entrance as visited)
        game_state.enter()

        initial_gold = game_state.current_character.gold

        # Move to visit remaining rooms (3 total rooms)
        game_state.move("north")  # Hall
        game_state.move("south")  # Back to entrance
        success, message = game_state.move("east")  # Chamber - should trigger full exploration

        # Should have gold bonus (XP causes level up so check gold instead)
        # Formula: XP = 50 * total_rooms, Gold = 25 * total_rooms
        total_rooms = 3
        expected_gold_bonus = 25 * total_rooms

        assert game_state.current_character.gold >= initial_gold + expected_gold_bonus
        assert "fully explored" in message.lower()
        # Check that message mentions XP and gold amounts
        assert "+150 XP" in message
        assert "+75 gold" in message

    def test_fully_explored_bonus_only_once(self):
        """Bonus is not given on subsequent visits after full exploration."""
        # Spec: "Fully explored" bonus only once
        game_state, sub_grid = self._create_subgrid_game_state()

        # Enter and explore all rooms
        game_state.enter()
        game_state.move("north")
        game_state.move("south")
        game_state.move("east")

        # Record state after first full exploration
        xp_after_first = game_state.current_character.xp
        gold_after_first = game_state.current_character.gold

        # Move around more - should NOT get bonus again
        game_state.move("west")
        game_state.move("north")
        game_state.move("south")
        game_state.move("east")

        # XP and gold should be same (no additional bonus)
        # Note: may have other small increases from game mechanics,
        # but not the large exploration bonus again
        assert game_state.current_character.xp == xp_after_first
        assert game_state.current_character.gold == gold_after_first


class TestMapRendererExploration:
    """Tests for exploration display in map renderer."""

    def test_subgrid_map_shows_exploration_percentage(self):
        """Map shows 'Explored: X/Y (Z%)' for SubGrids."""
        # Spec: Exploration percentage visible in map command
        from cli_rpg.map_renderer import render_map

        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0), parent_name="Dungeon")
        loc1 = Location(name="Room1", description="test", coordinates=(0, 0, 0))
        loc2 = Location(name="Room2", description="test", coordinates=(1, 0, 0))
        sub_grid.add_location(loc1, 0, 0, 0)
        sub_grid.add_location(loc2, 1, 0, 0)

        # Mark one room visited
        sub_grid.mark_visited(0, 0, 0)

        # Render map
        output = render_map({}, "Room1", sub_grid=sub_grid)

        # Should show exploration stats
        assert "Explored:" in output or "explored:" in output.lower()
        assert "1/2" in output or "50%" in output

    def test_subgrid_map_visited_rooms_styling(self):
        """Visited and unvisited rooms should look different on map."""
        # Spec: Visited rooms marked differently on map (green color)
        from cli_rpg.map_renderer import render_map
        from cli_rpg import colors

        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0), parent_name="Dungeon")
        loc1 = Location(name="Room1", description="test", coordinates=(0, 0, 0))
        loc2 = Location(name="Room2", description="test", coordinates=(1, 0, 0))
        sub_grid.add_location(loc1, 0, 0, 0)
        sub_grid.add_location(loc2, 1, 0, 0)

        # Mark only Room1 as visited
        sub_grid.mark_visited(0, 0, 0)

        # Enable colors for this test
        colors.set_colors_enabled(True)
        try:
            # Render map from Room2 position (so both rooms show as letters, not @)
            output = render_map({}, "Room2", sub_grid=sub_grid)

            # Room1 is visited - its marker should have green color code
            assert colors.GREEN in output

            # Legend should explain the visited styling
            assert "visited" in output.lower()
        finally:
            # Reset color setting
            colors.set_colors_enabled(None)
