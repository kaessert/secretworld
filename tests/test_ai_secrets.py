"""Tests for AI-generated hidden secrets in locations.

Tests the secret generation system that populates Location.hidden_secrets
during AI world generation and SubGrid creation.
"""

import pytest
from cli_rpg.ai_world import (
    SECRET_CATEGORIES,
    SECRET_TEMPLATES,
    _generate_secrets_for_location,
)


class TestSecretConstants:
    """Tests for secret generation constants."""

    def test_secret_categories_defined(self):
        """Verify SECRET_CATEGORIES constant exists and contains expected values."""
        # Spec: Categories that should have secrets
        assert isinstance(SECRET_CATEGORIES, frozenset)
        assert "dungeon" in SECRET_CATEGORIES
        assert "cave" in SECRET_CATEGORIES
        assert "ruins" in SECRET_CATEGORIES
        assert "temple" in SECRET_CATEGORIES
        assert "forest" in SECRET_CATEGORIES

    def test_secret_templates_for_each_category(self):
        """Each secret category should have templates defined."""
        # Spec: Each category in SECRET_CATEGORIES has entries in SECRET_TEMPLATES
        for category in SECRET_CATEGORIES:
            assert category in SECRET_TEMPLATES, f"Missing templates for {category}"
            assert len(SECRET_TEMPLATES[category]) >= 1, f"No templates for {category}"


class TestGenerateSecretsForLocation:
    """Tests for _generate_secrets_for_location function."""

    def test_generates_1_to_2_secrets(self):
        """Output count should be 1-2 secrets for valid categories."""
        # Spec: Generate 1-2 hidden secrets
        for category in SECRET_CATEGORIES:
            secrets = _generate_secrets_for_location(category, distance=0)
            assert 1 <= len(secrets) <= 2, f"Wrong count for {category}: {len(secrets)}"

    def test_secret_has_required_fields(self):
        """Each secret dict should have required schema fields."""
        # Spec: Schema matches Location.hidden_secrets
        secrets = _generate_secrets_for_location("dungeon", distance=0)
        for secret in secrets:
            assert "type" in secret
            assert "description" in secret
            assert "threshold" in secret
            assert "discovered" in secret
            assert secret["discovered"] is False

    def test_hidden_treasure_has_gold(self):
        """Hidden treasure secrets should have reward_gold field."""
        # Spec: hidden_treasure type includes reward_gold
        # Generate multiple times to ensure we get a treasure
        found_treasure = False
        for _ in range(20):  # Increase chances
            secrets = _generate_secrets_for_location("dungeon", distance=0)
            for secret in secrets:
                if secret["type"] == "hidden_treasure":
                    assert "reward_gold" in secret
                    assert secret["reward_gold"] > 0
                    found_treasure = True
                    break
            if found_treasure:
                break
        assert found_treasure, "No hidden_treasure generated after 20 attempts"

    def test_trap_has_damage(self):
        """Trap secrets should have trap_damage field."""
        # Spec: trap type includes trap_damage
        found_trap = False
        for _ in range(20):
            secrets = _generate_secrets_for_location("cave", distance=0)
            for secret in secrets:
                if secret["type"] == "trap":
                    assert "trap_damage" in secret
                    assert secret["trap_damage"] > 0
                    found_trap = True
                    break
            if found_trap:
                break
        assert found_trap, "No trap generated after 20 attempts"

    def test_hidden_door_has_direction(self):
        """Hidden door secrets should have exit_direction field."""
        # Spec: hidden_door type includes exit_direction
        found_door = False
        for _ in range(20):
            secrets = _generate_secrets_for_location("dungeon", distance=0)
            for secret in secrets:
                if secret["type"] == "hidden_door":
                    assert "exit_direction" in secret
                    assert secret["exit_direction"] in ("north", "south", "east", "west")
                    found_door = True
                    break
            if found_door:
                break
        assert found_door, "No hidden_door generated after 20 attempts"

    def test_distance_scales_threshold(self):
        """Higher distance should increase detection threshold."""
        # Spec: threshold = base_threshold + min(distance, 4)
        # Compare thresholds at distance 0 vs distance 4
        thresholds_d0 = []
        thresholds_d4 = []

        for _ in range(10):
            secrets_d0 = _generate_secrets_for_location("dungeon", distance=0)
            secrets_d4 = _generate_secrets_for_location("dungeon", distance=4)
            thresholds_d0.extend(s["threshold"] for s in secrets_d0)
            thresholds_d4.extend(s["threshold"] for s in secrets_d4)

        # Average threshold at distance 4 should be higher
        avg_d0 = sum(thresholds_d0) / len(thresholds_d0)
        avg_d4 = sum(thresholds_d4) / len(thresholds_d4)
        assert avg_d4 > avg_d0, f"Distance 4 threshold ({avg_d4}) should be higher than distance 0 ({avg_d0})"

    def test_non_secret_category_returns_empty(self):
        """Non-secret categories (town, village) should return empty list."""
        # Spec: town/village returns []
        for category in ["town", "village", "settlement", "city", "shop"]:
            secrets = _generate_secrets_for_location(category, distance=0)
            assert secrets == [], f"Expected empty for {category}, got {secrets}"

    def test_unknown_category_returns_empty(self):
        """Unknown categories should return empty list."""
        secrets = _generate_secrets_for_location("unknown_category", distance=0)
        assert secrets == []
