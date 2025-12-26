"""Tests for Luck (LCK) stat affecting combat critical hit chance."""
import pytest
from cli_rpg.combat import calculate_crit_chance


class TestLuckCritChance:
    """Test luck affecting critical hit chance."""

    def test_crit_chance_with_high_luck(self):
        """High LCK increases crit chance above baseline."""
        # Baseline: LCK 10, stat 10
        baseline_crit = calculate_crit_chance(stat=10, luck=10)
        # High luck: LCK 15, stat 10
        high_luck_crit = calculate_crit_chance(stat=10, luck=15)
        assert high_luck_crit > baseline_crit

    def test_crit_chance_with_low_luck(self):
        """Low LCK decreases crit chance below baseline."""
        # Baseline: LCK 10, stat 10
        baseline_crit = calculate_crit_chance(stat=10, luck=10)
        # Low luck: LCK 5, stat 10
        low_luck_crit = calculate_crit_chance(stat=10, luck=5)
        assert low_luck_crit < baseline_crit

    def test_crit_chance_formula(self):
        """Test crit chance formula: ±0.5% per LCK from 10."""
        # Base formula: 5% + stat% + (luck-10)*0.5%
        # With stat=10, luck=10: 5 + 10 = 15%
        crit_at_baseline = calculate_crit_chance(stat=10, luck=10)
        assert crit_at_baseline == 0.15  # 15%

        # With stat=10, luck=15: 5 + 10 + 2.5 = 17.5%
        crit_at_high_luck = calculate_crit_chance(stat=10, luck=15)
        assert crit_at_high_luck == 0.175  # 17.5%

        # With stat=10, luck=5: 5 + 10 - 2.5 = 12.5%
        crit_at_low_luck = calculate_crit_chance(stat=10, luck=5)
        assert crit_at_low_luck == 0.125  # 12.5%

    def test_crit_chance_capped_at_max(self):
        """Crit chance is capped at 25% even with very high stats/luck."""
        # With very high stat and luck, should still cap at 25%
        crit = calculate_crit_chance(stat=20, luck=20)
        assert crit == 0.25  # 25% cap

    def test_crit_chance_minimum(self):
        """Crit chance has a minimum (doesn't go negative)."""
        # With very low stat and luck
        crit = calculate_crit_chance(stat=1, luck=1)
        # 5 + 1 + (1-10)*0.5 = 5 + 1 - 4.5 = 1.5%
        assert crit == 0.015  # 1.5%, not negative

    def test_crit_chance_backward_compat_default_luck(self):
        """calculate_crit_chance works with default luck parameter."""
        # Old behavior: stat=10 -> 5 + 10 = 15%
        # With default luck=10, should be same
        crit = calculate_crit_chance(stat=10)
        assert crit == 0.15
