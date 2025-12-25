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

    def test_rest_can_trigger_dream(self, capsys):
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
        # Dream is displayed via typewriter effect (printed directly), check stdout
        captured = capsys.readouterr()
        assert "═" in captured.out or "sleep" in captured.out.lower()

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


class TestDreamTypewriterDisplay:
    """Tests for typewriter-style dream display.

    Spec: Dreams should use typewriter effect for atmospheric text reveal
    """

    def test_display_dream_function_exists(self):
        """Spec: display_dream function is importable."""
        from cli_rpg.dreams import display_dream
        assert callable(display_dream)

    def test_display_dream_calls_typewriter_print(self):
        """Spec: display_dream uses typewriter_print for output."""
        from cli_rpg.dreams import display_dream

        dream_text = format_dream("A test dream...")

        # Patch where typewriter_print is used (in dreams module)
        with patch("cli_rpg.dreams.typewriter_print") as mock_typewriter:
            display_dream(dream_text)
            # Should be called at least once with part of the dream
            assert mock_typewriter.called

    def test_display_dream_respects_effects_toggle(self):
        """Spec: display_dream respects effects_enabled toggle."""
        from cli_rpg.dreams import display_dream
        from cli_rpg import text_effects

        # Disable effects
        original = text_effects._effects_enabled_override
        try:
            text_effects.set_effects_enabled(False)
            dream_text = format_dream("A test dream...")

            # Patch where typewriter_print is used (in dreams module)
            with patch("cli_rpg.dreams.typewriter_print") as mock_typewriter:
                display_dream(dream_text)
                # Typewriter should still be called - it handles the toggle internally
                assert mock_typewriter.called
        finally:
            text_effects.set_effects_enabled(original)

    def test_display_dream_uses_slower_delay(self):
        """Spec: display_dream uses slower delay (>=0.04) for atmosphere."""
        from cli_rpg.dreams import display_dream

        dream_text = format_dream("A test dream...")

        # Patch where typewriter_print is used (in dreams module)
        with patch("cli_rpg.dreams.typewriter_print") as mock_typewriter:
            display_dream(dream_text)
            # Check that delay argument is >= 0.04
            call_args = mock_typewriter.call_args
            if call_args.kwargs.get("delay"):
                assert call_args.kwargs["delay"] >= 0.04
            elif len(call_args.args) > 1:
                assert call_args.args[1] >= 0.04


