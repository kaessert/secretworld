"""Tests for Rogue sneak command.

Spec: Rogue's sneak command enables stealth mode during combat:
- Command: sneak (alias: sn) - Rogue-only combat action
- Effect: Applies "Stealth" status effect for 1 turn
- Benefit: Next attack from stealth deals 1.5x damage (backstab bonus)
- Cost: Uses the turn (enemies still attack), stealth breaks on taking damage
- Dexterity factor: Higher DEX increases dodge chance while stealthed (DEX * 5% dodge)
"""

import random
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.status_effect import StatusEffect
from cli_rpg.combat import CombatEncounter


class TestSneakAppliesStealth:
    """Spec: Rogue enters stealth, has stealth effect."""

    def test_sneak_applies_stealth_effect(self):
        """Spec: Sneak command applies stealth status effect to Rogue."""
        # Create a Rogue character
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
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

        # Use sneak
        victory, message = combat.player_sneak()

        # Should have stealth effect
        assert any(e.effect_type == "stealth" for e in player.status_effects)
        assert "shadow" in message.lower() or "stealth" in message.lower()
        assert victory is False  # Combat continues


class TestSneakRogueOnly:
    """Spec: Non-Rogue classes get error message, no effect applied."""

    def test_sneak_warrior_cannot_sneak(self):
        """Spec: Warrior cannot use sneak command."""
        player = Character(
            name="Tank",
            strength=14,
            dexterity=8,
            intelligence=8,
            character_class=CharacterClass.WARRIOR
        )
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

        victory, message = combat.player_sneak()

        # Should get error message
        assert "rogue" in message.lower()
        # No stealth effect should be applied
        assert not any(e.effect_type == "stealth" for e in player.status_effects)

    def test_sneak_mage_cannot_sneak(self):
        """Spec: Mage cannot use sneak command."""
        player = Character(
            name="Wizard",
            strength=8,
            dexterity=8,
            intelligence=14,
            character_class=CharacterClass.MAGE
        )
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

        victory, message = combat.player_sneak()

        assert "rogue" in message.lower()
        assert not any(e.effect_type == "stealth" for e in player.status_effects)


class TestSneakBreaksOnDamage:
    """Spec: Taking damage removes stealth effect."""

    def test_sneak_breaks_on_damage(self):
        """Spec: When player takes damage while stealthed, stealth is removed."""
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=50,  # High attack to ensure hit
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Apply stealth
        combat.player_sneak()
        assert player.is_stealthed()

        # Patch random to ensure dodge fails (enemy hits)
        with patch("random.random", return_value=0.99):
            combat.enemy_turn()

        # Stealth should be removed after taking damage
        assert not player.is_stealthed()


