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
        """Test that default world has 23 locations: 6 overworld + 3 Town sub + 3 Forest sub + 3 Millbrook sub + 4 Mines sub + 4 Ironhold sub.

        Spec: World has 23 locations total (6 main + 3 Town sub-locations + 3 Forest sub-locations + 3 Millbrook sub-locations + 4 Mines sub-locations + 4 Ironhold sub-locations)
        """
        world, _ = create_default_world()
        assert len(world) == 23
    
    def test_default_world_location_names(self):
        """Test that default world has correct location names.

        Spec: Locations should be "Town Square", "Forest", "Cave" + sub-locations
        """
        world, _ = create_default_world()
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world
        # Sub-locations should also exist
        assert "Market District" in world
        assert "Guard Post" in world
        assert "Town Well" in world

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
        """All Town Square sub-locations exist in world dict.

        Spec: Sub-locations listed in town_square.sub_locations are in world
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        for sub_name in town_square.sub_locations:
            assert sub_name in world, f"Sub-location '{sub_name}' not in world"

    def test_default_world_sub_locations_have_parent(self):
        """Sub-locations reference Town Square as parent.

        Spec: Each sub-location has parent_location="Town Square" and is_safe_zone=True
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        for sub_name in town_square.sub_locations:
            sub = world[sub_name]
            assert sub.parent_location == "Town Square"
            assert sub.is_safe_zone is True

    def test_default_world_sub_locations_have_no_cardinal_connections(self):
        """Sub-locations have no n/s/e/w exits (only enter/exit navigation).

        Spec: Sub-locations have no cardinal connections
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        for sub_name in town_square.sub_locations:
            sub = world[sub_name]
            assert len(sub.connections) == 0

    def test_default_world_merchant_in_market_district(self):
        """Merchant NPC is in Market District sub-location.

        Spec: Merchant NPC moved to Market District with is_merchant=True
        """
        world, _ = create_default_world()
        market = world["Market District"]
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
        """All Forest sub-locations exist in world dict.

        Spec: Sub-locations listed in forest.sub_locations are in world
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        for sub_name in forest.sub_locations:
            assert sub_name in world, f"Sub-location '{sub_name}' not in world"

    def test_default_world_forest_sub_locations_have_parent(self):
        """Forest sub-locations reference Forest as parent and are danger zones.

        Spec: Each sub-location has parent_location="Forest" and is_safe_zone=False
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        for sub_name in forest.sub_locations:
            sub = world[sub_name]
            assert sub.parent_location == "Forest"
            assert sub.is_safe_zone is False  # All danger zones

    def test_default_world_forest_sub_locations_no_cardinal_exits(self):
        """Forest sub-locations have no n/s/e/w exits (only enter/exit).

        Spec: Forest sub-locations have no cardinal connections
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        for sub_name in forest.sub_locations:
            sub = world[sub_name]
            assert len(sub.connections) == 0

    def test_default_world_hermit_in_ancient_grove(self):
        """Hermit NPC is in Ancient Grove and is recruitable.

        Spec: Hermit NPC in Ancient Grove with is_recruitable=True
        """
        world, _ = create_default_world()
        grove = world["Ancient Grove"]
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
        """All Millbrook Village sub-locations exist in world dict.

        Spec: Sub-locations listed in millbrook.sub_locations are in world
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        for sub_name in millbrook.sub_locations:
            assert sub_name in world, f"Sub-location '{sub_name}' not in world"

    def test_default_world_millbrook_village_sub_locations_have_parent(self):
        """Millbrook Village sub-locations reference Millbrook Village as parent and are safe zones.

        Spec: Each sub-location has parent_location="Millbrook Village" and is_safe_zone=True
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        for sub_name in millbrook.sub_locations:
            sub = world[sub_name]
            assert sub.parent_location == "Millbrook Village"
            assert sub.is_safe_zone is True

    def test_default_world_millbrook_village_sub_locations_no_cardinal_exits(self):
        """Millbrook Village sub-locations have no n/s/e/w exits (only enter/exit).

        Spec: Millbrook Village sub-locations have no cardinal connections
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        for sub_name in millbrook.sub_locations:
            sub = world[sub_name]
            assert len(sub.connections) == 0

    def test_default_world_millbrook_village_connections(self):
        """Millbrook Village has east connection to Town Square.

        Spec: Millbrook Village has east->Town Square
        """
        world, _ = create_default_world()
        millbrook = world["Millbrook Village"]
        assert millbrook.get_connection("east") == "Town Square"

    def test_default_world_town_square_has_west_connection(self):
        """Town Square has west connection to Millbrook Village.

        Spec: Town Square has west->Millbrook Village
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.get_connection("west") == "Millbrook Village"

    def test_default_world_elder_in_village_square(self):
        """Elder NPC is in Village Square.

        Spec: Elder NPC exists in Village Square sub-location
        """
        world, _ = create_default_world()
        village_square = world["Village Square"]
        elder = village_square.find_npc_by_name("Elder")
        assert elder is not None

    def test_default_world_innkeeper_in_inn(self):
        """Innkeeper NPC is in Inn and is recruitable.

        Spec: Innkeeper NPC in Inn with is_recruitable=True
        """
        world, _ = create_default_world()
        inn = world["Inn"]
        innkeeper = inn.find_npc_by_name("Innkeeper")
        assert innkeeper is not None
        assert innkeeper.is_recruitable is True

    def test_default_world_blacksmith_in_blacksmith(self):
        """Blacksmith NPC is in Blacksmith and is a merchant.

        Spec: Blacksmith NPC in Blacksmith with is_merchant=True
        """
        world, _ = create_default_world()
        blacksmith_loc = world["Blacksmith"]
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
        """All Abandoned Mines sub-locations exist in world dict.

        Spec: Sub-locations listed in abandoned_mines.sub_locations are in world
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            assert sub_name in world, f"Sub-location '{sub_name}' not in world"

    def test_default_world_abandoned_mines_sub_locations_have_parent(self):
        """Abandoned Mines sub-locations reference Abandoned Mines as parent and are danger zones.

        Spec: Each sub-location has parent_location="Abandoned Mines" and is_safe_zone=False
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            sub = world[sub_name]
            assert sub.parent_location == "Abandoned Mines"
            assert sub.is_safe_zone is False  # All danger zones

    def test_default_world_abandoned_mines_sub_locations_have_dungeon_category(self):
        """Abandoned Mines sub-locations have category="dungeon".

        Spec: All Mines sub-locations have category="dungeon"
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            sub = world[sub_name]
            assert sub.category == "dungeon"

    def test_default_world_abandoned_mines_sub_locations_no_cardinal_exits(self):
        """Abandoned Mines sub-locations have no n/s/e/w exits (only enter/exit).

        Spec: Mines sub-locations have no cardinal connections
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        for sub_name in mines.sub_locations:
            sub = world[sub_name]
            assert len(sub.connections) == 0

    def test_default_world_abandoned_mines_connections(self):
        """Abandoned Mines has south connection to Cave.

        Spec: Abandoned Mines has south->Cave
        """
        world, _ = create_default_world()
        mines = world["Abandoned Mines"]
        assert mines.get_connection("south") == "Cave"

    def test_default_world_cave_has_north_connection(self):
        """Cave has north connection to Abandoned Mines.

        Spec: Cave has north->Abandoned Mines
        """
        world, _ = create_default_world()
        cave = world["Cave"]
        assert cave.get_connection("north") == "Abandoned Mines"

    def test_default_world_old_miner_in_mine_entrance(self):
        """Old Miner NPC is in Mine Entrance.

        Spec: Old Miner NPC exists in Mine Entrance sub-location
        """
        world, _ = create_default_world()
        mine_entrance = world["Mine Entrance"]
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
        """All Ironhold City sub-locations exist in world dict.

        Spec: Sub-locations listed in ironhold.sub_locations are in world
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        for sub_name in ironhold.sub_locations:
            assert sub_name in world, f"Sub-location '{sub_name}' not in world"

    def test_default_world_ironhold_city_sub_locations_have_parent(self):
        """Ironhold City sub-locations reference Ironhold City as parent and are safe zones.

        Spec: Each sub-location has parent_location="Ironhold City" and is_safe_zone=True
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        for sub_name in ironhold.sub_locations:
            sub = world[sub_name]
            assert sub.parent_location == "Ironhold City"
            assert sub.is_safe_zone is True

    def test_default_world_ironhold_city_sub_locations_no_cardinal_exits(self):
        """Ironhold City sub-locations have no n/s/e/w exits (only enter/exit).

        Spec: Ironhold City sub-locations have no cardinal connections
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        for sub_name in ironhold.sub_locations:
            sub = world[sub_name]
            assert len(sub.connections) == 0

    def test_default_world_ironhold_city_connections(self):
        """Ironhold City has north connection to Town Square.

        Spec: Ironhold City has north->Town Square
        """
        world, _ = create_default_world()
        ironhold = world["Ironhold City"]
        assert ironhold.get_connection("north") == "Town Square"

    def test_default_world_town_square_has_south_connection(self):
        """Town Square has south connection to Ironhold City.

        Spec: Town Square has south->Ironhold City
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.get_connection("south") == "Ironhold City"

    def test_default_world_merchant_in_ironhold_market(self):
        """Wealthy Merchant NPC is in Ironhold Market.

        Spec: Wealthy Merchant NPC in Ironhold Market with is_merchant=True
        """
        world, _ = create_default_world()
        market = world["Ironhold Market"]
        merchant = market.find_npc_by_name("Wealthy Merchant")
        assert merchant is not None
        assert merchant.is_merchant is True

    def test_default_world_captain_in_castle_ward(self):
        """Captain of the Guard NPC is in Castle Ward.

        Spec: Captain of the Guard NPC exists in Castle Ward sub-location
        """
        world, _ = create_default_world()
        castle_ward = world["Castle Ward"]
        captain = castle_ward.find_npc_by_name("Captain of the Guard")
        assert captain is not None

    def test_default_world_beggar_in_slums(self):
        """Beggar NPC is in Slums and is recruitable.

        Spec: Beggar NPC in Slums with is_recruitable=True
        """
        world, _ = create_default_world()
        slums = world["Slums"]
        beggar = slums.find_npc_by_name("Beggar")
        assert beggar is not None
        assert beggar.is_recruitable is True

    def test_default_world_priest_in_temple_quarter(self):
        """Priest NPC is in Temple Quarter.

        Spec: Priest NPC exists in Temple Quarter sub-location
        """
        world, _ = create_default_world()
        temple_quarter = world["Temple Quarter"]
        priest = temple_quarter.find_npc_by_name("Priest")
        assert priest is not None

    def test_default_world_all_valid_locations(self):
        """Test that all values in world dict are Location instances.
        
        Spec: All values must be Location objects
        """
        world, _ = create_default_world()
        for location in world.values():
            assert isinstance(location, Location)
    
    def test_default_world_town_square_connections(self):
        """Test Town Square has correct connections.
        
        Spec: Town Square has north->Forest, east->Cave
        """
        world, _ = create_default_world()
        town_square = world["Town Square"]
        assert town_square.get_connection("north") == "Forest"
        assert town_square.get_connection("east") == "Cave"
    
    def test_default_world_forest_connections(self):
        """Test Forest has correct connections.
        
        Spec: Forest has south->Town Square
        """
        world, _ = create_default_world()
        forest = world["Forest"]
        assert forest.get_connection("south") == "Town Square"
    
    def test_default_world_cave_connections(self):
        """Test Cave has correct connections.
        
        Spec: Cave has west->Town Square
        """
        world, _ = create_default_world()
        cave = world["Cave"]
        assert cave.get_connection("west") == "Town Square"
    
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
        # Use Cave which only has west and north connections
        world1["Cave"].add_connection("south", "Somewhere")
        assert world2["Cave"].get_connection("south") is None

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
        """Test that default world has bidirectional connections.

        Spec: Grid-based world ensures north/south and east/west are symmetric.
        """
        world, _ = create_default_world()

        # Town Square -> Forest and Forest -> Town Square
        assert world["Town Square"].get_connection("north") == "Forest"
        assert world["Forest"].get_connection("south") == "Town Square"

        # Town Square -> Cave and Cave -> Town Square
        assert world["Town Square"].get_connection("east") == "Cave"
        assert world["Cave"].get_connection("west") == "Town Square"

    def test_default_world_all_exits_have_valid_destinations(self):
        """Test that every exit in every location points to an existing location.

        Spec: Remove dangling exits that point to non-existent locations.
        No exit should reference a destination that doesn't exist in the world.
        """
        world, _ = create_default_world()

        for location_name, location in world.items():
            for direction, destination in location.connections.items():
                assert destination in world, (
                    f"Location '{location_name}' has exit '{direction}' to "
                    f"'{destination}' which does not exist in the world"
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
