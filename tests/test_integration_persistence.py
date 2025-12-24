"""Integration tests for persistence system."""
import pytest
from pathlib import Path
from cli_rpg.models.character import Character
from cli_rpg.persistence import save_character, load_character, list_saves


@pytest.fixture
def temp_save_dir(tmp_path):
    """Provide temporary save directory for tests."""
    save_dir = tmp_path / "integration_saves"
    return str(save_dir)


class TestIntegrationPersistence:
    """Integration tests for persistence functionality."""
    
    def test_create_save_load_workflow(self, temp_save_dir):
        """Test: Full workflow from main menu."""
        # Test spec: Complete workflow of creating, saving, and loading a character
        
        # Step 1: Create a character
        character = Character(name="Aragorn", strength=16, dexterity=14, intelligence=12)
        
        # Step 2: Save the character
        filepath = save_character(character, temp_save_dir)
        assert Path(filepath).exists()
        
        # Step 3: List saves to verify it's available
        saves = list_saves(temp_save_dir)
        assert len(saves) == 1
        assert saves[0]['name'] == "Aragorn"
        
        # Step 4: Load the character
        loaded = load_character(filepath)
        
        # Step 5: Verify loaded character matches original
        assert loaded.name == character.name
        assert loaded.strength == character.strength
        assert loaded.dexterity == character.dexterity
        assert loaded.intelligence == character.intelligence
    
    def test_multiple_saves_list_and_load(self, temp_save_dir):
        """Test: Create multiple, list, load specific one."""
        # Test spec: Multiple characters can be saved, listed, and individually loaded
        
        # Create and save multiple characters
        char1 = Character(name="Fighter", strength=18, dexterity=10, intelligence=8)
        char2 = Character(name="Wizard", strength=8, dexterity=10, intelligence=18)
        char3 = Character(name="Thief", strength=10, dexterity=18, intelligence=10)
        
        file1 = save_character(char1, temp_save_dir)
        file2 = save_character(char2, temp_save_dir)
        file3 = save_character(char3, temp_save_dir)
        
        # List all saves
        saves = list_saves(temp_save_dir)
        assert len(saves) == 3
        
        # Verify all character names are present
        character_names = [save['name'] for save in saves]
        assert "Fighter" in character_names
        assert "Wizard" in character_names
        assert "Thief" in character_names
        
        # Load specific character and verify
        loaded_wizard = load_character(file2)
        assert loaded_wizard.name == "Wizard"
        assert loaded_wizard.intelligence == 18
        
        loaded_thief = load_character(file3)
        assert loaded_thief.name == "Thief"
        assert loaded_thief.dexterity == 18
    
    def test_save_overwrite_protection(self, temp_save_dir):
        """Test: Verify unique filenames prevent overwrites."""
        # Test spec: Multiple saves of same character name create unique files
        import time
        
        character = Character(name="Hero", strength=12, dexterity=12, intelligence=12)
        
        # Save same character twice
        file1 = save_character(character, temp_save_dir)
        time.sleep(1.1)  # Ensure different timestamp
        file2 = save_character(character, temp_save_dir)
        
        # Verify both files exist and are different
        assert Path(file1).exists()
        assert Path(file2).exists()
        assert file1 != file2
        
        # Verify list_saves shows both
        saves = list_saves(temp_save_dir)
        assert len(saves) == 2
    
    def test_load_character_with_modified_state(self, temp_save_dir):
        """Test: Character with modified state (damaged health) is preserved."""
        # Test spec: Character state changes (like damage) are preserved through save/load
        
        # Create character and modify state
        character = Character(name="Wounded", strength=15, dexterity=12, intelligence=10)
        original_health = character.health
        character.take_damage(75)
        
        assert character.health < original_health
        assert character.is_alive()
        
        # Save and load
        filepath = save_character(character, temp_save_dir)
        loaded = load_character(filepath)
        
        # Verify damaged state is preserved
        assert loaded.health == character.health
        assert loaded.health < loaded.max_health
        assert loaded.is_alive()
    
    def test_save_directory_created_automatically(self, tmp_path):
        """Test: Save directory is created if it doesn't exist."""
        # Test spec: Persistence system creates necessary directories automatically
        
        non_existent_dir = str(tmp_path / "auto_created" / "saves")
        assert not Path(non_existent_dir).exists()
        
        character = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        filepath = save_character(character, non_existent_dir)
        
        # Verify directory was created
        assert Path(non_existent_dir).exists()
        assert Path(filepath).exists()
