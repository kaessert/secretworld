"""Tests for main.py game loop state handling."""

from unittest.mock import patch
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.enemy import Enemy
from cli_rpg.game_state import GameState
from cli_rpg.combat import CombatEncounter


class TestGameLoopCombatStateCheck:
    """Test game loop checks combat state each iteration."""
    
    def test_game_loop_uses_is_in_combat_for_command_routing(self):
        """Spec: Main loop must call is_in_combat() to determine command routing."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        
        # Test: Verify is_in_combat() method exists and works
        assert hasattr(game_state, 'is_in_combat'), "GameState should have is_in_combat method"
        assert callable(game_state.is_in_combat), "is_in_combat should be callable"
        
        # Test with no combat
        assert game_state.is_in_combat() is False
        
        # Test with combat
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        assert game_state.is_in_combat() is True


class TestExplorationToCombatTransition:
    """Test transition from exploration to combat."""
    
    def test_random_encounter_triggers_combat_state(self):
        """Spec: Random encounter triggers combat state."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location(name="Town", description="A town", connections={"north": "Forest"}),
            "Forest": Location(name="Forest", description="A forest", connections={"south": "Town"})
        }
        game_state = GameState(character, world, starting_location="Town")
        
        # Test: Move multiple times to trigger encounter
        encounter_triggered = False
        for _ in range(50):
            game_state.current_location = "Town"
            game_state.current_combat = None
            success, message = game_state.move("north")
            
            if game_state.is_in_combat():
                encounter_triggered = True
                break
        
        # Assert: At least one encounter triggered
        assert encounter_triggered, "Should trigger encounter with multiple moves"
    
    def test_trigger_encounter_sets_combat_state(self):
        """Spec: trigger_encounter() should set is_in_combat() to True when successful."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Forest": Location(name="Forest", description="A forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        
        # Test: Try trigger_encounter multiple times
        for _ in range(50):
            game_state.current_combat = None
            result = game_state.trigger_encounter("Forest")
            
            if result is not None:
                # Encounter triggered
                assert game_state.is_in_combat() is True
                break


class TestCombatToExplorationTransition:
    """Test transition from combat to exploration."""
    
    def test_ending_combat_returns_to_exploration_state(self):
        """Spec: Ending combat (victory/flee) returns to exploration state."""
        # Setup
        character = Character(name="Hero", strength=20, dexterity=10, intelligence=10)  # Max strength
        enemy = Enemy(name="Weak Wolf", health=5, max_health=5, attack_power=1, defense=0, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test: Defeat enemy using handle_combat_command
        from cli_rpg.main import handle_combat_command
        handle_combat_command(game_state, "attack", [])
        
        # Assert: No longer in combat
        assert game_state.is_in_combat() is False
    
    def test_successful_flee_returns_to_exploration_state(self):
        """Spec: Successful flee returns to exploration state."""
        # Setup: Max dex for reliable flee
        character = Character(name="Hero", strength=10, dexterity=20, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        
        # Test: Try flee multiple times
        from cli_rpg.main import handle_combat_command
        for _ in range(30):
            game_state.current_combat = CombatEncounter(character, enemy)
            game_state.current_combat.is_active = True
            handle_combat_command(game_state, "flee", [])
            
            if not game_state.is_in_combat():
                # Successfully fled
                break
        
        # Assert: Eventually returns to exploration
        assert game_state.is_in_combat() is False


class TestSaveCommandAvailability:
    """Test save command availability based on combat state."""
    
    def test_save_during_exploration_allowed(self):
        """Spec: Save command works when not in combat."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        
        # Test
        from cli_rpg.main import handle_exploration_command
        with patch('cli_rpg.main.save_game_state') as mock_save:
            mock_save.return_value = "/tmp/test_save.json"
            continue_game, result = handle_exploration_command(game_state, "save", [])
            
            # Assert: Save was called
            mock_save.assert_called_once_with(game_state)
            assert "saved" in result.lower()
    
    def test_save_during_combat_blocked(self):
        """Spec: Save command blocked when in combat."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "save", [])

        # Assert: Error message about combat
        assert "combat" in result.lower()
        assert "can't" in result.lower() or "cannot" in result.lower()
