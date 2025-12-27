"""Tests for converting default world sub-locations to SubGrid architecture.

Spec: Phase 1, Step 6 of SubGrid migration - Default world sub-locations should use
SubGrid instead of legacy sub_locations list pattern.
"""

import pytest
from cli_rpg.world import create_default_world
from cli_rpg.world_grid import SubGrid


class TestTownSquareSubGrid:
    """Test Town Square SubGrid implementation."""

    def test_town_square_has_sub_grid(self):
        """Town Square should have a sub_grid attached (not None)."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.sub_grid is not None
        assert isinstance(town_square.sub_grid, SubGrid)

    def test_town_square_sub_grid_parent_name(self):
        """Town Square sub_grid should have correct parent_name."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.sub_grid.parent_name == "Town Square"

    def test_town_square_sub_grid_entry_is_exit_point(self):
        """Market District (entry point) should be marked as exit point."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        market_district = town_square.sub_grid.get_by_name("Market District")
        assert market_district is not None
        assert market_district.is_exit_point is True

    def test_town_square_sub_grid_contains_all_locations(self):
        """Town Square sub_grid should contain 3 locations."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        # All 3 sub-locations should be in the sub_grid
        assert town_square.sub_grid.get_by_name("Market District") is not None
        assert town_square.sub_grid.get_by_name("Guard Post") is not None
        assert town_square.sub_grid.get_by_name("Town Well") is not None

    def test_town_square_sub_locations_not_in_world_dict(self):
        """Sub-locations should NOT be in the main world dict."""
        world, _ = create_default_world()
        assert "Market District" not in world
        assert "Guard Post" not in world
        assert "Town Well" not in world


class TestForestSubGrid:
    """Test Forest SubGrid implementation."""

    def test_forest_has_sub_grid(self):
        """Forest should have a sub_grid attached."""
        world, _ = create_default_world()
        forest = world["Forest"]
        assert forest.sub_grid is not None
        assert isinstance(forest.sub_grid, SubGrid)

    def test_forest_sub_grid_parent_name(self):
        """Forest sub_grid should have correct parent_name."""
        world, _ = create_default_world()
        forest = world["Forest"]
        assert forest.sub_grid.parent_name == "Forest"

    def test_forest_sub_grid_entry_is_exit_point(self):
        """Forest Edge (entry point) should be marked as exit point."""
        world, _ = create_default_world()
        forest = world["Forest"]
        forest_edge = forest.sub_grid.get_by_name("Forest Edge")
        assert forest_edge is not None
        assert forest_edge.is_exit_point is True

    def test_forest_sub_grid_contains_all_locations(self):
        """Forest sub_grid should contain 3 locations."""
        world, _ = create_default_world()
        forest = world["Forest"]
        assert forest.sub_grid.get_by_name("Forest Edge") is not None
        assert forest.sub_grid.get_by_name("Deep Woods") is not None
        assert forest.sub_grid.get_by_name("Ancient Grove") is not None

    def test_forest_sub_locations_not_in_world_dict(self):
        """Sub-locations should NOT be in the main world dict."""
        world, _ = create_default_world()
        assert "Forest Edge" not in world
        assert "Deep Woods" not in world
        assert "Ancient Grove" not in world


class TestMillbrookSubGrid:
    """Test Millbrook Village SubGrid implementation."""

    def test_millbrook_has_sub_grid(self):
        """Millbrook Village should have a sub_grid attached."""
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        assert millbrook.sub_grid is not None
        assert isinstance(millbrook.sub_grid, SubGrid)

    def test_millbrook_sub_grid_parent_name(self):
        """Millbrook sub_grid should have correct parent_name."""
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        assert millbrook.sub_grid.parent_name == "Millbrook Village"

    def test_millbrook_sub_grid_entry_is_exit_point(self):
        """Village Square (entry point) should be marked as exit point."""
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        village_square = millbrook.sub_grid.get_by_name("Village Square")
        assert village_square is not None
        assert village_square.is_exit_point is True

    def test_millbrook_sub_grid_contains_all_locations(self):
        """Millbrook sub_grid should contain 3 locations."""
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        assert millbrook.sub_grid.get_by_name("Village Square") is not None
        assert millbrook.sub_grid.get_by_name("Inn") is not None
        assert millbrook.sub_grid.get_by_name("Blacksmith") is not None

    def test_millbrook_sub_locations_not_in_world_dict(self):
        """Sub-locations should NOT be in the main world dict."""
        world, _ = create_default_world()
        assert "Village Square" not in world
        assert "Inn" not in world
        # Note: "Blacksmith" location is the sub-location (blacksmith_loc variable)
        assert "Blacksmith" not in world


