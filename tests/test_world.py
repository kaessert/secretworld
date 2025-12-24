"""Tests for world module."""

import pytest
from cli_rpg.world import create_default_world
from cli_rpg.models.location import Location


class TestCreateDefaultWorld:
    """Tests for create_default_world() function."""
    
    def test_default_world_has_three_locations(self):
        """Test that default world has exactly 3 locations.
        
        Spec: create_default_world() returns dict with 3 locations
        """
        world = create_default_world()
        assert len(world) == 3
    
    def test_default_world_location_names(self):
        """Test that default world has correct location names.
        
        Spec: Locations should be "Town Square", "Forest", "Cave"
        """
        world = create_default_world()
        assert "Town Square" in world
        assert "Forest" in world
        assert "Cave" in world
    
    def test_default_world_all_valid_locations(self):
        """Test that all values in world dict are Location instances.
        
        Spec: All values must be Location objects
        """
        world = create_default_world()
        for location in world.values():
            assert isinstance(location, Location)
    
    def test_default_world_town_square_connections(self):
        """Test Town Square has correct connections.
        
        Spec: Town Square has north->Forest, east->Cave
        """
        world = create_default_world()
        town_square = world["Town Square"]
        assert town_square.get_connection("north") == "Forest"
        assert town_square.get_connection("east") == "Cave"
    
    def test_default_world_forest_connections(self):
        """Test Forest has correct connections.
        
        Spec: Forest has south->Town Square
        """
        world = create_default_world()
        forest = world["Forest"]
        assert forest.get_connection("south") == "Town Square"
    
    def test_default_world_cave_connections(self):
        """Test Cave has correct connections.
        
        Spec: Cave has west->Town Square
        """
        world = create_default_world()
        cave = world["Cave"]
        assert cave.get_connection("west") == "Town Square"
    
    def test_default_world_locations_have_descriptions(self):
        """Test that all locations have non-empty descriptions.
        
        Spec: All locations must have descriptions
        """
        world = create_default_world()
        for location in world.values():
            assert location.description
            assert len(location.description) > 0
    
    def test_default_world_immutable_returns(self):
        """Test that multiple calls return independent copies.
        
        Spec: Each call should return a new dict with new Location instances
        """
        world1 = create_default_world()
        world2 = create_default_world()
        
        # Dicts should not be the same object
        assert world1 is not world2
        
        # Locations should not be the same objects
        assert world1["Town Square"] is not world2["Town Square"]
        
        # Modifying one shouldn't affect the other
        world1["Town Square"].add_connection("south", "Somewhere")
        assert world2["Town Square"].get_connection("south") is None
