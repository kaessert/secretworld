"""Tests for companion combat abilities.

These tests verify the combat bonus system based on companion bond levels:
- STRANGER (0-24): No bonus
- ACQUAINTANCE (25-49): +3% attack
- TRUSTED (50-74): +5% attack
- DEVOTED (75-100): +10% attack
"""

from unittest.mock import patch

import pytest
from cli_rpg.models.companion import Companion, BondLevel
from cli_rpg.models.character import Character
from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter


class TestCompanionCombatBonus:
    """Test companion bond level combat bonuses (spec: bond level -> attack bonus)."""

    def test_stranger_provides_no_bonus(self):
        """Companions at STRANGER level (0-24 points) give 0% attack bonus."""
        companion = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=0
        )
        assert companion.get_combat_bonus() == 0.0
        # Also test upper bound of STRANGER range
        companion_at_24 = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=24
        )
        assert companion_at_24.get_combat_bonus() == 0.0

    def test_acquaintance_provides_3_percent_bonus(self):
        """Companions at ACQUAINTANCE level (25-49 points) give 3% attack bonus."""
        companion = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=25
        )
        assert companion.get_combat_bonus() == 0.03
        # Also test upper bound
        companion_at_49 = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=49
        )
        assert companion_at_49.get_combat_bonus() == 0.03

    def test_trusted_provides_5_percent_bonus(self):
        """Companions at TRUSTED level (50-74 points) give 5% attack bonus."""
        companion = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=50
        )
        assert companion.get_combat_bonus() == 0.05
        # Also test upper bound
        companion_at_74 = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=74
        )
        assert companion_at_74.get_combat_bonus() == 0.05

    def test_devoted_provides_10_percent_bonus(self):
        """Companions at DEVOTED level (75-100 points) give 10% attack bonus."""
        companion = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=75
        )
        assert companion.get_combat_bonus() == 0.10
        # Also test max
        companion_at_100 = Companion(
            name="Test", description="Test", recruited_at="Test", bond_points=100
        )
        assert companion_at_100.get_combat_bonus() == 0.10


class TestCombatWithCompanions:
    """Test combat damage with companion bonuses applied."""

    @pytest.fixture
    def player(self):
        """Create a test player with known stats."""
        return Character(
            name="TestPlayer",
            strength=10,
            dexterity=10,
            intelligence=10,
        )

    @pytest.fixture
    def weak_enemy(self):
        """Create a weak enemy for testing damage calculations."""
        return Enemy(
            name="TestEnemy",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,  # 0 defense to simplify damage calculation
            xp_reward=10,
            level=1,
        )

    def test_attack_damage_increased_by_companion_bonus(self, player, weak_enemy):
        """Attack damage should be multiplied by (1 + companion_bonus).

        Spec: Player attack is multiplied by companion bonus.
        """
        # Create a DEVOTED companion (+10%)
        companion = Companion(
            name="Loyal Friend",
            description="A loyal companion",
            recruited_at="Town",
            bond_points=75,
        )

        # Combat without companion
        combat_no_companion = CombatEncounter(player, enemy=weak_enemy)
        # Get base damage (strength 10, no weapon, 0 defense) = 10
        base_damage = max(1, player.get_attack_power() - weak_enemy.defense)
        assert base_damage == 10  # Sanity check

        # Create fresh enemy for second test
        enemy_with_companion = Enemy(
            name="TestEnemy",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=10,
            level=1,
        )

        # Combat with companion
        combat_with_companion = CombatEncounter(
            player, enemy=enemy_with_companion, companions=[companion]
        )

        # Attack and check damage (patch random to prevent critical hits)
        with patch('cli_rpg.combat.random.random', return_value=0.50):
            combat_with_companion.player_attack()
        # Expected: 10 * 1.10 = 11 damage
        expected_health = 100 - 11
        assert enemy_with_companion.health == expected_health

    def test_cast_damage_increased_by_companion_bonus(self, player, weak_enemy):
        """Cast damage should be multiplied by (1 + companion_bonus).

        Spec: Magic damage is also multiplied by companion bonus.
        """
        # Create a DEVOTED companion (+10%)
        companion = Companion(
            name="Mystic Ally",
            description="A magical companion",
            recruited_at="Tower",
            bond_points=75,
        )

        combat = CombatEncounter(player, enemy=weak_enemy, companions=[companion])

        # Cast spell
        # Base magic damage = int(intelligence * 1.5) = int(10 * 1.5) = 15
        # With companion: 15 * 1.10 = 16.5 -> 16 (int truncation)
        combat.player_cast()
        expected_health = 100 - 16
        assert weak_enemy.health == expected_health

    def test_multiple_companions_stack_bonuses(self, player, weak_enemy):
        """Multiple companions should stack their bonuses additively.

        Spec: Bonuses stack if multiple companions.
        """
        # Two DEVOTED companions = +10% + 10% = +20% total
        companion1 = Companion(
            name="Friend 1",
            description="First companion",
            recruited_at="Town",
            bond_points=75,
        )
        companion2 = Companion(
            name="Friend 2",
            description="Second companion",
            recruited_at="Forest",
            bond_points=75,
        )

        combat = CombatEncounter(
            player, enemy=weak_enemy, companions=[companion1, companion2]
        )

        # Attack
        # Base damage = 10, with +20% bonus = 12
        combat.player_attack()
        expected_health = 100 - 12
        assert weak_enemy.health == expected_health

    def test_no_companions_means_no_bonus(self, player, weak_enemy):
        """Combat without companions should work normally (no bonus applied)."""
        combat = CombatEncounter(player, enemy=weak_enemy)

        # Attack should deal base damage only
        combat.player_attack()
        # Base damage = 10 (strength) - 0 (defense) = 10
        expected_health = 100 - 10
        assert weak_enemy.health == expected_health

    def test_combat_status_shows_companion_bonus(self, player, weak_enemy):
        """Combat status should display active companion bonus if > 0.

        Spec: Display bonus in combat status.
        """
        companion = Companion(
            name="Battle Buddy",
            description="A combat companion",
            recruited_at="Arena",
            bond_points=50,  # TRUSTED = +5%
        )

        combat = CombatEncounter(player, enemy=weak_enemy, companions=[companion])
        combat.start()

        status = combat.get_status()
        assert "Companion Bonus" in status
        assert "+5% attack" in status

    def test_combat_status_hides_bonus_when_zero(self, player, weak_enemy):
        """Combat status should not display companion bonus if it's 0.

        STRANGER companions give no bonus, so it shouldn't be shown.
        """
        companion = Companion(
            name="New Friend",
            description="A new companion",
            recruited_at="Town",
            bond_points=10,  # STRANGER = 0%
        )

        combat = CombatEncounter(player, enemy=weak_enemy, companions=[companion])
        combat.start()

        status = combat.get_status()
        assert "Companion Bonus" not in status

    def test_empty_companions_list_handled_correctly(self, player, weak_enemy):
        """Passing an empty companions list should work correctly."""
        combat = CombatEncounter(player, enemy=weak_enemy, companions=[])

        # Attack should deal base damage
        combat.player_attack()
        expected_health = 100 - 10
        assert weak_enemy.health == expected_health

        # Status should not show companion bonus
        status = combat.get_status()
        assert "Companion Bonus" not in status
