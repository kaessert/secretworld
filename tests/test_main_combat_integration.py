"""Tests for main.py combat command integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.enemy import Enemy
from cli_rpg.game_state import GameState
from cli_rpg.combat import CombatEncounter
from cli_rpg.main import start_game


class TestCombatCommandRouting:
    """Test combat command routing during combat."""
    
    def test_attack_command_during_combat_executes_player_attack(self):
        """Spec: When in combat, attack command should execute combat actions."""
        # Setup: Create game state with combat
        character = Character(name="Hero", strength=15, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {
            "Forest": Location(
                name="Forest",
                description="A dark forest",
                connections={}
            )
        }
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test: Import and call handle_combat_command
        from cli_rpg.main import handle_combat_command
        
        initial_enemy_health = enemy.health
        _, result = handle_combat_command(game_state, "attack", [])

        # Assert: Enemy health decreased and message returned
        assert enemy.health < initial_enemy_health
        assert "attack" in result.lower() or "damage" in result.lower()
    
    def test_defend_command_during_combat_sets_defensive_stance(self):
        """Spec: When in combat, defend command should set defensive stance."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "defend", [])

        # Assert: Defensive message returned
        assert "defensive" in result.lower() or "defend" in result.lower() or "brace" in result.lower()
    
    def test_flee_command_during_combat_attempts_escape(self):
        """Spec: When in combat, flee command should attempt to flee from combat."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=20, intelligence=10)  # Max dex for reliable flee
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test - try multiple times since flee has randomness
        from cli_rpg.main import handle_combat_command
        flee_succeeded = False
        for _ in range(30):  # With high dex, should succeed eventually
            game_state.current_combat = CombatEncounter(character, enemy)
            game_state.current_combat.is_active = True
            _, result = handle_combat_command(game_state, "flee", [])
            if "successfully" in result.lower() and game_state.current_combat is None:
                flee_succeeded = True
                break

        # Assert: Flee eventually succeeds with high dexterity
        assert flee_succeeded


class TestExplorationCommandBlocking:
    """Test exploration commands blocked during combat."""
    
    def test_go_command_blocked_during_combat(self):
        """Spec: When in combat, go command should show error message."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {
            "Forest": Location(name="Forest", description="A dark forest", connections={"north": "Town"}),
            "Town": Location(name="Town", description="A town", connections={"south": "Forest"})
        }
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "go", ["north"])

        # Assert: Error message about combat
        assert "combat" in result.lower() and ("can't" in result.lower() or "cannot" in result.lower())
    
    def test_look_command_blocked_during_combat(self):
        """Spec: When in combat, look command should show error message."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "look", [])

        # Assert: Error message about combat
        assert "combat" in result.lower()
    
    def test_save_command_blocked_during_combat(self):
        """Spec: When in combat, save command should show error message."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "save", [])

        # Assert: Error message about combat
        assert "combat" in result.lower()


class TestCombatCommandBlockingDuringExploration:
    """Test combat commands blocked during exploration."""
    
    def test_attack_command_blocked_outside_combat(self):
        """Spec: When not in combat, attack command should show error."""
        # Setup: Game state with no combat
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "attack", [])

        # Assert: Error message about not being in combat
        assert "not in combat" in result.lower()

    def test_defend_command_blocked_outside_combat(self):
        """Spec: When not in combat, defend command should show error."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "defend", [])

        # Assert: Error message about not being in combat
        assert "not in combat" in result.lower()

    def test_flee_command_blocked_outside_combat(self):
        """Spec: When not in combat, flee command should show error."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")

        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "flee", [])

        # Assert: Error message about not being in combat
        assert "not in combat" in result.lower()


class TestStatusCommand:
    """Test status command in both modes."""
    
    def test_status_command_in_exploration_shows_character_stats(self):
        """Spec: Status command during exploration shows character stats."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world = {"Town": Location(name="Town", description="A town", connections={})}
        game_state = GameState(character, world, starting_location="Town")
        
        # Test
        from cli_rpg.main import handle_exploration_command
        continue_game, result = handle_exploration_command(game_state, "status", [])
        
        # Assert: Character stats displayed
        assert "Hero" in result
        assert "level" in result.lower() or "Level" in result
    
    def test_status_command_in_combat_shows_combat_status(self):
        """Spec: Status command during combat shows combat status."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "status", [])

        # Assert: Combat status displayed (both player and enemy health)
        assert "Hero" in result or "Player" in result
        assert "Wolf" in result or "Enemy" in result


