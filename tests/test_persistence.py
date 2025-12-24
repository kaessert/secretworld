"""Tests for character persistence system."""
import json
import os
import pytest
from pathlib import Path
from cli_rpg.models.character import Character
from cli_rpg.persistence import (
    save_character,
    load_character,
    list_saves,
    delete_save,
)


@pytest.fixture
def temp_save_dir(tmp_path):
    """Provide temporary save directory for tests."""
    save_dir = tmp_path / "test_saves"
    return str(save_dir)


@pytest.fixture
def sample_character():
    """Provide sample character for testing."""
    return Character(name="TestHero", strength=10, dexterity=12, intelligence=8)


@pytest.fixture
def damaged_character():
    """Provide character with reduced health."""
    char = Character(name="WoundedHero", strength=15, dexterity=10, intelligence=10)
    char.take_damage(50)
    return char


class TestSaveCharacter:
    """Tests for save_character function."""
    
    def test_save_character_creates_file(self, sample_character, temp_save_dir):
        """Test: Verify file is created with correct name."""
        # Test spec: save_character creates a JSON file in the saves directory
        filepath = save_character(sample_character, temp_save_dir)
        assert Path(filepath).exists()
    
    def test_save_character_returns_filepath(self, sample_character, temp_save_dir):
        """Test: Returns valid path string."""
        # Test spec: save_character returns the full path to the saved file
        filepath = save_character(sample_character, temp_save_dir)
        assert isinstance(filepath, str)
        assert filepath.endswith(".json")
        assert temp_save_dir in filepath
    
    def test_save_character_creates_directory(self, sample_character, tmp_path):
        """Test: Creates save dir if missing."""
        # Test spec: save_character creates the save directory if it doesn't exist
        non_existent_dir = str(tmp_path / "new_saves")
        assert not Path(non_existent_dir).exists()
        
        filepath = save_character(sample_character, non_existent_dir)
        
        assert Path(non_existent_dir).exists()
        assert Path(filepath).exists()
    
    def test_save_character_unique_filenames(self, sample_character, temp_save_dir):
        """Test: Multiple saves create unique files."""
        # Test spec: Each save creates a unique file with timestamp to prevent overwrites
        import time
        
        filepath1 = save_character(sample_character, temp_save_dir)
        time.sleep(1.1)  # Ensure different timestamp
        filepath2 = save_character(sample_character, temp_save_dir)
        
        assert filepath1 != filepath2
        assert Path(filepath1).exists()
        assert Path(filepath2).exists()
    
    def test_save_character_valid_json(self, sample_character, temp_save_dir):
        """Test: File contains valid JSON."""
        # Test spec: Saved file contains valid JSON that can be parsed
        filepath = save_character(sample_character, temp_save_dir)
        
        with open(filepath, 'r') as f:
            data = json.load(f)  # Should not raise exception
        
        assert isinstance(data, dict)
    
    def test_save_character_contains_correct_data(self, sample_character, temp_save_dir):
        """Test: JSON matches character data."""
        # Test spec: Saved JSON contains all character attributes from to_dict()
        filepath = save_character(sample_character, temp_save_dir)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        expected = sample_character.to_dict()
        assert data == expected
    
    def test_save_character_custom_directory(self, sample_character, tmp_path):
        """Test: Respects custom save_dir parameter."""
        # Test spec: save_character accepts custom directory path parameter
        custom_dir = str(tmp_path / "custom_saves")
        filepath = save_character(sample_character, custom_dir)
        
        assert custom_dir in filepath
        assert Path(filepath).exists()
    
    def test_save_character_io_error(self, sample_character):
        """Test: Handles permission/write errors gracefully."""
        # Test spec: save_character raises IOError when write fails
        invalid_dir = "/root/impossible_saves"  # Typically no permission
        
        with pytest.raises(IOError):
            save_character(sample_character, invalid_dir)
    
    def test_save_character_filename_sanitization(self, temp_save_dir):
        """Test: Handles special chars in names."""
        # Test spec: Character names with special characters are sanitized in filenames
        char = Character(name="Test/Hero*Name?", strength=10, dexterity=10, intelligence=10)
        filepath = save_character(char, temp_save_dir)
        
        # Filename should not contain invalid filesystem characters
        filename = Path(filepath).name
        invalid_chars = ['/', '\\', '*', '?', '<', '>', '|', ':', '"']
        for char in invalid_chars:
            assert char not in filename


