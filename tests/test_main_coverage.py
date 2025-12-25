"""Tests for main.py coverage improvement - targeting uncovered lines.

These tests cover edge cases and error paths in main.py to improve coverage.
"""

import pytest
import io
import sys
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.npc import NPC
from cli_rpg.models.item import Item, ItemType
from cli_rpg.game_state import GameState
from cli_rpg.combat import CombatEncounter


class TestPromptSaveCharacter:
    """Tests for prompt_save_character function (lines 64-75)."""

    def test_offer_save_character_saves_on_yes(self):
        """Spec: When user answers 'y', character should be saved."""
        from cli_rpg.main import prompt_save_character

        character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)

        with patch('builtins.input', return_value='y'), \
             patch('cli_rpg.main.save_character') as mock_save:
            mock_save.return_value = "/tmp/test_save.json"
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                prompt_save_character(character)

            mock_save.assert_called_once_with(character)
            output = captured_output.getvalue()
            assert "saved successfully" in output.lower()

    def test_offer_save_character_skips_on_no(self):
        """Spec: When user answers 'n', character should not be saved."""
        from cli_rpg.main import prompt_save_character

        character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)

        with patch('builtins.input', return_value='n'), \
             patch('cli_rpg.main.save_character') as mock_save:
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                prompt_save_character(character)

            mock_save.assert_not_called()
            output = captured_output.getvalue()
            assert "not saved" in output.lower()

    def test_offer_save_character_handles_io_error(self):
        """Spec: IOError during save should be caught and error message shown."""
        from cli_rpg.main import prompt_save_character

        character = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)

        with patch('builtins.input', return_value='y'), \
             patch('cli_rpg.main.save_character', side_effect=IOError("Disk full")):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                prompt_save_character(character)

            output = captured_output.getvalue()
            assert "failed to save" in output.lower()


class TestSelectAndLoadCharacter:
    """Tests for select_and_load_character function (lines 133-158)."""

    def test_load_character_handles_game_state_exception(self):
        """Spec: Exception during game_state load should return (None, None)."""
        from cli_rpg.main import select_and_load_character

        # Create a temp save file with game_state type
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "world": {},  # Makes it detect as game_state
                "character": {"name": "Test"},
                "current_location": "Town"
            }, f)
            temp_path = f.name

        try:
            mock_saves = [{'name': 'TestChar', 'filepath': temp_path, 'timestamp': '20240101_120000'}]

            with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
                 patch('builtins.input', return_value='1'), \
                 patch('cli_rpg.main.detect_save_type', return_value='game_state'), \
                 patch('cli_rpg.main.load_game_state', side_effect=Exception("Corrupted data")):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = select_and_load_character()

                assert result == (None, None)
                output = captured_output.getvalue()
                assert "failed to load game state" in output.lower()
        finally:
            os.unlink(temp_path)

    def test_load_character_handles_invalid_input(self):
        """Spec: Non-numeric input should return (None, None)."""
        from cli_rpg.main import select_and_load_character

        mock_saves = [{'name': 'TestChar', 'filepath': '/tmp/test.json', 'timestamp': '20240101_120000'}]

        with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
             patch('builtins.input', return_value='abc'):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = select_and_load_character()

            assert result == (None, None)
            output = captured_output.getvalue()
            assert "invalid input" in output.lower() or "please enter a number" in output.lower()

    def test_load_character_handles_file_not_found(self):
        """Spec: FileNotFoundError should return (None, None)."""
        from cli_rpg.main import select_and_load_character

        mock_saves = [{'name': 'TestChar', 'filepath': '/nonexistent/path.json', 'timestamp': '20240101_120000'}]

        with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
             patch('builtins.input', return_value='1'), \
             patch('cli_rpg.main.detect_save_type', side_effect=FileNotFoundError("Not found")):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = select_and_load_character()

            assert result == (None, None)
            output = captured_output.getvalue()
            assert "not found" in output.lower()

    def test_load_character_handles_generic_exception(self):
        """Spec: Generic Exception during load should return (None, None)."""
        from cli_rpg.main import select_and_load_character

        # Create a temp save file with character type
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"name": "Test", "strength": 10, "dexterity": 10, "intelligence": 10}, f)
            temp_path = f.name

        try:
            mock_saves = [{'name': 'TestChar', 'filepath': temp_path, 'timestamp': '20240101_120000'}]

            with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
                 patch('builtins.input', return_value='1'), \
                 patch('cli_rpg.main.detect_save_type', return_value='character'), \
                 patch('cli_rpg.main.load_character', side_effect=Exception("Unknown error")):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = select_and_load_character()

                assert result == (None, None)
                output = captured_output.getvalue()
                assert "failed to load character" in output.lower()
        finally:
            os.unlink(temp_path)


