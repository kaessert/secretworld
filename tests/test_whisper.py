"""Tests for the whisper system.

The whisper system displays ambient narrative hints when entering locations.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.whisper import (
    CATEGORY_WHISPERS,
    PLAYER_HISTORY_WHISPERS,
    PLAYER_HISTORY_CHANCE,
    WHISPER_CHANCE,
    WHISPER_TYPEWRITER_DELAY,
    WhisperService,
    display_whisper,
    format_whisper,
)


class TestWhisperServiceCreation:
    """Tests for WhisperService initialization.

    Spec: Service initializes with optional AI
    """

    def test_whisper_service_creation_without_ai(self):
        """Spec: Service can be created without an AI service."""
        service = WhisperService()
        assert service.ai_service is None

    def test_whisper_service_creation_with_ai(self):
        """Spec: Service can be created with an AI service."""
        mock_ai = MagicMock()
        service = WhisperService(ai_service=mock_ai)
        assert service.ai_service is mock_ai


class TestGetWhisper:
    """Tests for get_whisper() method.

    Spec: Returns whisper text or None based on 30% trigger rate
    """

    def test_get_whisper_returns_string_or_none(self):
        """Spec: get_whisper returns either a string whisper or None."""
        service = WhisperService()
        # Run multiple times to check return types
        for _ in range(20):
            result = service.get_whisper("town")
            assert result is None or isinstance(result, str)

    def test_whisper_chance_respected(self):
        """Spec: ~30% trigger rate (statistical test).

        We run 1000 trials and check that trigger rate is roughly 30%.
        With binomial distribution, expect ~300 +/- ~50 triggers.
        """
        service = WhisperService()
        random.seed(42)  # For reproducibility

        triggers = 0
        trials = 1000
        for _ in range(trials):
            result = service.get_whisper("town")
            if result is not None:
                triggers += 1

        # Allow 15-45% range (being generous for statistical variance)
        trigger_rate = triggers / trials
        assert 0.15 <= trigger_rate <= 0.45, f"Trigger rate {trigger_rate} outside expected range"


class TestCategoryWhispers:
    """Tests for template whispers based on location category.

    Spec: Different categories get thematic whispers
    """

    def test_town_whispers_thematic(self):
        """Spec: Town locations get town-related whispers."""
        service = WhisperService()
        # Force whisper to always trigger for this test
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            for _ in range(10):
                result = service.get_whisper("town")
                assert result is not None
                # Check that it's from the town category
                assert result in CATEGORY_WHISPERS["town"]

    def test_dungeon_whispers_thematic(self):
        """Spec: Dungeon locations get dark/dangerous whispers."""
        service = WhisperService()
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            for _ in range(10):
                result = service.get_whisper("dungeon")
                assert result is not None
                assert result in CATEGORY_WHISPERS["dungeon"]

    def test_wilderness_whispers_thematic(self):
        """Spec: Wilderness gets nature-themed whispers."""
        service = WhisperService()
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            for _ in range(10):
                result = service.get_whisper("wilderness")
                assert result is not None
                assert result in CATEGORY_WHISPERS["wilderness"]

    def test_fallback_whisper_for_unknown_category(self):
        """Spec: Generic whisper for unmapped categories."""
        service = WhisperService()
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            for _ in range(10):
                result = service.get_whisper("unknown_category_xyz")
                assert result is not None
                assert result in CATEGORY_WHISPERS["default"]

    def test_fallback_whisper_for_none_category(self):
        """Spec: Generic whisper when category is None."""
        service = WhisperService()
        with patch("cli_rpg.whisper.random.random", return_value=0.1):
            for _ in range(10):
                result = service.get_whisper(None)
                assert result is not None
                assert result in CATEGORY_WHISPERS["default"]


class TestPlayerHistoryWhispers:
    """Tests for player-history-aware whispers.

    Spec: Whispers can reference player's stats or past actions
    """

    def _create_character(self, **kwargs) -> Character:
        """Helper to create a test character with specific attributes."""
        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        for key, value in kwargs.items():
            setattr(char, key, value)
        return char

    def test_high_gold_whisper(self):
        """Spec: Player with 500+ gold gets wealth-related whispers."""
        service = WhisperService()
        char = self._create_character(gold=500)

        # Force whisper trigger and player history whisper trigger
        with patch("cli_rpg.whisper.random.random", side_effect=[0.1, 0.01]):
            result = service.get_whisper("town", character=char)
            assert result is not None
            assert result in PLAYER_HISTORY_WHISPERS["high_gold"]

    def test_high_level_whisper(self):
        """Spec: Level 5+ player gets recognition whispers."""
        service = WhisperService()
        char = self._create_character(level=5, gold=0)  # No gold to avoid gold whisper

        with patch("cli_rpg.whisper.random.random", side_effect=[0.1, 0.01]):
            result = service.get_whisper("town", character=char)
            assert result is not None
            assert result in PLAYER_HISTORY_WHISPERS["high_level"]

    def test_low_health_whisper(self):
        """Spec: Player below 30% health gets warning whispers."""
        service = WhisperService()
        char = self._create_character(gold=0, level=1)
        # Set health to below 30% of max
        char.health = int(char.max_health * 0.2)

        with patch("cli_rpg.whisper.random.random", side_effect=[0.1, 0.01]):
            result = service.get_whisper("town", character=char)
            assert result is not None
            assert result in PLAYER_HISTORY_WHISPERS["low_health"]

    def test_many_kills_whisper(self):
        """Spec: Player with 10+ kills gets kill-related whispers."""
        service = WhisperService()
        char = self._create_character(gold=0, level=1)
        char.health = char.max_health  # Full health
        # Add bestiary entries with total 10+ kills
        char.bestiary = {
            "goblin": {"count": 5},
            "wolf": {"count": 6}
        }

        with patch("cli_rpg.whisper.random.random", side_effect=[0.1, 0.01]):
            result = service.get_whisper("town", character=char)
            assert result is not None
            assert result in PLAYER_HISTORY_WHISPERS["many_kills"]

    def test_player_history_whisper_probability(self):
        """Spec: History whispers are rarer (10% of whispers).

        When we force a whisper to always trigger, player history whispers
        should only appear ~10% of the time.
        """
        service = WhisperService()
        char = self._create_character(gold=500)  # Qualifies for gold whisper
        random.seed(42)

        history_count = 0
        total_whispers = 0
        trials = 1000

        for _ in range(trials):
            # Force whisper trigger
            with patch.object(
                random, "random", side_effect=[0.1, random.random()]
            ):
                result = service.get_whisper("town", character=char)
                if result is not None:
                    total_whispers += 1
                    if result in PLAYER_HISTORY_WHISPERS["high_gold"]:
                        history_count += 1

        # History whispers should be about 10% of all whispers
        if total_whispers > 0:
            history_rate = history_count / total_whispers
            # Allow 2-25% range for statistical variance
            assert 0.02 <= history_rate <= 0.25, f"History rate {history_rate} outside expected range"


class TestFormatWhisper:
    """Tests for whisper formatting.

    Spec: Output has correct style/prefix
    """

    def test_whisper_formatted_correctly(self):
        """Spec: Whisper has [Whisper]: prefix and quotes."""
        whisper_text = "The stones here remember ancient sorrows..."
        result = format_whisper(whisper_text)

        # Check the format (colors may be stripped in some contexts)
        assert '[Whisper]: "' in result
        assert whisper_text in result
        assert result.endswith('"') or "\x1b[0m" in result  # May have color reset

    def test_format_whisper_with_colors_disabled(self):
        """Spec: Format works when colors are disabled."""
        from cli_rpg import colors

        old_setting = colors._colors_enabled_override
        try:
            colors.set_colors_enabled(False)
            whisper_text = "A strange feeling washes over you..."
            result = format_whisper(whisper_text)

            # Without colors, should be plain text
            assert result == f'[Whisper]: "{whisper_text}"'
        finally:
            colors.set_colors_enabled(old_setting)


class TestWhisperIntegration:
    """Integration tests for whisper system with game state.

    These tests verify the whisper system works correctly when integrated
    with the game loop.
    """

    def _create_test_world(self) -> dict[str, Location]:
        """Create a minimal test world."""
        town = Location(
            name="Town Square",
            description="A bustling town center.",
            connections={"north": "Forest Path"},
            coordinates=(0, 0),
            category="town"
        )
        forest = Location(
            name="Forest Path",
            description="A winding path through the woods.",
            connections={"south": "Town Square"},
            coordinates=(0, 1),
            category="forest"
        )
        return {"Town Square": town, "Forest Path": forest}

    def test_whisper_service_initialized_in_game_state(self):
        """Spec: GameState has a whisper service."""
        from cli_rpg.game_state import GameState

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        world = self._create_test_world()
        gs = GameState(char, world)

        assert hasattr(gs, "whisper_service")
        assert isinstance(gs.whisper_service, WhisperService)

    def test_whisper_displayed_on_location_entry(self):
        """Spec: Whisper triggers display_whisper after move (when triggered)."""
        from cli_rpg.game_state import GameState

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        world = self._create_test_world()
        gs = GameState(char, world)

        # Mock whisper to always return a value and patch display_whisper
        with patch.object(gs.whisper_service, "get_whisper", return_value="Test whisper"):
            with patch("cli_rpg.game_state.display_whisper") as mock_display:
                # Also need to prevent combat encounters
                with patch.object(gs, "trigger_encounter", return_value=None):
                    success, message = gs.move("north")

                assert success
                # Verify display_whisper was called with the whisper text
                mock_display.assert_called_once_with("Test whisper")

    def test_no_whisper_when_none_returned(self):
        """Spec: No whisper displayed when get_whisper returns None."""
        from cli_rpg.game_state import GameState

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        world = self._create_test_world()
        gs = GameState(char, world)

        with patch.object(gs.whisper_service, "get_whisper", return_value=None):
            with patch("cli_rpg.game_state.display_whisper") as mock_display:
                with patch.object(gs, "trigger_encounter", return_value=None):
                    success, message = gs.move("north")

                assert success
                # Verify display_whisper was NOT called
                mock_display.assert_not_called()

    def test_no_whisper_during_combat(self):
        """Spec: Whispers disabled during combat.

        The whisper system should not trigger when in combat.
        """
        from cli_rpg.game_state import GameState
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        world = self._create_test_world()
        gs = GameState(char, world)

        # Put player in combat (must call start() to set is_active=True)
        enemy = Enemy(
            name="Goblin", health=10, max_health=10, attack_power=5, defense=2, xp_reward=10
        )
        gs.current_combat = CombatEncounter(char, enemies=[enemy])
        gs.current_combat.start()  # Activates combat so is_in_combat() returns True

        # During combat, move should be blocked (combat blocks movement)
        # So whispers won't appear since move fails
        # This test verifies the system doesn't crash when combat is active
        with patch("cli_rpg.game_state.display_whisper") as mock_display:
            success, message = gs.move("north")
            # Movement during combat may be blocked by game logic
            # The key is that display_whisper should not be called during combat
            mock_display.assert_not_called()


class TestDisplayWhisper:
    """Tests for display_whisper function with typewriter effect.

    Spec: Whispers display with typewriter effect for enhanced atmosphere
    """

    def test_display_whisper_calls_typewriter_print(self):
        """Spec: display_whisper uses typewriter_print for text output."""
        whisper_text = "The darkness whispers secrets..."

        with patch("cli_rpg.text_effects.typewriter_print") as mock_typewriter:
            display_whisper(whisper_text)

            mock_typewriter.assert_called_once()
            # The call should include the formatted whisper text
            call_args = mock_typewriter.call_args
            assert "[Whisper]:" in call_args[0][0]
            assert whisper_text in call_args[0][0]

    def test_display_whisper_uses_correct_delay(self):
        """Spec: display_whisper uses WHISPER_TYPEWRITER_DELAY constant."""
        whisper_text = "Something stirs in the shadows..."

        with patch("cli_rpg.text_effects.typewriter_print") as mock_typewriter:
            display_whisper(whisper_text)

            mock_typewriter.assert_called_once()
            call_kwargs = mock_typewriter.call_args[1]
            assert call_kwargs.get("delay") == WHISPER_TYPEWRITER_DELAY

    def test_whisper_typewriter_delay_value(self):
        """Spec: WHISPER_TYPEWRITER_DELAY is 0.03 (slightly faster than dreams)."""
        assert WHISPER_TYPEWRITER_DELAY == 0.03


class TestAIWhisperGeneration:
    """Tests for AI-generated whispers.

    Spec: AI can generate dynamic, context-aware atmospheric whispers
    """

    def test_generate_whisper_exists_in_ai_service(self):
        """Spec: AIService has generate_whisper method."""
        from cli_rpg.ai_service import AIService
        assert hasattr(AIService, 'generate_whisper')
        assert callable(getattr(AIService, 'generate_whisper'))

    def test_whisper_generation_prompt_in_config(self):
        """Spec: AIConfig has whisper_generation_prompt field."""
        from cli_rpg.ai_config import AIConfig, DEFAULT_WHISPER_GENERATION_PROMPT

        # Check default prompt exists
        assert DEFAULT_WHISPER_GENERATION_PROMPT is not None
        assert len(DEFAULT_WHISPER_GENERATION_PROMPT) > 50

        # Check config has the field
        config = AIConfig(api_key="test-key")
        assert hasattr(config, 'whisper_generation_prompt')
        assert config.whisper_generation_prompt == DEFAULT_WHISPER_GENERATION_PROMPT

    def test_get_whisper_uses_ai_when_available(self):
        """Spec: When ai_service is available, attempts AI generation."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Create whisper service with AI
        service = WhisperService(ai_service=ai_service)

        # Mock generate_whisper to return a whisper
        generated_whisper = "Ancient secrets lurk in the shadows..."
        with patch.object(ai_service, 'generate_whisper', return_value=generated_whisper):
            with patch("cli_rpg.whisper.random.random", return_value=0.1):  # Force trigger
                result = service.get_whisper("dungeon", theme="dark fantasy")

                # Result should be the AI-generated whisper
                assert result == generated_whisper

    def test_get_whisper_falls_back_on_ai_failure(self):
        """Spec: Falls back to template when AI raises exception."""
        from cli_rpg.ai_service import AIService, AIGenerationError
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Create whisper service with AI
        service = WhisperService(ai_service=ai_service)

        # Mock generate_whisper to raise an error
        with patch.object(ai_service, 'generate_whisper', side_effect=AIGenerationError("Test error")):
            with patch("cli_rpg.whisper.random.random", return_value=0.1):  # Force trigger
                result = service.get_whisper("dungeon", theme="fantasy")

                # Should still return a whisper (from templates)
                assert result is not None
                # Should be from template pools
                assert result in CATEGORY_WHISPERS["dungeon"]

    def test_ai_whisper_content_is_validated(self):
        """Spec: AI-generated whisper text is validated (length 10-100 chars)."""
        from cli_rpg.ai_service import AIService, AIGenerationError
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Test too short (should raise error)
        with patch.object(ai_service, '_call_llm', return_value="Short"):
            with pytest.raises(AIGenerationError):
                ai_service.generate_whisper(theme="fantasy", location_category="dungeon")

    def test_ai_whisper_truncated_if_too_long(self):
        """Spec: AI-generated whisper is truncated if over 100 chars."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Generate a response that's too long (150 chars)
        long_response = "A" * 150
        with patch.object(ai_service, '_call_llm', return_value=long_response):
            result = ai_service.generate_whisper(theme="fantasy", location_category="dungeon")
            # Should be truncated to 100 chars with ellipsis
            assert len(result) <= 100
            assert result.endswith("...")

    def test_ai_whisper_prompt_includes_context(self):
        """Spec: AI whisper prompt includes theme and category context."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(api_key="test-key", enable_caching=False)
        ai_service = AIService(config)

        # Mock _call_llm to capture the prompt
        valid_whisper = "The darkness here whispers ancient truths..."
        with patch.object(ai_service, '_call_llm', return_value=valid_whisper) as mock_llm:
            ai_service.generate_whisper(
                theme="dark fantasy",
                location_category="cave"
            )

            # Check the prompt includes context
            prompt = mock_llm.call_args[0][0]
            assert "dark fantasy" in prompt
            assert "cave" in prompt

    def test_ai_config_whisper_prompt_serialization(self):
        """Spec: whisper_generation_prompt is serialized in to_dict/from_dict."""
        from cli_rpg.ai_config import AIConfig, DEFAULT_WHISPER_GENERATION_PROMPT

        config = AIConfig(api_key="test-key")

        # Check to_dict includes whisper_generation_prompt
        config_dict = config.to_dict()
        assert "whisper_generation_prompt" in config_dict
        assert config_dict["whisper_generation_prompt"] == DEFAULT_WHISPER_GENERATION_PROMPT

        # Check from_dict restores it
        restored_config = AIConfig.from_dict(config_dict)
        assert restored_config.whisper_generation_prompt == DEFAULT_WHISPER_GENERATION_PROMPT
