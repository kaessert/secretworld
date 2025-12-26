"""End-to-end tests for AI integration in main game flow."""

import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService
from cli_rpg.game_state import GameState


@pytest.fixture
def mock_ai_config():
    """Create mock AI config.
    
    Tests: AI config loading at startup requirement from spec.
    """
    config = Mock(spec=AIConfig)
    config.api_key = "test-key"
    config.model = "gpt-4"
    config.temperature = 0.7
    config.max_tokens = 150
    return config


@pytest.fixture
def mock_ai_service():
    """Create mock AI service.
    
    Tests: AI service initialization requirement from spec.
    """
    service = Mock(spec=AIService)
    
    # Mock location generation - returns a dict, not a Location
    def mock_generate_location(theme, context_locations=None, source_location=None, direction=None):
        name = f"{theme.capitalize()} Location"
        if source_location and direction:
            name = f"{theme.capitalize()} {direction.capitalize()}"
        return {
            "name": name,
            "description": f"AI-generated {theme} location",
            "connections": {}
        }
    
    service.generate_location.side_effect = mock_generate_location
    
    return service


def test_ai_config_loading_at_startup(mock_ai_config):
    """Test that main() loads AI config at startup when available.
    
    Tests: AI config loading at startup requirement from spec.
    """
    from cli_rpg.main import main
    
    with patch('cli_rpg.main.load_ai_config', return_value=mock_ai_config), \
         patch('cli_rpg.main.AIService') as MockAIService, \
         patch('builtins.input', return_value="3"):  # Exit immediately
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main(args=[])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify AI service was initialized
        MockAIService.assert_called_once_with(mock_ai_config)
        
        # Verify success message displayed
        assert "AI world generation enabled" in output or "AI" in output
        assert result == 0


def test_ai_graceful_fallback_when_unavailable():
    """Test that main() gracefully falls back when AI is unavailable.
    
    Tests: Graceful fallback when AI unavailable requirement from spec.
    """
    from cli_rpg.main import main
    
    with patch('cli_rpg.main.load_ai_config', return_value=None), \
         patch('builtins.input', return_value="3"):  # Exit immediately
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main(args=[])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Should run without errors
        assert result == 0

        # Should indicate AI not available
        assert "AI" in output or "not available" in output


def test_theme_selection_flow_with_ai(mock_ai_config, mock_ai_service):
    """Test theme selection during character creation with AI.
    
    Tests: Theme selection flow requirement from spec.
    """
    from cli_rpg.main import main
    
    # Simulate: select new character, complete creation, select theme, play, then quit
    inputs = [
        "1",           # Create new character
        "TestHero",    # Character name
        "1",           # Select Warrior class
        "2",           # Random stats
        "yes",         # Confirm character
        "2",           # Select sci-fi theme
        "quit",        # Quit game
        "n",           # Don't save
        "3"            # Exit main menu
    ]
    
    with patch('cli_rpg.main.load_ai_config', return_value=mock_ai_config), \
         patch('cli_rpg.main.AIService', return_value=mock_ai_service), \
         patch('cli_rpg.main.create_world') as mock_create_world, \
         patch('builtins.input', side_effect=inputs):
        
        # Mock world creation to return a simple world
        mock_world = {
            "Town Square": Location(
                name="Town Square",
                description="Starting location"
            )
        }
        mock_create_world.return_value = (mock_world, "Town Square")
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main(args=[])
            sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify create_world was called with AI service and theme
        assert mock_create_world.called
        call_args = mock_create_world.call_args
        assert call_args is not None
        # Check that ai_service was passed
        assert 'ai_service' in call_args.kwargs or len(call_args.args) > 0
        # Check that theme was passed
        assert 'theme' in call_args.kwargs
        
        assert result == 0


def test_world_creation_with_ai_service(mock_ai_service):
    """Test that world is created with AI service when available.
    
    Tests: World creation with AI service requirement from spec.
    """
    from cli_rpg.main import start_game
    
    character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
    
    with patch('cli_rpg.main.create_world') as mock_create_world, \
         patch('cli_rpg.main.GameState') as MockGameState, \
         patch('builtins.input', return_value="quit"):  # Quit immediately
        
        # Mock world
        mock_world = {
            "Town Square": Location(
                name="Town Square",
                description="Starting location"
            )
        }
        mock_create_world.return_value = (mock_world, "Town Square")
        
        # Mock GameState
        mock_game_state_instance = Mock()
        mock_game_state_instance.look.return_value = "You are here"
        mock_game_state_instance.is_in_combat.return_value = False  # Not in combat for this test
        mock_game_state_instance.current_character.is_alive.return_value = True
        MockGameState.return_value = mock_game_state_instance
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            start_game(character, ai_service=mock_ai_service, theme="fantasy")
        finally:
            sys.stdout = old_stdout
        
        # Verify create_world called with AI service
        # Note: strict=True is the default when not specified
        mock_create_world.assert_called_once_with(
            ai_service=mock_ai_service,
            theme="fantasy",
            strict=True
        )
        
        # Verify GameState initialized with AI service
        MockGameState.assert_called_once()
        call_args = MockGameState.call_args
        assert call_args.kwargs.get('ai_service') == mock_ai_service
        assert call_args.kwargs.get('theme') == "fantasy"


