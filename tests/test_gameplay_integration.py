"""Integration tests for gameplay loop."""

import pytest
import tempfile
import os

from cli_rpg.game_state import GameState
from cli_rpg.world import create_default_world
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.persistence import save_game_state, load_game_state


class TestGameplayIntegration:
    """Integration tests for complete gameplay scenarios."""
    
    def test_gameplay_initialization(self):
        """Test that game state can be initialized from character.
        
        Spec: Game state should be created from character with default world
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        
        game_state = GameState(character, world, starting_location)
        
        assert game_state.current_character == character
        assert game_state.current_location == "Town Square"
        assert len(game_state.world) == 3
    
    def test_gameplay_look_command(self):
        """Test that look command displays location.
        
        Spec: Look should display current location description
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        description = game_state.look()
        
        assert "Town Square" in description
        assert isinstance(description, str)
        assert len(description) > 0
    
    def test_gameplay_move_command_success(self):
        """Test that move command to valid direction works.
        
        Spec: Move to valid direction should succeed
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        success, message = game_state.move("north")
        
        assert success is True
        assert game_state.current_location == "Forest"
        assert isinstance(message, str)
    
    def test_gameplay_move_command_failure(self):
        """Test that move command to invalid direction shows error.
        
        Spec: Move to invalid direction should fail with error message
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        success, message = game_state.move("west")  # No west exit from Town Square
        
        assert success is False
        assert isinstance(message, str)
        assert game_state.current_location == "Town Square"
    
    def test_gameplay_navigation_sequence(self):
        """Test that multiple moves in sequence work correctly.
        
        Spec: Multiple moves should work correctly in sequence
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        # Town Square -> Forest
        success, _ = game_state.move("north")
        assert success is True
        assert game_state.current_location == "Forest"
        
        # Forest -> Town Square
        success, _ = game_state.move("south")
        assert success is True
        assert game_state.current_location == "Town Square"
        
        # Town Square -> Cave
        success, _ = game_state.move("east")
        assert success is True
        assert game_state.current_location == "Cave"
        
        # Cave -> Town Square
        success, _ = game_state.move("west")
        assert success is True
        assert game_state.current_location == "Town Square"
    
    def test_gameplay_save_during_game(self, tmp_path):
        """Test that save preserves current location.
        
        Spec: Save should preserve current game state including location
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        # Move to Forest
        game_state.move("north")
        
        # Save
        filepath = save_game_state(game_state, str(tmp_path))
        
        assert os.path.exists(filepath)
    
    def test_gameplay_load_continues_from_saved_location(self, tmp_path):
        """Test that load restores position correctly.
        
        Spec: Load should restore exact position in world
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        # Move to Cave
        game_state.move("east")
        
        # Save
        filepath = save_game_state(game_state, str(tmp_path))
        
        # Load
        loaded_state = load_game_state(filepath)
        
        assert loaded_state.current_location == "Cave"
        assert loaded_state.current_character.name == "Hero"
    
    def test_gameplay_full_session(self, tmp_path):
        """Test complete session: create, move, save, load, continue.
        
        Spec: Complete gameplay session should work end-to-end
        """
        # Create character and initialize game
        character = Character("TestHero", strength=12, dexterity=10, intelligence=8)
        world, starting_location = create_default_world()
        game_state = GameState(character, world, starting_location)
        
        # Verify starting location
        assert game_state.current_location == "Town Square"
        
        # Look around
        description = game_state.look()
        assert "Town Square" in description
        
        # Navigate: Town Square -> Forest
        success, message = game_state.move("north")
        assert success is True
        assert game_state.current_location == "Forest"
        
        # Look in Forest
        description = game_state.look()
        assert "Forest" in description
        
        # Navigate: Forest -> Town Square -> Cave
        game_state.move("south")
        game_state.move("east")
        assert game_state.current_location == "Cave"
        
        # Save game
        filepath = save_game_state(game_state, str(tmp_path))
        assert os.path.exists(filepath)
        
        # Load game
        loaded_state = load_game_state(filepath)
        
        # Verify state is preserved
        assert loaded_state.current_location == "Cave"
        assert loaded_state.current_character.name == "TestHero"
        assert loaded_state.current_character.strength == 12
        
        # Continue playing from loaded state
        success, _ = loaded_state.move("west")
        assert success is True
        assert loaded_state.current_location == "Town Square"
        
        # Verify world is intact
        description = loaded_state.look()
        assert "Town Square" in description
        assert "Exits" in description
