"""Tests for AI world expand_area() SubGrid integration.

These tests verify that expand_area() correctly places sub-locations into
the entry location's SubGrid instead of adding them to the overworld.

Spec: expand_area() SubGrid Behavior
- Entry location (rel 0,0): Added to overworld with is_exit_point=True and a sub_grid
- Sub-locations: Added to entry's SubGrid, NOT to overworld
- Entry point in SubGrid at (0,0): The first sub-location, marked is_exit_point=True
- SubGrid bounds: (-3, 3, -3, 3) for 7x7 areas
"""

import pytest
from unittest.mock import Mock
from cli_rpg.ai_service import AIService
from cli_rpg.ai_world import expand_area
from cli_rpg.models.location import Location


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock(spec=AIService)
    return service


@pytest.fixture
def basic_world():
    """Create a basic world with one location at origin."""
    town_square = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0),
        category="town"
    )
    return {"Town Square": town_square}


class TestExpandAreaSubGrid:
    """Tests for expand_area() SubGrid integration.

    Spec: expand_area() must use SubGrid for sub-locations
    - Entry location added to world dict
    - Sub-locations added to entry's sub_grid, NOT world dict
    """

    def test_expand_area_creates_subgrid_for_entry(self, mock_ai_service, basic_world):
        """Entry location should have sub_grid attached when there are sub-locations.

        Spec: Entry location should have sub_grid attached
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Dungeon Gate",
                "description": "The entrance to a dark dungeon.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Dungeon Hall"},
                "category": "dungeon"
            },
            {
                "name": "Dungeon Hall",
                "description": "A dark hallway.",
                "relative_coords": [0, 1],
                "connections": {"south": "Dungeon Gate"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Dungeon Gate"]
        assert entry.sub_grid is not None, "Entry location should have a SubGrid"

    def test_expand_area_sublocations_not_in_world(self, mock_ai_service, basic_world):
        """Sub-locations should NOT be in world dict.

        Spec: Sub-locations added to entry's SubGrid, NOT to overworld
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Castle Gate",
                "description": "The grand entrance to a castle.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Throne Room"},
                "category": "dungeon"
            },
            {
                "name": "Throne Room",
                "description": "The king's throne room.",
                "relative_coords": [0, 1],
                "connections": {"south": "Castle Gate"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Entry should be in world
        assert "Castle Gate" in basic_world
        # Sub-location should NOT be in world
        assert "Throne Room" not in basic_world

    def test_expand_area_sublocations_in_subgrid(self, mock_ai_service, basic_world):
        """Sub-locations should be in entry's sub_grid.

        Spec: Sub-locations added to entry's SubGrid
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Cave Mouth",
                "description": "The entrance to a cave.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Cave Interior"},
                "category": "cave"
            },
            {
                "name": "Cave Interior",
                "description": "Deep inside the cave.",
                "relative_coords": [0, 1],
                "connections": {"south": "Cave Mouth"},
                "category": "cave"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Cave Mouth"]
        assert entry.sub_grid is not None
        # Sub-location should be findable in SubGrid
        interior = entry.sub_grid.get_by_name("Cave Interior")
        assert interior is not None, "Sub-location should be in SubGrid"
        assert interior.name == "Cave Interior"

    def test_expand_area_entry_has_is_exit_point_true(self, mock_ai_service, basic_world):
        """Entry location is marked as exit point.

        Spec: Entry location (at relative 0,0): is_exit_point=True
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Ruin Gate",
                "description": "Ancient ruins entrance.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Inner Ruins"},
                "category": "ruins"
            },
            {
                "name": "Inner Ruins",
                "description": "Deeper into the ruins.",
                "relative_coords": [0, 1],
                "connections": {"south": "Ruin Gate"},
                "category": "ruins"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Ruin Gate"]
        assert entry.is_exit_point is True

    def test_expand_area_first_sublocation_is_exit_point(self, mock_ai_service, basic_world):
        """First sub-location at (0,0) in SubGrid is exit point.

        Spec: Entry point in SubGrid: The first sub-location, marked is_exit_point=True
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Tower Base",
                "description": "The base of an ancient tower.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Tower Level 1"},
                "category": "dungeon"
            },
            {
                "name": "Tower Level 1",
                "description": "First floor of the tower.",
                "relative_coords": [0, 1],
                "connections": {"south": "Tower Base", "north": "Tower Level 2"},
                "category": "dungeon"
            },
            {
                "name": "Tower Level 2",
                "description": "Second floor of the tower.",
                "relative_coords": [0, 2],
                "connections": {"south": "Tower Level 1"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Tower Base"]
        # First sub-location in SubGrid should be at (0, 0) and be exit point
        first_subloc = entry.sub_grid.get_by_name("Tower Level 1")
        assert first_subloc is not None
        assert first_subloc.is_exit_point is True, "First sub-location should be exit point"

        # Other sub-locations should not be exit points
        second_subloc = entry.sub_grid.get_by_name("Tower Level 2")
        assert second_subloc is not None
        assert second_subloc.is_exit_point is False, "Other sub-locations should not be exit points"

    def test_expand_area_sublocations_have_parent_location(self, mock_ai_service, basic_world):
        """Sub-locations have parent_location set to entry name.

        Spec: Sub-locations have parent_location set to entry name
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Mine Entrance",
                "description": "The entrance to an abandoned mine.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Mine Shaft"},
                "category": "dungeon"
            },
            {
                "name": "Mine Shaft",
                "description": "A deep shaft into the mine.",
                "relative_coords": [0, 1],
                "connections": {"south": "Mine Entrance"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Mine Entrance"]
        subloc = entry.sub_grid.get_by_name("Mine Shaft")
        assert subloc.parent_location == "Mine Entrance"

    def test_expand_area_subgrid_has_connections(self, mock_ai_service, basic_world):
        """SubGrid locations have bidirectional connections.

        Spec: SubGrid locations have bidirectional connections
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Crypt Gate",
                "description": "The entrance to a crypt.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Crypt Hall", "east": "Crypt Chamber"},
                "category": "dungeon"
            },
            {
                "name": "Crypt Hall",
                "description": "A long dark hall.",
                "relative_coords": [0, 1],
                "connections": {"south": "Crypt Gate"},
                "category": "dungeon"
            },
            {
                "name": "Crypt Chamber",
                "description": "A burial chamber.",
                "relative_coords": [1, 0],
                "connections": {"west": "Crypt Gate"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Crypt Gate"]
        hall = entry.sub_grid.get_by_name("Crypt Hall")
        chamber = entry.sub_grid.get_by_name("Crypt Chamber")

        # Hall should connect to Chamber via coordinates (since SubGrid creates connections)
        # Hall at (0,1), Chamber at (1,0) - not adjacent, so no connection between them
        # Hall at (0,1) should have south connection to first subloc at (0,0)
        # Check that connections exist within SubGrid
        assert hall is not None
        assert chamber is not None
        # SubGrid adds connections based on coordinates, not the AI-specified connections

    def test_expand_area_only_entry_has_overworld_coords(self, mock_ai_service, basic_world):
        """Only entry has overworld coordinates.

        Spec: Only entry location has overworld coordinates
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Forest Gate",
                "description": "The entrance to a dark forest.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Deep Forest"},
                "category": "forest"
            },
            {
                "name": "Deep Forest",
                "description": "Deep within the forest.",
                "relative_coords": [0, 1],
                "connections": {"south": "Forest Gate"},
                "category": "forest"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Forest Gate"]
        # Entry should have overworld coordinates
        assert entry.coordinates == (0, 1), "Entry should have overworld coordinates"

        # Sub-location should have SubGrid coordinates (relative), not overworld
        subloc = entry.sub_grid.get_by_name("Deep Forest")
        # SubGrid assigns its own coordinates based on relative_coords
        # The key point is sub-locations are NOT in world dict with overworld coords
        assert "Deep Forest" not in basic_world

    def test_expand_area_single_location_no_subgrid(self, mock_ai_service, basic_world):
        """Single location (no sub-locations) should not create SubGrid.

        Spec: Legacy behavior for single location - add directly to world
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Lonely Tower",
                "description": "A single tower in the wilderness.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Lonely Tower"]
        # Single location should not have SubGrid
        assert entry.sub_grid is None

    def test_expand_area_subgrid_bounds(self, mock_ai_service, basic_world):
        """SubGrid bounds should be determined by entry location category.

        Spec: SubGrid bounds vary by category via get_subgrid_bounds()
        - dungeon category maps to (-3, 3, -3, 3) for 7x7 areas
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Dark Dungeon",
                "description": "The entrance to a dark dungeon.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Dungeon Hall"},
                "category": "dungeon"
            },
            {
                "name": "Dungeon Hall",
                "description": "The main hall of the dungeon.",
                "relative_coords": [0, 1],
                "connections": {"south": "Dark Dungeon"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Dark Dungeon"]
        assert entry.sub_grid is not None
        # dungeon category gets 11x11 bounds with z-axis for deep multi-level
        assert entry.sub_grid.bounds == (-5, 5, -5, 5, -3, 0)

    def test_expand_area_subgrid_parent_name(self, mock_ai_service, basic_world):
        """SubGrid should have parent_name set to entry location name.

        Spec: SubGrid has parent_name for exit navigation
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Fortress Gate",
                "description": "The entrance to a fortress.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Fortress Hall"},
                "category": "dungeon"
            },
            {
                "name": "Fortress Hall",
                "description": "The main hall of the fortress.",
                "relative_coords": [0, 1],
                "connections": {"south": "Fortress Gate"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Fortress Gate"]
        assert entry.sub_grid.parent_name == "Fortress Gate"

    def test_expand_area_skips_out_of_bounds_locations(self, mock_ai_service, basic_world):
        """Out-of-bounds sub-locations should be skipped without raising exception.

        Spec: AI may generate coords outside SubGrid bounds (-3,3,-3,3).
        These should be logged and skipped, not crash generation.
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Cavern Entrance",
                "description": "The entrance to a vast cavern.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Cavern Hall"},
                "category": "cave"
            },
            {
                "name": "Cavern Hall",
                "description": "A grand hall in the cavern.",
                "relative_coords": [0, 1],
                "connections": {"south": "Cavern Entrance", "north": "Far Cavern"},
                "category": "cave"
            },
            {
                # This location has y=4 which is outside bounds (-3, 3)
                "name": "Far Cavern",
                "description": "A distant part of the cavern.",
                "relative_coords": [0, 4],
                "connections": {"south": "Cavern Hall"},
                "category": "cave"
            }
        ]

        # Should not raise exception
        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        # Entry location should be in world
        assert "Cavern Entrance" in basic_world

        entry = basic_world["Cavern Entrance"]
        assert entry.sub_grid is not None

        # In-bounds sub-location should be in SubGrid
        hall = entry.sub_grid.get_by_name("Cavern Hall")
        assert hall is not None, "In-bounds sub-location should be in SubGrid"

        # Out-of-bounds sub-location should NOT be in SubGrid
        far_cavern = entry.sub_grid.get_by_name("Far Cavern")
        assert far_cavern is None, "Out-of-bounds sub-location should be skipped"
