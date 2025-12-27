"""Integration tests for main.py save/load functionality.

This test module verifies the integration between main.py and the persistence system,
testing the complete flow of saving and loading both character-only and game state saves.
"""

import json
import pytest
from io import StringIO
from unittest.mock import Mock, patch

from cli_rpg.main import select_and_load_character, main
from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState
from cli_rpg.world import create_world


@pytest.fixture
def sample_character():
    """Create a sample character for testing."""
    return Character(
        name="TestHero",
        strength=10,
        dexterity=12,
        intelligence=8
    )


@pytest.fixture
def sample_game_state(sample_character):
    """Create a sample game state for testing."""
    world, starting_location = create_world()
    return GameState(sample_character, world, starting_location, theme="fantasy")


class TestSelectAndLoadCharacterIntegration:
    """Integration tests for select_and_load_character function."""
    
    def test_returns_tuple(self, tmp_path, sample_character):
        """Test that select_and_load_character returns a tuple.
        
        Spec: Modified function signature - returns tuple of (Character, GameState)
        """
        # Create a character-only save
        save_file = tmp_path / "test_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_character.to_dict(), f)
        
        # Mock user input to select the first save
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                result = select_and_load_character()
        
        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_character_only_save_returns_character(self, tmp_path, sample_character):
        """Test loading character-only save returns (character, None).
        
        Spec: Backward compatibility - character-only saves return character in tuple
        """
        # Create a character-only save
        save_file = tmp_path / "test_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_character.to_dict(), f)
        
        # Mock user input
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                character, game_state = select_and_load_character()
        
        # Should return character, not game state
        assert character is not None
        assert isinstance(character, Character)
        assert character.name == "TestHero"
        assert game_state is None
    
    def test_game_state_save_returns_game_state(self, tmp_path, sample_game_state):
        """Test loading game state save returns (None, game_state).
        
        Spec: Game state loading - full saves return game state in tuple
        """
        # Create a game state save
        save_file = tmp_path / "test_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_game_state.to_dict(), f)
        
        # Mock user input
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                character, game_state = select_and_load_character()
        
        # Should return game state, not character
        assert character is None
        assert game_state is not None
        assert isinstance(game_state, GameState)
        assert game_state.current_character.name == "TestHero"
        assert game_state.current_location == "Town Square"
    
    def test_cancel_returns_none_tuple(self):
        """Test canceling returns (None, None).
        
        Spec: Error handling - cancel returns (None, None)
        """
        # Mock user input to cancel (select option beyond saves)
        with patch('builtins.input', return_value='2'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': 'test.json', 'timestamp': '20240101_120000'}
            ]):
                character, game_state = select_and_load_character()
        
        assert character is None
        assert game_state is None
    
    def test_corrupted_file_returns_none_tuple(self, tmp_path):
        """Test corrupted file returns (None, None).
        
        Spec: Error handling - corrupted files return (None, None)
        """
        # Create corrupted file
        save_file = tmp_path / "corrupted.json"
        with open(save_file, 'w') as f:
            f.write("{invalid json")
        
        # Mock user input
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'Test', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                character, game_state = select_and_load_character()
        
        assert character is None
        assert game_state is None


class TestMainMenuIntegration:
    """Integration tests for main menu handling of loaded saves."""
    
    def test_main_handles_character_load(self, tmp_path, sample_character):
        """Test main menu properly handles character-only load.
        
        Spec: Main menu integration - character loads start new game
        """
        # Create a character-only save
        save_file = tmp_path / "test_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_character.to_dict(), f)
        
        # Mock the entire flow: select load -> select save -> quit game
        inputs = ['2', '1', 'quit', 'n', '3']  # 2=load, 1=first save, quit, no save, 3=exit
        
        with patch('builtins.input', side_effect=inputs):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                with patch('builtins.print'):  # Suppress output
                    result = main(args=[])

        assert result == 0

    def test_main_handles_game_state_load(self, tmp_path, sample_game_state):
        """Test main menu properly handles game state load.
        
        Spec: Main menu integration - game state loads resume from saved location
        """
        # Create a game state save
        save_file = tmp_path / "test_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_game_state.to_dict(), f)
        
        # Mock the flow: select load -> select save -> quit
        inputs = ['2', '1', 'quit', 'n', '3']
        
        with patch('builtins.input', side_effect=inputs):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                with patch('builtins.print'):  # Suppress output
                    result = main(args=[])

        assert result == 0


