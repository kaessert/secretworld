"""Tests for consistent terrain blocking messages.

All movement blocking scenarios should have descriptive, consistent messages.
"""

import pytest
from unittest.mock import Mock, MagicMock

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid


class TestOverworldBlockingMessages:
    """Test blocking messages for overworld movement."""

    def test_water_terrain_blocking_message(self):
        """Water terrain shows 'The water ahead is impassable.'"""
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        start = Location(name="Start", description="Start", coordinates=(0, 0))
        world = {"Start": start}
        game_state = GameState(character, world, "Start")

        mock_cm = MagicMock()
        mock_cm.get_tile_at.return_value = "water"
        game_state.chunk_manager = mock_cm

        success, message = game_state.move("north")

        assert not success
        assert "water" in message.lower()
        assert "impassable" in message.lower()


class TestSubGridBlockingMessages:
    """Test blocking messages for SubGrid interior movement."""

    def test_subgrid_bounds_exceeded_message(self):
        """Moving past SubGrid bounds shows edge-of-area message."""
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create small subgrid with bounds (-1, 1, -1, 1)
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1), parent_name="Parent")
        edge_loc = Location(name="Edge Room", description="At the edge", coordinates=(0, 1))
        sub_grid.add_location(edge_loc, 0, 1)

        # Create parent location in overworld
        parent = Location(name="Parent", description="Parent", coordinates=(0, 0))
        world = {"Parent": parent, "Edge Room": edge_loc}
        game_state = GameState(character, world, "Edge Room")
        game_state.in_sub_location = True
        game_state.current_sub_grid = sub_grid

        # Try to move north (past bounds)
        success, message = game_state.move("north")

        assert not success
        assert "edge" in message.lower() or "boundary" in message.lower()

    def test_subgrid_wall_blocking_message(self):
        """Moving to empty SubGrid cell shows wall message."""
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create subgrid with location at (0,0) but nothing at (0,1)
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2), parent_name="Parent")
        room = Location(name="Room", description="A room", coordinates=(0, 0))
        sub_grid.add_location(room, 0, 0)

        parent = Location(name="Parent", description="Parent", coordinates=(0, 0))
        world = {"Parent": parent, "Room": room}
        game_state = GameState(character, world, "Room")
        game_state.in_sub_location = True
        game_state.current_sub_grid = sub_grid

        # Try to move north (empty cell within bounds)
        success, message = game_state.move("north")

        assert not success
        assert "wall" in message.lower() or "blocked" in message.lower()
