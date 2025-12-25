"""Tests for the dream system.

Dreams are triggered during rest and add atmospheric storytelling.
High dread (50%+) triggers nightmares instead of normal dreams.
"""

import random
from unittest.mock import patch

import pytest

from cli_rpg.dreams import (
    DREAM_CHANCE,
    NIGHTMARE_DREAD_THRESHOLD,
    PROPHETIC_DREAMS,
    ATMOSPHERIC_DREAMS,
    NIGHTMARES,
    CHOICE_DREAMS,
    maybe_trigger_dream,
    format_dream,
)


class TestDreamConstants:
    """Tests for dream system constants.

    Spec: Dream constants exist with correct values
    """

    def test_dream_chance_is_25_percent(self):
        """Spec: DREAM_CHANCE is 0.25 (25%)."""
        assert DREAM_CHANCE == 0.25

    def test_nightmare_dread_threshold_is_50(self):
        """Spec: NIGHTMARE_DREAD_THRESHOLD is 50."""
        assert NIGHTMARE_DREAD_THRESHOLD == 50


class TestMaybeTriggerDream:
    """Tests for maybe_trigger_dream() function.

    Spec: Returns formatted dream text or None based on 25% trigger rate
    """

    def test_returns_string_or_none(self):
        """Spec: maybe_trigger_dream returns either a string or None."""
        for _ in range(20):
            result = maybe_trigger_dream()
            assert result is None or isinstance(result, str)

    def test_dream_chance_is_25_percent(self):
        """Spec: ~25% trigger rate (statistical test).

        We run 1000 trials and check that trigger rate is roughly 25%.
        """
        random.seed(42)

        triggers = 0
        trials = 1000
        for _ in range(trials):
            result = maybe_trigger_dream()
            if result is not None:
                triggers += 1

        # Allow 15-35% range for statistical variance
        trigger_rate = triggers / trials
        assert 0.15 <= trigger_rate <= 0.35, f"Trigger rate {trigger_rate} outside expected range"

    def test_nightmare_at_high_dread(self):
        """Spec: High dread (50%+) uses NIGHTMARES pool."""
        # Force dream to always trigger
        with patch("cli_rpg.dreams.random.random", return_value=0.1):
            for _ in range(10):
                result = maybe_trigger_dream(dread=50)
                assert result is not None
                # Check nightmare text is in the result
                assert any(nightmare in result for nightmare in NIGHTMARES)

    def test_normal_dream_at_low_dread(self):
        """Spec: Low dread (<50) uses normal dream pools."""
        # Force dream to always trigger
        with patch("cli_rpg.dreams.random.random", return_value=0.1):
            for _ in range(10):
                result = maybe_trigger_dream(dread=0)
                assert result is not None
                # Should be from prophetic or atmospheric pools (not nightmares)
                all_normal_dreams = PROPHETIC_DREAMS + ATMOSPHERIC_DREAMS
                assert any(dream in result for dream in all_normal_dreams)


class TestChoiceInfluencedDreams:
    """Tests for choice-based dream selection.

    Spec: Player choices influence dream content
    """

    def test_flee_choices_influence_dreams(self):
        """Spec: Multiple flee choices can trigger running dreams."""
        flee_choices = [{"choice_type": "combat_flee"} for _ in range(5)]

        # Force dream and choice dream trigger
        with patch("cli_rpg.dreams.random.random", side_effect=[0.1, 0.1]):
            result = maybe_trigger_dream(dread=0, choices=flee_choices)
            assert result is not None
            # Should be a flee-related dream
            assert any(dream in result for dream in CHOICE_DREAMS["combat_flee"])

    def test_kill_choices_influence_dreams(self):
        """Spec: Many kill choices can trigger combat dreams."""
        kill_choices = [{"choice_type": "combat_kill"} for _ in range(15)]

        # Force dream and choice dream trigger
        with patch("cli_rpg.dreams.random.random", side_effect=[0.1, 0.1]):
            result = maybe_trigger_dream(dread=0, choices=kill_choices)
            assert result is not None
            # Should be a kill-related dream
            assert any(dream in result for dream in CHOICE_DREAMS["combat_kill"])

    def test_normal_dream_without_enough_choices(self):
        """Spec: Not enough choices falls back to normal dreams."""
        few_choices = [{"choice_type": "combat_flee"} for _ in range(2)]  # Less than threshold

        # Force dream and choice dream check
        with patch("cli_rpg.dreams.random.random", side_effect=[0.1, 0.1]):
            result = maybe_trigger_dream(dread=0, choices=few_choices)
            assert result is not None
            # Should be from prophetic or atmospheric (not choice dreams)
            all_normal_dreams = PROPHETIC_DREAMS + ATMOSPHERIC_DREAMS
            assert any(dream in result for dream in all_normal_dreams)


