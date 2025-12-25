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
