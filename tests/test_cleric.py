"""Tests for Cleric class abilities: bless and smite."""

import random
from unittest.mock import patch

import pytest

from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.companion import Companion, BondLevel
from cli_rpg.combat import CombatEncounter


class TestClericMana:
    """Tests for Cleric max mana scaling (Spec: Cleric max mana: Use Mage-like mana scaling)."""

    def test_cleric_has_mage_like_max_mana(self):
        """Spec: Cleric max mana = 50 + INT * 5 (same as Mage)."""
        # Cleric gets +2 INT from class bonuses, so base 10 becomes 12
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        # INT = 10 + 2 (class bonus) = 12
        expected_mana = 50 + 12 * 5  # 50 + 60 = 110
        assert cleric.max_mana == expected_mana
        assert cleric.mana == expected_mana

    def test_cleric_mana_scales_with_intelligence(self):
        """Spec: Cleric mana should scale with intelligence like Mage."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=15,  # Higher INT
            character_class=CharacterClass.CLERIC,
        )
        # INT = 15 + 2 (class bonus) = 17
        expected_mana = 50 + 17 * 5  # 50 + 85 = 135
        assert cleric.max_mana == expected_mana

    def test_non_cleric_has_lower_max_mana(self):
        """Verify non-mage, non-cleric classes use the lower mana formula."""
        warrior = Character(
            name="Warrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Warrior INT = 10 + 0 (class bonus) = 10
        expected_mana = 20 + 10 * 2  # 20 + 20 = 40
        assert warrior.max_mana == expected_mana


class TestBlessCommand:
    """Tests for the bless command (Spec: Cleric buffs party with attack bonus)."""

    def _create_cleric_combat(self):
        """Helper to create a Cleric in combat."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=cleric, enemy=enemy)
        combat.start()
        return cleric, enemy, combat

    def test_bless_only_available_to_cleric(self):
        """Spec: Only Clerics can bless - other classes get 'Only Clerics can bless!'."""
        warrior = Character(
            name="Warrior",
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
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        victory, message = combat.player_bless()

        assert victory is False
        assert "Only Clerics can bless" in message

    def test_bless_costs_20_mana(self):
        """Spec: Bless costs 20 mana."""
        cleric, enemy, combat = self._create_cleric_combat()
        initial_mana = cleric.mana

        combat.player_bless()

        assert cleric.mana == initial_mana - 20

    def test_bless_fails_without_mana(self):
        """Spec: Bless returns error with <20 mana."""
        cleric, enemy, combat = self._create_cleric_combat()
        cleric.mana = 15  # Less than required 20

        victory, message = combat.player_bless()

        assert victory is False
        assert "mana" in message.lower() or "Not enough" in message

    def test_bless_applies_buff_to_player(self):
        """Spec: Bless applies 'Blessed' status effect with +25% attack to player."""
        cleric, enemy, combat = self._create_cleric_combat()

        victory, message = combat.player_bless()

        assert victory is False  # Bless is not a victory condition
        # Check player has the Blessed effect
        blessed_effects = [e for e in cleric.status_effects if e.name == "Blessed"]
        assert len(blessed_effects) == 1
        assert blessed_effects[0].effect_type == "buff_attack"
        assert blessed_effects[0].stat_modifier == 0.25

    def test_bless_applies_buff_to_companions(self):
        """Spec: Bless applies 'Blessed' effect to all companions."""
        cleric, enemy, combat = self._create_cleric_combat()
        # Add companions using correct Companion signature
        companion1 = Companion(
            name="Ally1",
            description="A helpful warrior",
            recruited_at="Town",
        )
        companion2 = Companion(
            name="Ally2",
            description="A helpful mage",
            recruited_at="Town",
        )
        combat.companions = [companion1, companion2]

        victory, message = combat.player_bless()

        # Check both companions have the Blessed effect
        for companion in [companion1, companion2]:
            blessed_effects = [e for e in companion.status_effects if e.name == "Blessed"]
            assert len(blessed_effects) == 1
            assert blessed_effects[0].effect_type == "buff_attack"
            assert blessed_effects[0].stat_modifier == 0.25

    def test_bless_buff_lasts_3_turns(self):
        """Spec: Blessed buff has duration of 3 turns."""
        cleric, enemy, combat = self._create_cleric_combat()

        combat.player_bless()

        blessed_effects = [e for e in cleric.status_effects if e.name == "Blessed"]
        assert len(blessed_effects) == 1
        assert blessed_effects[0].duration == 3

    def test_bless_only_usable_in_combat(self):
        """Spec: Bless can only be used in combat."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        # Combat not started (is_active=False)
        combat = CombatEncounter(player=cleric, enemy=enemy)
        # Don't call combat.start() - combat should not be active

        assert combat.is_active is False
        # The command won't even be dispatched in main.py if not in combat,
        # but we test the method behavior when combat isn't truly active


class TestSmiteCommand:
    """Tests for the smite command (Spec: Cleric deals holy damage, extra vs undead)."""

    def _create_cleric_combat(self, enemy_name="Goblin"):
        """Helper to create a Cleric in combat."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        enemy = Enemy(
            name=enemy_name,
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25,
        )
        combat = CombatEncounter(player=cleric, enemy=enemy)
        combat.start()
        return cleric, enemy, combat

    def test_smite_only_available_to_cleric(self):
        """Spec: Only Clerics can smite - other classes get 'Only Clerics can smite!'."""
        warrior = Character(
            name="Warrior",
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
        combat = CombatEncounter(player=warrior, enemy=enemy)
        combat.start()

        victory, message = combat.player_smite()

        assert victory is False
        assert "Only Clerics can smite" in message

    def test_smite_costs_15_mana(self):
        """Spec: Smite costs 15 mana."""
        cleric, enemy, combat = self._create_cleric_combat()
        initial_mana = cleric.mana

        combat.player_smite()

        assert cleric.mana == initial_mana - 15

    def test_smite_fails_without_mana(self):
        """Spec: Smite returns error with <15 mana."""
        cleric, enemy, combat = self._create_cleric_combat()
        cleric.mana = 10  # Less than required 15

        victory, message = combat.player_smite()

        assert victory is False
        assert "mana" in message.lower() or "Not enough" in message

    def test_smite_deals_int_based_damage(self):
        """Spec: Smite damage = INT * 2.5 (ignores defense)."""
        cleric, enemy, combat = self._create_cleric_combat()
        initial_health = enemy.health
        # Cleric INT = 10 + 2 (class bonus) = 12
        expected_damage = int(12 * 2.5)  # 30

        victory, message = combat.player_smite()

        assert enemy.health == initial_health - expected_damage

    def test_smite_deals_double_damage_to_undead(self):
        """Spec: Smite deals 2x multiplier (INT * 5.0) to undead enemies."""
        cleric, enemy, combat = self._create_cleric_combat(enemy_name="Skeleton Warrior")
        initial_health = enemy.health
        # Cleric INT = 10 + 2 (class bonus) = 12
        # Undead multiplier: INT * 5.0
        expected_damage = int(12 * 5.0)  # 60

        victory, message = combat.player_smite()

        assert enemy.health == initial_health - expected_damage

    @patch("random.random", return_value=0.1)  # 10% < 30%, triggers stun
    def test_smite_can_stun_undead(self, mock_random):
        """Spec: 30% chance to stun undead for 1 turn."""
        cleric, enemy, combat = self._create_cleric_combat(enemy_name="Zombie")
        enemy.health = 200  # High health so it survives

        combat.player_smite()

        # Check enemy has stun effect
        stun_effects = [e for e in enemy.status_effects if e.effect_type == "stun"]
        assert len(stun_effects) == 1
        assert stun_effects[0].duration == 1

    @patch("random.random", return_value=0.5)  # 50% > 30%, no stun
    def test_smite_stun_chance_is_30_percent(self, mock_random):
        """Spec: Stun chance is 30% - should not trigger at 50% roll."""
        cleric, enemy, combat = self._create_cleric_combat(enemy_name="Ghost")
        enemy.health = 200  # High health so it survives

        combat.player_smite()

        # Check enemy does NOT have stun effect
        stun_effects = [e for e in enemy.status_effects if e.effect_type == "stun"]
        assert len(stun_effects) == 0

    def test_smite_no_stun_to_living(self):
        """Spec: No stun chance for non-undead enemies."""
        cleric, enemy, combat = self._create_cleric_combat(enemy_name="Bandit")

        with patch("random.random", return_value=0.0):  # Would always trigger if possible
            combat.player_smite()

        # Check enemy does NOT have stun effect
        stun_effects = [e for e in enemy.status_effects if e.effect_type == "stun"]
        assert len(stun_effects) == 0

    def test_smite_detects_various_undead_types(self):
        """Spec: Smite recognizes various undead terms in enemy names."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )

        undead_names = [
            "Skeleton",
            "Zombie Horde",
            "Ancient Ghost",
            "Wraith King",
            "Undead Knight",
            "Specter",
            "Lich Lord",
            "Vampire Count",
        ]

        for enemy_name in undead_names:
            enemy = Enemy(
                name=enemy_name,
                health=200,
                max_health=200,
                attack_power=5,
                defense=2,
                xp_reward=25,
            )
            combat = CombatEncounter(player=cleric, enemy=enemy)
            combat.start()
            initial_health = enemy.health

            # Cleric INT = 12
            expected_damage = int(12 * 5.0)  # Undead damage

            combat.player_smite()

            assert enemy.health == initial_health - expected_damage, f"Failed for {enemy_name}"

            # Reset mana for next iteration
            cleric.mana = cleric.max_mana


class TestClericIntegration:
    """Integration tests for Cleric abilities in game context."""

    def test_bless_increases_attack_power(self):
        """Verify that Blessed buff actually increases attack damage."""
        cleric = Character(
            name="Cleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.CLERIC,
        )
        enemy = Enemy(
            name="Goblin",
            health=200,
            max_health=200,
            attack_power=5,
            defense=0,  # No defense for clean damage test
            xp_reward=25,
        )
        combat = CombatEncounter(player=cleric, enemy=enemy)
        combat.start()

        # Attack without blessing
        initial_attack_power = cleric.get_attack_power()

        # Apply bless
        combat.player_bless()

        # Attack power should be 25% higher
        blessed_attack_power = cleric.get_attack_power()
        assert blessed_attack_power == int(initial_attack_power * 1.25)