class TestDreamCategories:
    """Tests for dream content pools.

    Spec: Different dream categories exist with content
    """

    def test_prophetic_dreams_exist(self):
        """Spec: PROPHETIC_DREAMS pool has content."""
        assert len(PROPHETIC_DREAMS) >= 3
        for dream in PROPHETIC_DREAMS:
            assert isinstance(dream, str)
            assert len(dream) > 10  # Meaningful content

    def test_atmospheric_dreams_exist(self):
        """Spec: ATMOSPHERIC_DREAMS pool has content."""
        assert len(ATMOSPHERIC_DREAMS) >= 3
        for dream in ATMOSPHERIC_DREAMS:
            assert isinstance(dream, str)
            assert len(dream) > 10

    def test_nightmares_exist(self):
        """Spec: NIGHTMARES pool has content."""
        assert len(NIGHTMARES) >= 3
        for nightmare in NIGHTMARES:
            assert isinstance(nightmare, str)
            assert len(nightmare) > 10

    def test_choice_dreams_exist(self):
        """Spec: CHOICE_DREAMS has flee and kill categories."""
        assert "combat_flee" in CHOICE_DREAMS
        assert "combat_kill" in CHOICE_DREAMS
        assert len(CHOICE_DREAMS["combat_flee"]) >= 1
        assert len(CHOICE_DREAMS["combat_kill"]) >= 1


class TestFormatDream:
    """Tests for dream formatting.

    Spec: Dreams have decorative borders and intro/outro
    """

    def test_format_dream_has_borders(self):
        """Spec: Formatted dream has decorative borders."""
        dream_text = "You dream of ancient secrets..."
        result = format_dream(dream_text)

        # Check for border characters
        assert "═" in result

    def test_format_dream_has_intro_outro(self):
        """Spec: Formatted dream has intro and outro text."""
        dream_text = "You dream of ancient secrets..."
        result = format_dream(dream_text)

        # Check for intro/outro (may have color codes)
        assert "uneasy sleep" in result or "drift" in result
        assert "wake" in result or "lingering" in result

    def test_format_dream_contains_content(self):
        """Spec: Formatted dream contains the dream text."""
        dream_text = "You dream of ancient secrets..."
        result = format_dream(dream_text)

        assert dream_text in result

    def test_format_dream_with_colors_disabled(self):
        """Spec: Format works when colors are disabled."""
        from cli_rpg import colors

        old_setting = colors._colors_enabled_override
        try:
            colors.set_colors_enabled(False)
            dream_text = "You dream of ancient secrets..."
            result = format_dream(dream_text)

            # Without colors, should still have structure
            assert "═" in result
            assert dream_text in result
            assert "sleep" in result.lower()
            assert "wake" in result.lower()
        finally:
            colors.set_colors_enabled(old_setting)


class TestDreamIntegration:
    """Integration tests for dream system with rest command.

    Spec: Dreams can trigger when player rests
    """

    def _create_test_character(self):
        """Helper to create a test character."""
        from cli_rpg.models.character import Character
        return Character(name="TestHero", strength=10, dexterity=10, intelligence=10)

    def _create_test_world(self):
        """Helper to create a minimal test world."""
        from cli_rpg.models.location import Location
        return {
            "Town Square": Location(
                name="Town Square",
                description="A town center.",
                connections={},
                coordinates=(0, 0),
                category="town"
            )
        }

    def test_rest_can_trigger_dream(self):
        """Spec: Rest command can display a dream when triggered."""
        from cli_rpg.game_state import GameState
        from cli_rpg.main import handle_exploration_command

        char = self._create_test_character()
        char.health = char.max_health // 2  # Ensure rest does something
        world = self._create_test_world()
        gs = GameState(char, world)

        # Force dream to trigger
        with patch("cli_rpg.dreams.random.random", return_value=0.1):
            success, message = handle_exploration_command(gs, "rest", [])

        assert success
        # Dream should be in the output
        assert "═" in message or "sleep" in message.lower()

    def test_rest_without_dream(self):
        """Spec: Rest works normally when no dream triggers."""
        from cli_rpg.game_state import GameState
        from cli_rpg.main import handle_exploration_command

        char = self._create_test_character()
        char.health = char.max_health // 2
        world = self._create_test_world()
        gs = GameState(char, world)

        # Force dream to NOT trigger
        with patch("cli_rpg.dreams.random.random", return_value=0.9):
            success, message = handle_exploration_command(gs, "rest", [])

        assert success
        # Basic rest message should be there
        assert "rest" in message.lower() or "recover" in message.lower()