class TestAbandonedMinesSubGrid:
    """Test Abandoned Mines SubGrid implementation."""

    def test_abandoned_mines_has_sub_grid(self):
        """Abandoned Mines should have a sub_grid attached."""
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        assert mines.sub_grid is not None
        assert isinstance(mines.sub_grid, SubGrid)

    def test_abandoned_mines_sub_grid_parent_name(self):
        """Abandoned Mines sub_grid should have correct parent_name."""
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        assert mines.sub_grid.parent_name == "Abandoned Mines"

    def test_abandoned_mines_sub_grid_entry_is_exit_point(self):
        """Mine Entrance (entry point) should be marked as exit point."""
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        mine_entrance = mines.sub_grid.get_by_name("Mine Entrance")
        assert mine_entrance is not None
        assert mine_entrance.is_exit_point is True

    def test_abandoned_mines_sub_grid_contains_all_locations(self):
        """Abandoned Mines sub_grid should contain 4 locations."""
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        assert mines.sub_grid.get_by_name("Mine Entrance") is not None
        assert mines.sub_grid.get_by_name("Upper Tunnels") is not None
        assert mines.sub_grid.get_by_name("Flooded Level") is not None
        assert mines.sub_grid.get_by_name("Boss Chamber") is not None

    def test_abandoned_mines_sub_locations_not_in_world_dict(self):
        """Sub-locations should NOT be in the main world dict."""
        world, _ = create_default_world()
        assert "Mine Entrance" not in world
        assert "Upper Tunnels" not in world
        assert "Flooded Level" not in world
        assert "Boss Chamber" not in world


class TestIronholdSubGrid:
    """Test Ironhold City SubGrid implementation."""

    def test_ironhold_has_sub_grid(self):
        """Ironhold City should have a sub_grid attached."""
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        assert ironhold.sub_grid is not None
        assert isinstance(ironhold.sub_grid, SubGrid)

    def test_ironhold_sub_grid_parent_name(self):
        """Ironhold sub_grid should have correct parent_name."""
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        assert ironhold.sub_grid.parent_name == "Ironhold City"

    def test_ironhold_sub_grid_entry_is_exit_point(self):
        """Ironhold Market (entry point) should be marked as exit point."""
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        ironhold_market = ironhold.sub_grid.get_by_name("Ironhold Market")
        assert ironhold_market is not None
        assert ironhold_market.is_exit_point is True

    def test_ironhold_sub_grid_contains_all_locations(self):
        """Ironhold sub_grid should contain 4 locations."""
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        assert ironhold.sub_grid.get_by_name("Ironhold Market") is not None
        assert ironhold.sub_grid.get_by_name("Castle Ward") is not None
        assert ironhold.sub_grid.get_by_name("Slums") is not None
        assert ironhold.sub_grid.get_by_name("Temple Quarter") is not None

    def test_ironhold_sub_locations_not_in_world_dict(self):
        """Sub-locations should NOT be in the main world dict."""
        world, _ = create_default_world()
        assert "Ironhold Market" not in world
        assert "Castle Ward" not in world
        assert "Slums" not in world
        assert "Temple Quarter" not in world


