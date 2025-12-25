"""Tests for save file type detection functionality.

This test module verifies the specification in docs/save_file_detection_spec.md
"""

import json
import os
import pytest

from cli_rpg.persistence import detect_save_type, load_character, load_game_state
from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState


@pytest.fixture
def character_only_save_data():
    """Character-only save file data (legacy format)."""
    # Tests spec: Character-only save structure
    return {
        "name": "TestHero",
        "strength": 10,
        "dexterity": 12,
        "intelligence": 8,
        "constitution": 10,
        "level": 1,
        "health": 100,
        "max_health": 100,
        "xp": 0,
        "xp_to_next_level": 100
    }


@pytest.fixture
def game_state_save_data():
    """Game state save file data (full format)."""
    # Tests spec: Game state save structure
    return {
        "character": {
            "name": "TestHero",
            "strength": 10,
            "dexterity": 12,
            "intelligence": 8,
            "constitution": 10,
            "level": 1,
            "health": 100,
            "max_health": 100,
            "xp": 0,
            "xp_to_next_level": 100
        },
        "world": {
            "Test Location": {
                "name": "Test Location",
                "description": "A test location",
                "connections": {}
            }
        },
        "current_location": "Test Location",
        "theme": "fantasy"
    }


@pytest.fixture
def temp_character_save(tmp_path, character_only_save_data):
    """Create a temporary character-only save file."""
    save_file = tmp_path / "character_save.json"
    with open(save_file, 'w') as f:
        json.dump(character_only_save_data, f)
    return str(save_file)


@pytest.fixture
def temp_game_state_save(tmp_path, game_state_save_data):
    """Create a temporary game state save file."""
    save_file = tmp_path / "game_state_save.json"
    with open(save_file, 'w') as f:
        json.dump(game_state_save_data, f)
    return str(save_file)


@pytest.fixture
def temp_corrupted_save(tmp_path):
    """Create a temporary corrupted save file."""
    save_file = tmp_path / "corrupted_save.json"
    with open(save_file, 'w') as f:
        f.write("{invalid json content")
    return str(save_file)


class TestDetectSaveType:
    """Tests for detect_save_type() function."""
    
    def test_detect_character_only_save(self, temp_character_save):
        """Test detecting character-only save file.
        
        Spec: Detection method - returns "character" for saves without "world" key
        """
        save_type = detect_save_type(temp_character_save)
        assert save_type == "character"
    
    def test_detect_game_state_save(self, temp_game_state_save):
        """Test detecting game state save file.
        
        Spec: Detection method - returns "game_state" for saves with "world" key
        """
        save_type = detect_save_type(temp_game_state_save)
        assert save_type == "game_state"
    
    def test_handle_missing_file(self, tmp_path):
        """Test handling of missing file.
        
        Spec: Error handling - raises FileNotFoundError for missing files
        """
        nonexistent_file = str(tmp_path / "nonexistent.json")
        with pytest.raises(FileNotFoundError):
            detect_save_type(nonexistent_file)
    
    def test_handle_corrupted_json(self, temp_corrupted_save):
        """Test handling of corrupted JSON file.
        
        Spec: Error handling - raises ValueError for invalid JSON
        """
        with pytest.raises(ValueError, match="Invalid JSON"):
            detect_save_type(temp_corrupted_save)


class TestLoadCharacterOnlySave:
    """Tests for loading character-only save files."""
    
    def test_load_character_only_file(self, temp_character_save):
        """Test loading character-only save file.
        
        Spec: Character-only save loading - loads character with all attributes
        """
        character = load_character(temp_character_save)
        assert isinstance(character, Character)
        assert character.name == "TestHero"
        assert character.strength == 10
        assert character.dexterity == 12
        assert character.intelligence == 8
        assert character.level == 1
        assert character.health == 100
        # max_health is recalculated from strength: 100 + 10*5 = 150
        assert character.max_health == 150
    
    def test_character_only_starts_new_game(self, temp_character_save):
        """Test that character-only save starts new game with default world.
        
        Spec: Character-only save loading - starts new game with default world
        Note: This is an integration test that will be verified in start_game()
        """
        # Verify character loads correctly - starting new game is handled by main()
        character = load_character(temp_character_save)
        assert character is not None
        assert character.name == "TestHero"


