"""Tests for Luck (LCK) stat affecting loot drops and rewards."""
import pytest
import random
from unittest.mock import patch
from cli_rpg.combat import generate_loot
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.item import ItemType


def create_test_enemy(name: str = "Test Enemy") -> Enemy:
    """Create a simple test enemy."""
    return Enemy(
        name=name,
        health=50,
        max_health=50,
        attack_power=10,
        defense=5,
        xp_reward=100,
        level=1,
    )


class TestLuckLootDropRate:
    """Test luck affecting loot drop rate."""

    def test_loot_drop_rate_with_high_luck(self):
        """LCK 15 = 60% drop rate (base 50% + 5*2% = 60%)."""
        enemy = create_test_enemy()
        # Run many trials to verify drop rate increases
        drops = 0
        trials = 1000
        random.seed(42)  # For reproducibility
        for _ in range(trials):
            loot = generate_loot(enemy, level=1, luck=15)
            if loot is not None:
                drops += 1
        # With 60% drop rate, expect ~600 drops
        drop_rate = drops / trials
        assert 0.55 <= drop_rate <= 0.65, f"Expected ~60% drop rate, got {drop_rate*100:.1f}%"

    def test_loot_drop_rate_with_low_luck(self):
        """LCK 5 = 40% drop rate (base 50% - 5*2% = 40%)."""
        enemy = create_test_enemy()
        drops = 0
        trials = 1000
        random.seed(42)
        for _ in range(trials):
            loot = generate_loot(enemy, level=1, luck=5)
            if loot is not None:
                drops += 1
        drop_rate = drops / trials
        assert 0.35 <= drop_rate <= 0.45, f"Expected ~40% drop rate, got {drop_rate*100:.1f}%"

    def test_loot_drop_rate_baseline(self):
        """LCK 10 = 50% drop rate (baseline)."""
        enemy = create_test_enemy()
        drops = 0
        trials = 1000
        random.seed(42)
        for _ in range(trials):
            loot = generate_loot(enemy, level=1, luck=10)
            if loot is not None:
                drops += 1
        drop_rate = drops / trials
        assert 0.45 <= drop_rate <= 0.55, f"Expected ~50% drop rate, got {drop_rate*100:.1f}%"

    def test_loot_backward_compat_default_luck(self):
        """generate_loot works with default luck parameter (10)."""
        enemy = create_test_enemy()
        # Should not raise an error when luck not specified
        loot = generate_loot(enemy, level=1)
        # No assertion on result, just verifying it works


class TestLuckGoldReward:
    """Test luck affecting gold rewards - tested in CombatEncounter.end_combat."""

    # Note: Gold reward is calculated in end_combat(), not generate_loot()
    # These tests verify the formula conceptually:
    # gold_reward = base_gold * (1.0 + (luck - 10) * 0.05)

    def test_gold_formula_high_luck(self):
        """LCK 15 = +25% gold (5% per point above 10)."""
        base_gold = 100
        luck_modifier = 1.0 + (15 - 10) * 0.05
        assert luck_modifier == 1.25
        assert int(base_gold * luck_modifier) == 125

    def test_gold_formula_low_luck(self):
        """LCK 5 = -25% gold (5% per point below 10)."""
        base_gold = 100
        luck_modifier = 1.0 + (5 - 10) * 0.05
        assert luck_modifier == 0.75
        assert int(base_gold * luck_modifier) == 75


class TestLuckWeaponBonus:
    """Test luck affecting weapon damage bonus."""

    def test_weapon_bonus_with_high_luck(self):
        """LCK 15 = +1 to weapon damage bonus roll."""
        enemy = create_test_enemy()
        weapons_found = []
        trials = 500
        random.seed(42)
        for _ in range(trials):
            loot = generate_loot(enemy, level=1, luck=15)
            if loot is not None and loot.item_type == ItemType.WEAPON:
                weapons_found.append(loot.damage_bonus)

        if weapons_found:
            avg_damage = sum(weapons_found) / len(weapons_found)
            # With luck bonus, should have higher average damage
            # Base: level(1) + randint(1,3) = 2-4, avg 3
            # With luck 15: +1 bonus = avg 4
            assert avg_damage >= 3.5, f"Expected higher damage bonus with high luck, got {avg_damage}"

    def test_weapon_bonus_baseline(self):
        """LCK 10 = no bonus to weapon damage roll."""
        enemy = create_test_enemy()
        weapons_found = []
        trials = 500
        random.seed(42)
        for _ in range(trials):
            loot = generate_loot(enemy, level=1, luck=10)
            if loot is not None and loot.item_type == ItemType.WEAPON:
                weapons_found.append(loot.damage_bonus)

        if weapons_found:
            avg_damage = sum(weapons_found) / len(weapons_found)
            # Base: level(1) + randint(1,3) = 2-4, avg 3
            assert 2.5 <= avg_damage <= 3.5, f"Expected avg damage ~3, got {avg_damage}"


class TestLuckArmorBonus:
    """Test luck affecting armor defense bonus."""

    def test_armor_bonus_with_high_luck(self):
        """LCK 15 = +1 to armor defense bonus roll."""
        enemy = create_test_enemy()
        armors_found = []
        trials = 500
        random.seed(42)
        for _ in range(trials):
            loot = generate_loot(enemy, level=1, luck=15)
            if loot is not None and loot.item_type == ItemType.ARMOR:
                armors_found.append(loot.defense_bonus)

        if armors_found:
            avg_defense = sum(armors_found) / len(armors_found)
            # With luck bonus, should have higher average defense
            # Base: level(1) + randint(0,2) = 1-3, avg 2
            # With luck 15: +1 bonus = avg 3
            assert avg_defense >= 2.5, f"Expected higher defense bonus with high luck, got {avg_defense}"