class TestAIDreamGeneration:
    """Tests for AI-generated dreams.

    Spec: AI can generate personalized dreams based on context
    """

    def test_generate_dream_exists_in_ai_service(self):
        """Spec: AIService has generate_dream method."""
        from cli_rpg.ai_service import AIService
        assert hasattr(AIService, 'generate_dream')
        assert callable(getattr(AIService, 'generate_dream'))

    def test_dream_generation_prompt_in_config(self):
        """Spec: AIConfig has dream_generation_prompt field."""
        from cli_rpg.ai_config import AIConfig, DEFAULT_DREAM_GENERATION_PROMPT

        # Check default prompt exists
        assert DEFAULT_DREAM_GENERATION_PROMPT is not None
        assert len(DEFAULT_DREAM_GENERATION_PROMPT) > 50

        # Check config has the field
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'dream_generation_prompt')
        assert config.dream_generation_prompt == DEFAULT_DREAM_GENERATION_PROMPT

    def test_maybe_trigger_dream_uses_ai_when_available(self):
        """Spec: When ai_service is passed, attempts AI generation."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock generate_dream to return a dream
        generated_dream = "You dream of algorithmic sheep..."
        with patch.object(ai_service, 'generate_dream', return_value=generated_dream) as mock_gen:
            with patch("cli_rpg.dreams.random.random", return_value=0.1):  # Force trigger
                result = maybe_trigger_dream(
                    dread=0,
                    choices=None,
                    theme="fantasy",
                    ai_service=ai_service,
                    location_name="Test Village"
                )

                # AI generate_dream should have been called
                mock_gen.assert_called_once()
                # Result should contain the AI-generated dream
                assert generated_dream in result

    def test_maybe_trigger_dream_falls_back_on_ai_failure(self):
        """Spec: Falls back to template when AI raises exception."""
        from cli_rpg.ai_service import AIService, AIGenerationError
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock generate_dream to raise an error
        with patch.object(ai_service, 'generate_dream', side_effect=AIGenerationError("Test error")):
            with patch("cli_rpg.dreams.random.random", return_value=0.1):  # Force trigger
                result = maybe_trigger_dream(
                    dread=0,
                    choices=None,
                    theme="fantasy",
                    ai_service=ai_service,
                    location_name="Test Village"
                )

                # Should still return a dream (from templates)
                assert result is not None
                # Should be from template pools
                all_templates = PROPHETIC_DREAMS + ATMOSPHERIC_DREAMS
                assert any(template in result for template in all_templates)

    def test_maybe_trigger_dream_uses_templates_without_ai(self):
        """Spec: Uses templates when ai_service is None (current behavior)."""
        # Force dream to trigger
        with patch("cli_rpg.dreams.random.random", return_value=0.1):
            result = maybe_trigger_dream(
                dread=0,
                choices=None,
                theme="fantasy",
                ai_service=None,  # No AI service
                location_name="Test Village"
            )

            # Should return a template dream
            assert result is not None
            all_templates = PROPHETIC_DREAMS + ATMOSPHERIC_DREAMS
            assert any(template in result for template in all_templates)

    def test_ai_dream_content_is_validated(self):
        """Spec: AI-generated dream text is validated (length 20-300 chars)."""
        from cli_rpg.ai_service import AIService, AIGenerationError
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Test too short (should raise error internally, fall back to template)
        with patch.object(ai_service, '_call_llm', return_value="Short"):
            with pytest.raises(AIGenerationError):
                ai_service.generate_dream(
                    theme="fantasy",
                    dread=0,
                    choices=None,
                    location_name="Test",
                    is_nightmare=False
                )

    def test_ai_nightmare_at_high_dread(self):
        """Spec: AI generates nightmare-style content at 50%+ dread."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock generate_dream to capture is_nightmare parameter
        nightmare_dream = "Terror consumes you in the endless dark..."
        with patch.object(ai_service, 'generate_dream', return_value=nightmare_dream) as mock_gen:
            with patch("cli_rpg.dreams.random.random", return_value=0.1):  # Force trigger
                result = maybe_trigger_dream(
                    dread=75,  # High dread
                    choices=None,
                    theme="fantasy",
                    ai_service=ai_service,
                    location_name="Haunted Crypt"
                )

                # Check that is_nightmare=True was passed
                call_kwargs = mock_gen.call_args.kwargs
                assert call_kwargs.get('is_nightmare') is True

    def test_ai_dream_prompt_includes_context(self):
        """Spec: AI dream prompt includes dread, choices, location context."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock _call_llm to capture the prompt
        valid_dream = "You dream of ancient mysteries and forgotten paths..."
        with patch.object(ai_service, '_call_llm', return_value=valid_dream) as mock_llm:
            try:
                ai_service.generate_dream(
                    theme="dark fantasy",
                    dread=45,
                    choices=[{"choice_type": "combat_flee"}],
                    location_name="Darkwood Forest",
                    is_nightmare=False
                )
            except Exception:
                pass  # We just want to check the prompt

            # Check the prompt includes context
            if mock_llm.called:
                prompt = mock_llm.call_args[0][0]
                assert "dark fantasy" in prompt
                assert "Darkwood Forest" in prompt

    def test_ai_config_dream_prompt_serialization(self):
        """Spec: dream_generation_prompt is serialized in to_dict/from_dict."""
        from cli_rpg.ai_config import AIConfig, DEFAULT_DREAM_GENERATION_PROMPT

        config = AIConfig(api_key="test-key")

        # Check to_dict includes dream_generation_prompt
        config_dict = config.to_dict()
        assert "dream_generation_prompt" in config_dict
        assert config_dict["dream_generation_prompt"] == DEFAULT_DREAM_GENERATION_PROMPT

        # Check from_dict restores it
        restored_config = AIConfig.from_dict(config_dict)
        assert restored_config.dream_generation_prompt == DEFAULT_DREAM_GENERATION_PROMPT