class TestLoadCharacter:
    """Tests for load_character function."""
    
    def test_load_character_success(self, sample_character, temp_save_dir):
        """Test: Loads valid saved character."""
        # Test spec: load_character successfully loads a saved character file
        filepath = save_character(sample_character, temp_save_dir)
        loaded = load_character(filepath)
        
        assert isinstance(loaded, Character)
        assert loaded.name == sample_character.name
    
    def test_load_character_restores_all_attributes(self, sample_character, temp_save_dir):
        """Test: All stats match original."""
        # Test spec: Loaded character has all attributes matching the saved character
        filepath = save_character(sample_character, temp_save_dir)
        loaded = load_character(filepath)
        
        assert loaded.name == sample_character.name
        assert loaded.strength == sample_character.strength
        assert loaded.dexterity == sample_character.dexterity
        assert loaded.intelligence == sample_character.intelligence
        assert loaded.level == sample_character.level
        assert loaded.health == sample_character.health
        assert loaded.max_health == sample_character.max_health
    
    def test_load_character_damaged_health(self, damaged_character, temp_save_dir):
        """Test: Preserves reduced health state."""
        # Test spec: Characters with reduced health maintain that state when loaded
        filepath = save_character(damaged_character, temp_save_dir)
        loaded = load_character(filepath)
        
        assert loaded.health == damaged_character.health
        assert loaded.health < loaded.max_health
    
    def test_load_character_file_not_found(self):
        """Test: Raises FileNotFoundError."""
        # Test spec: load_character raises FileNotFoundError for non-existent files
        with pytest.raises(FileNotFoundError):
            load_character("nonexistent_file.json")
    
    def test_load_character_invalid_json(self, temp_save_dir):
        """Test: Raises ValueError for malformed JSON."""
        # Test spec: load_character raises ValueError for invalid JSON files
        filepath = Path(temp_save_dir)
        filepath.mkdir(parents=True, exist_ok=True)
        bad_file = filepath / "bad.json"
        bad_file.write_text("{ this is not valid json }")
        
        with pytest.raises(ValueError):
            load_character(str(bad_file))
    
    def test_load_character_missing_required_fields(self, temp_save_dir):
        """Test: Raises ValueError."""
        # Test spec: load_character raises ValueError when required character fields are missing
        filepath = Path(temp_save_dir)
        filepath.mkdir(parents=True, exist_ok=True)
        incomplete_file = filepath / "incomplete.json"
        
        # Missing strength field
        incomplete_data = {
            "name": "Test",
            "dexterity": 10,
            "intelligence": 10
        }
        incomplete_file.write_text(json.dumps(incomplete_data))
        
        with pytest.raises(ValueError):
            load_character(str(incomplete_file))
    
    def test_load_character_invalid_stat_values(self, temp_save_dir):
        """Test: Validates character constraints."""
        # Test spec: load_character validates loaded data against Character constraints
        filepath = Path(temp_save_dir)
        filepath.mkdir(parents=True, exist_ok=True)
        invalid_file = filepath / "invalid.json"
        
        # Strength out of valid range
        invalid_data = {
            "name": "Test",
            "strength": 999,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
            "health": 100,
            "max_health": 100
        }
        invalid_file.write_text(json.dumps(invalid_data))
        
        with pytest.raises(ValueError):
            load_character(str(invalid_file))
    
    def test_load_character_empty_file(self, temp_save_dir):
        """Test: Handles empty file gracefully."""
        # Test spec: load_character raises ValueError for empty files
        filepath = Path(temp_save_dir)
        filepath.mkdir(parents=True, exist_ok=True)
        empty_file = filepath / "empty.json"
        empty_file.write_text("")
        
        with pytest.raises(ValueError):
            load_character(str(empty_file))


class TestListSaves:
    """Tests for list_saves function."""
    
    def test_list_saves_empty_directory(self, temp_save_dir):
        """Test: Returns empty list."""
        # Test spec: list_saves returns empty list for empty directory
        Path(temp_save_dir).mkdir(parents=True, exist_ok=True)
        saves = list_saves(temp_save_dir)
        
        assert saves == []
    
    def test_list_saves_nonexistent_directory(self, tmp_path):
        """Test: Returns empty list."""
        # Test spec: list_saves returns empty list when directory doesn't exist
        non_existent = str(tmp_path / "does_not_exist")
        saves = list_saves(non_existent)
        
        assert saves == []
    
    def test_list_saves_single_save(self, sample_character, temp_save_dir):
        """Test: Returns list with one entry."""
        # Test spec: list_saves returns list with single entry for one saved file
        save_character(sample_character, temp_save_dir)
        saves = list_saves(temp_save_dir)
        
        assert len(saves) == 1
    
    def test_list_saves_multiple_saves(self, temp_save_dir):
        """Test: Returns all saves."""
        # Test spec: list_saves returns all saved character files
        char1 = Character(name="Hero1", strength=10, dexterity=10, intelligence=10)
        char2 = Character(name="Hero2", strength=12, dexterity=8, intelligence=10)
        
        save_character(char1, temp_save_dir)
        save_character(char2, temp_save_dir)
        
        saves = list_saves(temp_save_dir)
        assert len(saves) == 2
    
    def test_list_saves_sorted_by_timestamp(self, sample_character, temp_save_dir):
        """Test: Most recent first."""
        # Test spec: list_saves returns saves sorted by timestamp, most recent first
        import time
        
        save_character(sample_character, temp_save_dir)
        time.sleep(1.1)
        filepath2 = save_character(sample_character, temp_save_dir)
        
        saves = list_saves(temp_save_dir)
        
        # Most recent save should be first
        assert saves[0]['filepath'] == filepath2
    
    def test_list_saves_correct_structure(self, sample_character, temp_save_dir):
        """Test: Each dict has name, filepath, timestamp."""
        # Test spec: Each entry in list_saves has required keys: name, filepath, timestamp
        save_character(sample_character, temp_save_dir)
        saves = list_saves(temp_save_dir)
        
        assert len(saves) == 1
        save_entry = saves[0]
        
        assert 'name' in save_entry
        assert 'filepath' in save_entry
        assert 'timestamp' in save_entry
        assert isinstance(save_entry['name'], str)
        assert isinstance(save_entry['filepath'], str)
        assert isinstance(save_entry['timestamp'], str)
    
    def test_list_saves_ignores_non_json(self, sample_character, temp_save_dir):
        """Test: Ignores non-JSON files."""
        # Test spec: list_saves only returns JSON files, ignoring other file types
        save_character(sample_character, temp_save_dir)
        
        # Create a non-JSON file
        Path(temp_save_dir).mkdir(parents=True, exist_ok=True)
        (Path(temp_save_dir) / "readme.txt").write_text("Not a save file")
        
        saves = list_saves(temp_save_dir)
        
        # Should only find the one JSON save
        assert len(saves) == 1
    
    def test_list_saves_custom_directory(self, sample_character, tmp_path):
        """Test: Respects custom save_dir parameter."""
        # Test spec: list_saves accepts custom directory path parameter
        custom_dir = str(tmp_path / "custom_saves")
        save_character(sample_character, custom_dir)
        
        saves = list_saves(custom_dir)
        assert len(saves) == 1


