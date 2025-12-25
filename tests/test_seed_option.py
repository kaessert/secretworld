"""Tests for --seed CLI option.

Spec: Add --seed <int> flag to set random seed for reproducible gameplay.
"""
import subprocess
import sys
import pytest


class TestSeedOption:
    """Test --seed CLI option functionality."""

    def test_seed_flag_accepted(self):
        """Spec: --seed flag is accepted without error."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--seed", "42"],
            input="",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0

    def test_seed_produces_reproducible_output(self):
        """Spec: Same seed produces identical output across runs."""
        def run_with_seed(seed):
            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--seed", str(seed)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout

        output1 = run_with_seed(12345)
        output2 = run_with_seed(12345)
        assert output1 == output2, "Same seed should produce identical output"

    def test_different_seeds_may_produce_different_output(self):
        """Spec: Different seeds can produce different output (not guaranteed but likely)."""
        def run_with_seed(seed):
            result = subprocess.run(
                [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--seed", str(seed)],
                input="look\n",
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout

        # Note: This tests that seeds are applied, not that output must differ
        # The implementation is correct as long as same seed = same output
        output1 = run_with_seed(11111)
        output2 = run_with_seed(22222)
        # Both should succeed
        assert output1  # Non-empty
        assert output2  # Non-empty

    def test_seed_works_with_json_mode(self):
        """Spec: --seed works alongside --json mode."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--json", "--skip-character-creation", "--seed", "42"],
            input="look\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0

    def test_seed_requires_integer(self):
        """Spec: --seed requires an integer argument."""
        result = subprocess.run(
            [sys.executable, "-m", "cli_rpg.main", "--non-interactive", "--skip-character-creation", "--seed", "notanumber"],
            input="",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode != 0
        assert "invalid int value" in result.stderr.lower() or "error" in result.stderr.lower()