class TestGameStateResumption:
    """Tests for resuming game from saved game state."""
    
    def test_game_state_preserves_location(self, tmp_path, sample_character):
        """Test that loading game state preserves exact location.
        
        Spec: Game state loading - location is preserved
        """
        # Create game state at a specific location
        world, starting_location = create_world()
        game_state = GameState(sample_character, world, starting_location)
        
        # Move to a different location
        game_state.move("north")
        moved_location = game_state.current_location
        
        # Save game state
        save_file = tmp_path / "game_save.json"
        with open(save_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        
        # Load game state
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                _, loaded_state = select_and_load_character()
        
        # Verify location is preserved
        assert loaded_state is not None
        assert loaded_state.current_location == moved_location
        assert loaded_state.current_location != "Town Square"
    
    def test_game_state_preserves_world_structure(self, tmp_path, sample_game_state):
        """Test that loading game state preserves world structure.
        
        Spec: Game state loading - world structure is preserved
        """
        # Save game state
        save_file = tmp_path / "game_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_game_state.to_dict(), f)
        
        # Track original world size
        original_world_size = len(sample_game_state.world)
        
        # Load game state
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                _, loaded_state = select_and_load_character()
        
        # Verify world is preserved
        assert loaded_state is not None
        assert len(loaded_state.world) == original_world_size
        assert "Town Square" in loaded_state.world
    
    def test_game_state_preserves_theme(self, tmp_path, sample_character):
        """Test that loading game state preserves theme.
        
        Spec: Theme preservation - theme is restored
        """
        # Create game state with specific theme
        world, starting_location = create_world()
        game_state = GameState(sample_character, world, starting_location, theme="sci-fi")
        
        # Save game state
        save_file = tmp_path / "game_save.json"
        with open(save_file, 'w') as f:
            json.dump(game_state.to_dict(), f)
        
        # Load game state
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                _, loaded_state = select_and_load_character()
        
        # Verify theme is preserved
        assert loaded_state is not None
        assert loaded_state.theme == "sci-fi"
    
    def test_ai_service_reattachment(self, tmp_path, sample_game_state):
        """Test that AI service can be re-attached to loaded game state.
        
        Spec: AI service re-attachment - AI service can be re-attached
        """
        # Create a game state save
        save_file = tmp_path / "game_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_game_state.to_dict(), f)
        
        # Mock AI service
        mock_ai_service = Mock()
        
        # Load and re-attach AI service
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                _, loaded_state = select_and_load_character()
        
        # Re-attach AI service (simulating what main() does)
        loaded_state.ai_service = mock_ai_service
        
        # Verify AI service is attached
        assert loaded_state.ai_service is mock_ai_service


class TestBackwardCompatibilityFlow:
    """Tests for backward compatibility with character-only saves."""
    
    def test_character_only_starts_new_game(self, tmp_path, sample_character):
        """Test that character-only save starts a new game.
        
        Spec: Backward compatibility - character-only saves start new game
        """
        # Create character-only save
        save_file = tmp_path / "character_save.json"
        with open(save_file, 'w') as f:
            json.dump(sample_character.to_dict(), f)
        
        # Load character
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'TestHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                character, game_state = select_and_load_character()
        
        # Should get character, not game state
        assert character is not None
        assert game_state is None
        
        # When passed to start_game(), it should create a new world
        # (This is tested implicitly by the main menu integration test)
    
    def test_old_saves_still_work(self, tmp_path):
        """Test that old character-only saves can still be loaded.
        
        Spec: Backward compatibility - all existing saves must work
        """
        # Create an old-style save with minimal fields
        old_save = {
            "name": "OldHero",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
            "health": 150,
            "max_health": 150,
            "xp": 0
        }
        
        save_file = tmp_path / "old_save.json"
        with open(save_file, 'w') as f:
            json.dump(old_save, f)
        
        # Should load without errors
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=[
                {'name': 'OldHero', 'filepath': str(save_file), 'timestamp': '20240101_120000'}
            ]):
                character, game_state = select_and_load_character()
        
        assert character is not None
        assert character.name == "OldHero"
        assert game_state is None