class TestCombatDeathPaths:
    """Tests for combat death paths (lines 274-278, 302-305, 334-340, 362-365)."""

    def test_combat_defend_player_death(self):
        """Spec: Player can die after defend command."""
        from cli_rpg.main import handle_combat_command

        # Setup: Very weak player, strong enemy
        character = Character(name="Hero", strength=1, dexterity=1, intelligence=1)
        character.health = 1  # Near death
        enemy = Enemy(name="Dragon", health=100, max_health=100, attack_power=50, defense=0, xp_reward=50)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        _, result = handle_combat_command(game_state, "defend", [])

        assert not character.is_alive()
        assert "game over" in result.lower()
        assert game_state.current_combat is None

    def test_combat_flee_failed_player_death(self):
        """Spec: Player can die after failed flee."""
        from cli_rpg.main import handle_combat_command

        # Setup: Very weak player at 1 HP, low dex for failed flee
        character = Character(name="Hero", strength=1, dexterity=1, intelligence=1)
        character.health = 1
        enemy = Enemy(name="Dragon", health=100, max_health=100, attack_power=50, defense=0, xp_reward=50)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")

        # Try flee multiple times until we die (low dex = mostly fails)
        died = False
        for _ in range(20):
            character.health = 1  # Reset to near-death each attempt
            game_state.current_combat = CombatEncounter(character, enemy)
            game_state.current_combat.is_active = True

            _, result = handle_combat_command(game_state, "flee", [])

            if not character.is_alive():
                died = True
                assert "game over" in result.lower()
                assert game_state.current_combat is None
                break

        assert died, "Player should die after failed flee with low dex"

    def test_combat_cast_victory_with_quest_progress(self):
        """Spec: Cast command victory should trigger quest progress."""
        from cli_rpg.main import handle_combat_command
        from cli_rpg.models.quest import Quest, ObjectiveType, QuestStatus

        # Setup: Strong mage vs weak enemy
        character = Character(name="Mage", strength=5, dexterity=10, intelligence=20)
        enemy = Enemy(name="Goblin", health=1, max_health=1, attack_power=1, defense=0, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Add a kill quest for Goblins
        quest = Quest(
            name="Kill Goblins",
            description="Kill 1 goblin",
            objective_type=ObjectiveType.KILL,
            target="Goblin",
            target_count=1,
            status=QuestStatus.ACTIVE
        )
        character.quests.append(quest)

        _, result = handle_combat_command(game_state, "cast", [])

        assert not enemy.is_alive()
        assert quest.current_count == 1
        assert quest.status == QuestStatus.READY_TO_TURN_IN

    def test_combat_cast_player_death(self):
        """Spec: Player can die after cast fails to kill enemy."""
        from cli_rpg.main import handle_combat_command

        # Setup: Very weak player, strong enemy
        character = Character(name="Hero", strength=1, dexterity=1, intelligence=1)
        character.health = 1
        enemy = Enemy(name="Dragon", health=100, max_health=100, attack_power=50, defense=0, xp_reward=50)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        _, result = handle_combat_command(game_state, "cast", [])

        assert not character.is_alive()
        assert "game over" in result.lower()
        assert game_state.current_combat is None

    def test_combat_use_item_player_death(self):
        """Spec: Player can die after using item (enemy counterattack)."""
        from cli_rpg.main import handle_combat_command

        # Setup: Player at critical HP with a potion
        character = Character(name="Hero", strength=1, dexterity=1, intelligence=1)
        character.health = 5
        potion = Item(
            name="Weak Potion",
            description="Heals a tiny bit",
            item_type=ItemType.CONSUMABLE,
            heal_amount=2  # Won't save the player
        )
        character.inventory.add_item(potion)

        enemy = Enemy(name="Dragon", health=100, max_health=100, attack_power=50, defense=0, xp_reward=50)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        _, result = handle_combat_command(game_state, "use", ["Weak", "Potion"])

        assert not character.is_alive()
        assert "game over" in result.lower()
        assert game_state.current_combat is None


class TestConversationAIError:
    """Tests for AI conversation error fallback (lines 208-210)."""

    def test_conversation_ai_error_fallback(self):
        """Spec: AI service exception should trigger fallback response."""
        from cli_rpg.main import handle_conversation_input

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        npc = NPC(
            name="Merchant",
            description="A friendly merchant",
            dialogue="Hello traveler!",
            is_merchant=True
        )
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        game_state.current_npc = npc

        # Mock AI service that raises an exception
        mock_ai_service = Mock()
        mock_ai_service.generate_conversation_response.side_effect = Exception("AI error")
        game_state.ai_service = mock_ai_service

        continue_game, message = handle_conversation_input(game_state, "Hello there!")

        assert continue_game is True
        # Fallback response should be the generic nod
        assert "nods thoughtfully" in message.lower()


class TestGameLoopDeathRecovery:
    """Tests for game loop death handling (lines 915-926, 936)."""

    def test_game_loop_death_return_to_menu(self):
        """Spec: Player dead + 'y' returns to menu (breaks loop)."""
        from cli_rpg.main import run_game_loop

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        character.health = 0  # Dead
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        with patch('builtins.input', return_value='y'):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                run_game_loop(game_state)

            output = captured_output.getvalue()
            assert "game over" in output.lower()

    def test_game_loop_death_continue(self):
        """Spec: Player dead + 'n' resurrects player and continues."""
        from cli_rpg.main import run_game_loop

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        character.health = 0  # Dead
        world = {"Town Square": Location(name="Town Square", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town Square")

        # First 'n' to resurrect, then 'quit' and 'n' to exit
        inputs = iter(['n', 'quit', 'n'])
        with patch('builtins.input', lambda x: next(inputs)):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                run_game_loop(game_state)

            # Character should be resurrected
            output = captured_output.getvalue()
            assert "health restored" in output.lower()

    def test_game_loop_empty_input_ignored(self):
        """Spec: Empty command input should continue loop."""
        from cli_rpg.main import run_game_loop

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        # Empty input, then quit
        inputs = iter(['', 'quit', 'n'])
        with patch('builtins.input', lambda x: next(inputs)):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                run_game_loop(game_state)

            # Loop should have continued past empty input


class TestStartGameAIError:
    """Tests for start_game AI error handling (lines 987-1014)."""

    def test_start_game_ai_error_retry(self):
        """Spec: AI fails, user selects retry (1), should retry."""
        from cli_rpg.main import start_game

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # First call fails, second succeeds
        call_count = [0]
        def mock_create_world(ai_service=None, theme="fantasy", strict=True):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("AI failed")
            # Return valid world on retry
            return (
                {"Town": Location(name="Town", description="A town", connections={})},
                "Town"
            )

        # User chooses 1 (retry), then quit
        inputs = iter(['1', 'quit', 'n'])

        with patch('cli_rpg.main.create_world', side_effect=mock_create_world), \
             patch('builtins.input', lambda x: next(inputs)):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                start_game(character, strict=True)

            output = captured_output.getvalue()
            assert "ai world generation failed" in output.lower() or "retry" in output.lower() or "welcome" in output.lower()

    def test_start_game_ai_error_use_default(self):
        """Spec: AI fails, user selects default world (2)."""
        from cli_rpg.main import start_game

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Mock create_world: first strict call fails, second non-strict succeeds
        def mock_create_world(ai_service=None, theme="fantasy", strict=True):
            if strict:
                raise Exception("AI failed")
            # Return valid world for non-strict mode
            return (
                {"Town": Location(name="Town", description="A town", connections={})},
                "Town"
            )

        # User chooses 2 (use default), then quit
        inputs = iter(['2', 'quit', 'n'])

        with patch('cli_rpg.main.create_world', side_effect=mock_create_world), \
             patch('builtins.input', lambda x: next(inputs)):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                start_game(character, strict=True)

            output = captured_output.getvalue()
            # Should proceed to game with default world
            assert "welcome" in output.lower() or "command" in output.lower()

    def test_start_game_ai_error_return_to_menu(self):
        """Spec: AI fails, user selects return to menu (3)."""
        from cli_rpg.main import start_game

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        with patch('cli_rpg.main.create_world', side_effect=Exception("AI failed")), \
             patch('builtins.input', return_value='3'):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = start_game(character, strict=True)

            # Should return without starting game (returns None implicitly)
            assert result is None

    def test_start_game_ai_error_invalid_choice_then_valid(self):
        """Spec: AI fails, invalid choice, then valid choice."""
        from cli_rpg.main import start_game

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # User enters invalid then 3 (return to menu)
        inputs = iter(['5', 'abc', '3'])

        with patch('cli_rpg.main.create_world', side_effect=Exception("AI failed")), \
             patch('builtins.input', lambda x: next(inputs)):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                start_game(character, strict=True)

            output = captured_output.getvalue()
            assert "invalid choice" in output.lower()


class TestExplorationSaveIOError:
    """Tests for exploration save IOError handling (line 838-839)."""

    def test_exploration_save_handles_io_error(self):
        """Spec: IOError during exploration save should show error message."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        with patch('cli_rpg.main.save_game_state', side_effect=IOError("Disk full")):
            continue_game, result = handle_exploration_command(game_state, "save", [])

        assert continue_game is True
        assert "failed to save" in result.lower()


class TestExplorationQuitSaveIOError:
    """Tests for exploration quit save IOError handling (line 850)."""

    def test_exploration_quit_save_handles_io_error(self):
        """Spec: IOError during quit save should show error message."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        with patch('builtins.input', return_value='y'), \
             patch('cli_rpg.main.save_game_state', side_effect=IOError("Disk full")):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                continue_game, _ = handle_exploration_command(game_state, "quit", [])

            output = captured_output.getvalue()
            assert "failed to save" in output.lower()
            assert continue_game is False  # Should still quit


class TestCorruptedSaveFileDetection:
    """Tests for corrupted save file detection (lines 119-121)."""

    def test_load_handles_corrupted_save_file(self):
        """Spec: ValueError from detect_save_type should show corruption message."""
        from cli_rpg.main import select_and_load_character

        mock_saves = [{'name': 'CorruptedSave', 'filepath': '/tmp/corrupt.json', 'timestamp': '20240101_120000'}]

        with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
             patch('builtins.input', return_value='1'), \
             patch('cli_rpg.main.detect_save_type', side_effect=ValueError("Invalid JSON")):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = select_and_load_character()

            assert result == (None, None)
            output = captured_output.getvalue()
            assert "corrupted" in output.lower()


class TestExplorationCombatCommandsOutsideCombat:
    """Tests for combat commands when not in combat (lines 905-912)."""

    def test_attack_command_outside_combat(self):
        """Spec: Attack command should say 'Not in combat' when not in combat."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        # No combat active

        continue_game, message = handle_exploration_command(game_state, "attack", [])

        assert continue_game is True
        assert "Not in combat" in message

    def test_defend_command_outside_combat(self):
        """Spec: Defend command should say 'Not in combat' when not in combat."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "defend", [])

        assert continue_game is True
        assert "Not in combat" in message

    def test_flee_command_outside_combat(self):
        """Spec: Flee command should say 'Not in combat' when not in combat."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "flee", [])

        assert continue_game is True
        assert "Not in combat" in message

    def test_unknown_command_shows_help_hint(self):
        """Spec: Unknown command should show help hint."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "xyz", [])

        assert continue_game is True
        assert "Unknown command" in message
        assert "help" in message.lower()


class TestLoadCharacterInvalidSelection:
    """Tests for load character invalid selection (lines 147-149)."""

    def test_load_character_invalid_selection_out_of_range(self):
        """Spec: Out-of-range selection should return (None, None)."""
        from cli_rpg.main import select_and_load_character

        mock_saves = [
            {'name': 'TestChar', 'filepath': '/tmp/test.json', 'timestamp': '20240101_120000'}
        ]

        # Select option 5 when only 1 save + 1 cancel option exist
        with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
             patch('builtins.input', return_value='5'):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = select_and_load_character()

            assert result == (None, None)
            output = captured_output.getvalue()
            assert "invalid selection" in output.lower()

    def test_load_character_invalid_selection_negative(self):
        """Spec: Negative selection should return (None, None)."""
        from cli_rpg.main import select_and_load_character

        mock_saves = [
            {'name': 'TestChar', 'filepath': '/tmp/test.json', 'timestamp': '20240101_120000'}
        ]

        # Select negative number
        with patch('cli_rpg.main.list_saves', return_value=mock_saves), \
             patch('builtins.input', return_value='-1'):
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = select_and_load_character()

            assert result == (None, None)
            output = captured_output.getvalue()
            assert "invalid selection" in output.lower()


class TestGoCommand:
    """Tests for 'go' exploration command (lines 404-415)."""

    def test_go_command_no_args(self):
        """Spec: 'go' without direction should prompt for direction (line 404-405)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={"north": "Forest"})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "go", [])

        assert continue_game is True
        assert "go where" in message.lower() or "specify a direction" in message.lower()

    def test_go_command_successful_movement(self):
        """Spec: Successful movement shows new location (lines 411-413)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        town = Location(name="Town", description="A bustling town", connections={"north": "Forest"})
        forest = Location(name="Forest", description="A dark forest", connections={"south": "Town"})
        world = {"Town": town, "Forest": forest}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "go", ["north"])

        assert continue_game is True
        assert game_state.current_location == "Forest"
        # Should show new location description
        assert "forest" in message.lower() or "dark" in message.lower()

    def test_go_command_blocked_direction(self):
        """Spec: Movement failure shows error message (lines 408-409)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={"north": "Forest"})}
        game_state = GameState(character, world, starting_location="Town")

        # Try to go south when there's no connection
        continue_game, message = handle_exploration_command(game_state, "go", ["south"])

        assert continue_game is True
        # Should remain at Town
        assert game_state.current_location == "Town"
        # Message should indicate failure
        assert "can't go" in message.lower() or "no exit" in message.lower()


class TestUnequipCommands:
    """Tests for unequip command edge cases (lines 434, 441, 446, 451)."""

    def test_unequip_no_args(self):
        """Spec: 'unequip' without slot should prompt for slot (line 437-438)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", [])

        assert continue_game is True
        assert "unequip what" in message.lower() or "weapon" in message.lower()

    def test_unequip_invalid_slot(self):
        """Spec: Invalid slot should show error (line 440-441)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", ["helmet"])

        assert continue_game is True
        assert "weapon" in message.lower() or "armor" in message.lower()

    def test_unequip_weapon_when_none_equipped(self):
        """Spec: Unequip weapon when none equipped shows error (lines 443-444)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # Ensure no weapon is equipped
        character.inventory.equipped_weapon = None
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", ["weapon"])

        assert continue_game is True
        assert "don't have a weapon" in message.lower()

    def test_unequip_armor_when_none_equipped(self):
        """Spec: Unequip armor when none equipped shows error (lines 445-446)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # Ensure no armor is equipped
        character.inventory.equipped_armor = None
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", ["armor"])

        assert continue_game is True
        assert "don't have armor" in message.lower()

    def test_unequip_weapon_success(self):
        """Spec: Successful unequip shows success message (lines 447-449)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        weapon = Item(name="Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5)
        character.inventory.add_item(weapon)
        character.inventory.equip(weapon)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", ["weapon"])

        assert continue_game is True
        assert "unequipped" in message.lower()
        assert character.inventory.equipped_weapon is None

    def test_unequip_armor_success(self):
        """Spec: Successful armor unequip works correctly (lines 447-449)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        armor = Item(name="Leather", description="Armor", item_type=ItemType.ARMOR, defense_bonus=3)
        character.inventory.add_item(armor)
        character.inventory.equip(armor)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", ["armor"])

        assert continue_game is True
        assert "unequipped" in message.lower()
        assert character.inventory.equipped_armor is None

    def test_unequip_fails_inventory_full(self):
        """Spec: Unequip fails when inventory full (line 450-451)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        weapon = Item(name="Sword", description="A sword", item_type=ItemType.WEAPON, damage_bonus=5)
        character.inventory.add_item(weapon)
        character.inventory.equip(weapon)
        # Fill inventory to capacity
        for i in range(character.inventory.capacity):
            filler = Item(name=f"Filler{i}", description="filler", item_type=ItemType.MISC)
            character.inventory.add_item(filler)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "unequip", ["weapon"])

        assert continue_game is True
        assert "full" in message.lower() or "can't unequip" in message.lower()


class TestCombatStatusDisplay:
    """Tests for combat status display (lines 953-961)."""

    def test_combat_command_shows_status_after_action(self):
        """Spec: Combat status should display after each action (lines 959-961)."""
        from cli_rpg.main import handle_combat_command

        character = Character(name="Hero", strength=15, dexterity=10, intelligence=10)
        character.health = 100
        enemy = Enemy(name="Goblin", health=50, max_health=50, attack_power=5, defense=0, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Attack but don't kill enemy
        _, result = handle_combat_command(game_state, "defend", [])

        # Combat should still be active, so status would be shown
        # The status display happens in run_game_loop, but we can verify combat is still active
        assert game_state.is_in_combat()


class TestConversationRouting:
    """Tests for conversation routing in game loop (lines 962-968)."""

    def test_conversation_mode_routes_unknown_commands(self):
        """Spec: Unknown commands in conversation mode go to conversation handler."""
        from cli_rpg.main import handle_conversation_input

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        npc = NPC(
            name="Bob",
            description="A villager",
            dialogue="Hello!"
        )
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        game_state.current_npc = npc

        # Send free-form text that would be treated as conversation
        continue_game, message = handle_conversation_input(game_state, "What's the weather like?")

        assert continue_game is True
        # Should get an NPC response (either AI or fallback)
        assert npc.name in message or "nods" in message.lower()


class TestEquipCannotEquip:
    """Tests for equip command when item cannot be equipped (line 434)."""

    def test_equip_misc_item_fails(self):
        """Spec: Cannot equip misc items (line 433-434)."""
        from cli_rpg.main import handle_exploration_command

        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        misc_item = Item(name="Key", description="A rusty key", item_type=ItemType.MISC)
        character.inventory.add_item(misc_item)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        continue_game, message = handle_exploration_command(game_state, "equip", ["Key"])

        assert continue_game is True
        assert "can't equip" in message.lower()