class TestLoadGameStateSave:
    """Tests for loading game state save files."""
    
    def test_load_game_state_file(self, temp_game_state_save):
        """Test loading game state save file.
        
        Spec: Game state save loading - loads complete game state
        """
        game_state = load_game_state(temp_game_state_save)
        assert isinstance(game_state, GameState)
        assert game_state.current_character.name == "TestHero"
        assert game_state.current_location == "Test Location"
        assert game_state.theme == "fantasy"
        assert game_state.world is not None
    
    def test_game_state_restores_location(self, temp_game_state_save):
        """Test that game state save restores exact location.
        
        Spec: Game state save loading - game resumes from exact saved location
        """
        game_state = load_game_state(temp_game_state_save)
        assert game_state.current_location == "Test Location"
        location_obj = game_state.world.get("Test Location")
        assert location_obj is not None
        assert location_obj.name == "Test Location"
    
    def test_game_state_restores_theme(self, temp_game_state_save):
        """Test that game state save restores theme.
        
        Spec: Theme preservation - theme is restored when loading game state
        """
        game_state = load_game_state(temp_game_state_save)
        assert game_state.theme == "fantasy"
    
    def test_game_state_restores_world_structure(self, temp_game_state_save):
        """Test that game state save restores world structure.
        
        Spec: Game state save loading - world structure is preserved
        """
        game_state = load_game_state(temp_game_state_save)
        assert game_state.world is not None
        assert len(game_state.world) > 0
        assert "Test Location" in game_state.world
        assert game_state.world["Test Location"].name == "Test Location"


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing saves."""
    
    def test_load_existing_character_save(self):
        """Test loading real existing character-only save.
        
        Spec: Backward compatibility - all existing character-only saves must work
        """
        # Check if the real save file exists
        existing_save = "saves/sasdf_20251224_011809.json"
        if not os.path.exists(existing_save):
            pytest.skip("Real save file not found for backward compatibility test")
        
        # Verify it's detected as character-only
        save_type = detect_save_type(existing_save)
        assert save_type == "character"
        
        # Verify it loads without errors
        character = load_character(existing_save)
        assert character is not None
        assert character.name == "sasdf"


class TestErrorHandling:
    """Tests for error handling in save file loading."""
    
    def test_corrupted_file_graceful_handling(self, temp_corrupted_save):
        """Test graceful handling of corrupted save file.
        
        Spec: Error handling - display user-friendly error, do not crash
        """
        with pytest.raises(ValueError):
            detect_save_type(temp_corrupted_save)
    
    def test_missing_required_keys_character(self, tmp_path):
        """Test handling of missing required keys in character save.
        
        Spec: Error handling - validate presence of required keys
        """
        incomplete_save = tmp_path / "incomplete.json"
        with open(incomplete_save, 'w') as f:
            json.dump({"name": "Test", "strength": 10}, f)  # Missing other required fields
        
        # Should raise an error when trying to create character
        with pytest.raises((ValueError, KeyError, TypeError)):
            load_character(str(incomplete_save))
    
    def test_invalid_data_types(self, tmp_path):
        """Test handling of invalid data types in save.
        
        Spec: Error handling - let Character/GameState validation handle it
        """
        invalid_save = tmp_path / "invalid_types.json"
        with open(invalid_save, 'w') as f:
            json.dump({
                "name": "Test",
                "strength": "not_a_number",  # Invalid type
                "dexterity": 10,
                "intelligence": 10,
                "level": 1,
                "health": 100,
                "max_health": 100
            }, f)
        
        # Should raise an error during validation
        with pytest.raises((ValueError, TypeError)):
            load_character(str(invalid_save))
