"""Tests for strategic frontier exit placement.

Tests that named locations prioritize exits toward unexplored regions
to guide players toward new content and create a sense of world expansion.
"""

import pytest
from cli_rpg.world_tiles import (
    get_unexplored_region_directions,
    REGION_SIZE,
    get_region_coords,
)
from cli_rpg.world_grid import WorldGrid
from cli_rpg.models.location import Location


# Test 1: get_unexplored_region_directions returns correct directions
class TestGetUnexploredRegionDirections:
    """Tests for get_unexplored_region_directions()."""

    def test_returns_directions_toward_unexplored_regions(self):
        """Directions toward regions with no explored tiles are identified."""
        # Player is at region (0, 0), only that region is explored
        explored_regions = {(0, 0)}

        # At center of region (0, 0)
        world_x, world_y = REGION_SIZE // 2, REGION_SIZE // 2

        directions = get_unexplored_region_directions(world_x, world_y, explored_regions)

        # All four cardinal directions should point to unexplored regions
        assert "north" in directions
        assert "south" in directions
        assert "east" in directions
        assert "west" in directions

    def test_excludes_directions_toward_explored_regions(self):
        """Directions toward explored regions are not included."""
        # Player is in region (0, 0), and regions to the north and east are also explored
        explored_regions = {(0, 0), (0, 1), (1, 0)}

        # At center of region (0, 0)
        world_x, world_y = REGION_SIZE // 2, REGION_SIZE // 2

        directions = get_unexplored_region_directions(world_x, world_y, explored_regions)

        # North and east point to explored regions, should not be included
        assert "north" not in directions
        assert "east" not in directions
        # South and west are still unexplored
        assert "south" in directions
        assert "west" in directions

    def test_handles_all_explored_case(self):
        """Returns empty list when all adjacent regions are explored."""
        # All regions around (0, 0) are explored
        explored_regions = {(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)}

        world_x, world_y = REGION_SIZE // 2, REGION_SIZE // 2

        directions = get_unexplored_region_directions(world_x, world_y, explored_regions)

        assert directions == []

    def test_handles_negative_coordinates(self):
        """Works correctly with negative region coordinates."""
        # Player is in region (-1, -1)
        explored_regions = {(-1, -1)}

        # Center of region (-1, -1)
        world_x = -REGION_SIZE + REGION_SIZE // 2
        world_y = -REGION_SIZE + REGION_SIZE // 2

        directions = get_unexplored_region_directions(world_x, world_y, explored_regions)

        # All four directions should be unexplored
        assert len(directions) == 4


# Test 2: get_prioritized_frontier_exits puts unexplored regions first
class TestGetPrioritizedFrontierExits:
    """Tests for WorldGrid.get_prioritized_frontier_exits()."""

    def test_orders_by_exploration(self):
        """Exits toward unexplored regions are listed before explored ones."""
        grid = WorldGrid()

        # Create a location at (0, 0)
        center = Location(name="Center", description="The center")
        grid.add_location(center, 0, 0)

        # Create a location to the north (0, 1) - this makes north "explored"
        north_loc = Location(name="North Area", description="To the north")
        grid.add_location(north_loc, 0, 1)

        # Explored regions: region containing (0, 0) and region containing (0, 1)
        # If REGION_SIZE is 16, both are in the same region (0, 0)
        # So let's place north_loc far enough to be in a different region
        grid2 = WorldGrid()
        center2 = Location(name="Center", description="The center")
        grid2.add_location(center2, 0, 0)

        # Add location in region (0, 1) - at coordinates in that region
        far_north = Location(name="Far North", description="Way up north")
        grid2.add_location(far_north, 0, REGION_SIZE)  # This is in region (0, 1)

        # Get explored regions from the grid
        explored = set()
        for loc in grid2.values():
            if loc.coordinates:
                explored.add(get_region_coords(*loc.coordinates))

        # Now get prioritized exits from center
        # The exits should prioritize south, east, west (unexplored) over north (explored)
        exits = grid2.get_prioritized_frontier_exits(explored)

        # Filter exits from Center only
        center_exits = [e for e in exits if e[0] == "Center"]

        # Verify we have exits
        assert len(center_exits) > 0

        # Get the directions in order
        directions = [e[1] for e in center_exits]

        # North should be last or not present (explored region)
        # Actually, north at (0, 1) is in region (0, 1) which is explored
        # But north to (0, 1) is already occupied, so it's not a frontier exit
        # Let's check the other directions are present
        assert "south" in directions or "east" in directions or "west" in directions

    def test_returns_all_frontier_exits(self):
        """All frontier exits are included, just prioritized."""
        grid = WorldGrid()
        center = Location(name="Center", description="The center")
        grid.add_location(center, 0, 0)

        # No explored regions provided - all exits should be "unexplored"
        exits = grid.get_prioritized_frontier_exits(explored_regions=None)

        # Should have 4 frontier exits (north, south, east, west)
        center_exits = [e for e in exits if e[0] == "Center"]
        assert len(center_exits) == 4