class TestDeleteSave:
    """Tests for delete_save function."""
    
    def test_delete_save_success(self, sample_character, temp_save_dir):
        """Test: Returns True and removes file."""
        # Test spec: delete_save removes the file and returns True on success
        filepath = save_character(sample_character, temp_save_dir)
        assert Path(filepath).exists()
        
        result = delete_save(filepath)
        
        assert result is True
        assert not Path(filepath).exists()
    
    def test_delete_save_file_not_found(self):
        """Test: Returns False."""
        # Test spec: delete_save returns False when file doesn't exist
        result = delete_save("nonexistent_file.json")
        assert result is False
    
    def test_delete_save_permission_error(self, sample_character, temp_save_dir):
        """Test: Raises OSError."""
        # Test spec: delete_save raises OSError on permission errors
        filepath = save_character(sample_character, temp_save_dir)
        
        # Make file read-only and directory read-only
        os.chmod(filepath, 0o444)
        os.chmod(temp_save_dir, 0o555)
        
        try:
            with pytest.raises(OSError):
                delete_save(filepath)
        finally:
            # Cleanup: restore permissions
            os.chmod(temp_save_dir, 0o755)
            os.chmod(filepath, 0o644)


class TestIntegrationSaveLoad:
    """Integration tests for save/load functionality."""
    
    def test_round_trip_save_and_load(self, sample_character, temp_save_dir):
        """Test: Save then load produces identical character."""
        # Test spec: Complete save/load cycle preserves all character data
        filepath = save_character(sample_character, temp_save_dir)
        loaded = load_character(filepath)
        
        assert loaded.to_dict() == sample_character.to_dict()
    
    def test_multiple_characters_save_load(self, temp_save_dir):
        """Test: Multiple characters don't interfere."""
        # Test spec: Multiple characters can be saved and loaded independently
        char1 = Character(name="Warrior", strength=18, dexterity=10, intelligence=8)
        char2 = Character(name="Mage", strength=8, dexterity=10, intelligence=18)
        char3 = Character(name="Rogue", strength=10, dexterity=18, intelligence=10)
        
        file1 = save_character(char1, temp_save_dir)
        file2 = save_character(char2, temp_save_dir)
        file3 = save_character(char3, temp_save_dir)
        
        loaded1 = load_character(file1)
        loaded2 = load_character(file2)
        loaded3 = load_character(file3)
        
        assert loaded1.to_dict() == char1.to_dict()
        assert loaded2.to_dict() == char2.to_dict()
        assert loaded3.to_dict() == char3.to_dict()
    
    def test_save_load_with_special_states(self, temp_save_dir):
        """Test: Edge cases (0 health, max stats, etc.)."""
        # Test spec: Characters with edge case states are saved/loaded correctly
        
        # Test with 0 health (dead character)
        dead_char = Character(name="Dead", strength=10, dexterity=10, intelligence=10)
        dead_char.take_damage(1000)
        assert dead_char.health == 0
        
        file_dead = save_character(dead_char, temp_save_dir)
        loaded_dead = load_character(file_dead)
        assert loaded_dead.health == 0
        assert not loaded_dead.is_alive()
        
        # Test with max stats
        max_char = Character(name="MaxStats", strength=20, dexterity=20, intelligence=20)
        file_max = save_character(max_char, temp_save_dir)
        loaded_max = load_character(file_max)
        assert loaded_max.strength == 20
        assert loaded_max.dexterity == 20
        assert loaded_max.intelligence == 20
