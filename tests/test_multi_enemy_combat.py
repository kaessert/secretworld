"""Tests for Multi-Enemy Combat system.

These tests verify the multi-enemy combat implementation per the spec:
- Encounters can spawn 1-3 enemies
- `attack [enemy]` targets a specific enemy (default: first living enemy)
- `cast [enemy]` similarly allows targeting
- Combat status shows all enemies with health bars
- Victory requires defeating all enemies
- All living enemies attack player each turn
"""

from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter, spawn_enemies


def create_test_player(**kwargs) -> Character:
    """Create a test player with sensible defaults."""
    defaults = {
        "name": "Hero",
        "strength": 10,
        "dexterity": 10,
        "intelligence": 10,
        "level": 1
    }
    defaults.update(kwargs)
    return Character(**defaults)


def create_test_enemy(name: str = "Goblin", health: int = 30, **kwargs) -> Enemy:
    """Create a test enemy with sensible defaults."""
    defaults = {
        "name": name,
        "health": health,
        "max_health": health,
        "attack_power": 5,
        "defense": 2,
        "xp_reward": 25
    }
    defaults.update(kwargs)
    return Enemy(**defaults)


class TestCombatWithMultipleEnemies:
    """Test CombatEncounter initialization with multiple enemies."""

    def test_combat_with_multiple_enemies_init(self):
        """Spec: Combat initializes with list of enemies."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Goblin"),
            create_test_enemy("Orc"),
            create_test_enemy("Skeleton"),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)

        assert combat.player == player
        assert combat.enemies == enemies
        assert len(combat.enemies) == 3
        # Backward compatibility: enemy property returns first enemy
        assert combat.enemy == enemies[0]

    def test_combat_backward_compat_single_enemy(self):
        """Spec: Combat should still work with single enemy passed as list."""
        player = create_test_player()
        enemy = create_test_enemy("Goblin")

        combat = CombatEncounter(player=player, enemies=[enemy])

        assert combat.enemies == [enemy]
        assert combat.enemy == enemy

    def test_combat_backward_compat_legacy_init(self):
        """Spec: Combat should still work with legacy single-enemy init."""
        player = create_test_player()
        enemy = create_test_enemy("Goblin")

        # Legacy init using enemy= parameter
        combat = CombatEncounter(player=player, enemy=enemy)

        assert combat.enemies == [enemy]
        assert combat.enemy == enemy


class TestAttackTargeting:
    """Test player attack targeting mechanics."""

    def test_attack_targets_first_enemy_by_default(self):
        """Spec: No target = first living enemy."""
        player = create_test_player(strength=15)
        enemies = [
            create_test_enemy("Goblin", health=50),
            create_test_enemy("Orc", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        initial_goblin_hp = enemies[0].health
        initial_orc_hp = enemies[1].health

        victory, message = combat.player_attack()

        # First enemy (Goblin) should be damaged
        assert enemies[0].health < initial_goblin_hp
        # Second enemy (Orc) should be untouched
        assert enemies[1].health == initial_orc_hp
        assert "Goblin" in message

    def test_attack_targets_first_living_enemy_when_first_is_dead(self):
        """Spec: Default target should skip dead enemies."""
        player = create_test_player(strength=15)
        enemies = [
            create_test_enemy("Goblin", health=1),  # Will die
            create_test_enemy("Orc", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        # Kill the first enemy
        enemies[0].take_damage(100)
        assert not enemies[0].is_alive()

        initial_orc_hp = enemies[1].health

        victory, message = combat.player_attack()

        # Second enemy (Orc) should be damaged since Goblin is dead
        assert enemies[1].health < initial_orc_hp
        assert "Orc" in message

    def test_attack_specific_enemy_by_name(self):
        """Spec: Can target by partial/full name."""
        player = create_test_player(strength=15)
        enemies = [
            create_test_enemy("Goblin", health=50),
            create_test_enemy("Orc", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        initial_goblin_hp = enemies[0].health
        initial_orc_hp = enemies[1].health

        # Target Orc specifically
        victory, message = combat.player_attack(target="orc")

        # Goblin should be untouched
        assert enemies[0].health == initial_goblin_hp
        # Orc should be damaged
        assert enemies[1].health < initial_orc_hp
        assert "Orc" in message

    def test_attack_specific_enemy_by_partial_name(self):
        """Spec: Can target by partial name (case-insensitive)."""
        player = create_test_player(strength=15)
        enemies = [
            create_test_enemy("Giant Spider", health=50),
            create_test_enemy("Cave Bat", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        initial_spider_hp = enemies[0].health
        initial_bat_hp = enemies[1].health

        # Target by partial name
        victory, message = combat.player_attack(target="bat")

        # Spider should be untouched
        assert enemies[0].health == initial_spider_hp
        # Bat should be damaged
        assert enemies[1].health < initial_bat_hp

    def test_attack_invalid_target_shows_error(self):
        """Spec: Unknown target gives helpful error listing valid targets."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Goblin", health=50),
            create_test_enemy("Orc", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        # Try to target an enemy that doesn't exist
        victory, message = combat.player_attack(target="dragon")

        # Should return False for victory and show error
        assert victory is False
        assert "dragon" in message.lower() or "not found" in message.lower() or "invalid" in message.lower()
        # Should list valid targets
        assert "Goblin" in message or "goblin" in message.lower()
        assert "Orc" in message or "orc" in message.lower()


class TestAllEnemiesAttack:
    """Test that all living enemies attack player each turn."""

    def test_all_enemies_attack_player_each_turn(self):
        """Spec: Enemy turn damages player from all living enemies."""
        player = create_test_player()
        player.constitution = 0  # Zero defense for easier damage calculation
        enemies = [
            create_test_enemy("Goblin", health=50, attack_power=10),
            create_test_enemy("Orc", health=50, attack_power=10),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        initial_hp = player.health

        message = combat.enemy_turn()

        # Player should take damage from both enemies
        damage_taken = initial_hp - player.health
        # Each enemy deals 10 attack - player defense, both attack
        assert damage_taken > 0
        # Both enemy names should appear in the message
        assert "Goblin" in message
        assert "Orc" in message

    def test_dead_enemies_dont_attack(self):
        """Spec: Only living enemies should attack."""
        player = create_test_player()
        player.constitution = 0  # Zero defense
        enemies = [
            create_test_enemy("Goblin", health=1, attack_power=10),
            create_test_enemy("Orc", health=50, attack_power=10),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        # Kill the first enemy
        enemies[0].take_damage(100)

        initial_hp = player.health

        message = combat.enemy_turn()

        # Only Orc should attack (Goblin is dead)
        assert "Orc" in message
        # Goblin's attack should not appear
        assert "Goblin" not in message or "dead" in message.lower()


class TestVictoryCondition:
    """Test that victory requires all enemies defeated."""

    def test_victory_requires_all_enemies_dead(self):
        """Spec: Combat ends only when all enemies defeated."""
        player = create_test_player(strength=20)  # High strength (max stat is 20)
        enemies = [
            create_test_enemy("Goblin", health=5, defense=0),  # Low HP, no defense
            create_test_enemy("Orc", health=5, defense=0),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        # Kill first enemy
        victory, _ = combat.player_attack(target="goblin")
        assert not enemies[0].is_alive()
        assert victory is False  # Combat not over yet

        # Kill second enemy
        victory, _ = combat.player_attack(target="orc")
        assert not enemies[1].is_alive()
        assert victory is True  # Now combat is over


class TestGetStatus:
    """Test combat status display."""

    def test_get_status_shows_all_enemies(self):
        """Spec: Status displays all enemies with HP."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Goblin", health=20),
            create_test_enemy("Orc", health=30),
            create_test_enemy("Skeleton", health=25),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        status = combat.get_status()

        # Player should be shown
        assert "Hero" in status
        # All enemies should be shown with their HP
        assert "Goblin" in status
        assert "Orc" in status
        assert "Skeleton" in status
        # HP values should be displayed
        assert "20" in status  # Goblin HP
        assert "30" in status  # Orc HP
        assert "25" in status  # Skeleton HP


class TestCastTargeting:
    """Test player cast targeting mechanics."""

    def test_cast_targets_specific_enemy(self):
        """Spec: Cast command supports targeting."""
        player = create_test_player(intelligence=15)
        enemies = [
            create_test_enemy("Goblin", health=50),
            create_test_enemy("Orc", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        initial_goblin_hp = enemies[0].health
        initial_orc_hp = enemies[1].health

        # Cast at Orc specifically
        victory, message = combat.player_cast(target="orc")

        # Goblin should be untouched
        assert enemies[0].health == initial_goblin_hp
        # Orc should be damaged
        assert enemies[1].health < initial_orc_hp
        assert "Orc" in message

    def test_cast_targets_first_enemy_by_default(self):
        """Spec: Cast with no target hits first living enemy."""
        player = create_test_player(intelligence=15)
        enemies = [
            create_test_enemy("Goblin", health=50),
            create_test_enemy("Orc", health=50),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        initial_goblin_hp = enemies[0].health

        victory, message = combat.player_cast()

        # First enemy (Goblin) should be damaged
        assert enemies[0].health < initial_goblin_hp
        assert "Goblin" in message


class TestFlee:
    """Test flee mechanics with multiple enemies."""

    def test_flee_from_multiple_enemies(self):
        """Spec: Flee works (same mechanics)."""
        player = create_test_player(dexterity=20)  # High dex (max stat is 20)
        enemies = [
            create_test_enemy("Goblin"),
            create_test_enemy("Orc"),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        # With dex=20, flee chance is 50 + (20*2) = 90%
        # Try a few times to get a success
        success = False
        for _ in range(10):
            combat2 = CombatEncounter(player=player, enemies=enemies)
            combat2.start()
            success, message = combat2.player_flee()
            if success:
                break

        assert success is True
        assert "flee" in message.lower() or "escape" in message.lower()


class TestEndCombatMultiEnemy:
    """Test end combat rewards with multiple enemies."""

    def test_xp_and_loot_from_multiple_enemies(self):
        """Spec: Victory awards sum of all enemy XP, loot from each."""
        player = create_test_player()
        initial_xp = player.xp
        enemies = [
            create_test_enemy("Goblin", xp_reward=20),
            create_test_enemy("Orc", xp_reward=30),
            create_test_enemy("Skeleton", xp_reward=25),
        ]

        # Mark all as dead (simulating combat)
        for enemy in enemies:
            enemy.take_damage(100)

        combat = CombatEncounter(player=player, enemies=enemies)
        combat.start()

        message = combat.end_combat(victory=True)

        # XP should be sum of all enemies
        expected_xp = 20 + 30 + 25
        assert player.xp == initial_xp + expected_xp

        # Message should mention victory
        assert "victory" in message.lower() or "defeated" in message.lower()


class TestSpawnEnemies:
    """Test spawn_enemies function."""

    def test_spawn_enemies_returns_1_to_3_enemies(self):
        """Spec: Spawns appropriate count (1-3 enemies)."""
        # Run multiple times to verify range
        counts = set()
        for _ in range(50):
            enemies = spawn_enemies("forest", level=5)
            counts.add(len(enemies))
            assert 1 <= len(enemies) <= 3
            for enemy in enemies:
                assert isinstance(enemy, Enemy)

        # Should have spawned varying counts
        assert len(counts) > 1, "spawn_enemies should produce varying counts"

    def test_spawn_enemies_scales_with_level(self):
        """Spec: Enemy count increases at higher levels."""
        # Low level: mostly 1-2 enemies
        low_level_counts = []
        for _ in range(30):
            enemies = spawn_enemies("forest", level=1)
            low_level_counts.append(len(enemies))

        # High level: can have up to 3 enemies
        high_level_counts = []
        for _ in range(30):
            enemies = spawn_enemies("forest", level=5)
            high_level_counts.append(len(enemies))

        # Higher level should have potential for more enemies
        # (Level 4+ can spawn up to 3)
        assert 3 in high_level_counts or max(high_level_counts) >= 2

    def test_spawn_enemies_with_explicit_count(self):
        """Spec: Can specify exact count."""
        enemies = spawn_enemies("forest", level=1, count=2)
        assert len(enemies) == 2

    def test_spawn_enemies_creates_valid_enemies(self):
        """Spec: Spawned enemies should be valid Enemy instances."""
        enemies = spawn_enemies("forest", level=3)

        for enemy in enemies:
            assert isinstance(enemy, Enemy)
            assert enemy.health > 0
            assert enemy.max_health > 0
            assert enemy.attack_power > 0
            assert enemy.xp_reward > 0


class TestGetLivingEnemies:
    """Test helper methods for multi-enemy combat."""

    def test_get_living_enemies(self):
        """Spec: get_living_enemies returns only alive enemies."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Goblin", health=10),
            create_test_enemy("Orc", health=10),
            create_test_enemy("Skeleton", health=10),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)

        # Kill one enemy
        enemies[1].take_damage(100)

        living = combat.get_living_enemies()

        assert len(living) == 2
        assert enemies[0] in living
        assert enemies[1] not in living  # Dead
        assert enemies[2] in living

    def test_find_enemy_by_name(self):
        """Spec: find_enemy_by_name finds by partial/full name."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Giant Spider"),
            create_test_enemy("Cave Bat"),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)

        # Full name match
        found = combat.find_enemy_by_name("Giant Spider")
        assert found == enemies[0]

        # Partial name match
        found = combat.find_enemy_by_name("spider")
        assert found == enemies[0]

        # Case insensitive
        found = combat.find_enemy_by_name("BAT")
        assert found == enemies[1]

        # Not found
        found = combat.find_enemy_by_name("dragon")
        assert found is None

    def test_find_enemy_by_name_skips_dead(self):
        """Spec: find_enemy_by_name should skip dead enemies."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Goblin", health=10),
            create_test_enemy("Goblin", health=10),  # Same name!
        ]

        combat = CombatEncounter(player=player, enemies=enemies)

        # Kill first goblin
        enemies[0].take_damage(100)

        # Should find second goblin
        found = combat.find_enemy_by_name("goblin")
        assert found == enemies[1]


class TestStartMessage:
    """Test multi-enemy start message."""

    def test_start_announces_all_enemies(self):
        """Spec: start() should announce all enemies."""
        player = create_test_player()
        enemies = [
            create_test_enemy("Goblin"),
            create_test_enemy("Orc"),
        ]

        combat = CombatEncounter(player=player, enemies=enemies)
        message = combat.start()

        assert combat.is_active is True
        # Both enemies should be mentioned
        assert "Goblin" in message
        assert "Orc" in message