class TestPlayerAttackSequence:
    """Test player attack sequence."""
    
    def test_player_attack_damages_enemy_and_triggers_enemy_turn(self):
        """Spec: Attack command damages enemy, triggers enemy turn if combat continues."""
        # Setup
        character = Character(name="Hero", strength=15, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        initial_player_health = character.health
        initial_enemy_health = enemy.health
        handle_combat_command(game_state, "attack", [])

        # Assert: Enemy damaged and enemy counterattacked
        assert enemy.health < initial_enemy_health, "Enemy should take damage"
        assert character.health < initial_player_health, "Enemy should counterattack"


class TestPlayerDefendSequence:
    """Test player defend sequence."""
    
    def test_player_defend_reduces_enemy_damage(self):
        """Spec: Defend command sets defensive stance, enemy attack does reduced damage."""
        # Setup: Use an enemy with high attack to make damage difference clearer
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=20, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        
        # First, get baseline damage without defending
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        initial_health_1 = character.health
        game_state.current_combat.enemy_turn()
        normal_damage = initial_health_1 - character.health
        
        # Reset health
        character.health = character.max_health
        
        # Now test with defend
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        from cli_rpg.main import handle_combat_command
        initial_health_2 = character.health
        handle_combat_command(game_state, "defend", [])
        defended_damage = initial_health_2 - character.health

        # Assert: Defended damage is less than normal damage
        assert defended_damage < normal_damage, f"Defended damage ({defended_damage}) should be less than normal damage ({normal_damage})"


class TestFleeFromCombat:
    """Test fleeing from combat."""
    
    def test_successful_flee_exits_combat_without_xp(self):
        """Spec: Flee command exits combat without XP when successful."""
        # Setup: Max dexterity character for reliable flee
        character = Character(name="Hero", strength=10, dexterity=20, intelligence=10)
        initial_xp = character.xp
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        
        # Test - try multiple times
        from cli_rpg.main import handle_combat_command
        for _ in range(30):
            game_state.current_combat = CombatEncounter(character, enemy)
            game_state.current_combat.is_active = True
            _, result = handle_combat_command(game_state, "flee", [])

            if game_state.current_combat is None:
                # Flee succeeded
                assert character.xp == initial_xp, "Should not gain XP from fleeing"
                assert "successfully" in result.lower() or "flee" in result.lower()
                break

    def test_failed_flee_continues_combat_and_player_takes_damage(self):
        """Spec: Failed flee triggers enemy turn and combat continues."""
        # Setup: Low dexterity for reliable failure
        character = Character(name="Hero", strength=10, dexterity=1, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")

        # Test
        from cli_rpg.main import handle_combat_command
        for _ in range(10):
            game_state.current_combat = CombatEncounter(character, enemy)
            game_state.current_combat.is_active = True
            initial_health = character.health
            handle_combat_command(game_state, "flee", [])

            if game_state.current_combat is not None:
                # Flee failed
                assert game_state.is_in_combat(), "Combat should still be active"
                assert character.health < initial_health, "Player should take damage from enemy"
                break


class TestVictoryEndsCombat:
    """Test victory ends combat and awards XP."""
    
    def test_defeating_enemy_ends_combat_and_awards_xp(self):
        """Spec: Defeating enemy ends combat, awards XP, may trigger level up."""
        # Setup: Strong character vs weak enemy
        character = Character(name="Hero", strength=20, dexterity=10, intelligence=10)  # Max strength
        initial_xp = character.xp
        enemy = Enemy(name="Weak Wolf", health=5, max_health=5, attack_power=1, defense=0, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "attack", [])

        # Assert: Enemy defeated, XP gained, combat cleared
        assert not enemy.is_alive(), "Enemy should be defeated"
        assert character.xp > initial_xp, "Should gain XP"
        assert game_state.current_combat is None, "Combat should be cleared"
        assert "victory" in result.lower() or "defeated" in result.lower()


class TestPlayerDeath:
    """Test player death ends combat."""
    
    def test_player_death_ends_combat(self):
        """Spec: When player health reaches 0, combat ends."""
        # Setup: Weak character at low health
        character = Character(name="Hero", strength=1, dexterity=10, intelligence=10)
        character.health = 1  # Critical health
        enemy = Enemy(name="Strong Wolf", health=50, max_health=50, attack_power=20, defense=0, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test: Attack, which will trigger enemy counterattack
        from cli_rpg.main import handle_combat_command
        _, result = handle_combat_command(game_state, "attack", [])

        # Assert: Player died, combat ended
        assert not character.is_alive(), "Player should be dead"
        assert game_state.current_combat is None, "Combat should be cleared"
        assert "game over" in result.lower() or "defeated" in result.lower()


class TestQuitCommandDuringCombat:
    """Test quit command during combat."""

    def test_quit_command_during_combat_exits_game(self):
        """Spec: When in combat, quit command should allow exiting the game."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Test: Call handle_combat_command with quit, mock input to return 'n' (no save)
        from cli_rpg.main import handle_combat_command
        with patch('builtins.input', return_value='n'):
            continue_game, message = handle_combat_command(game_state, "quit", [])

        # Assert: Function returns False (signal to exit game loop)
        assert continue_game is False

    def test_quit_command_during_combat_shows_warning(self):
        """Spec: When in combat, quit command should show warning about unsaved progress."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Test: Capture printed output
        from cli_rpg.main import handle_combat_command
        import io
        import sys
        captured_output = io.StringIO()
        with patch('builtins.input', return_value='n'), patch('sys.stdout', captured_output):
            continue_game, message = handle_combat_command(game_state, "quit", [])

        # Assert: Warning message was printed
        output = captured_output.getvalue()
        assert "combat" in output.lower() or "warning" in output.lower()

    def test_quit_command_with_save_saves_game(self):
        """Spec: When choosing to save before quitting, game should save."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Test: Mock input to return 'y' (yes save), mock save_game_state
        from cli_rpg.main import handle_combat_command
        with patch('builtins.input', return_value='y'), \
             patch('cli_rpg.main.save_game_state', return_value='/fake/path.json') as mock_save:
            continue_game, message = handle_combat_command(game_state, "quit", [])

        # Assert: save_game_state was called and function returns False
        mock_save.assert_called_once_with(game_state)
        assert continue_game is False


class TestUseItemDuringCombat:
    """Test using consumable items during combat."""

    def test_use_health_potion_during_combat_heals_player(self):
        """Spec: Using a health potion during combat heals the player."""
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.main import handle_combat_command

        # Setup: Create character with a health potion, reduce health
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        character.health = 50  # Take some damage
        potion = Item(
            name="Health Potion",
            description="Restores 30 health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30
        )
        character.inventory.add_item(potion)

        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        initial_health = character.health

        # Test
        continue_game, result = handle_combat_command(game_state, "use", ["Health", "Potion"])

        # Assert: Health increased, potion consumed
        assert character.health > initial_health, "Health should increase"
        assert "healed" in result.lower() or "health" in result.lower()
        assert character.inventory.find_item_by_name("Health Potion") is None, "Potion should be consumed"

    def test_use_item_during_combat_triggers_enemy_turn(self):
        """Spec: After using an item during combat, the enemy attacks."""
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.main import handle_combat_command

        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        character.health = 50  # Take some damage
        potion = Item(
            name="Health Potion",
            description="Restores 30 health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30
        )
        character.inventory.add_item(potion)

        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=10, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # After healing 30, expect 80. Then enemy with 10 attack should deal some damage
        # We need to track if enemy turn happened
        _, result = handle_combat_command(game_state, "use", ["Health", "Potion"])

        # Assert: Enemy attack message in result
        assert "wolf" in result.lower() or "attack" in result.lower() or "damage" in result.lower()

    def test_use_item_not_found_during_combat(self):
        """Spec: Using a non-existent item shows an error."""
        from cli_rpg.main import handle_combat_command

        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Test
        continue_game, result = handle_combat_command(game_state, "use", ["Nonexistent", "Item"])

        # Assert: Error message about not having the item
        assert "don't have" in result.lower() or "not found" in result.lower()

    def test_use_no_args_during_combat(self):
        """Spec: Using 'use' without specifying an item shows an error."""
        from cli_rpg.main import handle_combat_command

        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Test
        continue_game, result = handle_combat_command(game_state, "use", [])

        # Assert: Error message about specifying an item
        assert "use what" in result.lower() or "specify" in result.lower()

    def test_use_non_consumable_during_combat(self):
        """Spec: Using a non-consumable item (weapon/armor) shows an error."""
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.main import handle_combat_command

        # Setup: Create character with a weapon
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        sword = Item(
            name="Iron Sword",
            description="A sturdy iron sword",
            item_type=ItemType.WEAPON,
            damage_bonus=5
        )
        character.inventory.add_item(sword)

        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Test
        continue_game, result = handle_combat_command(game_state, "use", ["Iron", "Sword"])

        # Assert: Error message about not being a consumable
        assert "consumable" in result.lower() or "can't use" in result.lower()

    def test_use_potion_at_full_health_during_combat(self):
        """Spec: Using a health potion when at full health shows an error."""
        from cli_rpg.models.item import Item, ItemType
        from cli_rpg.main import handle_combat_command

        # Setup: Character at full health with a potion
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        potion = Item(
            name="Health Potion",
            description="Restores 30 health",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30
        )
        character.inventory.add_item(potion)

        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True

        # Verify at full health
        assert character.health == character.max_health

        # Test
        continue_game, result = handle_combat_command(game_state, "use", ["Health", "Potion"])

        # Assert: Error message about full health
        assert "full health" in result.lower()
        # Potion should NOT be consumed
        assert character.inventory.find_item_by_name("Health Potion") is not None


class TestCombatStatePersistence:
    """Test combat encounter object persists through turns."""

    def test_combat_instance_persists_across_turns(self):
        """Spec: Combat encounter object remains active through multiple turns."""
        # Setup
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=5, defense=2, xp_reward=20)
        world = {"Forest": Location(name="Forest", description="A dark forest", connections={})}
        game_state = GameState(character, world, starting_location="Forest")
        game_state.current_combat = CombatEncounter(character, enemy)
        game_state.current_combat.is_active = True
        
        # Test: Store reference and perform multiple actions
        from cli_rpg.main import handle_combat_command
        combat_instance = game_state.current_combat
        
        handle_combat_command(game_state, "defend", [])
        assert game_state.current_combat is combat_instance, "Combat instance should persist"
        
        handle_combat_command(game_state, "attack", [])
        # Only check if combat still active (might end if enemy defeated)
        if game_state.current_combat is not None:
            assert game_state.current_combat is combat_instance, "Combat instance should persist"
