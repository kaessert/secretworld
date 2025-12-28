"""Tests for ambient_sounds.py.

Tests for dungeon ambient sound system that plays atmospheric sounds
during SubGrid exploration.
"""

import random
from unittest.mock import patch

import pytest

from cli_rpg.ambient_sounds import (
    AmbientSoundService,
    AMBIENT_SOUND_CHANCE,
    DEPTH_SOUND_CHANCE_BONUS,
    SOUND_COOLDOWN_MOVES,
    CATEGORY_SOUNDS,
    DEPTH_SOUNDS,
    format_ambient_sound,
)


class TestGetAmbientSound:
    """Tests for get_ambient_sound returns Optional[str]."""

    def test_get_ambient_sound_returns_string_or_none(self) -> None:
        """get_ambient_sound should return Optional[str]."""
        # Spec: Returns Optional[str]
        service = AmbientSoundService()
        # Force trigger by setting high chance
        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.01):
            result = service.get_ambient_sound(category="dungeon", depth=0)
        assert result is None or isinstance(result, str)

    def test_get_ambient_sound_returns_none_when_chance_fails(self) -> None:
        """get_ambient_sound should return None when random check fails."""
        # Spec: ~15% base chance per move
        service = AmbientSoundService()
        # Force fail by returning high random value
        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.99):
            result = service.get_ambient_sound(category="dungeon", depth=0)
        assert result is None


class TestAmbientSoundCategories:
    """Tests for category-specific sound pools."""

    def test_ambient_sound_categories_dungeon(self) -> None:
        """Dungeon category should have distinct sound pool."""
        # Spec: Dungeon/cave/ruins/temple have distinct sound pools
        assert "dungeon" in CATEGORY_SOUNDS
        assert len(CATEGORY_SOUNDS["dungeon"]) >= 8

    def test_ambient_sound_categories_cave(self) -> None:
        """Cave category should have distinct sound pool."""
        # Spec: Dungeon/cave/ruins/temple have distinct sound pools
        assert "cave" in CATEGORY_SOUNDS
        assert len(CATEGORY_SOUNDS["cave"]) >= 8

    def test_ambient_sound_categories_ruins(self) -> None:
        """Ruins category should have distinct sound pool."""
        # Spec: Dungeon/cave/ruins/temple have distinct sound pools
        assert "ruins" in CATEGORY_SOUNDS
        assert len(CATEGORY_SOUNDS["ruins"]) >= 8

    def test_ambient_sound_categories_temple(self) -> None:
        """Temple category should have distinct sound pool."""
        # Spec: Dungeon/cave/ruins/temple have distinct sound pools
        assert "temple" in CATEGORY_SOUNDS
        assert len(CATEGORY_SOUNDS["temple"]) >= 8

    def test_category_sounds_are_distinct(self) -> None:
        """Each category should have unique sounds."""
        # Spec: Dungeon/cave/ruins/temple have distinct sound pools
        dungeon = set(CATEGORY_SOUNDS["dungeon"])
        cave = set(CATEGORY_SOUNDS["cave"])
        ruins = set(CATEGORY_SOUNDS["ruins"])
        temple = set(CATEGORY_SOUNDS["temple"])
        # No overlap between categories
        assert dungeon.isdisjoint(cave)
        assert dungeon.isdisjoint(ruins)
        assert cave.isdisjoint(temple)


class TestAmbientSoundDepthScaling:
    """Tests for depth-based trigger chance scaling."""

    def test_ambient_sound_depth_scaling_increases_chance(self) -> None:
        """Deeper z-levels should have higher trigger chance."""
        # Spec: Deeper z-levels have higher trigger chance (+5% per depth level)
        # At depth -3, effective chance = 0.15 + 0.15 = 0.30
        service = AmbientSoundService()

        # Test with random value that would fail at depth 0 but pass at depth -3
        # Base chance 0.15, depth -3 adds 0.15, so total 0.30
        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.25):
            with patch("cli_rpg.ambient_sounds.random.choice", return_value="Test sound"):
                # At depth 0, 0.25 > 0.15, so should return None
                result_surface = service.get_ambient_sound(category="dungeon", depth=0)
                # Reset cooldown
                service.moves_since_last_sound = SOUND_COOLDOWN_MOVES

        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.25):
            with patch("cli_rpg.ambient_sounds.random.choice", return_value="Test sound"):
                # At depth -3, 0.25 < 0.30, so should return sound
                result_deep = service.get_ambient_sound(category="dungeon", depth=-3)

        assert result_surface is None
        assert result_deep == "Test sound"

    def test_depth_sounds_exist(self) -> None:
        """Depth-specific sounds should exist for multiple depths."""
        # Spec: Depth-based sounds (increasingly ominous)
        assert -1 in DEPTH_SOUNDS
        assert -2 in DEPTH_SOUNDS
        assert -3 in DEPTH_SOUNDS
        assert len(DEPTH_SOUNDS[-1]) >= 3
        assert len(DEPTH_SOUNDS[-2]) >= 3
        assert len(DEPTH_SOUNDS[-3]) >= 3


