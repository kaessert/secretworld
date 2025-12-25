"""Tests for Enemy model."""

import pytest
from cli_rpg.models.enemy import Enemy


class TestEnemyCreation:
    """Test enemy creation with valid attributes."""
    
    def test_create_enemy_with_valid_attributes(self):
        """Spec: Enemy class should be created with name, health, max_health, attack_power, defense, xp_reward."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        assert enemy.name == "Goblin"
        assert enemy.health == 30
        assert enemy.max_health == 30
        assert enemy.attack_power == 5
        assert enemy.defense == 2
        assert enemy.xp_reward == 25


class TestEnemyValidation:
    """Test enemy validation (negative health, invalid stats)."""
    
    def test_enemy_rejects_negative_health(self):
        """Spec: Enemy should validate that health cannot be negative."""
        with pytest.raises(ValueError, match="health cannot be negative"):
            Enemy(
                name="Goblin",
                health=-10,
                max_health=30,
                attack_power=5,
                defense=2,
                xp_reward=25
            )
    
    def test_enemy_rejects_negative_max_health(self):
        """Spec: Enemy should validate that max_health cannot be negative."""
        with pytest.raises(ValueError, match="max_health must be positive"):
            Enemy(
                name="Goblin",
                health=30,
                max_health=-30,
                attack_power=5,
                defense=2,
                xp_reward=25
            )
    
    def test_enemy_rejects_health_exceeding_max(self):
        """Spec: Enemy should validate that health cannot exceed max_health."""
        with pytest.raises(ValueError, match="health cannot exceed max_health"):
            Enemy(
                name="Goblin",
                health=50,
                max_health=30,
                attack_power=5,
                defense=2,
                xp_reward=25
            )
    
    def test_enemy_rejects_negative_attack_power(self):
        """Spec: Enemy should validate that attack_power cannot be negative."""
        with pytest.raises(ValueError, match="attack_power cannot be negative"):
            Enemy(
                name="Goblin",
                health=30,
                max_health=30,
                attack_power=-5,
                defense=2,
                xp_reward=25
            )
    
    def test_enemy_rejects_negative_defense(self):
        """Spec: Enemy should validate that defense cannot be negative."""
        with pytest.raises(ValueError, match="defense cannot be negative"):
            Enemy(
                name="Goblin",
                health=30,
                max_health=30,
                attack_power=5,
                defense=-2,
                xp_reward=25
            )
    
    def test_enemy_rejects_negative_xp_reward(self):
        """Spec: Enemy should validate that xp_reward cannot be negative."""
        with pytest.raises(ValueError, match="xp_reward cannot be negative"):
            Enemy(
                name="Goblin",
                health=30,
                max_health=30,
                attack_power=5,
                defense=2,
                xp_reward=-25
            )


class TestEnemyTakeDamage:
    """Test take_damage() method."""
    
    def test_take_damage_reduces_health(self):
        """Spec: take_damage(amount) should reduce health by amount."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        enemy.take_damage(10)
        assert enemy.health == 20
    
    def test_take_damage_floors_at_zero(self):
        """Spec: take_damage() should floor health at 0 (min 0)."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        enemy.take_damage(50)
        assert enemy.health == 0
    
    def test_take_damage_accepts_zero(self):
        """Spec: take_damage(0) should not change health."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        enemy.take_damage(0)
        assert enemy.health == 30


class TestEnemyIsAlive:
    """Test is_alive() method."""
    
    def test_is_alive_returns_true_when_health_positive(self):
        """Spec: is_alive() should return True when health > 0."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        assert enemy.is_alive() is True
    
    def test_is_alive_returns_false_when_health_zero(self):
        """Spec: is_alive() should return False when health = 0."""
        enemy = Enemy(
            name="Goblin",
            health=0,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        assert enemy.is_alive() is False


class TestEnemyCalculateDamage:
    """Test calculate_damage() method."""
    
    def test_calculate_damage_returns_attack_power(self):
        """Spec: calculate_damage() should return attack_power."""
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        damage = enemy.calculate_damage()
        assert damage == 5


class TestEnemySerialization:
    """Test enemy serialization (to_dict(), from_dict())."""
    
    def test_to_dict_serializes_enemy(self):
        """Spec: to_dict() should serialize enemy to dictionary."""
        enemy = Enemy(
            name="Goblin",
            health=20,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        data = enemy.to_dict()
        assert data == {
            "name": "Goblin",
            "health": 20,
            "max_health": 30,
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 25,
            "level": 1,
            "description": "",
            "attack_flavor": "",
            "ascii_art": "",
        }
    
    def test_from_dict_deserializes_enemy(self):
        """Spec: from_dict(data) should deserialize enemy from dictionary."""
        data = {
            "name": "Orc",
            "health": 40,
            "max_health": 50,
            "attack_power": 8,
            "defense": 3,
            "xp_reward": 50
        }
        enemy = Enemy.from_dict(data)
        assert enemy.name == "Orc"
        assert enemy.health == 40
        assert enemy.max_health == 50
        assert enemy.attack_power == 8
        assert enemy.defense == 3
        assert enemy.xp_reward == 50
    
    def test_serialization_roundtrip(self):
        """Spec: Enemy should survive serialization roundtrip unchanged."""
        original = Enemy(
            name="Dragon",
            health=100,
            max_health=150,
            attack_power=20,
            defense=10,
            xp_reward=500
        )
        data = original.to_dict()
        restored = Enemy.from_dict(data)
        
        assert restored.name == original.name
        assert restored.health == original.health
        assert restored.max_health == original.max_health
        assert restored.attack_power == original.attack_power
        assert restored.defense == original.defense
        assert restored.xp_reward == original.xp_reward
