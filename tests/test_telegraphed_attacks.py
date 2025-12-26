"""Tests for Telegraphed Enemy Attacks system.

Spec: Bosses telegraph powerful special attacks the turn before executing them,
giving players a chance to defend/block/parry strategically.
"""

import random
from typing import List, Optional
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy, SpecialAttack
from cli_rpg.combat import CombatEncounter


def make_player(level: int = 1, **kwargs) -> Character:
    """Create a test player with sensible defaults.

    Note: constitution is derived from strength, not a direct parameter.
    Use 'strength' to indirectly control defense/constitution.
    """
    defaults = {
        "name": "TestHero",
        "strength": 10,
        "dexterity": 10,
        "intelligence": 10,
        "luck": 10,
        "perception": 10,
        "charisma": 10,
        "level": level,
    }
    defaults.update(kwargs)
    return Character(**defaults)


def make_boss(special_attacks: Optional[List[SpecialAttack]] = None, **kwargs) -> Enemy:
    """Create a test boss with sensible defaults."""
    defaults = {
        "name": "Test Boss",
        "health": 200,
        "max_health": 200,
        "attack_power": 20,
        "defense": 5,
        "xp_reward": 500,
        "level": 5,
        "is_boss": True,
    }
    defaults.update(kwargs)
    if special_attacks:
        defaults["special_attacks"] = special_attacks
    return Enemy(**defaults)


def make_normal_enemy(**kwargs) -> Enemy:
    """Create a normal (non-boss) enemy."""
    defaults = {
        "name": "Goblin",
        "health": 30,
        "max_health": 30,
        "attack_power": 5,
        "defense": 2,
        "xp_reward": 25,
        "level": 1,
        "is_boss": False,
    }
    defaults.update(kwargs)
    return Enemy(**defaults)


class TestSpecialAttackModel:
    """Test SpecialAttack dataclass and Enemy integration."""

    def test_special_attack_dataclass_creation(self):
        """Spec: SpecialAttack should have name, damage_multiplier, telegraph/hit messages."""
        attack = SpecialAttack(
            name="Crushing Blow",
            damage_multiplier=2.0,
            telegraph_message="The boss raises its fist high...",
            hit_message="brings down a CRUSHING BLOW",
        )
        assert attack.name == "Crushing Blow"
        assert attack.damage_multiplier == 2.0
        assert "raises its fist" in attack.telegraph_message
        assert "CRUSHING BLOW" in attack.hit_message

    def test_special_attack_with_effect(self):
        """Spec: SpecialAttack can have optional status effect configuration."""
        attack = SpecialAttack(
            name="Venomous Strike",
            damage_multiplier=1.5,
            telegraph_message="The boss's fangs drip with venom...",
            hit_message="sinks poisoned fangs into you",
            effect_type="poison",
            effect_damage=5,
            effect_duration=3,
            effect_chance=0.75,
        )
        assert attack.effect_type == "poison"
        assert attack.effect_damage == 5
        assert attack.effect_duration == 3
        assert attack.effect_chance == 0.75

    def test_enemy_can_have_special_attacks(self):
        """Spec: Enemy dataclass should have special_attacks list field."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="The boss raises its fist...",
                hit_message="brings down a crushing blow",
            )
        ]
        boss = make_boss(special_attacks=attacks)
        assert len(boss.special_attacks) == 1
        assert boss.special_attacks[0].name == "Crushing Blow"

    def test_enemy_telegraphed_attack_field(self):
        """Spec: Enemy should have telegraphed_attack field to track pending special."""
        boss = make_boss()
        assert boss.telegraphed_attack is None
        boss.telegraphed_attack = "Crushing Blow"
        assert boss.telegraphed_attack == "Crushing Blow"


class TestSpecialAttackSerialization:
    """Test persistence of special attacks."""

    def test_special_attack_serialization(self):
        """Spec: to_dict/from_dict should preserve special attacks."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="Raises fist...",
                hit_message="brings down crushing blow",
                effect_type="stun",
                effect_duration=1,
                effect_chance=0.75,
            )
        ]
        boss = make_boss(special_attacks=attacks, telegraphed_attack="Crushing Blow")

        # Serialize
        data = boss.to_dict()
        assert "special_attacks" in data
        assert len(data["special_attacks"]) == 1
        assert data["special_attacks"][0]["name"] == "Crushing Blow"
        assert data["telegraphed_attack"] == "Crushing Blow"

        # Deserialize
        restored = Enemy.from_dict(data)
        assert len(restored.special_attacks) == 1
        assert restored.special_attacks[0].name == "Crushing Blow"
        assert restored.special_attacks[0].damage_multiplier == 2.0
        assert restored.special_attacks[0].effect_type == "stun"
        assert restored.telegraphed_attack == "Crushing Blow"