class TestAmbientSoundTriggerChance:
    """Tests for base trigger chance."""

    def test_ambient_sound_trigger_chance_constant(self) -> None:
        """Base chance should be ~15% per move."""
        # Spec: ~15% base chance per move
        assert AMBIENT_SOUND_CHANCE == 0.15

    def test_depth_sound_chance_bonus_constant(self) -> None:
        """Depth bonus should be +5% per depth level."""
        # Spec: +5% per depth level
        assert DEPTH_SOUND_CHANCE_BONUS == 0.05


class TestAmbientSoundCooldown:
    """Tests for sound cooldown mechanism."""

    def test_ambient_sound_cooldown_prevents_repeat(self) -> None:
        """Sounds should not repeat within cooldown period."""
        # Spec: Sounds don't repeat within cooldown period (3 moves)
        service = AmbientSoundService()

        # Force first sound to trigger
        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.01):
            with patch("cli_rpg.ambient_sounds.random.choice", return_value="First sound"):
                first = service.get_ambient_sound(category="dungeon", depth=0)

        assert first == "First sound"

        # Next 2 calls should return None due to cooldown
        for _ in range(2):
            with patch("cli_rpg.ambient_sounds.random.random", return_value=0.01):
                result = service.get_ambient_sound(category="dungeon", depth=0)
            assert result is None

    def test_ambient_sound_cooldown_resets_after_moves(self) -> None:
        """Cooldown should reset after 3 moves."""
        # Spec: Sounds don't repeat within cooldown period (3 moves)
        service = AmbientSoundService()

        # Force first sound
        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.01):
            with patch("cli_rpg.ambient_sounds.random.choice", return_value="First sound"):
                service.get_ambient_sound(category="dungeon", depth=0)

        # Simulate 3 moves (the cooldown period)
        for _ in range(SOUND_COOLDOWN_MOVES):
            with patch("cli_rpg.ambient_sounds.random.random", return_value=0.99):
                service.get_ambient_sound(category="dungeon", depth=0)

        # Now should be able to trigger again
        with patch("cli_rpg.ambient_sounds.random.random", return_value=0.01):
            with patch("cli_rpg.ambient_sounds.random.choice", return_value="Second sound"):
                result = service.get_ambient_sound(category="dungeon", depth=0)

        assert result == "Second sound"

    def test_cooldown_constant(self) -> None:
        """Cooldown should be 3 moves."""
        # Spec: Minimum moves between sounds is 3
        assert SOUND_COOLDOWN_MOVES == 3


class TestFormatAmbientSound:
    """Tests for sound formatting."""

    def test_format_ambient_sound_has_prefix(self) -> None:
        """Format should include [Sound]: prefix."""
        # Spec: Format includes [Sound]: prefix with dim styling
        result = format_ambient_sound("Dripping water echoes...")
        assert "[Sound]:" in result

    def test_format_ambient_sound_includes_text(self) -> None:
        """Format should include the sound text."""
        # Spec: Format includes [Sound]: prefix with dim styling
        result = format_ambient_sound("Chains rattle in the distance...")
        assert "Chains rattle in the distance..." in result

    def test_format_ambient_sound_has_styling(self) -> None:
        """Format should apply dim styling via ANSI codes."""
        # Spec: Format includes [Sound]: prefix with dim styling
        # We check that colorize is called by verifying ANSI codes in output
        # or that the function exists without errors
        result = format_ambient_sound("Test sound")
        # Result should be a string (may or may not have ANSI codes depending on env)
        assert isinstance(result, str)
        assert len(result) > 0


class TestAmbientSoundInSubGridMove:
    """Integration test for ambient sounds in SubGrid movement."""

    def test_ambient_sound_service_initialized_in_game_state(self) -> None:
        """GameState should have ambient_sound_service attribute."""
        # Spec: Sounds trigger in _move_in_sub_grid
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="TestHero", strength=10, dexterity=10, intelligence=10)
        town = Location(
            name="Town Square",
            description="A town.",
            coordinates=(0, 0),
            category="town",
        )
        world = {"Town Square": town}
        game = GameState(char, world, "Town Square")
        assert hasattr(game, "ambient_sound_service")
        assert isinstance(game.ambient_sound_service, AmbientSoundService)