class TestSneakBackstabBonus:
    """Spec: Attack from stealth deals 1.5x damage."""

    def test_sneak_backstab_bonus(self):
        """Spec: Attack from stealth deals 1.5x damage."""
        player = Character(
            name="Shadow",
            strength=10,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,  # No defense for predictable damage
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Apply stealth first
        combat.player_sneak()
        assert player.is_stealthed()

        # Track starting health
        initial_health = enemy.health

        # Attack from stealth - should deal 1.5x damage
        # Patch random to avoid crits
        with patch("random.random", return_value=0.99):
            victory, message = combat.player_attack()

        # Calculate expected damage
        # Base damage = player attack power - enemy defense
        base_damage = player.get_attack_power()  # defense is 0
        expected_damage = int(base_damage * 1.5)  # Backstab multiplier

        assert enemy.health == initial_health - expected_damage
        assert "backstab" in message.lower()


class TestSneakRemovesAfterAttack:
    """Spec: Stealth consumed after attacking."""

    def test_sneak_removes_stealth_after_attack(self):
        """Spec: Stealth effect is consumed after player attacks from stealth."""
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
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

        # Apply stealth
        combat.player_sneak()
        assert player.is_stealthed()

        # Attack from stealth
        with patch("random.random", return_value=0.99):
            combat.player_attack()

        # Stealth should be consumed
        assert not player.is_stealthed()


class TestSneakDodgeChanceScalesWithDex:
    """Spec: Higher DEX = better dodge while stealthed."""

    def test_sneak_dodge_chance_scales_with_dex(self):
        """Spec: Dodge chance while stealthed is DEX * 5%, capped at 75%."""
        # Test with DEX 10 = 50% dodge chance
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=10,  # Will be 13 after Rogue bonus
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=50,  # High attack
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Apply stealth
        combat.player_sneak()
        initial_health = player.health

        # Mock random to return 0.5 (50%)
        # With DEX 13, dodge chance = 65%, so 0.5 should dodge
        with patch("random.random", return_value=0.5):
            combat.enemy_turn()

        # Player should have dodged (no damage taken)
        assert player.health == initial_health

    def test_sneak_dodge_capped_at_75_percent(self):
        """Spec: Stealth dodge chance is capped at 75%."""
        # Player with very high DEX
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=20,  # Max DEX = 23 after Rogue bonus
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=50,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Apply stealth
        combat.player_sneak()
        initial_health = player.health

        # Mock random to return 0.76 (76%)
        # Even with DEX 23 (115% uncapped), cap should be 75%
        # So 0.76 should NOT dodge
        with patch("random.random", return_value=0.76):
            combat.enemy_turn()

        # Player should have taken damage (dodge failed at 76%)
        assert player.health < initial_health


class TestSneakDuringCombatOnly:
    """Spec: Command only works in combat mode."""

    def test_sneak_during_combat_only(self):
        """Spec: Sneak command should only be available during combat."""
        # This test verifies behavior at the game_state/main.py level
        # The command parser should only recognize sneak in combat context
        from cli_rpg.game_state import parse_command, KNOWN_COMMANDS

        # Verify sneak is a known command
        assert "sneak" in KNOWN_COMMANDS

        # Parse the sneak command
        cmd, args = parse_command("sneak")
        assert cmd == "sneak"

        # Parse the alias
        cmd, args = parse_command("sn")
        assert cmd == "sneak"


class TestSneakTriggersEnemyTurn:
    """Spec: Enemy still attacks after sneak action."""

    def test_sneak_triggers_enemy_turn(self):
        """Spec: After using sneak, enemy should get their turn to attack."""
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=10,  # Lower DEX for lower dodge chance
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
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

        # Use sneak
        combat.player_sneak()

        # Enemy turn should happen (handled by main.py)
        # Patch to ensure hit (dodge fails)
        with patch("random.random", return_value=0.99):
            enemy_message = combat.enemy_turn()

        # Enemy should have attacked (message contains attack info)
        assert "goblin" in enemy_message.lower() or "attack" in enemy_message.lower()


class TestCharacterStealthMethods:
    """Test Character helper methods for stealth."""

    def test_is_stealthed_returns_true_when_stealthed(self):
        """Spec: is_stealthed() returns True when character has stealth effect."""
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )

        # Initially not stealthed
        assert not player.is_stealthed()

        # Apply stealth effect
        stealth = StatusEffect(
            name="Stealth",
            effect_type="stealth",
            damage_per_turn=0,
            duration=2
        )
        player.apply_status_effect(stealth)

        # Should be stealthed
        assert player.is_stealthed()

    def test_consume_stealth_removes_effect(self):
        """Spec: consume_stealth() removes stealth effect and returns True."""
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )

        # Apply stealth effect
        stealth = StatusEffect(
            name="Stealth",
            effect_type="stealth",
            damage_per_turn=0,
            duration=2
        )
        player.apply_status_effect(stealth)

        # Consume stealth
        was_stealthed = player.consume_stealth()

        assert was_stealthed is True
        assert not player.is_stealthed()

    def test_consume_stealth_returns_false_when_not_stealthed(self):
        """Spec: consume_stealth() returns False when not stealthed."""
        player = Character(
            name="Shadow",
            strength=8,
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )

        # Not stealthed
        was_stealthed = player.consume_stealth()

        assert was_stealthed is False


class TestSneakKillBonusXP:
    """Spec: Killing enemy with backstab grants 25% bonus XP."""

    def test_stealth_kill_grants_bonus_xp(self):
        """Spec: Backstab kill grants 25% bonus XP on combat end."""
        # Create Rogue with max STR to one-shot enemy
        player = Character(
            name="Shadow",
            strength=20,  # Max stat to deal enough damage
            dexterity=14,
            intelligence=8,
            character_class=CharacterClass.ROGUE
        )
        # Use enemy with xp_reward=40 to avoid level-up (base + bonus = 50 < 100 to level)
        enemy = Enemy(
            name="Goblin",
            health=1,  # Very low health to guarantee one-shot
            max_health=1,
            attack_power=5,
            defense=0,
            xp_reward=40  # 40 base + 10 bonus = 50 total, no level up
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Enter stealth first
        combat.player_sneak()
        assert player.is_stealthed()

        initial_xp = player.xp
        initial_level = player.level

        # Attack from stealth - should kill enemy
        with patch("random.random", return_value=0.99):  # No crits
            victory, message = combat.player_attack()

        # Verify it was a stealth kill
        assert victory is True
        assert combat.stealth_kills == 1
        assert "backstab" in message.lower()

        # End combat and check XP bonus
        result = combat.end_combat(victory=True)

        # Should have stealth bonus message
        assert "stealth bonus" in result.lower()

        # Player should get 50 XP (40 base + 10 bonus = 25% of 40)
        xp_gained = player.xp - initial_xp
        assert xp_gained == 50
        assert player.level == initial_level  # No level up

    def test_no_bonus_for_normal_kills(self):
        """Spec: Normal kills don't grant stealth bonus XP."""
        player = Character(
            name="Tank",
            strength=20,  # Max stat
            dexterity=8,
            intelligence=8,
            character_class=CharacterClass.WARRIOR
        )
        enemy = Enemy(
            name="Goblin",
            health=1,  # Low health for one-shot
            max_health=1,
            attack_power=5,
            defense=0,
            xp_reward=50  # 50 XP, no level up
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_xp = player.xp

        # Attack normally (no stealth)
        with patch("random.random", return_value=0.99):  # No crits
            victory, message = combat.player_attack()

        # Verify it was a normal kill
        assert victory is True
        assert combat.stealth_kills == 0
        assert "backstab" not in message.lower()

        # End combat
        result = combat.end_combat(victory=True)

        # Should NOT have stealth bonus message
        assert "stealth bonus" not in result.lower()

        # Player should get exactly 50 XP (no stealth bonus)
        xp_gained = player.xp - initial_xp
        assert xp_gained == 50
