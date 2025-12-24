"""Tests for game state persistence."""

import json
import os
import pytest
import tempfile
from pathlib import Path

from cli_rpg.persistence import save_game_state, load_game_state
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


class TestSaveGameState:
    """Tests for save_game_state() function."""
    
    def test_save_game_state_creates_file(self, tmp_path):
        """Test that save_game_state creates a file.
        
        Spec: File should be created
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        assert os.path.exists(filepath)
    
    def test_save_game_state_returns_filepath(self, tmp_path):
        """Test that save_game_state returns a string path.
        
        Spec: Should return string path
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        assert isinstance(filepath, str)
        assert len(filepath) > 0
    
    def test_save_game_state_creates_directory(self):
        """Test that save_game_state creates save_dir if missing.
        
        Spec: Should create save_dir if it doesn't exist
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_dir = os.path.join(tmp_dir, "new_saves")
            
            character = Character("Hero", strength=10, dexterity=10, intelligence=10)
            world = {
                "Start": Location("Start", "Start location")
            }
            game_state = GameState(character, world, "Start")
            
            filepath = save_game_state(game_state, save_dir)
            
            assert os.path.exists(save_dir)
            assert os.path.exists(filepath)
    
    def test_save_game_state_valid_json(self, tmp_path):
        """Test that saved file contains valid JSON.
        
        Spec: File should contain valid JSON
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
    
    def test_save_game_state_contains_complete_data(self, tmp_path):
        """Test that saved file contains character, location, and world.
        
        Spec: Should contain character, current_location, world
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        assert "character" in data
        assert "current_location" in data
        assert "world" in data
        assert data["character"]["name"] == "Hero"
        assert data["current_location"] == "Start"
        assert "Start" in data["world"]
        assert "End" in data["world"]
    
    def test_save_game_state_custom_directory(self):
        """Test that save_game_state respects save_dir parameter.
        
        Spec: Should save to custom directory
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_dir = os.path.join(tmp_dir, "custom_saves")
            
            character = Character("Hero", strength=10, dexterity=10, intelligence=10)
            world = {
                "Start": Location("Start", "Start location")
            }
            game_state = GameState(character, world, "Start")
            
            filepath = save_game_state(game_state, custom_dir)
            
            assert custom_dir in filepath
            assert os.path.exists(filepath)


class TestLoadGameState:
    """Tests for load_game_state() function."""
    
    def test_load_game_state_success(self, tmp_path):
        """Test that load_game_state loads a valid file.
        
        Spec: Should load valid file successfully
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert loaded_state is not None
    
    def test_load_game_state_returns_game_state(self, tmp_path):
        """Test that load_game_state returns GameState instance.
        
        Spec: Should return GameState instance
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert isinstance(loaded_state, GameState)
    
    def test_load_game_state_restores_character(self, tmp_path):
        """Test that load_game_state restores character correctly.
        
        Spec: Character should match original
        """
        character = Character("TestHero", strength=12, dexterity=15, intelligence=8)
        world = {
            "Start": Location("Start", "Start location")
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert loaded_state.current_character.name == "TestHero"
        assert loaded_state.current_character.strength == 12
        assert loaded_state.current_character.dexterity == 15
        assert loaded_state.current_character.intelligence == 8
    
    def test_load_game_state_restores_location(self, tmp_path):
        """Test that load_game_state restores location correctly.
        
        Spec: Location should match original
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }
        game_state = GameState(character, world, "Start")
        game_state.move("north")  # Move to End
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert loaded_state.current_location == "End"
    
    def test_load_game_state_restores_world(self, tmp_path):
        """Test that load_game_state restores world correctly.
        
        Spec: World should match original
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location", {"south": "Start"})
        }
        game_state = GameState(character, world, "Start")
        
        filepath = save_game_state(game_state, str(tmp_path))
        loaded_state = load_game_state(filepath)
        
        assert "Start" in loaded_state.world
        assert "End" in loaded_state.world
        assert loaded_state.world["Start"].get_connection("north") == "End"
        assert loaded_state.world["End"].get_connection("south") == "Start"
    
    def test_load_game_state_file_not_found(self):
        """Test that load_game_state raises FileNotFoundError for missing file.
        
        Spec: Should raise FileNotFoundError
        """
        with pytest.raises(FileNotFoundError):
            load_game_state("nonexistent_file.json")
    
    def test_load_game_state_invalid_json(self, tmp_path):
        """Test that load_game_state raises ValueError for invalid JSON.
        
        Spec: Should raise ValueError
        """
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_game_state(str(invalid_file))
    
    def test_load_game_state_missing_fields(self, tmp_path):
        """Test that load_game_state raises ValueError for missing required fields.
        
        Spec: Should raise ValueError for missing fields
        """
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_file.write_text(json.dumps({"character": {}}))
        
        with pytest.raises((ValueError, KeyError)):
            load_game_state(str(incomplete_file))
    
    def test_load_game_state_roundtrip(self, tmp_path):
        """Test that save -> load preserves complete state.
        
        Spec: Save and load should preserve complete state
        """
        character = Character("Hero", strength=12, dexterity=15, intelligence=8)
        character.take_damage(20)  # Test that modified health is preserved
        
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location", {"south": "Start"})
        }
        game_state = GameState(character, world, "Start")
        game_state.move("north")  # Move to End
        
        # Save
        filepath = save_game_state(game_state, str(tmp_path))
        
        # Load
        loaded_state = load_game_state(filepath)
        
        # Verify everything is preserved
        assert loaded_state.current_character.name == "Hero"
        assert loaded_state.current_character.strength == 12
        assert loaded_state.current_character.health == character.health
        assert loaded_state.current_location == "End"
        assert "Start" in loaded_state.world
        assert "End" in loaded_state.world
        
        # Verify we can continue playing
        success, _ = loaded_state.move("south")
        assert success is True
        assert loaded_state.current_location == "Start"
