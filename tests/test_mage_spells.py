"""Tests for Mage-specific spells (Fireball, Ice Bolt, Heal).

Spec: Mage-exclusive spells to leverage the mana system and give Mages their unique playstyle.
"""

from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.status_effect import StatusEffect
from cli_rpg.combat import CombatEncounter


class TestFireballClassRestriction:
    """Tests for Fireball class restriction."""

    def test_fireball_mage_only(self):
        """Spec: Only Mages can cast Fireball. Non-mages get error message."""
        # Create a Warrior (non-Mage)
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_fireball()

        assert victory is False
        assert "only mages" in message.lower() or "mage" in message.lower()


class TestFireballManaCost:
    """Tests for Fireball mana costs."""

    def test_fireball_costs_20_mana(self):
        """Spec: Fireball costs 20 mana to cast."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        initial_mana = player.mana
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to prevent burn proc
        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_fireball()

        assert player.mana == initial_mana - 20

    def test_fireball_fails_without_mana(self):
        """Spec: Fireball fails if player has < 20 mana."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        player.mana = 15  # Less than 20
        initial_mana = player.mana
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_fireball()

        assert victory is False
        assert player.mana == initial_mana  # Mana unchanged
        assert "mana" in message.lower()


class TestFireballDamage:
    """Tests for Fireball damage calculation."""

    def test_fireball_deals_int_times_2_5_damage(self):
        """Spec: Fireball deals INT * 2.5 damage."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Mage gets +3 INT bonus, so total INT = 13
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=10,  # High defense to verify it's ignored
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        # Mock random to prevent burn proc
        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_fireball()

        # Damage = INT * 2.5 = 13 * 2.5 = 32 (rounded down)
        expected_damage = int(player.intelligence * 2.5)
        assert initial_health - enemy.health == expected_damage

    def test_fireball_ignores_enemy_defense(self):
        """Spec: Fireball ignores enemy defense like cast."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Create enemy with very high defense
        enemy = Enemy(
            name="Armored Golem",
            health=100,
            max_health=100,
            attack_power=5,
            defense=100,  # Very high defense
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_fireball()

        # Damage should still be INT * 2.5, not reduced by defense
        expected_damage = int(player.intelligence * 2.5)
        assert initial_health - enemy.health == expected_damage


class TestFireballBurnEffect:
    """Tests for Fireball burn effect."""

    def test_fireball_can_apply_burn(self):
        """Spec: Fireball has 25% chance to apply Burn (5 damage/turn, 2 turns)."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to trigger burn (< 0.25)
        with patch('cli_rpg.combat.random.random', return_value=0.10):
            victory, message = combat.player_fireball()

        # Check enemy has Burn effect
        burn_effects = [e for e in enemy.status_effects if e.name == "Burn"]
        assert len(burn_effects) == 1
        assert burn_effects[0].damage_per_turn == 5
        assert burn_effects[0].duration == 2
        assert "burn" in message.lower()


class TestIceBoltClassRestriction:
    """Tests for Ice Bolt class restriction."""

    def test_ice_bolt_mage_only(self):
        """Spec: Only Mages can cast Ice Bolt. Non-mages get error message."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.ROGUE,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_ice_bolt()

        assert victory is False
        assert "only mages" in message.lower() or "mage" in message.lower()


class TestIceBoltManaCost:
    """Tests for Ice Bolt mana costs."""

    def test_ice_bolt_costs_15_mana(self):
        """Spec: Ice Bolt costs 15 mana to cast."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        initial_mana = player.mana
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to prevent freeze proc
        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_ice_bolt()

        assert player.mana == initial_mana - 15

    def test_ice_bolt_fails_without_mana(self):
        """Spec: Ice Bolt fails if player has < 15 mana."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        player.mana = 10  # Less than 15
        initial_mana = player.mana
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_ice_bolt()

        assert victory is False
        assert player.mana == initial_mana  # Mana unchanged
        assert "mana" in message.lower()


class TestIceBoltDamage:
    """Tests for Ice Bolt damage calculation."""

    def test_ice_bolt_deals_int_times_2_damage(self):
        """Spec: Ice Bolt deals INT * 2.0 damage."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Mage gets +3 INT bonus, so total INT = 13
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=10,  # Defense should be ignored
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        # Mock random to prevent freeze proc
        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_ice_bolt()

        # Damage = INT * 2.0 = 13 * 2 = 26
        expected_damage = int(player.intelligence * 2.0)
        assert initial_health - enemy.health == expected_damage


class TestIceBoltFreezeEffect:
    """Tests for Ice Bolt freeze effect."""

    def test_ice_bolt_can_apply_freeze(self):
        """Spec: Ice Bolt has 30% chance to apply Freeze (50% attack reduction, 2 turns)."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Mock random to trigger freeze (< 0.30)
        with patch('cli_rpg.combat.random.random', return_value=0.15):
            victory, message = combat.player_ice_bolt()

        # Check enemy has Freeze effect
        freeze_effects = [e for e in enemy.status_effects if e.name == "Freeze"]
        assert len(freeze_effects) == 1
        assert freeze_effects[0].effect_type == "freeze"
        assert freeze_effects[0].duration == 2
        assert "freeze" in message.lower() or "frozen" in message.lower()


class TestHealClassRestriction:
    """Tests for Heal class restriction."""

    def test_heal_mage_only(self):
        """Spec: Only Mages can cast Heal. Non-mages get error message."""
        player = Character(
            name="Hero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,  # Even Clerics can't use this spell
        )
        player.health = 50  # Damage player
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_heal()

        assert victory is False
        assert "only mages" in message.lower() or "mage" in message.lower()


class TestHealManaCost:
    """Tests for Heal mana costs."""

    def test_heal_costs_25_mana(self):
        """Spec: Heal costs 25 mana to cast."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        player.health = 50  # Damage player so heal can be used
        initial_mana = player.mana
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_heal()

        assert player.mana == initial_mana - 25

    def test_heal_fails_without_mana(self):
        """Spec: Heal fails if player has < 25 mana."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        player.health = 50  # Damage player
        player.mana = 20  # Less than 25
        initial_mana = player.mana
        initial_health = player.health
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_heal()

        assert victory is False
        assert player.mana == initial_mana  # Mana unchanged
        assert player.health == initial_health  # Health unchanged
        assert "mana" in message.lower()


class TestHealEffect:
    """Tests for Heal effect."""

    def test_heal_restores_int_times_2_hp(self):
        """Spec: Heal restores INT * 2 HP."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Mage gets +3 INT bonus, so total INT = 13
        player.health = 50  # Damage player
        initial_health = player.health
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_heal()

        # Heal amount = INT * 2 = 13 * 2 = 26
        expected_heal = int(player.intelligence * 2)
        assert player.health == initial_health + expected_heal

    def test_heal_capped_at_max_health(self):
        """Spec: Heal cannot exceed max_health."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Set health to just below max so heal would exceed
        player.health = player.max_health - 5
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_heal()

        assert player.health == player.max_health

    def test_heal_fails_at_full_health(self):
        """Spec: Heal fails if player is already at full health."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        initial_mana = player.mana
        # Player is at full health by default
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_heal()

        assert victory is False
        assert player.mana == initial_mana  # Mana not consumed
        assert "full health" in message.lower() or "already" in message.lower()


class TestCombatIntegration:
    """Tests for spell combat integration."""

    def test_spells_trigger_enemy_turn(self):
        """Spec: After using a spell, the enemy should attack (handled in main.py)."""
        # This is really tested via the main.py integration, but we verify
        # spells return False for victory when enemy survives
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        with patch('cli_rpg.combat.random.random', return_value=0.99):
            victory, _ = combat.player_fireball()

        # Victory should be False (enemy still alive), combat continues
        assert victory is False
        assert enemy.is_alive()

    def test_spells_can_defeat_enemy(self):
        """Spec: Spells can defeat enemy and return victory=True."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Enemy with very low health
        enemy = Enemy(
            name="Goblin",
            health=5,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        with patch('cli_rpg.combat.random.random', return_value=0.99):
            victory, message = combat.player_fireball()

        assert victory is True
        assert not enemy.is_alive()
        assert "defeat" in message.lower() or "victory" in message.lower()

    def test_stunned_mage_cannot_cast_spells(self):
        """Spec: Stunned player cannot cast spells."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        # Apply stun effect
        stun = StatusEffect(name="Stun", effect_type="stun", damage_per_turn=0, duration=1)
        player.apply_status_effect(stun)

        initial_mana = player.mana

        # Try each spell while stunned
        victory, message = combat.player_fireball()
        assert victory is False
        assert "stunned" in message.lower()
        assert player.mana == initial_mana  # No mana consumed

        # Re-apply stun for ice bolt test
        stun = StatusEffect(name="Stun", effect_type="stun", damage_per_turn=0, duration=1)
        player.apply_status_effect(stun)

        victory, message = combat.player_ice_bolt()
        assert victory is False
        assert "stunned" in message.lower()

        # Re-apply stun for heal test
        stun = StatusEffect(name="Stun", effect_type="stun", damage_per_turn=0, duration=1)
        player.apply_status_effect(stun)
        player.health = 50  # Damage player for heal test

        victory, message = combat.player_heal()
        assert victory is False
        assert "stunned" in message.lower()


class TestComboSystem:
    """Tests for spell combo tracking."""

    def test_fireball_records_cast_action(self):
        """Spec: Fireball records 'cast' action for Arcane Burst combo tracking."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_fireball()

        assert "cast" in combat.action_history

    def test_ice_bolt_records_cast_action(self):
        """Spec: Ice Bolt records 'cast' action for Arcane Burst combo tracking."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        with patch('cli_rpg.combat.random.random', return_value=0.99):
            combat.player_ice_bolt()

        assert "cast" in combat.action_history


class TestHealRecordsCast:
    """Tests for Heal combo tracking."""

    def test_heal_records_cast_action(self):
        """Spec: Heal records 'cast' action for combo tracking."""
        player = Character(
            name="Wizard",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        player.health = 50  # Damage player so heal works
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        combat.player_heal()

        assert "cast" in combat.action_history