class TestSubGridNavigation:
    """Test that SubGrid locations have proper coordinate-based navigation.

    Navigation between SubGrid locations is now coordinate-based, not connection-based.
    Adjacent locations are traversable based on their coordinates.
    """

    def test_town_square_grid_layout(self):
        """Market District should be adjacent to Guard Post (east) and Town Well (north)."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        market = town_square.sub_grid.get_by_name("Market District")
        guard_post = town_square.sub_grid.get_by_name("Guard Post")
        town_well = town_square.sub_grid.get_by_name("Town Well")

        # Market at (0,0), Guard Post at (1,0), Town Well at (0,1)
        assert market.coordinates == (0, 0)
        assert guard_post.coordinates == (1, 0)  # east of market
        assert town_well.coordinates == (0, 1)  # north of market

    def test_town_square_grid_adjacency(self):
        """Guard Post should be west of Market District by coordinates."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        market = town_square.sub_grid.get_by_name("Market District")
        guard_post = town_square.sub_grid.get_by_name("Guard Post")

        # Verify adjacency: Guard Post at (1,0) is east of Market at (0,0)
        assert guard_post.coordinates[0] - market.coordinates[0] == 1
        assert guard_post.coordinates[1] - market.coordinates[1] == 0

    def test_abandoned_mines_linear_progression(self):
        """Abandoned Mines should have vertical progression for dungeon."""
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]

        # Mine Entrance (0,0) -> north -> Flooded Level (0,1) -> north -> Boss Chamber (0,2)
        entrance = mines.sub_grid.get_by_name("Mine Entrance")
        flooded = mines.sub_grid.get_by_name("Flooded Level")
        boss = mines.sub_grid.get_by_name("Boss Chamber")
        upper_tunnels = mines.sub_grid.get_by_name("Upper Tunnels")

        # Verify coordinates for dungeon progression
        assert entrance.coordinates == (0, 0)
        assert flooded.coordinates == (0, 1)  # north of entrance
        assert boss.coordinates == (0, 2)  # north of flooded
        assert upper_tunnels.coordinates == (1, 0)  # east of entrance

    def test_ironhold_four_way_layout(self):
        """Ironhold Market should have adjacent locations in multiple directions."""
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        market = ironhold.sub_grid.get_by_name("Ironhold Market")
        castle_ward = ironhold.sub_grid.get_by_name("Castle Ward")
        temple_quarter = ironhold.sub_grid.get_by_name("Temple Quarter")
        slums = ironhold.sub_grid.get_by_name("Slums")

        # Market at (0,0), Castle Ward at (1,0), Temple Quarter at (0,1), Slums at (0,-1)
        assert market.coordinates == (0, 0)
        assert castle_ward.coordinates == (1, 0)  # east of market
        assert temple_quarter.coordinates == (0, 1)  # north of market
        assert slums.coordinates == (0, -1)  # south of market


class TestSubGridParentLocation:
    """Test that sub-locations have correct parent_location set."""

    def test_town_square_sub_locations_have_parent(self):
        """All Town Square sub-locations should have parent_location set."""
        world, _ = create_default_world()
        town_square = world["Town Square"]

        for name in ["Market District", "Guard Post", "Town Well"]:
            loc = town_square.sub_grid.get_by_name(name)
            assert loc.parent_location == "Town Square"

    def test_forest_sub_locations_have_parent(self):
        """All Forest sub-locations should have parent_location set."""
        world, _ = create_default_world()
        forest = world["Forest"]

        for name in ["Forest Edge", "Deep Woods", "Ancient Grove"]:
            loc = forest.sub_grid.get_by_name(name)
            assert loc.parent_location == "Forest"


class TestNonExitPointsNotExitPoints:
    """Test that non-entry locations are NOT exit points."""

    def test_non_entry_locations_not_exit_points(self):
        """Only entry locations should be exit points."""
        world, _ = create_default_world()

        # Town Square - Guard Post and Town Well should NOT be exit points
        town_square = world["Town Square"]
        guard_post = town_square.sub_grid.get_by_name("Guard Post")
        town_well = town_square.sub_grid.get_by_name("Town Well")
        assert guard_post.is_exit_point is False
        assert town_well.is_exit_point is False

        # Forest - Deep Woods and Ancient Grove should NOT be exit points
        forest = world["Forest"]
        deep_woods = forest.sub_grid.get_by_name("Deep Woods")
        ancient_grove = forest.sub_grid.get_by_name("Ancient Grove")
        assert deep_woods.is_exit_point is False
        assert ancient_grove.is_exit_point is False


class TestOverworldStillHasSubLocationsList:
    """Test that overworld landmarks still have sub_locations list for display purposes."""

    def test_town_square_has_sub_locations_list(self):
        """Town Square should still have sub_locations list for UI."""
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.sub_locations == ["Market District", "Guard Post", "Town Well"]

    def test_forest_has_sub_locations_list(self):
        """Forest should still have sub_locations list for UI."""
        world, _ = create_default_world()
        forest = world["Forest"]
        assert forest.sub_locations == ["Forest Edge", "Deep Woods", "Ancient Grove"]
