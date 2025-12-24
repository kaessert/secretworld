"""Tests for the help command during exploration and combat modes.

These tests verify that:
1. The 'help' command displays the command reference during exploration
2. The 'help' command displays the command reference during combat
3. The help command returns (True, message) so the game continues
"""

import pytest
from cli_rpg.main import handle_exploration_command, handle_combat_command, get_command_reference
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.combat import CombatEncounter
from cli_rpg.models.enemy import Enemy


@pytest.fixture
def basic_character():
    """Create a basic character for testing."""
    return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def basic_world():
    """Create a basic world for testing."""
    return {
        "Test Room": Location(
            name="Test Room",
            description="A test room.",
            connections={},
            coordinates=(0, 0)
        )
    }


@pytest.fixture
def game_state(basic_character, basic_world):
    """Create a basic game state for testing."""
    return GameState(basic_character, basic_world, starting_location="Test Room")


@pytest.fixture
def combat_game_state(game_state):
    """Create a game state with active combat."""
    enemy = Enemy(
        name="Test Goblin", health=20, max_health=20, attack_power=5, defense=2, xp_reward=10
    )
    combat = CombatEncounter(game_state.current_character, enemy)
    combat.start()  # Activate combat
    game_state.current_combat = combat
    return game_state


# Test get_command_reference function
class TestGetCommandReference:
    """Tests for the get_command_reference() helper function."""

    def test_get_command_reference_returns_string(self):
        """get_command_reference() returns a non-empty string."""
        result = get_command_reference()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_command_reference_includes_exploration_commands(self):
        """get_command_reference() includes exploration commands."""
        result = get_command_reference()
        # Verify key exploration commands are present
        assert "look" in result.lower()
        assert "go" in result.lower()
        assert "status" in result.lower()
        assert "inventory" in result.lower()
        assert "equip" in result.lower()
        assert "save" in result.lower()
        assert "quit" in result.lower()

    def test_get_command_reference_includes_combat_commands(self):
        """get_command_reference() includes combat commands."""
        result = get_command_reference()
        # Verify key combat commands are present
        assert "attack" in result.lower()
        assert "defend" in result.lower()
        assert "cast" in result.lower()
        assert "flee" in result.lower()

    def test_get_command_reference_includes_help_command(self):
        """get_command_reference() lists 'help' as an available command."""
        result = get_command_reference()
        assert "help" in result.lower()
        assert "command reference" in result.lower() or "commands" in result.lower()


# Test exploration mode
class TestHelpCommandDuringExploration:
    """Tests for 'help' command during exploration mode."""

    def test_help_command_during_exploration(self, game_state):
        """'help' command returns command reference with exploration commands."""
        continue_game, message = handle_exploration_command(game_state, "help", [])

        # Should contain exploration commands
        assert "look" in message.lower()
        assert "go" in message.lower()
        assert "inventory" in message.lower()

    def test_help_command_shows_combat_commands(self, game_state):
        """'help' command output includes combat commands (attack, defend, cast, flee)."""
        continue_game, message = handle_exploration_command(game_state, "help", [])

        # Should contain combat commands
        assert "attack" in message.lower()
        assert "defend" in message.lower()
        assert "cast" in message.lower()
        assert "flee" in message.lower()

    def test_help_continues_game(self, game_state):
        """'help' command returns (True, message) - doesn't exit game."""
        continue_game, message = handle_exploration_command(game_state, "help", [])

        assert continue_game is True
        assert isinstance(message, str)
        assert len(message) > 0


# Test combat mode
class TestHelpCommandDuringCombat:
    """Tests for 'help' command during combat mode."""

    def test_help_command_during_combat(self, combat_game_state):
        """'help' command works during combat and returns command reference."""
        continue_game, message = handle_combat_command(combat_game_state, "help", [])

        # Should contain commands
        assert "attack" in message.lower()
        assert "defend" in message.lower()
        assert "look" in message.lower()

    def test_help_combat_continues_game(self, combat_game_state):
        """'help' command during combat returns (True, message) - doesn't exit game."""
        continue_game, message = handle_combat_command(combat_game_state, "help", [])

        assert continue_game is True
        assert isinstance(message, str)
        assert len(message) > 0
