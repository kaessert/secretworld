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
    WhisperService,
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
        """Spec: Whisper appears after move (when triggered)."""
        from cli_rpg.game_state import GameState

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        world = self._create_test_world()
        gs = GameState(char, world)

        # Mock whisper to always return a value
        with patch.object(gs.whisper_service, "get_whisper", return_value="Test whisper"):
            # Also need to prevent combat encounters
            with patch.object(gs, "trigger_encounter", return_value=None):
                success, message = gs.move("north")

        assert success
        assert "[Whisper]:" in message
        assert "Test whisper" in message

    def test_no_whisper_when_none_returned(self):
        """Spec: No whisper displayed when get_whisper returns None."""
        from cli_rpg.game_state import GameState

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        world = self._create_test_world()
        gs = GameState(char, world)

        with patch.object(gs.whisper_service, "get_whisper", return_value=None):
            with patch.object(gs, "trigger_encounter", return_value=None):
                success, message = gs.move("north")

        assert success
        assert "[Whisper]:" not in message

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

        # Put player in combat
        enemy = Enemy(
            name="Goblin", health=10, max_health=10, attack_power=5, defense=2, xp_reward=10
        )
        gs.current_combat = CombatEncounter(char, enemies=[enemy])

        # During combat, move should be blocked (combat blocks movement)
        # So whispers won't appear since move fails
        # This test verifies the system doesn't crash when combat is active
        success, message = gs.move("north")
        # Movement during combat may be blocked by game logic
        # The key is that no whisper appears
        if "[Whisper]:" in message:
            # Whispers should not appear during combat
            pytest.fail("Whisper appeared during combat")