class TestTelegraphMechanic:
    """Test telegraphing and execution of special attacks."""

    def test_boss_can_telegraph_special_attack(self):
        """Spec: Boss sets telegraphed_attack, message appears in enemy_turn output."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="The boss raises its massive fist high...",
                hit_message="brings down a CRUSHING BLOW",
            )
        ]
        player = make_player(strength=20)  # High STR for health to survive hits
        boss = make_boss(special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        # Force the boss to telegraph (mock random to always trigger)
        with patch("random.random", return_value=0.0):  # < 0.3 threshold
            # Also prevent dodge
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                result = combat.enemy_turn()

        # Boss should have telegraphed an attack
        assert boss.telegraphed_attack == "Crushing Blow"
        assert "raises its massive fist" in result

    def test_telegraphed_attack_executes_next_turn(self):
        """Spec: Special attack fires on the turn after telegraph."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="The boss raises its fist...",
                hit_message="brings down a CRUSHING BLOW",
            )
        ]
        player = make_player(strength=20)  # High STR for health to survive
        boss = make_boss(special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        # Set up telegraphed attack (simulating previous turn)
        boss.telegraphed_attack = "Crushing Blow"

        # Execute enemy turn - should execute the special attack
        with patch("random.random", return_value=0.99):  # No crit, no new telegraph
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                result = combat.enemy_turn()

        # Special attack should have executed
        assert "CRUSHING BLOW" in result
        # Telegraphed attack should be cleared
        assert boss.telegraphed_attack is None

    def test_telegraphed_attack_bonus_damage(self):
        """Spec: Special attack deals multiplied damage."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="Raises fist...",
                hit_message="brings down a CRUSHING BLOW",
            )
        ]
        player = make_player(strength=5)  # Low stats (less defense)
        boss = make_boss(attack_power=20, special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        initial_health = player.health
        boss.telegraphed_attack = "Crushing Blow"

        # Execute enemy turn with special attack
        with patch("random.random", return_value=0.99):  # No crit
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                combat.enemy_turn()

        damage_taken = initial_health - player.health
        # Normal damage would be attack_power - defense = 20 - 5 = 15
        # Special attack with 2.0x multiplier should deal ~30 damage (base * 2)
        # We're testing that special attack deals MORE than normal
        assert damage_taken >= 28  # At least 2x base damage (with some tolerance)

    def test_telegraph_cleared_after_execution(self):
        """Spec: telegraphed_attack reset to None after special attack fires."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="Raises fist...",
                hit_message="CRUSHING BLOW",
            )
        ]
        player = make_player(strength=20)  # High STR for health
        boss = make_boss(special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        boss.telegraphed_attack = "Crushing Blow"

        with patch("random.random", return_value=0.99):
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                combat.enemy_turn()

        assert boss.telegraphed_attack is None


class TestDefensiveMitigation:
    """Test that defensive actions reduce telegraphed attack damage."""

    def test_defend_reduces_telegraphed_damage(self):
        """Spec: Defending still mitigates special attack (50% reduction)."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="Raises fist...",
                hit_message="CRUSHING BLOW",
            )
        ]
        player = make_player(strength=5)  # Low stats
        boss = make_boss(attack_power=20, special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        # Take undefended special attack
        boss.telegraphed_attack = "Crushing Blow"
        with patch("random.random", return_value=0.99):
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                combat.enemy_turn()
        undefended_damage = 200 - player.health

        # Reset for defended test
        player.health = 200
        player.max_health = 200
        boss.telegraphed_attack = "Crushing Blow"

        # Defend and take special attack
        combat.defending = True
        with patch("random.random", return_value=0.99):
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                combat.enemy_turn()
        defended_damage = 200 - player.health

        # Defended damage should be ~50% of undefended
        assert defended_damage < undefended_damage
        assert defended_damage <= undefended_damage // 2 + 1  # Allow rounding

    def test_block_reduces_telegraphed_damage(self):
        """Spec: Blocking provides 75% mitigation against special attacks."""
        attacks = [
            SpecialAttack(
                name="Crushing Blow",
                damage_multiplier=2.0,
                telegraph_message="Raises fist...",
                hit_message="CRUSHING BLOW",
            )
        ]
        player = make_player(strength=5)  # Low stats
        boss = make_boss(attack_power=20, special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        # Take undefended special attack
        boss.telegraphed_attack = "Crushing Blow"
        with patch("random.random", return_value=0.99):
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                combat.enemy_turn()
        undefended_damage = 200 - player.health

        # Reset for blocked test
        player.health = 200
        player.max_health = 200
        boss.telegraphed_attack = "Crushing Blow"

        # Block and take special attack
        combat.blocking = True
        with patch("random.random", return_value=0.99):
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                combat.enemy_turn()
        blocked_damage = 200 - player.health

        # Blocked damage should be ~25% of undefended
        assert blocked_damage < undefended_damage
        assert blocked_damage <= undefended_damage // 4 + 1  # Allow rounding


class TestNonBossEnemies:
    """Test that normal enemies don't use telegraph system."""

    def test_non_boss_no_telegraph(self):
        """Spec: Regular enemies never telegraph special attacks."""
        player = make_player()
        enemy = make_normal_enemy()

        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Run many turns to ensure no telegraph ever happens
        for _ in range(20):
            with patch("random.random", return_value=0.0):  # Would trigger for boss
                with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                    result = combat.enemy_turn()
            # Non-boss should never telegraph
            assert enemy.telegraphed_attack is None
            # Reset player health
            player.health = player.max_health


class TestSpecialAttackEffects:
    """Test status effects applied by special attacks."""

    def test_special_attack_applies_effect(self):
        """Spec: Status effects apply on special hit based on effect_chance."""
        attacks = [
            SpecialAttack(
                name="Stunning Strike",
                damage_multiplier=1.5,
                telegraph_message="Winds up...",
                hit_message="STUNNING STRIKE",
                effect_type="stun",
                effect_damage=0,
                effect_duration=1,
                effect_chance=1.0,  # Guaranteed for testing
            )
        ]
        player = make_player(strength=20)  # High STR for health
        boss = make_boss(special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        boss.telegraphed_attack = "Stunning Strike"

        # No stun effect initially
        assert not any(e.effect_type == "stun" for e in player.status_effects)

        with patch("random.random", return_value=0.99):  # No dodge, no crit
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                result = combat.enemy_turn()

        # Stun effect should be applied
        assert any(e.effect_type == "stun" for e in player.status_effects)
        assert "stun" in result.lower()

    def test_special_attack_poison_effect(self):
        """Spec: Poison effect applies damage over time."""
        attacks = [
            SpecialAttack(
                name="Venomous Bite",
                damage_multiplier=1.5,
                telegraph_message="Opens its maw...",
                hit_message="VENOMOUS BITE",
                effect_type="poison",
                effect_damage=5,
                effect_duration=3,
                effect_chance=1.0,
            )
        ]
        player = make_player(strength=20)  # High STR for health
        boss = make_boss(special_attacks=attacks)

        combat = CombatEncounter(player=player, enemy=boss)
        combat.start()

        boss.telegraphed_attack = "Venomous Bite"

        with patch("random.random", return_value=0.99):
            with patch("cli_rpg.combat.calculate_dodge_chance", return_value=0.0):
                result = combat.enemy_turn()

        # Poison should be applied (tracked as DOT)
        dot_effects = [e for e in player.status_effects if e.effect_type == "dot"]
        assert len(dot_effects) > 0
        assert "poison" in result.lower()
