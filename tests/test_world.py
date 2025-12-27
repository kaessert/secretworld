"""Tests for world module."""

import pytest
from unittest.mock import Mock, patch
from cli_rpg.world import create_default_world, create_world
from cli_rpg.models.location import Location


class TestCreateDefaultWorld:
    """Tests for create_default_world() function."""
    
    def test_default_world_returns_tuple(self):
        """Test that create_default_world() returns a tuple.
        
        Spec (Fix): create_default_world() must return tuple (world, starting_location)
        """
        result = create_default_world()
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_default_world_tuple_contains_world_and_starting_location(self):
        """Test that tuple contains world dict and starting location string.
        
        Spec (Fix): Tuple must contain (dict[str, Location], str)
        """
        world, starting_location = create_default_world()
        assert isinstance(world, dict)
        assert isinstance(starting_location, str)
        assert len(starting_location) > 0
    
    def test_default_world_starting_location_is_town_square(self):
        """Test that default world returns "Town Square" as starting location.
        
        Spec (Fix): Default world must return "Town Square" as starting location
        """
        world, starting_location = create_default_world()
        assert starting_location == "Town Square"
    
    def test_default_world_starting_location_exists_in_world(self):
        """Test that starting location exists in world dict.
        
        Spec (Fix): Starting location must exist in returned world
        """
        world, starting_location = create_default_world()
        assert starting_location in world
    
    def test_default_world_location_count_with_sublocations(self):
        """Test that default world has 6 overworld locations (sub-locations in sub_grids).

        Spec: World dict has 6 overworld locations. Sub-locations accessed via sub_grid.
        """
        world, _ = create_default_world()
        # Only overworld locations are in world dict now
        assert len(world) == 6
    
    def test_default_world_location_names(self):
        """Test that default world has correct location names.

        Spec: Locations should be "Town Square", "Forest", "Cave" (sub-locations in sub_grid)
        """
        world, _ = create_default_world()
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world
        # Sub-locations are now in sub_grid, not world dict
        town_square = world["Town Square"]
        assert town_square.sub_grid.get_by_name("Market District") is not None
        assert town_square.sub_grid.get_by_name("Guard Post") is not None
        assert town_square.sub_grid.get_by_name("Town Well") is not None

    def test_default_world_town_square_is_overworld(self):
        """Town Square is an overworld landmark with sub-locations.

        Spec: Town Square is overworld with 2+ sub-locations
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.is_overworld is True
        assert town_square.is_safe_zone is True
        assert len(town_square.sub_locations) >= 2
        assert town_square.entry_point in town_square.sub_locations

    def test_default_world_sub_locations_exist(self):
        """All Town Square sub-locations exist in sub_grid.

        Spec: Sub-locations listed in town_square.sub_locations are in sub_grid
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        for sub_name in town_square.sub_locations:
            sub = town_square.sub_grid.get_by_name(sub_name)
            assert sub is not None, f"Sub-location '{sub_name}' not in sub_grid"

    def test_default_world_sub_locations_have_parent(self):
        """Sub-locations reference Town Square as parent.

        Spec: Each sub-location has parent_location="Town Square" and is_safe_zone=True
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        for sub_name in town_square.sub_locations:
            sub = town_square.sub_grid.get_by_name(sub_name)
            assert sub.parent_location == "Town Square"
            assert sub.is_safe_zone is True

    def test_default_world_sub_locations_have_coordinates(self):
        """Sub-locations have coordinates for grid-based navigation.

        Spec: Sub-locations use coordinate-based navigation within SubGrid
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        # Entry point (Market District) should have coordinates
        entry = town_square.sub_grid.get_by_name("Market District")
        guard_post = town_square.sub_grid.get_by_name("Guard Post")
        town_well = town_square.sub_grid.get_by_name("Town Well")
        # With SubGrid, entry is at (0,0), adjacent rooms via coordinates
        assert entry.coordinates == (0, 0)
        assert guard_post.coordinates is not None  # east of entry
        assert town_well.coordinates is not None  # north of entry

    def test_default_world_merchant_in_market_district(self):
        """Merchant NPC is in Market District sub-location.

        Spec: Merchant NPC moved to Market District with is_merchant=True
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        market = town_square.sub_grid.get_by_name("Market District")
        merchant = market.find_npc_by_name("Merchant")
        assert merchant is not None
        assert merchant.is_merchant is True

    # Forest hierarchical sub-location tests

    def test_default_world_forest_is_overworld(self):
        """Forest is an overworld landmark with sub-locations.

        Spec: Forest is overworld danger zone with 2+ sub-locations
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        assert forest.is_overworld is True
        assert forest.is_safe_zone is False  # Danger zone
        assert len(forest.sub_locations) >= 2
        assert forest.entry_point in forest.sub_locations

    def test_default_world_forest_sub_locations_exist(self):
        """All Forest sub-locations exist in sub_grid.

        Spec: Sub-locations listed in forest.sub_locations are in sub_grid
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        for sub_name in forest.sub_locations:
            sub = forest.sub_grid.get_by_name(sub_name)
            assert sub is not None, f"Sub-location '{sub_name}' not in sub_grid"

    def test_default_world_forest_sub_locations_have_parent(self):
        """Forest sub-locations reference Forest as parent and are danger zones.

        Spec: Each sub-location has parent_location="Forest" and is_safe_zone=False
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        for sub_name in forest.sub_locations:
            sub = forest.sub_grid.get_by_name(sub_name)
            assert sub.parent_location == "Forest"
            assert sub.is_safe_zone is False  # All danger zones

    def test_default_world_forest_sub_locations_have_coordinates(self):
        """Forest sub-locations have coordinates for grid-based navigation.

        Spec: Forest sub-locations use coordinate-based navigation
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        # Entry point (Forest Edge) should have coordinates
        entry = forest.sub_grid.get_by_name("Forest Edge")
        deep_woods = forest.sub_grid.get_by_name("Deep Woods")
        assert entry.coordinates == (0, 0)
        assert deep_woods.coordinates is not None  # Adjacent to entry

    def test_default_world_hermit_in_ancient_grove(self):
        """Hermit NPC is in Ancient Grove and is recruitable.

        Spec: Hermit NPC in Ancient Grove with is_recruitable=True
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        grove = forest.sub_grid.get_by_name("Ancient Grove")
        hermit = grove.find_npc_by_name("Hermit")
        assert hermit is not None
        assert hermit.is_recruitable is True

    # Millbrook Village hierarchical sub-location tests

    def test_default_world_millbrook_village_exists(self):
        """Millbrook Village exists in world dict.

        Spec: Millbrook Village is a location in the default world
        """
        world, _ = create_default_world()
        assert "Millbrook Village" in world

    def test_default_world_millbrook_village_is_overworld(self):
        """Millbrook Village is an overworld landmark with sub-locations.

        Spec: Millbrook Village is overworld safe zone with 3 sub-locations
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        assert millbrook.is_overworld is True
        assert millbrook.is_safe_zone is True
        assert len(millbrook.sub_locations) == 3
        assert millbrook.entry_point in millbrook.sub_locations

    def test_default_world_millbrook_village_sub_locations_exist(self):
        """All Millbrook Village sub-locations exist in sub_grid.

        Spec: Sub-locations listed in millbrook.sub_locations are in sub_grid
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        for sub_name in millbrook.sub_locations:
            sub = millbrook.sub_grid.get_by_name(sub_name)
            assert sub is not None, f"Sub-location '{sub_name}' not in sub_grid"

    def test_default_world_millbrook_village_sub_locations_have_parent(self):
        """Millbrook Village sub-locations reference Millbrook Village as parent and are safe zones.

        Spec: Each sub-location has parent_location="Millbrook Village" and is_safe_zone=True
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        for sub_name in millbrook.sub_locations:
            sub = millbrook.sub_grid.get_by_name(sub_name)
            assert sub.parent_location == "Millbrook Village"
            assert sub.is_safe_zone is True

    def test_default_world_millbrook_village_sub_locations_have_coordinates(self):
        """Millbrook Village sub-locations have coordinates for grid-based navigation.

        Spec: Millbrook Village sub-locations use coordinate-based navigation
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        # Entry point (Village Square) should have coordinates
        entry = millbrook.sub_grid.get_by_name("Village Square")
        assert entry.coordinates == (0, 0)

    def test_default_world_millbrook_village_coordinates(self):
        """Millbrook Village is west of Town Square.

        Spec: Millbrook Village coordinates are west of Town Square
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        town_square = world["Town Square"]
        # Millbrook is west (-1,0) of Town Square (0,0)
        assert millbrook.coordinates[0] == town_square.coordinates[0] - 1
        assert millbrook.coordinates[1] == town_square.coordinates[1]

    def test_default_world_town_square_has_west_neighbor(self):
        """Town Square has Millbrook Village to its west.

        Spec: Millbrook Village is at coordinates west of Town Square
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        millbrook = world["Millbrook Village"]
        # Verify relative positions
        assert millbrook.coordinates == (town_square.coordinates[0] - 1, town_square.coordinates[1])

    def test_default_world_elder_in_village_square(self):
        """Elder NPC is in Village Square.

        Spec: Elder NPC exists in Village Square sub-location
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        village_square = millbrook.sub_grid.get_by_name("Village Square")
        elder = village_square.find_npc_by_name("Elder")
        assert elder is not None

    def test_default_world_innkeeper_in_inn(self):
        """Innkeeper NPC is in Inn and is recruitable.

        Spec: Innkeeper NPC in Inn with is_recruitable=True
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        inn = millbrook.sub_grid.get_by_name("Inn")
        innkeeper = inn.find_npc_by_name("Innkeeper")
        assert innkeeper is not None
        assert innkeeper.is_recruitable is True

    def test_default_world_blacksmith_in_blacksmith(self):
        """Blacksmith NPC is in Blacksmith and is a merchant.

        Spec: Blacksmith NPC in Blacksmith with is_merchant=True
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        blacksmith_loc = millbrook.sub_grid.get_by_name("Blacksmith")
        blacksmith = blacksmith_loc.find_npc_by_name("Blacksmith")
        assert blacksmith is not None
        assert blacksmith.is_merchant is True

    # Abandoned Mines hierarchical dungeon tests

    def test_default_world_abandoned_mines_exists(self):
        """Abandoned Mines exists in world dict.

        Spec: Abandoned Mines is a location in the default world
        """
        world, _ = create_default_world()
        assert "Abandoned Mines" in world

    def test_default_world_abandoned_mines_is_overworld(self):
        """Abandoned Mines is an overworld dungeon with sub-locations.

        Spec: Abandoned Mines is overworld danger zone with 4 sub-locations
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        assert mines.is_overworld is True
        assert mines.is_safe_zone is False  # Danger zone
        assert len(mines.sub_locations) == 4
        assert mines.entry_point == "Mine Entrance"

    def test_default_world_abandoned_mines_sub_locations_exist(self):
        """All Abandoned Mines sub-locations exist in sub_grid.

        Spec: Sub-locations listed in abandoned_mines.sub_locations are in sub_grid
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            sub = mines.sub_grid.get_by_name(sub_name)
            assert sub is not None, f"Sub-location '{sub_name}' not in sub_grid"

    def test_default_world_abandoned_mines_sub_locations_have_parent(self):
        """Abandoned Mines sub-locations reference Abandoned Mines as parent and are danger zones.

        Spec: Each sub-location has parent_location="Abandoned Mines" and is_safe_zone=False
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            sub = mines.sub_grid.get_by_name(sub_name)
            assert sub.parent_location == "Abandoned Mines"
            assert sub.is_safe_zone is False  # All danger zones

    def test_default_world_abandoned_mines_sub_locations_have_dungeon_category(self):
        """Abandoned Mines sub-locations have category="dungeon".

        Spec: All Mines sub-locations have category="dungeon"
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            sub = mines.sub_grid.get_by_name(sub_name)
            assert sub.category == "dungeon"

    def test_default_world_abandoned_mines_sub_locations_have_coordinates(self):
        """Abandoned Mines sub-locations have coordinates for grid-based navigation.

        Spec: Mines sub-locations use coordinate-based navigation (dungeon progression)
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        # Entry point (Mine Entrance) should have coordinates
        entry = mines.sub_grid.get_by_name("Mine Entrance")
        assert entry.coordinates == (0, 0)

    def test_default_world_abandoned_mines_coordinates(self):
        """Abandoned Mines is north of Cave.

        Spec: Abandoned Mines coordinates are north of Cave
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        cave = world["Cave"]
        # Mines is north of Cave
        assert mines.coordinates[1] == cave.coordinates[1] + 1

    def test_default_world_cave_north_neighbor(self):
        """Cave has Abandoned Mines to its north.

        Spec: Abandoned Mines is at coordinates north of Cave
        """
        world, _ = create_default_world()
        cave = world["Cave"]
        mines = world["Abandoned Mines"]
        # Verify relative positions
        assert mines.coordinates == (cave.coordinates[0], cave.coordinates[1] + 1)

    def test_default_world_old_miner_in_mine_entrance(self):
        """Old Miner NPC is in Mine Entrance.

        Spec: Old Miner NPC exists in Mine Entrance sub-location
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        mine_entrance = mines.sub_grid.get_by_name("Mine Entrance")
        old_miner = mine_entrance.find_npc_by_name("Old Miner")
        assert old_miner is not None

    # Ironhold City hierarchical sub-location tests

    def test_default_world_ironhold_city_exists(self):
        """Ironhold City exists in world dict.

        Spec: Ironhold City is a location in the default world
        """
        world, _ = create_default_world()
        assert "Ironhold City" in world

    def test_default_world_ironhold_city_is_overworld(self):
        """Ironhold City is an overworld landmark with 4 sub-locations.

        Spec: Ironhold City is overworld safe zone with 4 sub-locations, entry_point="Ironhold Market"
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        assert ironhold.is_overworld is True
        assert ironhold.is_safe_zone is True
        assert len(ironhold.sub_locations) == 4
        assert ironhold.entry_point == "Ironhold Market"

    def test_default_world_ironhold_city_sub_locations_exist(self):
        """All Ironhold City sub-locations exist in sub_grid.

        Spec: Sub-locations listed in ironhold.sub_locations are in sub_grid
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        for sub_name in ironhold.sub_locations:
            sub = ironhold.sub_grid.get_by_name(sub_name)
            assert sub is not None, f"Sub-location '{sub_name}' not in sub_grid"

    def test_default_world_ironhold_city_sub_locations_have_parent(self):
        """Ironhold City sub-locations reference Ironhold City as parent and are safe zones.

        Spec: Each sub-location has parent_location="Ironhold City" and is_safe_zone=True
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        for sub_name in ironhold.sub_locations:
            sub = ironhold.sub_grid.get_by_name(sub_name)
            assert sub.parent_location == "Ironhold City"
            assert sub.is_safe_zone is True

    def test_default_world_ironhold_city_sub_locations_have_coordinates(self):
        """Ironhold City sub-locations have coordinates for grid-based navigation.

        Spec: Ironhold City sub-locations use coordinate-based navigation
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        # Entry point (Ironhold Market) should have coordinates
        entry = ironhold.sub_grid.get_by_name("Ironhold Market")
        assert entry.coordinates == (0, 0)

    def test_default_world_ironhold_city_coordinates(self):
        """Ironhold City is south of Town Square.

        Spec: Ironhold City coordinates are south of Town Square
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        town_square = world["Town Square"]
        # Ironhold is south (0,-1) of Town Square (0,0)
        assert ironhold.coordinates[1] == town_square.coordinates[1] - 1

    def test_default_world_town_square_south_neighbor(self):
        """Town Square has Ironhold City to its south.

        Spec: Ironhold City is at coordinates south of Town Square
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        ironhold = world["Ironhold City"]
        # Verify relative positions
        assert ironhold.coordinates == (town_square.coordinates[0], town_square.coordinates[1] - 1)

    def test_default_world_merchant_in_ironhold_market(self):
        """Wealthy Merchant NPC is in Ironhold Market.

        Spec: Wealthy Merchant NPC in Ironhold Market with is_merchant=True
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        market = ironhold.sub_grid.get_by_name("Ironhold Market")
        merchant = market.find_npc_by_name("Wealthy Merchant")
        assert merchant is not None
        assert merchant.is_merchant is True

    def test_default_world_captain_in_castle_ward(self):
        """Captain of the Guard NPC is in Castle Ward.

        Spec: Captain of the Guard NPC exists in Castle Ward sub-location
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        castle_ward = ironhold.sub_grid.get_by_name("Castle Ward")
        captain = castle_ward.find_npc_by_name("Captain of the Guard")
        assert captain is not None

    def test_default_world_beggar_in_slums(self):
        """Beggar NPC is in Slums and is recruitable.

        Spec: Beggar NPC in Slums with is_recruitable=True
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        slums = ironhold.sub_grid.get_by_name("Slums")
        beggar = slums.find_npc_by_name("Beggar")
        assert beggar is not None
        assert beggar.is_recruitable is True

    def test_default_world_priest_in_temple_quarter(self):
        """Priest NPC is in Temple Quarter.

        Spec: Priest NPC exists in Temple Quarter sub-location
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        temple_quarter = ironhold.sub_grid.get_by_name("Temple Quarter")
        priest = temple_quarter.find_npc_by_name("Priest")
        assert priest is not None

    def test_default_world_all_valid_locations(self):
        """Test that all values in world dict are Location instances.
        
        Spec: All values must be Location objects
        """
        world, _ = create_default_world()
        for location in world.values():
            assert isinstance(location, Location)
    
    def test_default_world_town_square_neighbor_locations(self):
        """Test Town Square has correct neighbors by coordinates.

        Spec: Town Square has Forest to north, Cave to east
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        forest = world["Forest"]
        cave = world["Cave"]
        # Forest is north (+y) of Town Square
        assert forest.coordinates == (town_square.coordinates[0], town_square.coordinates[1] + 1)
        # Cave is east (+x) of Town Square
        assert cave.coordinates == (town_square.coordinates[0] + 1, town_square.coordinates[1])

    def test_default_world_forest_location(self):
        """Test Forest is positioned north of Town Square.

        Spec: Forest is at (0, 1), south of which is Town Square at (0, 0)
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        town_square = world["Town Square"]
        assert forest.coordinates == (0, 1)
        assert town_square.coordinates == (0, 0)

    def test_default_world_cave_location(self):
        """Test Cave is positioned east of Town Square.

        Spec: Cave is at (1, 0), west of which is Town Square at (0, 0)
        """
        world, _ = create_default_world()
        cave = world["Cave"]
        town_square = world["Town Square"]
        assert cave.coordinates == (1, 0)
        assert town_square.coordinates == (0, 0)
    
    def test_default_world_locations_have_descriptions(self):
        """Test that all locations have non-empty descriptions.
        
        Spec: All locations must have descriptions
        """
        world, _ = create_default_world()
        for location in world.values():
            assert location.description
            assert len(location.description) > 0
    
    def test_default_world_immutable_returns(self):
        """Test that multiple calls return independent copies.

        Spec: Each call should return a new dict with new Location instances
        """
        world1, _ = create_default_world()
        world2, _ = create_default_world()

        # Dicts should not be the same object
        assert world1 is not world2

        # Locations should not be the same objects
        assert world1["Town Square"] is not world2["Town Square"]

        # Modifying one shouldn't affect the other
        original_desc = world2["Cave"].description
        world1["Cave"].description = "Modified description"
        assert world2["Cave"].description == original_desc

    def test_default_world_locations_have_coordinates(self):
        """Test that default world locations have grid coordinates.

        Spec: Locations placed on grid have coordinates assigned.
        """
        world, _ = create_default_world()

        # Town Square at origin (0, 0)
        assert world["Town Square"].coordinates == (0, 0)
        # Forest north of Town Square (0, 1)
        assert world["Forest"].coordinates == (0, 1)
        # Cave east of Town Square (1, 0)
        assert world["Cave"].coordinates == (1, 0)

    def test_default_world_bidirectional_consistency(self):
        """Test that default world has bidirectional coordinate consistency.

        Spec: Grid-based world ensures north/south and east/west are symmetric.
        """
        world, _ = create_default_world()

        # Town Square -> Forest and Forest -> Town Square (north/south)
        town = world["Town Square"]
        forest = world["Forest"]
        assert forest.coordinates[1] == town.coordinates[1] + 1  # Forest is north
        assert forest.coordinates[0] == town.coordinates[0]  # Same x

        # Town Square -> Cave and Cave -> Town Square (east/west)
        cave = world["Cave"]
        assert cave.coordinates[0] == town.coordinates[0] + 1  # Cave is east
        assert cave.coordinates[1] == town.coordinates[1]  # Same y

    def test_default_world_all_locations_have_coordinates(self):
        """Test that every location in the world has coordinates.

        Spec: All locations must have coordinates for grid-based navigation.
        """
        world, _ = create_default_world()

        for location_name, location in world.items():
            assert location.coordinates is not None, (
                f"Location '{location_name}' has no coordinates"
            )