def test_game_state_initialization_with_ai(mock_ai_service):
    """Test that GameState receives AI service and theme.
    
    Tests: GameState initialization with AI service requirement from spec.
    """
    from cli_rpg.main import start_game
    
    character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
    
    with patch('cli_rpg.main.create_world') as mock_create_world, \
         patch('cli_rpg.main.GameState') as MockGameState, \
         patch('builtins.input', return_value="quit"):
        
        # Mock world
        mock_world = {
            "Town Square": Location(
                name="Town Square",
                description="Starting location"
            )
        }
        mock_create_world.return_value = (mock_world, "Town Square")
        
        # Mock GameState
        mock_game_state_instance = Mock()
        mock_game_state_instance.look.return_value = "You are here"
        mock_game_state_instance.is_in_combat.return_value = False  # Not in combat for this test
        mock_game_state_instance.current_character.is_alive.return_value = True
        MockGameState.return_value = mock_game_state_instance
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            start_game(character, ai_service=mock_ai_service, theme="cyberpunk")
        finally:
            sys.stdout = old_stdout
        
        # Verify GameState received ai_service and theme
        MockGameState.assert_called_once()
        call_kwargs = MockGameState.call_args.kwargs
        assert call_kwargs['ai_service'] == mock_ai_service
        assert call_kwargs['theme'] == "cyberpunk"


def test_complete_e2e_flow_with_mocked_ai(mock_ai_config, mock_ai_service):
    """Test complete E2E flow: startup → character creation → theme selection → gameplay.
    
    Tests: Complete E2E flow requirement from spec.
    """
    from cli_rpg.main import main
    
    # Simulate complete game flow
    inputs = [
        "1",           # Create new character
        "Hero",        # Character name
        "1",           # Select Warrior class
        "1",           # Manual stats
        "12",          # Strength
        "10",          # Dexterity
        "14",          # Intelligence
        "10",          # Charisma
        "yes",         # Confirm character
        "3",           # Select cyberpunk theme
        "look",        # Look around
        "quit",        # Quit game
        "n",           # Don't save
        "3"            # Exit main menu
    ]
    
    with patch('cli_rpg.main.load_ai_config', return_value=mock_ai_config), \
         patch('cli_rpg.main.AIService', return_value=mock_ai_service), \
         patch('cli_rpg.main.create_world') as mock_create_world:
        
        # Mock world
        mock_world = {
            "Town Square": Location(
                name="Town Square",
                description="A futuristic plaza"
            )
        }
        mock_create_world.return_value = (mock_world, "Town Square")
        
        with patch('builtins.input', side_effect=inputs):
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                result = main(args=[])
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout

        # Verify successful execution
        assert result == 0

        # Verify AI was loaded
        assert "AI" in output

        # Verify character was created
        assert "Hero" in output
        
        # Verify theme was selected
        assert "theme" in output.lower() or "cyberpunk" in output.lower()
        
        # Verify world was created with AI
        assert mock_create_world.called


def test_theme_persistence_in_save_load(mock_ai_service):
    """Test that theme persists through save/load cycle.
    
    Tests: Theme persistence in save/load requirement from spec.
    """
    
    # Create game state with theme
    character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
    world = {
        "Town Square": Location(
            name="Town Square",
            description="Starting location"
        )
    }
    
    original_game_state = GameState(
        character=character,
        world=world,
        ai_service=mock_ai_service,
        theme="steampunk"
    )
    
    # Serialize and deserialize
    state_dict = original_game_state.to_dict()
    assert state_dict['theme'] == "steampunk"
    
    # Load game state
    loaded_game_state = GameState.from_dict(state_dict, ai_service=mock_ai_service)
    
    # Verify theme persisted
    assert loaded_game_state.theme == "steampunk"
    assert loaded_game_state.ai_service == mock_ai_service


def test_default_theme_when_ai_unavailable():
    """Test that default 'fantasy' theme is used when AI is not available.
    
    Tests: Default to 'fantasy' theme requirement from spec.
    """
    from cli_rpg.main import start_game
    
    character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
    
    with patch('cli_rpg.main.create_world') as mock_create_world, \
         patch('cli_rpg.main.GameState') as MockGameState, \
         patch('builtins.input', return_value="quit"):
        
        # Mock world
        mock_world = {
            "Town Square": Location(
                name="Town Square",
                description="Starting location"
            )
        }
        mock_create_world.return_value = (mock_world, "Town Square")
        
        # Mock GameState
        mock_game_state_instance = Mock()
        mock_game_state_instance.look.return_value = "You are here"
        mock_game_state_instance.is_in_combat.return_value = False  # Not in combat for this test
        mock_game_state_instance.current_character.is_alive.return_value = True
        MockGameState.return_value = mock_game_state_instance
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Call without ai_service (should default to fantasy)
            start_game(character)
        finally:
            sys.stdout = old_stdout
        
        # Verify create_world called with default theme
        call_kwargs = mock_create_world.call_args.kwargs
        assert call_kwargs.get('theme') == 'fantasy'


def test_backward_compatibility_with_existing_saves():
    """Test that game loads old saves without theme data.
    
    Tests: Backward compatibility requirement from spec.
    """
    
    # Create old-style save data without theme
    character_data = {
        "name": "OldHero",
        "level": 1,
        "experience": 0,
        "strength": 10,
        "dexterity": 10,
        "intelligence": 10,
        "max_hp": 100,
        "current_hp": 100
    }
    
    world_data = {
        "Town Square": {
            "name": "Town Square",
            "description": "Old location",
            "connections": {}
        }
    }
    
    old_save_data = {
        "character": character_data,
        "current_location": "Town Square",
        "world": world_data
        # Note: no 'theme' key
    }
    
    # Should load successfully with default theme
    game_state = GameState.from_dict(old_save_data)
    
    assert game_state.theme == "fantasy"  # Default theme
    assert game_state.current_character.name == "OldHero"
