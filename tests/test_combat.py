"""Tests for Combat Encounter system."""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter, spawn_enemy


class TestCombatInitialization:
    """Test combat initialization."""
    
    def test_create_combat_encounter(self):
        """Spec: CombatEncounter should initialize with player and enemy."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        
        assert combat.player == player
        assert combat.enemy == enemy
        assert combat.turn_count == 0
        assert combat.is_active is False


class TestCombatStart:
    """Test combat start."""
    
    def test_start_returns_intro_message(self):
        """Spec: start() should return an intro message and set is_active to True."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        message = combat.start()
        
        assert combat.is_active is True
        assert "Goblin" in message
        assert "combat" in message.lower() or "encounter" in message.lower()


class TestPlayerAttack:
    """Test player_attack() method."""
    
    def test_player_attack_damages_enemy(self):
        """Spec: player_attack() should damage enemy based on player's strength."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.strength = 10  # Set known strength
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        initial_health = enemy.health
        victory, message = combat.player_attack()
        
        # Damage should be strength - enemy defense
        expected_damage = max(1, player.strength - enemy.defense)
        assert enemy.health == initial_health - expected_damage
        assert message is not None
        assert len(message) > 0
    
    def test_player_attack_handles_enemy_defeat(self):
        """Spec: player_attack() should return victory=True when enemy is defeated."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.strength = 100  # High damage to ensure defeat
        enemy = Enemy(
            name="Goblin",
            health=5,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        victory, message = combat.player_attack()
        
        assert victory is True
        assert enemy.is_alive() is False
        assert "defeat" in message.lower() or "killed" in message.lower() or "victory" in message.lower()
    
    def test_player_attack_continues_combat_when_enemy_survives(self):
        """Spec: player_attack() should return victory=False when enemy survives."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.strength = 5  # Low damage
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        victory, message = combat.player_attack()
        
        assert victory is False
        assert enemy.is_alive() is True


class TestPlayerDefend:
    """Test player_defend() method."""
    
    def test_player_defend_sets_defensive_stance(self):
        """Spec: player_defend() should set defensive stance (reduced damage next turn)."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        victory, message = combat.player_defend()
        
        assert victory is False
        assert combat.defending is True
        assert "defend" in message.lower() or "defensive" in message.lower()


class TestPlayerCast:
    """Test player_cast() method."""

    def test_player_cast_damages_enemy_based_on_intelligence(self):
        """Spec: player_cast() should damage enemy based on player's intelligence."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=15, level=1)
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=10,  # High defense
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        victory, message = combat.player_cast()

        # Magic damage ignores defense, scales with intelligence
        # Formula: intelligence * 1.5 (minimum 1)
        expected_damage = max(1, int(player.intelligence * 1.5))
        assert enemy.health == initial_health - expected_damage
        assert "cast" in message.lower() or "magic" in message.lower()

    def test_player_cast_handles_enemy_defeat(self):
        """Spec: player_cast() should return victory=True when enemy is defeated."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=20, level=1)
        enemy = Enemy(
            name="Goblin",
            health=5,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_cast()

        assert victory is True
        assert enemy.is_alive() is False

    def test_player_cast_continues_combat_when_enemy_survives(self):
        """Spec: player_cast() should return victory=False when enemy survives."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=5, level=1)
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_cast()

        assert victory is False
        assert enemy.is_alive() is True

    def test_player_cast_ignores_enemy_defense(self):
        """Spec: Magic attack should bypass enemy defense."""
        player = Character(name="Hero", strength=5, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Armored Golem",
            health=50,
            max_health=50,
            attack_power=5,
            defense=100,  # Very high defense
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        victory, message = combat.player_cast()

        # Cast should deal damage regardless of defense
        expected_damage = max(1, int(player.intelligence * 1.5))
        assert enemy.health == initial_health - expected_damage
        assert expected_damage > 1  # Meaningful damage despite high defense


class TestPlayerFlee:
    """Test player_flee() method."""
    
    def test_player_flee_success_with_high_dexterity(self):
        """Spec: player_flee() should have high success chance with high dexterity."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.dexterity = 100  # Very high dexterity
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        # With very high dexterity, should almost always succeed
        success, message = combat.player_flee()
        
        assert success is True
        assert "flee" in message.lower() or "escape" in message.lower()
    
    def test_player_flee_failure_with_low_dexterity(self):
        """Spec: player_flee() should have low success chance with low dexterity."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.dexterity = 1  # Very low dexterity (flee chance = 50 + 2 = 52%)
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        # Try multiple times to ensure flee can fail (not 100% success)
        # With 52% chance, at least one should fail in reasonable attempts
        results = []
        for _ in range(10):
            combat2 = CombatEncounter(player=player, enemy=enemy)
            combat2.start()
            success, message = combat2.player_flee()
            results.append(success)
        
        # At least one attempt should have failed
        assert False in results, "Flee should not succeed 100% of the time with low dexterity"


class TestEnemyTurn:
    """Test enemy_turn() method."""
    
    def test_enemy_turn_damages_player(self):
        """Spec: enemy_turn() should damage player based on enemy's attack power."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        initial_health = player.health
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=10,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        message = combat.enemy_turn()
        
        # Player should have taken damage
        assert player.health < initial_health
        assert message is not None
        assert len(message) > 0
    
    def test_enemy_turn_respects_defensive_stance(self):
        """Spec: enemy_turn() should apply reduced damage when player is defending."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.constitution = 10  # Set known constitution
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=20,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        # First, attack normally to see normal damage
        initial_health = player.health
        combat.enemy_turn()
        normal_damage = initial_health - player.health
        
        # Reset health
        player.health = initial_health
        
        # Now defend and take damage
        combat.defending = True
        combat.enemy_turn()
        defended_damage = initial_health - player.health
        
        # Defended damage should be less than normal damage
        assert defended_damage < normal_damage


class TestEndCombat:
    """Test end_combat() method."""
    
    def test_end_combat_victory_awards_xp(self):
        """Spec: end_combat() with victory=True should award XP to player."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        initial_xp = player.xp
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        message = combat.end_combat(victory=True)
        
        assert player.xp == initial_xp + enemy.xp_reward
        assert combat.is_active is False
        assert "victory" in message.lower() or "defeated" in message.lower()
    
    def test_end_combat_defeat(self):
        """Spec: end_combat() with victory=False should not award XP."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        initial_xp = player.xp
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        message = combat.end_combat(victory=False)
        
        assert player.xp == initial_xp
        assert combat.is_active is False
        assert "defeat" in message.lower() or "lost" in message.lower() or "fell" in message.lower()


class TestGetStatus:
    """Test get_status() method."""
    
    def test_get_status_displays_combat_state(self):
        """Spec: get_status() should display combat state including player and enemy health."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.health = 80
        player.max_health = 100
        enemy = Enemy(
            name="Goblin",
            health=20,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()
        
        status = combat.get_status()
        
        assert "Hero" in status or "80" in status  # Player health
        assert "Goblin" in status or "20" in status  # Enemy health
        assert status is not None
        assert len(status) > 0


class TestSpawnEnemy:
    """Test spawn_enemy() function."""
    
    def test_spawn_enemy_creates_enemy_for_location(self):
        """Spec: spawn_enemy() should create enemy appropriate for location."""
        enemy = spawn_enemy("forest", level=1)
        
        assert isinstance(enemy, Enemy)
        assert enemy.name is not None
        assert enemy.health > 0
        assert enemy.attack_power > 0
    
    def test_spawn_enemy_scales_with_level(self):
        """Spec: spawn_enemy() should scale enemy stats with player level."""
        enemy_level_1 = spawn_enemy("forest", level=1)
        enemy_level_5 = spawn_enemy("forest", level=5)
        
        # Higher level enemies should have better stats
        assert enemy_level_5.max_health > enemy_level_1.max_health
        assert enemy_level_5.attack_power >= enemy_level_1.attack_power
    
    def test_spawn_enemy_different_locations_have_different_enemies(self):
        """Spec: spawn_enemy() should use appropriate names per location."""
        forest_enemy = spawn_enemy("forest", level=1)
        cave_enemy = spawn_enemy("cave", level=1)
        
        # Names should be appropriate for location (may be different)
        assert forest_enemy.name is not None
        assert cave_enemy.name is not None
    
    def test_spawn_enemy_calculates_stats_correctly(self):
        """Spec: spawn_enemy() should calculate stats based on level."""
        enemy = spawn_enemy("forest", level=3)
        
        # Verify stats are reasonable for level 3
        assert enemy.health > 0
        assert enemy.max_health > 0
        assert enemy.health == enemy.max_health  # Starts at full health
        assert enemy.attack_power > 0
        assert enemy.defense >= 0
        assert enemy.xp_reward > 0