class TestCreateWorld:
    """Tests for create_world() function."""
    
    def test_create_world_returns_tuple(self):
        """Test that create_world() returns a tuple.
        
        Spec (Fix): create_world() must return tuple (world, starting_location)
        """
        result = create_world()
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_create_world_tuple_contains_world_and_starting_location(self):
        """Test that tuple contains world dict and starting location string.
        
        Spec (Fix): Tuple must contain (dict[str, Location], str)
        """
        world, starting_location = create_world()
        assert isinstance(world, dict)
        assert isinstance(starting_location, str)
        assert len(starting_location) > 0
    
    def test_create_world_starting_location_exists_in_world(self):
        """Test that starting location exists in world dict.
        
        Spec (Fix): Starting location must exist in returned world
        """
        world, starting_location = create_world()
        assert starting_location in world
    
    def test_create_world_without_ai_returns_default_world(self):
        """Test that create_world() without AI returns default world.
        
        Spec (Fix): create_world() without AI service returns default world tuple
        """
        world, starting_location = create_world(ai_service=None, theme="fantasy")
        assert starting_location == "Town Square"
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world
    
    @patch('cli_rpg.world.create_ai_world')
    def test_create_world_with_ai_returns_ai_world_tuple(self, mock_create_ai_world):
        """Test that create_world() with AI returns tuple from create_ai_world().
        
        Spec (Fix): create_world() with AI service returns tuple from create_ai_world()
        """
        # Mock AI world generation
        mock_world = {"Central Plaza": Location("Central Plaza", "A central plaza")}
        mock_create_ai_world.return_value = (mock_world, "Central Plaza")
        
        mock_ai_service = Mock()
        world, starting_location = create_world(ai_service=mock_ai_service, theme="sci-fi")
        
        assert world == mock_world
        assert starting_location == "Central Plaza"
        mock_create_ai_world.assert_called_once()
    
    @patch('cli_rpg.world.create_ai_world')
    def test_create_world_raises_on_ai_error_in_strict_mode(self, mock_create_ai_world):
        """Test that create_world() raises exception on AI error in strict mode.

        Spec: When AI service is configured and provided, AI generation failures
        must raise an exception (no silent fallback) when strict=True (default)
        """
        # Mock AI world generation to fail
        mock_create_ai_world.side_effect = Exception("AI generation failed")

        mock_ai_service = Mock()
        with pytest.raises(Exception, match="AI generation failed"):
            create_world(ai_service=mock_ai_service, theme="fantasy", strict=True)

    @patch('cli_rpg.world.create_ai_world')
    def test_create_world_raises_by_default_on_ai_error(self, mock_create_ai_world):
        """Test that create_world() raises exception on AI error by default.

        Spec: strict=True is the default, so AI failures raise exceptions by default
        """
        # Mock AI world generation to fail
        mock_create_ai_world.side_effect = Exception("AI generation failed")

        mock_ai_service = Mock()
        # Default behavior (no strict parameter) should be strict mode
        with pytest.raises(Exception, match="AI generation failed"):
            create_world(ai_service=mock_ai_service, theme="fantasy")

    @patch('cli_rpg.world.create_ai_world')
    def test_create_world_falls_back_on_ai_error_in_non_strict_mode(self, mock_create_ai_world):
        """Test that create_world() falls back to default on AI error when strict=False.

        Spec: When strict=False, keep existing fallback behavior for backward compatibility
        """
        # Mock AI world generation to fail
        mock_create_ai_world.side_effect = Exception("AI generation failed")

        mock_ai_service = Mock()
        world, starting_location = create_world(
            ai_service=mock_ai_service, theme="fantasy", strict=False
        )

        # Should return default world tuple
        assert starting_location == "Town Square"
        assert "Town Square" in world

    @patch('cli_rpg.world.create_ai_world')
    def test_create_world_logs_warning_on_ai_failure_non_strict(self, mock_create_ai_world, caplog):
        """Test that warning is logged when AI fails in non-strict mode.

        Spec: When AI world generation fails in non-strict mode, a warning should be
        logged before falling back to default world (lines 144-146).
        """
        import logging

        # Mock AI world generation to fail
        mock_create_ai_world.side_effect = Exception("AI failed")
        mock_ai_service = Mock()

        # Capture at INFO level to get both WARNING and INFO logs
        with caplog.at_level(logging.INFO, logger='cli_rpg.world'):
            world, starting_location = create_world(
                ai_service=mock_ai_service, theme="fantasy", strict=False
            )

        # Verify warning was logged for the failure
        assert "AI world generation failed" in caplog.text
        # Verify info was logged for the fallback
        assert "Falling back to default world" in caplog.text

        # Should still return default world
        assert starting_location == "Town Square"
        assert "Town Square" in world

    def test_create_world_uses_default_when_no_ai_service(self, caplog):
        """Test that create_world uses default world when no AI service provided.

        Spec: When ai_service is None, should use default world (lines 149-151).
        """
        world, starting_location = create_world(ai_service=None)

        # Should return default world
        assert starting_location == "Town Square"
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world

    @patch('cli_rpg.world.AI_AVAILABLE', False)
    def test_create_world_with_ai_service_but_ai_unavailable(self):
        """Test that create_world uses default when AI is unavailable (lines 18-21, 131).

        Spec: When AI_AVAILABLE is False, should use default world even if
        ai_service is provided.
        """
        mock_ai_service = Mock()
        world, starting_location = create_world(ai_service=mock_ai_service, theme="fantasy")

        # Should return default world (not AI world)
        assert starting_location == "Town Square"
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world
        # AI service should not have been called
        mock_ai_service.generate_location.assert_not_called()

    @patch('cli_rpg.world.create_ai_world')
    def test_create_world_nonstrict_success_path(self, mock_create_ai_world):
        """Test that create_world non-strict mode returns AI world on success (line 142).

        Spec: When strict=False and AI succeeds, should return AI world.
        This covers line 142 (return in non-strict try block).
        """
        # Mock AI world generation to succeed
        mock_world = {"AI Plaza": Location("AI Plaza", "An AI-generated plaza")}
        mock_create_ai_world.return_value = (mock_world, "AI Plaza")

        mock_ai_service = Mock()
        world, starting_location = create_world(
            ai_service=mock_ai_service, theme="fantasy", strict=False
        )

        # Should return AI-generated world
        assert starting_location == "AI Plaza"
        assert "AI Plaza" in world
        mock_create_ai_world.assert_called_once()
