"""Complete end-to-end tests for save and load functionality.

This test module verifies the complete flow of creating a character,
playing the game, saving game state, loading it back, and continuing gameplay.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState
from cli_rpg.world import create_world
from cli_rpg.persistence import save_game_state, save_character, detect_save_type
from cli_rpg.main import select_and_load_character


class TestCompleteGameFlow:
    """Test complete game flow from creation to save to load."""
    
    def test_complete_save_and_load_cycle(self, tmp_path):
        """Test complete cycle: create -> play -> save -> load -> verify.
        
        Verifies:
        - Game state can be saved mid-game
        - Saved state can be loaded
        - Location is preserved
        - Character stats are preserved
        - World structure is preserved
        - Theme is preserved
        """
        # 1. Create character
        character = Character(
            name="Hero",
            strength=10,
            dexterity=12,
            intelligence=8
        )
        
        # 2. Start game (create world and game state)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location, theme="fantasy")
        
        # 3. Play game (move to different location)
        initial_location = game_state.current_location
        game_state.move("north")
        new_location = game_state.current_location
        
        # Verify we actually moved
        assert new_location != initial_location
        
        # 4. Save game state
        save_data = game_state.to_dict()
        save_file = tmp_path / "game_save.json"
        with open(save_file, 'w') as f:
            json.dump(save_data, f)
        
        # 5. Detect save type (should be game_state)
        save_type = detect_save_type(str(save_file))
        assert save_type == "game_state"
        
        # 6. Load game state
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'Hero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                loaded_char, loaded_state = select_and_load_character()
        
        # 7. Verify loaded state
        assert loaded_char is None  # Should be None for game state saves
        assert loaded_state is not None
        assert isinstance(loaded_state, GameState)
        
        # 8. Verify location preserved
        assert loaded_state.current_location == new_location
        assert loaded_state.current_location != initial_location
        
        # 9. Verify character preserved
        assert loaded_state.current_character.name == "Hero"
        assert loaded_state.current_character.strength == 10
        assert loaded_state.current_character.dexterity == 12
        
        # 10. Verify world preserved
        assert len(loaded_state.world) == len(world)
        assert new_location in loaded_state.world
        
        # 11. Verify theme preserved
        assert loaded_state.theme == "fantasy"
        
        # 12. Continue playing (move again)
        success, _ = loaded_state.move("south")
        assert success
        assert loaded_state.current_location == initial_location
    
    def test_backward_compatible_character_load(self, tmp_path):
        """Test backward compatibility: old character saves still work.
        
        Verifies:
        - Character-only saves can be loaded
        - Returns character, not game state
        - Character attributes are correct
        - Can start new game with loaded character
        """
        # 1. Create old-style character save
        character = Character(
            name="OldHero",
            strength=15,
            dexterity=10,
            intelligence=12
        )
        
        save_file = tmp_path / "character_save.json"
        with open(save_file, 'w') as f:
            json.dump(character.to_dict(), f)
        
        # 2. Detect save type (should be character)
        save_type = detect_save_type(str(save_file))
        assert save_type == "character"
        
        # 3. Load character
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'OldHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                loaded_char, loaded_state = select_and_load_character()
        
        # 4. Verify loaded character
        assert loaded_char is not None
        assert loaded_state is None  # Should be None for character-only saves
        assert isinstance(loaded_char, Character)
        assert loaded_char.name == "OldHero"
        assert loaded_char.strength == 15
        
        # 5. Verify can start new game with loaded character
        world, starting_location = create_world()
        new_game_state = GameState(loaded_char, world, starting_location)
        assert new_game_state.current_location == "Town Square"
        assert new_game_state.current_character.name == "OldHero"
    
    def test_multiple_saves_and_loads(self, tmp_path):
        """Test multiple save/load cycles maintain consistency.
        
        Verifies:
        - Can save multiple times
        - Each load restores correct state
        - States don't interfere with each other
        """
        # Create character and game
        character = Character(name="MultiSave", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)
        
        # Save 1: At starting location
        save1_file = tmp_path / "save1.json"
        with open(save1_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        save1_location = game_state.current_location
        
        # Move and save 2
        game_state.move("north")
        save2_file = tmp_path / "save2.json"
        with open(save2_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        save2_location = game_state.current_location
        
        # Move back and save 3
        game_state.move("south")
        save3_file = tmp_path / "save3.json"
        with open(save3_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        save3_location = game_state.current_location
        
        # Load save 1 and verify
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'MultiSave', 'filepath': str(save1_file), 'timestamp': '1'}
            ]):
                _, state1 = select_and_load_character()
        assert state1.current_location == save1_location
        
        # Load save 2 and verify
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'MultiSave', 'filepath': str(save2_file), 'timestamp': '2'}
            ]):
                _, state2 = select_and_load_character()
        assert state2.current_location == save2_location
        
        # Load save 3 and verify
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'MultiSave', 'filepath': str(save3_file), 'timestamp': '3'}
            ]):
                _, state3 = select_and_load_character()
        assert state3.current_location == save3_location
        
        # Verify all three are different
        assert save1_location != save2_location
        assert save2_location != save3_location
    
    def test_character_state_preservation(self, tmp_path):
        """Test that character state (health, xp, level) is preserved.
        
        Verifies:
        - Damaged health is preserved
        - XP is preserved
        - Level is preserved
        """
        # Create character and damage it
        character = Character(name="DamagedHero", strength=10, dexterity=10, intelligence=10)
        character.take_damage(50)
        character.gain_xp(75)
        
        # Create and save game state
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)
        save_file = tmp_path / "damaged_save.json"
        with open(save_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        
        # Load game state
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'DamagedHero', 'filepath': str(save_file), 'timestamp': '1'}
            ]):
                _, loaded_state = select_and_load_character()
        
        # Verify character state preserved
        loaded_char = loaded_state.current_character
        assert loaded_char.health < loaded_char.max_health
        assert loaded_char.xp == 75
        assert loaded_char.name == "DamagedHero"
    
    def test_theme_variations(self, tmp_path):
        """Test that different themes are preserved correctly.
        
        Verifies:
        - Fantasy theme is preserved
        - Sci-fi theme is preserved
        - Horror theme is preserved
        """
        character = Character(name="ThemeTest", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        
        # Test each theme
        for theme in ["fantasy", "sci-fi", "horror"]:
            game_state = GameState(character, world, starting_location, theme=theme)
            save_file = tmp_path / f"{theme}_save.json"
            with open(save_file, 'w') as f:
                json.dump(game_state.to_dict(), f)
            
            # Load and verify theme
            with patch('builtins.input', return_value='1'):
                with patch('cli_rpg.main.list_saves', return_value=[
                    {'name': 'ThemeTest', 'filepath': str(save_file), 'timestamp': '1'}
                ]):
                    _, loaded_state = select_and_load_character()
            
            assert loaded_state.theme == theme


class TestSaveTypeDetection:
    """Test save type detection across various scenarios."""
    
    def test_detect_mixed_save_types(self, tmp_path):
        """Test detection when saves directory has both types.
        
        Verifies:
        - Character-only saves detected correctly
        - Game state saves detected correctly
        - Both can coexist in same directory
        """
        # Create character-only save
        char_data = {
            "name": "CharOnly",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "constitution": 10,
            "level": 1,
            "health": 150,
            "max_health": 150,
            "xp": 0,
            "xp_to_next_level": 100
        }
        char_file = tmp_path / "char_save.json"
        with open(char_file, 'w') as f:
            json.dump(char_data, f)
        
        # Create game state save
        character = Character(name="GameState", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)
        state_file = tmp_path / "state_save.json"
        with open(state_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        
        # Detect both
        char_type = detect_save_type(str(char_file))
        state_type = detect_save_type(str(state_file))
        
        assert char_type == "character"
        assert state_type == "game_state"