class TestLoadScreenDisplay:
    """Tests for improved load screen display - grouping, limits, timestamps.

    Spec: Load character screen should:
    1. Group autosaves separately after manual saves
    2. Limit manual saves to 15 most recent with hint about more
    3. Display human-readable timestamps instead of raw format
    """

    def test_display_groups_autosaves_separately(self, tmp_path, sample_character, capsys):
        """Autosaves shown in collapsed section after manual saves.

        Spec: Autosaves are displayed after manual saves, collapsed to single entry.
        """
        # Create saves: 2 manual, 2 autosaves
        saves = [
            {'name': 'Hero', 'filepath': str(tmp_path / 'Hero_20241225_120000.json'),
             'timestamp': '20241225_120000', 'display_time': 'Dec 25, 2024 12:00 PM',
             'is_autosave': False},
            {'name': 'Hero', 'filepath': str(tmp_path / 'Hero_20241224_120000.json'),
             'timestamp': '20241224_120000', 'display_time': 'Dec 24, 2024 12:00 PM',
             'is_autosave': False},
            {'name': 'autosave_Hero', 'filepath': str(tmp_path / 'autosave_Hero_20241225_150000.json'),
             'timestamp': '20241225_150000', 'display_time': 'Dec 25, 2024 03:00 PM',
             'is_autosave': True},
            {'name': 'autosave_Hero', 'filepath': str(tmp_path / 'autosave_Hero_20241224_150000.json'),
             'timestamp': '20241224_150000', 'display_time': 'Dec 24, 2024 03:00 PM',
             'is_autosave': True},
        ]

        # Cancel to just see the output
        with patch('builtins.input', return_value='4'):
            with patch('cli_rpg.main.list_saves', return_value=saves):
                select_and_load_character()

        captured = capsys.readouterr()
        output = captured.out

        # Manual saves should appear first
        assert 'Saved Games:' in output
        # Autosave should be marked distinctly
        assert '[Autosave]' in output
        # Should show count of older autosaves
        assert '1 older autosave' in output

    def test_display_limits_manual_saves(self, tmp_path, sample_character, capsys):
        """Only 15 most recent manual saves shown with 'more available' hint.

        Spec: Display at most 15 manual saves with hint showing how many more exist.
        """
        # Create 20 manual saves
        saves = []
        for i in range(20):
            day = 20 - i  # Most recent first
            saves.append({
                'name': f'Hero_{i}',
                'filepath': str(tmp_path / f'Hero_{i}_202412{day:02d}_120000.json'),
                'timestamp': f'202412{day:02d}_120000',
                'display_time': f'Dec {day}, 2024 12:00 PM',
                'is_autosave': False,
            })

        # Cancel to just see the output
        with patch('builtins.input', return_value='16'):
            with patch('cli_rpg.main.list_saves', return_value=saves):
                select_and_load_character()

        captured = capsys.readouterr()
        output = captured.out

        # Should only show 15 saves (indexed 1-15)
        assert '15.' in output
        assert '16.' not in output or 'Cancel' in output  # 16 is cancel button
        # Should show hint about hidden saves
        assert '5 older saves' in output

    def test_display_shows_readable_timestamps(self, tmp_path, sample_character, capsys):
        """Timestamps displayed as 'Dec 25, 2024 3:45 PM' not '20241225_154500'.

        Spec: Timestamps should be human-readable in the display.
        """
        saves = [
            {'name': 'Hero', 'filepath': str(tmp_path / 'Hero_20241225_154530.json'),
             'timestamp': '20241225_154530', 'display_time': 'Dec 25, 2024 03:45 PM',
             'is_autosave': False},
        ]

        # Cancel to just see the output
        with patch('builtins.input', return_value='2'):
            with patch('cli_rpg.main.list_saves', return_value=saves):
                select_and_load_character()

        captured = capsys.readouterr()
        output = captured.out

        # Should show human-readable timestamp
        assert 'Dec 25, 2024' in output
        # Should NOT show raw timestamp format
        assert '20241225_154530' not in output

    def test_display_autosave_count_message(self, tmp_path, sample_character, capsys):
        """When multiple autosaves exist, show count of older ones.

        Spec: If more than one autosave exists, show '(X older autosaves available)'.
        """
        # Create 5 autosaves
        saves = []
        for i in range(5):
            day = 25 - i
            saves.append({
                'name': f'autosave_Hero',
                'filepath': str(tmp_path / f'autosave_Hero_202412{day:02d}_120000.json'),
                'timestamp': f'202412{day:02d}_120000',
                'display_time': f'Dec {day}, 2024 12:00 PM',
                'is_autosave': True,
            })

        # Cancel to just see the output
        with patch('builtins.input', return_value='2'):
            with patch('cli_rpg.main.list_saves', return_value=saves):
                select_and_load_character()

        captured = capsys.readouterr()
        output = captured.out

        # Should show count of older autosaves (5 - 1 = 4)
        assert '4 older autosaves' in output

    def test_loads_selected_autosave(self, tmp_path, sample_character):
        """Selecting autosave entry loads the most recent autosave.

        Spec: When user selects the autosave option, load the most recent autosave.
        """
        # Create a valid autosave file
        save_file = tmp_path / 'autosave_Hero_20241225_120000.json'
        save_file.write_text(json.dumps(sample_character.to_dict()))

        saves = [
            {'name': 'autosave_Hero', 'filepath': str(save_file),
             'timestamp': '20241225_120000', 'display_time': 'Dec 25, 2024 12:00 PM',
             'is_autosave': True},
        ]

        # Select option 1 (the autosave)
        with patch('builtins.input', return_value='1'):
            with patch('cli_rpg.main.list_saves', return_value=saves):
                character, game_state = select_and_load_character()

        # Should load character from autosave
        assert character is not None
        assert character.name == "TestHero"

    def test_no_saves_message(self, capsys):
        """When no saves exist, show appropriate message.

        Spec: If no saves exist, show 'No saved characters found' message.
        """
        with patch('cli_rpg.main.list_saves', return_value=[]):
            character, game_state = select_and_load_character()

        captured = capsys.readouterr()
        output = captured.out

        assert 'No saved characters found' in output
        assert character is None
        assert game_state is None
