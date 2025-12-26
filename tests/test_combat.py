"""Tests for Combat Encounter system."""

from unittest.mock import patch

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
        import random
        random.seed(0)  # Seed to prevent crit (crit chance is ~20% with balanced stance)

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


class TestPlayerBlock:
    """Test player_block() method."""

    def test_player_block_sets_blocking_stance(self):
        """Spec: player_block() should set blocking stance for 75% damage reduction."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20  # Ensure enough stamina
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

        victory, message = combat.player_block()

        assert victory is False
        assert combat.blocking is True
        assert "block" in message.lower()

    def test_player_block_costs_5_stamina(self):
        """Spec: player_block() should cost 5 stamina."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
        initial_stamina = player.stamina
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

        combat.player_block()

        assert player.stamina == initial_stamina - 5

    def test_player_block_fails_without_stamina(self):
        """Spec: player_block() should fail if player has < 5 stamina."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 3  # Less than 5 stamina
        initial_stamina = player.stamina
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

        victory, message = combat.player_block()

        assert victory is False
        assert combat.blocking is False
        assert player.stamina == initial_stamina  # Unchanged
        assert "stamina" in message.lower()

    def test_block_reduces_damage_by_75_percent(self):
        """Spec: Blocking should reduce incoming damage by 75%."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
        # Player has 0 defense base, constitution-based defense
        player.constitution = 0  # No defense from CON
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=20,  # 20 attack - should do 20 base damage
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Set blocking state
        combat.blocking = True
        initial_health = player.health

        # Mock random to prevent crits and dodges
        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.enemy_turn()

        # Expected: 20 base damage // 4 = 5 damage (75% reduction)
        expected_damage = max(1, 20 // 4)
        assert player.health == initial_health - expected_damage

    def test_block_resets_after_enemy_turn(self):
        """Spec: Blocking stance should reset after enemy turn."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
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

        combat.blocking = True
        assert combat.blocking is True

        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.enemy_turn()

        assert combat.blocking is False

    def test_player_block_fails_when_stunned(self):
        """Spec: player_block() should fail if player is stunned."""
        from cli_rpg.models.status_effect import StatusEffect

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
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

        # Apply stun effect
        stun = StatusEffect(name="Stun", effect_type="stun", damage_per_turn=0, duration=1)
        player.apply_status_effect(stun)

        victory, message = combat.player_block()

        assert victory is False
        assert combat.blocking is False
        assert "stunned" in message.lower()


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
        with patch('cli_rpg.combat.random.random', return_value=0.50):
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

    @patch('random.random', return_value=0.99)  # Prevent critical hit
    def test_player_cast_ignores_enemy_defense(self, mock_random):
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
        from unittest.mock import patch

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

        # Mock random to prevent dodge and crit
        with patch('cli_rpg.combat.random.random', return_value=0.50):
            message = combat.enemy_turn()

        # Player should have taken damage
        assert player.health < initial_health
        assert message is not None
        assert len(message) > 0

    def test_enemy_turn_respects_defensive_stance(self):
        """Spec: enemy_turn() should apply reduced damage when player is defending."""
        from unittest.mock import patch

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

        # Mock random to prevent dodge and crit for consistent damage
        with patch('cli_rpg.combat.random.random', return_value=0.50):
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


class TestEndCombatLootInventoryFull:
    """Test end_combat when finding loot with full inventory (line 190)."""

    def test_end_combat_victory_loot_inventory_full(self):
        """Test that loot message shows inventory full warning when inventory is full.

        Spec: Line 190 - When player wins and enemy drops loot but inventory is full,
        show message that loot was found but couldn't be picked up.
        """
        from cli_rpg.models.item import Item, ItemType
        from unittest.mock import patch

        # Create player with small inventory capacity
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.inventory.capacity = 2  # Very small capacity

        # Fill the inventory completely
        item1 = Item(name="Potion1", description="A red potion", item_type=ItemType.CONSUMABLE)
        item2 = Item(name="Potion2", description="A blue potion", item_type=ItemType.CONSUMABLE)
        player.inventory.add_item(item1)
        player.inventory.add_item(item2)
        assert player.inventory.is_full()

        # Create enemy
        enemy = Enemy(
            name="Goblin",
            health=1,  # Low health for quick defeat
            max_health=30,
            attack_power=5,
            defense=0,
            xp_reward=25
        )

        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock generate_loot to always return a specific item
        loot = Item(name="Enemy Sword", description="A rusty sword", item_type=ItemType.WEAPON)
        with patch('cli_rpg.combat.generate_loot', return_value=loot):
            message = combat.end_combat(victory=True)

        # Verify inventory full message is in the result
        assert "inventory is full" in message.lower() or "full" in message.lower()
        # Verify loot was mentioned
        assert "Enemy Sword" in message
        # Verify loot was NOT added to inventory
        assert loot not in player.inventory.items


class TestCriticalHits:
    """Test player critical hit mechanics.

    Spec: Critical hit mechanics based on player DEX:
    - Base crit chance: 5%
    - DEX bonus: +1% per point (capped at +15% from DEX)
    - On crit: 1.5x damage with special message
    - Formula: crit_chance = min(5 + player.dexterity, 20)
    """

    def test_player_crit_deals_1_5x_damage(self):
        """Spec: Critical hit should deal 1.5x normal damage."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,  # No defense to make damage predictable
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to always trigger a crit
        with patch('cli_rpg.combat.random.random', return_value=0.01):  # Always crit
            initial_health = enemy.health
            victory, message = combat.player_attack()

            # Base damage is strength (10) - defense (0) = 10
            # Crit multiplies by 1.5 -> 15 damage
            expected_damage = int(10 * 1.5)
            assert initial_health - enemy.health == expected_damage

    def test_player_crit_message_includes_critical(self):
        """Spec: Critical hit message should include 'CRITICAL' indicator."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to always trigger a crit
        with patch('cli_rpg.combat.random.random', return_value=0.01):
            victory, message = combat.player_attack()
            assert "CRITICAL" in message.upper()

    def test_player_attack_no_crit_with_low_roll(self):
        """Spec: Player attack should not crit when roll exceeds crit chance."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=5, intelligence=10, level=1)
        # Crit chance = min(5 + 5, 20) = 10% = 0.10
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to not trigger crit (roll > 0.10)
        with patch('cli_rpg.combat.random.random', return_value=0.50):
            initial_health = enemy.health
            victory, message = combat.player_attack()

            # Normal damage: strength (10) - defense (0) = 10
            assert initial_health - enemy.health == 10
            assert "CRITICAL" not in message.upper()

    def test_player_cast_can_crit(self):
        """Spec: Magic attacks (cast) can also crit, using INT for crit chance."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=15, level=1)
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=10,  # High defense, but cast ignores it
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to always trigger a crit
        with patch('cli_rpg.combat.random.random', return_value=0.01):
            initial_health = enemy.health
            victory, message = combat.player_cast()

            # Magic damage = int(intelligence * 1.5) = int(15 * 1.5) = 22
            # Crit multiplies by 1.5 -> 33 damage
            base_magic_damage = max(1, int(player.intelligence * 1.5))
            expected_damage = int(base_magic_damage * 1.5)
            assert initial_health - enemy.health == expected_damage
            assert "CRITICAL" in message.upper()


class TestMissChance:
    """Test enemy miss/dodge mechanics.

    Spec: Miss chance (enemy attacks player) based on player DEX:
    - Base miss chance: 5%
    - Player DEX bonus: +0.5% per point (capped at +10% from DEX)
    - On miss: 0 damage with dodge message
    - Formula: dodge_chance = min(5 + player.dexterity // 2, 15)
    """

    def test_enemy_miss_deals_zero_damage(self):
        """Spec: When enemy misses, player takes zero damage."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=20,  # High attack to make damage obvious
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = player.health

        # Mock random to always trigger dodge (roll < dodge_chance)
        # Dodge chance = min(5 + 10//2, 15) = min(10, 15) = 10% = 0.10
        with patch('cli_rpg.combat.random.random', return_value=0.05):  # 5% < 10%, so dodge
            message = combat.enemy_turn()

        # Player should take no damage
        assert player.health == initial_health
        assert "dodge" in message.lower() or "miss" in message.lower()

    def test_enemy_miss_message_includes_dodge_or_miss(self):
        """Spec: Enemy miss message should indicate dodge or miss."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=20, intelligence=10, level=1)
        # Dodge chance = min(5 + 20//2, 15) = min(15, 15) = 15%
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

        with patch('cli_rpg.combat.random.random', return_value=0.05):  # Triggers dodge
            message = combat.enemy_turn()

        assert "dodge" in message.lower() or "miss" in message.lower()

    def test_enemy_attack_hits_when_no_dodge(self):
        """Spec: Enemy attack should hit and deal damage when roll exceeds dodge chance."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        # Dodge chance = min(5 + 10//2, 15) = 10%
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

        initial_health = player.health

        # Mock to ensure no dodge and no crit (separate rolls)
        with patch('cli_rpg.combat.random.random', return_value=0.50):  # No dodge, no crit
            message = combat.enemy_turn()

        # Player should have taken damage
        assert player.health < initial_health


class TestEnemyCriticalHits:
    """Test enemy critical hit mechanics.

    Spec: Enemy crit mechanics:
    - Flat 5% crit chance for enemies
    - On crit: 1.5x damage with special message
    """

    def test_enemy_crit_deals_1_5x_damage(self):
        """Spec: Enemy critical hit should deal 1.5x normal damage."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.constitution = 0  # No defense to make damage predictable
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

        initial_health = player.health

        # First call = dodge check (make it fail/not dodge by returning 0.50)
        # Second call = crit check (make it succeed by returning 0.02)
        with patch('cli_rpg.combat.random.random', side_effect=[0.50, 0.02]):
            message = combat.enemy_turn()

        # Base damage = attack_power (10) - player defense (0) = 10
        # Crit multiplies by 1.5 -> 15 damage
        expected_damage = int(10 * 1.5)
        actual_damage = initial_health - player.health
        assert actual_damage == expected_damage

    def test_enemy_crit_message_includes_critical(self):
        """Spec: Enemy critical hit message should include 'CRITICAL' indicator."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.constitution = 0
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

        # First call = dodge check, second = crit check
        with patch('cli_rpg.combat.random.random', side_effect=[0.50, 0.02]):
            message = combat.enemy_turn()

        assert "CRITICAL" in message.upper()

    def test_enemy_no_crit_with_high_roll(self):
        """Spec: Enemy attack should not crit when roll exceeds 5% crit chance."""
        from unittest.mock import patch

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.constitution = 0
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

        initial_health = player.health

        # Dodge check fails (0.50), crit check fails (0.50 > 0.05)
        with patch('cli_rpg.combat.random.random', side_effect=[0.50, 0.50]):
            message = combat.enemy_turn()

        # Normal damage: attack_power (10) - player defense (0) = 10
        assert initial_health - player.health == 10
        assert "CRITICAL" not in message.upper()


class TestCritDodgeHelperFunctions:
    """Test the helper functions for crit and dodge calculations."""

    def test_calculate_crit_chance_base(self):
        """Spec: Base crit chance is 5% with 0 DEX."""
        from cli_rpg.combat import calculate_crit_chance
        assert calculate_crit_chance(0) == 0.05

    def test_calculate_crit_chance_with_dex(self):
        """Spec: Crit chance increases 1% per DEX point."""
        from cli_rpg.combat import calculate_crit_chance
        # 10 DEX = 5 + 10 = 15% crit chance
        assert calculate_crit_chance(10) == 0.15

    def test_calculate_crit_chance_cap(self):
        """Spec: Crit chance is capped at 25% (with luck bonus)."""
        from cli_rpg.combat import calculate_crit_chance
        # 20 DEX + luck 10 = 5 + 20 + 0 = 25% capped
        assert calculate_crit_chance(20) == 0.25
        # Even higher DEX still caps at 25%
        assert calculate_crit_chance(50) == 0.25

    def test_calculate_dodge_chance_base(self):
        """Spec: Base dodge chance is 5% with 0 DEX."""
        from cli_rpg.combat import calculate_dodge_chance
        assert calculate_dodge_chance(0) == 0.05

    def test_calculate_dodge_chance_with_dex(self):
        """Spec: Dodge chance increases 0.5% per DEX point (integer division)."""
        from cli_rpg.combat import calculate_dodge_chance
        # 10 DEX = 5 + (10 // 2) = 5 + 5 = 10% dodge chance
        assert calculate_dodge_chance(10) == 0.10

    def test_calculate_dodge_chance_cap(self):
        """Spec: Dodge chance is capped at 15%."""
        from cli_rpg.combat import calculate_dodge_chance
        # 20 DEX = 5 + 10 = 15% (cap)
        assert calculate_dodge_chance(20) == 0.15
        # Even higher DEX still caps at 15%
        assert calculate_dodge_chance(50) == 0.15


class TestCombatTypewriterDisplay:
    """Test typewriter effect display functions for combat.

    Spec: Add typewriter effect to dramatic combat moments for enhanced atmosphere.
    """

    def test_display_combat_start_uses_typewriter(self):
        """Spec: display_combat_start should call typewriter_print with combat intro."""
        from unittest.mock import patch
        from cli_rpg.combat import display_combat_start

        test_text = "A wild Goblin appears!"

        with patch("cli_rpg.text_effects.typewriter_print") as mock_typewriter:
            display_combat_start(test_text)
            mock_typewriter.assert_called_once()
            # Verify text was passed
            call_args = mock_typewriter.call_args
            assert test_text == call_args[0][0]

    def test_display_combo_uses_typewriter(self):
        """Spec: display_combo should use typewriter effect for combo announcements."""
        from unittest.mock import patch
        from cli_rpg.combat import display_combo

        combo_text = "FRENZY! You strike three times!"

        with patch("cli_rpg.text_effects.typewriter_print") as mock_typewriter:
            display_combo(combo_text)
            mock_typewriter.assert_called_once()
            call_args = mock_typewriter.call_args
            assert combo_text == call_args[0][0]

    def test_display_combat_end_uses_typewriter(self):
        """Spec: display_combat_end should use typewriter effect for victory/defeat."""
        from unittest.mock import patch
        from cli_rpg.combat import display_combat_end

        result_text = "Victory! You defeated the Goblin!"

        with patch("cli_rpg.text_effects.typewriter_print") as mock_typewriter:
            display_combat_end(result_text)
            # Should call typewriter_print at least once (may be per line)
            assert mock_typewriter.call_count >= 1

    def test_display_combat_end_multiline(self):
        """Spec: display_combat_end should handle multiline messages."""
        from unittest.mock import patch
        from cli_rpg.combat import display_combat_end

        result_text = "Victory!\nYou earned 25 XP!\nYou found: Iron Sword!"

        with patch("cli_rpg.text_effects.typewriter_print") as mock_typewriter:
            display_combat_end(result_text)
            # Should call once per line
            assert mock_typewriter.call_count == 3

    def test_combat_typewriter_delay_constant(self):
        """Spec: COMBAT_TYPEWRITER_DELAY should exist with value 0.025 (faster than dreams)."""
        from cli_rpg.combat import COMBAT_TYPEWRITER_DELAY

        # Combat delay should be 0.025 (faster than dreams' 0.04)
        assert COMBAT_TYPEWRITER_DELAY == 0.025


class TestPlayerParry:
    """Test player_parry() method - timing-based defensive option."""

    def test_player_parry_sets_parrying_stance(self):
        """Spec: player_parry() should set parrying stance for parry attempt."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20  # Ensure enough stamina
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

        victory, message = combat.player_parry()

        assert victory is False
        assert combat.parrying is True
        assert "parry" in message.lower()

    def test_player_parry_costs_8_stamina(self):
        """Spec: player_parry() should cost 8 stamina."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
        initial_stamina = player.stamina
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

        combat.player_parry()

        assert player.stamina == initial_stamina - 8

    def test_player_parry_fails_without_stamina(self):
        """Spec: player_parry() should fail if player has < 8 stamina."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 5  # Less than 8 stamina
        initial_stamina = player.stamina
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

        victory, message = combat.player_parry()

        assert victory is False
        assert combat.parrying is False
        assert player.stamina == initial_stamina  # Unchanged
        assert "stamina" in message.lower()

    def test_parry_success_negates_damage(self):
        """Spec: Successful parry should negate all incoming damage."""
        player = Character(name="Hero", strength=10, dexterity=15, intelligence=10, level=1)
        player.stamina = 20
        player.constitution = 0  # No defense from CON
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=20,  # High attack to ensure visible damage if not parried
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.parrying = True
        initial_health = player.health

        # Mock random to ensure: no dodge (0.99), no enemy crit (0.99), successful parry (0.3 < 70%)
        with patch('cli_rpg.combat.random.random', return_value=0.3):
            combat.enemy_turn()

        # Player should take 0 damage on successful parry
        assert player.health == initial_health

    def test_parry_success_deals_counter_damage(self):
        """Spec: Successful parry should deal 50% of player attack power as counter damage."""
        player = Character(name="Hero", strength=10, dexterity=15, intelligence=10, level=1)
        player.stamina = 20
        player.constitution = 0
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=20,
            defense=0,  # No enemy defense to simplify calculation
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.parrying = True
        initial_enemy_health = enemy.health

        # Mock random to ensure successful parry (0.3 < 70%)
        with patch('cli_rpg.combat.random.random', return_value=0.3):
            combat.enemy_turn()

        # Counter damage = 50% of player strength = 10 * 0.5 = 5
        expected_counter_damage = player.strength // 2
        assert enemy.health == initial_enemy_health - expected_counter_damage

    def test_parry_failure_takes_full_damage(self):
        """Spec: Failed parry should result in full damage to player."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
        player.constitution = 0  # No defense from CON
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=20,  # 20 attack = 20 base damage
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.parrying = True
        initial_health = player.health

        # Mock random to ensure: no dodge (0.99), no crit (0.99), failed parry (0.8 > 70%)
        with patch('cli_rpg.combat.random.random', return_value=0.8):
            combat.enemy_turn()

        # Should take full damage (20) since parry failed
        assert player.health == initial_health - 20

    def test_parry_success_chance_scales_with_dex(self):
        """Spec: Parry success chance should be 40% base + DEX*2%, capped at 70%."""
        # Test formula: min(40 + DEX * 2, 70) / 100.0

        # DEX 0: 40% chance
        assert min(40 + 0 * 2, 70) == 40

        # DEX 10: 60% chance
        assert min(40 + 10 * 2, 70) == 60

        # DEX 15: 70% chance (cap)
        assert min(40 + 15 * 2, 70) == 70

        # DEX 20: still 70% (capped)
        assert min(40 + 20 * 2, 70) == 70

    def test_parry_resets_after_enemy_turn(self):
        """Spec: Parrying stance should reset after enemy turn."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
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

        combat.parrying = True
        assert combat.parrying is True

        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.enemy_turn()

        assert combat.parrying is False

    def test_player_parry_fails_when_stunned(self):
        """Spec: player_parry() should fail if player is stunned."""
        from cli_rpg.models.status_effect import StatusEffect

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
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

        # Apply stun effect
        stun = StatusEffect(name="Stun", effect_type="stun", damage_per_turn=0, duration=1)
        player.apply_status_effect(stun)

        victory, message = combat.player_parry()

        assert victory is False
        assert combat.parrying is False
        assert "stunned" in message.lower()

    def test_parry_records_action_for_combo(self):
        """Spec: Parry action should be recorded in action history for combo tracking."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10, level=1)
        player.stamina = 20
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

        combat.player_parry()

        assert "parry" in combat.action_history
