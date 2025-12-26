"""Tests for hide command in combat.

Spec: Hide combat command makes the player untargetable for 1 turn:
- Command: hide (alias: hd) - Available to all classes
- Effect: Applies "Hidden" status effect for 1 turn
- Benefit: Enemies skip attacking hidden player
- Cost: 10 stamina, uses the player's action
- Duration: Hidden effect expires after enemy turn
"""

import random
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.status_effect import StatusEffect
from cli_rpg.combat import CombatEncounter


class TestHideAppliesHiddenEffect:
    """Spec: Hide applies Hidden status effect."""

    def test_hide_applies_hidden_effect(self):
        """Spec: Hide command applies hidden status effect to player."""
        # Create a character (any class)
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
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

        # Use hide
        victory, message = combat.player_hide()

        # Should have hidden effect
        assert any(e.effect_type == "hidden" for e in player.status_effects)
        assert "cover" in message.lower() or "hidden" in message.lower() or "hide" in message.lower()
        assert victory is False  # Combat continues


class TestHideWorksForAllClasses:
    """Spec: All classes can use hide (unlike sneak which is Rogue-only)."""

    @pytest.mark.parametrize("char_class", [
        CharacterClass.WARRIOR,
        CharacterClass.MAGE,
        CharacterClass.ROGUE,
        CharacterClass.RANGER,
        CharacterClass.CLERIC,
    ])
    def test_hide_works_for_all_classes(self, char_class):
        """Spec: All 5 classes can use the hide command."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=char_class
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

        # Ensure player has enough stamina
        player.stamina = player.max_stamina

        # Use hide
        victory, message = combat.player_hide()

        # Should have hidden effect (no class restriction error)
        assert any(e.effect_type == "hidden" for e in player.status_effects)
        assert "Only" not in message  # No class restriction message


class TestHideCostsStamina:
    """Spec: Hide costs 10 stamina."""

    def test_hide_costs_10_stamina(self):
        """Spec: Hide command consumes 10 stamina."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        player.stamina = 50  # Set known stamina
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

        # Use hide
        combat.player_hide()

        # Should cost 10 stamina
        assert player.stamina == initial_stamina - 10


class TestHideFailsWithoutStamina:
    """Spec: Hide fails if player has less than 10 stamina."""

    def test_hide_fails_without_stamina(self):
        """Spec: Hide fails when player has insufficient stamina."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        player.stamina = 5  # Not enough stamina

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

        # Try to hide
        victory, message = combat.player_hide()

        # Should fail with stamina error
        assert "stamina" in message.lower()
        # No hidden effect should be applied
        assert not any(e.effect_type == "hidden" for e in player.status_effects)


class TestHiddenPlayerNotAttacked:
    """Spec: Enemies skip attacking hidden player."""

    def test_hidden_player_not_attacked(self):
        """Spec: When player is hidden, enemies skip attacking them."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        enemy = Enemy(
            name="Goblin",
            health=30,
            max_health=30,
            attack_power=50,  # High attack to ensure damage if hit
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Apply hidden effect
        combat.player_hide()
        assert player.is_hidden()

        initial_health = player.health

        # Enemy turn - should skip attacking hidden player
        message = combat.enemy_turn()

        # Player should NOT take damage
        assert player.health == initial_health
        # Message should indicate enemies are searching
        assert "hidden" in message.lower() or "search" in message.lower()


class TestHiddenExpiresAfterEnemyTurn:
    """Spec: Hidden effect expires after 1 turn."""

    def test_hidden_expires_after_enemy_turn(self):
        """Spec: Hidden effect is removed after enemy turn."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
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

        # Apply hidden
        combat.player_hide()
        assert player.is_hidden()

        # Enemy turn
        combat.enemy_turn()

        # Hidden should be expired
        assert not player.is_hidden()


class TestHideBlockedWhenStunned:
    """Spec: Cannot hide while stunned."""

    def test_hide_blocked_when_stunned(self):
        """Spec: Player cannot use hide while stunned."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        # Apply stun effect
        stun = StatusEffect(
            name="Stun",
            effect_type="stun",
            damage_per_turn=0,
            duration=1
        )
        player.apply_status_effect(stun)

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

        # Try to hide while stunned
        victory, message = combat.player_hide()

        # Should fail with stun message
        assert "stun" in message.lower()
        # No hidden effect should be applied
        assert not any(e.effect_type == "hidden" for e in player.status_effects)


class TestIsHiddenMethod:
    """Test Character.is_hidden() helper method."""

    def test_is_hidden_returns_true_when_hidden(self):
        """Spec: is_hidden() returns True when character has hidden effect."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )

        # Initially not hidden
        assert not player.is_hidden()

        # Apply hidden effect
        hidden = StatusEffect(
            name="Hidden",
            effect_type="hidden",
            damage_per_turn=0,
            duration=1
        )
        player.apply_status_effect(hidden)

        # Should be hidden
        assert player.is_hidden()

    def test_is_hidden_returns_false_when_not_hidden(self):
        """Spec: is_hidden() returns False when character has no hidden effect."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )

        # Not hidden
        assert not player.is_hidden()

        # Apply some other effect (not hidden)
        poison = StatusEffect(
            name="Poison",
            effect_type="poison",
            damage_per_turn=3,
            duration=3
        )
        player.apply_status_effect(poison)

        # Still not hidden
        assert not player.is_hidden()
