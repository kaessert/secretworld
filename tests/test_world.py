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
    
    def test_default_world_has_three_locations(self):
        """Test that default world has exactly 3 locations.
        
        Spec: create_default_world() returns dict with 3 locations
        """
        world, _ = create_default_world()
        assert len(world) == 3
    
    def test_default_world_location_names(self):
        """Test that default world has correct location names.
        
        Spec: Locations should be "Town Square", "Forest", "Cave"
        """
        world, _ = create_default_world()
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world
    
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
        world1["Town Square"].add_connection("south", "Somewhere")
        assert world2["Town Square"].get_connection("south") is None

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
    def test_create_world_falls_back_on_ai_error(self, mock_create_ai_world):
        """Test that create_world() falls back to default on AI error.
        
        Spec (Fix): create_world() falls back to default world tuple on AI error
        """
        # Mock AI world generation to fail
        mock_create_ai_world.side_effect = Exception("AI generation failed")
        
        mock_ai_service = Mock()
        world, starting_location = create_world(ai_service=mock_ai_service, theme="fantasy")
        
        # Should return default world tuple
        assert starting_location == "Town Square"
        assert "Town Square" in world