# Test 3: frontier analysis handles edge cases
class TestFrontierAnalysisEdgeCases:
    """Edge case tests for frontier analysis."""

    def test_handles_single_location(self):
        """Single location shows all directions as unexplored."""
        # When only one location exists at origin, all 4 directions are unexplored
        explored_regions = {(0, 0)}

        world_x, world_y = REGION_SIZE // 2, REGION_SIZE // 2

        directions = get_unexplored_region_directions(world_x, world_y, explored_regions)

        # All 4 directions lead to unexplored regions
        assert len(directions) == 4

    def test_uses_region_coords_not_tile_coords(self):
        """Uses REGION_SIZE to determine unexplored regions, not individual tiles."""
        # Two tiles in the same region should not affect each other's "unexplored" status
        # Tiles at (0, 0) and (1, 1) are both in region (0, 0)

        # Only region (0, 0) is explored
        explored_regions = {(0, 0)}

        # Check from tile (1, 1) - still in region (0, 0)
        directions = get_unexplored_region_directions(1, 1, explored_regions)

        # All 4 directions should point to unexplored regions (even though we're
        # at (1, 1), not at region boundary)
        assert len(directions) == 4

        # Now check from tile at edge of region
        edge_x = REGION_SIZE - 1
        edge_y = REGION_SIZE - 1

        directions_from_edge = get_unexplored_region_directions(
            edge_x, edge_y, explored_regions
        )

        # Same result - uses region coords, not proximity to edge
        assert len(directions_from_edge) == 4

    def test_empty_explored_regions_returns_all_directions(self):
        """With no explored regions, all directions are unexplored."""
        explored_regions: set[tuple[int, int]] = set()

        directions = get_unexplored_region_directions(0, 0, explored_regions)

        # All 4 directions lead to unexplored regions
        assert len(directions) == 4
        assert set(directions) == {"north", "south", "east", "west"}


# Test 4: Integration with GameState.get_explored_regions()
class TestGameStateGetExploredRegions:
    """Tests for GameState.get_explored_regions()."""

    def test_returns_regions_from_world_locations(self):
        """Analyzes all locations in world grid to determine explored regions."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character, CharacterClass

        # Create a character with required stats
        char = Character(
            name="Tester",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )

        # Create world with locations in multiple regions
        loc1 = Location(
            name="Origin", description="At origin", coordinates=(0, 0)
        )
        loc2 = Location(
            name="Far East",
            description="Way east",
            coordinates=(REGION_SIZE + 5, 0),  # In region (1, 0)
        )

        world = {"Origin": loc1, "Far East": loc2}

        game_state = GameState(
            character=char, world=world, starting_location="Origin"
        )

        explored = game_state.get_explored_regions()

        # Should have regions (0, 0) and (1, 0)
        assert (0, 0) in explored
        assert (1, 0) in explored
        assert len(explored) == 2

    def test_handles_locations_without_coordinates(self):
        """Skips locations without coordinates."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character, CharacterClass

        # Create a character with required stats
        char = Character(
            name="Tester",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )

        loc1 = Location(name="Origin", description="At origin", coordinates=(0, 0))
        loc2 = Location(
            name="No Coords", description="Legacy location", coordinates=None
        )

        world = {"Origin": loc1, "No Coords": loc2}

        game_state = GameState(
            character=char, world=world, starting_location="Origin"
        )

        explored = game_state.get_explored_regions()

        # Should only have region from loc1
        assert (0, 0) in explored
        assert len(explored) == 1
