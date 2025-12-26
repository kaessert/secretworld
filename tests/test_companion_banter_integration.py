"""Integration tests for companion banter during travel.

Tests verify banter appears during GameState.move() when companions are present
and conditions are met.
"""

from unittest.mock import patch, MagicMock

import pytest

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.companion import Companion
from cli_rpg.models.location import Location


def create_test_world():
    """Create a minimal test world for movement tests."""
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        category="town",
        connections={"north": "Dark Forest"},
        coordinates=(0, 0),
    )
    forest = Location(
        name="Dark Forest",
        description="A dark, foreboding forest.",
        category="forest",
        connections={"south": "Town Square"},
        coordinates=(0, 1),
    )
    return {"Town Square": town, "Dark Forest": forest}


def create_test_character():
    """Create a basic test character."""
    return Character(name="Hero", strength=10, dexterity=10, intelligence=10)


class TestBanterOnMove:
    """Tests for banter appearing during movement."""

    def test_banter_appears_on_move_with_companion(self):
        """Test that banter can appear when moving with a companion."""
        # Spec: Banter appears on move when companions present
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        # Add a companion
        companion = Companion(
            name="Elara",
            description="A mysterious ranger",
            recruited_at="Town Square",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Force banter to trigger (patch the random check)
        found_banter = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):  # Force trigger
            # Move multiple times to find banter
            for _ in range(20):
                # Reset location for next test
                game_state.current_location = "Town Square"
                success, message = game_state.move("north")
                assert success
                if "[Companion]" in message:
                    found_banter = True
                    break

        assert found_banter, "Expected banter to appear during move with companion"

    def test_no_banter_on_move_without_companions(self):
        """Test that no banter appears when no companions present."""
        # Spec: No banter when no companions
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        # No companions added

        # Move many times
        for _ in range(20):
            game_state.current_location = "Town Square"
            success, message = game_state.move("north")
            assert success
            assert "[Companion]" not in message, "No banter should appear without companions"

    def test_no_banter_during_combat(self):
        """Test that banter does not appear during active combat."""
        # Spec: No banter during combat
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        # Add a companion
        companion = Companion(
            name="Elara",
            description="A mysterious ranger",
            recruited_at="Town Square",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Simulate active combat
        mock_combat = MagicMock()
        mock_combat.is_active = True
        game_state.current_combat = mock_combat

        # Move should not trigger banter during combat
        # Note: Movement is typically blocked during combat, but we verify
        # the banter system specifically respects combat state
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            # Even if we force move (bypassing normal combat block), no banter
            success, message = game_state.move("north")
            # Note: In real game, movement fails during combat
            # This test ensures banter check happens after combat check
            if success:
                assert "[Companion]" not in message

    def test_banter_and_whisper_can_coexist(self):
        """Test that both banter and whisper can trigger in same move."""
        # Spec: Both may appear in same move
        # Note: Whispers now display immediately via display_whisper() and aren't in message
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        # Add a companion
        companion = Companion(
            name="Elara",
            description="A mysterious ranger",
            recruited_at="Town Square",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Force both banter and whisper to trigger
        found_both = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):  # Force banter
            with patch("cli_rpg.whisper.random.random", return_value=0.1):  # Force whisper
                with patch("cli_rpg.game_state.display_whisper") as mock_display:
                    for _ in range(20):
                        game_state.current_location = "Town Square"
                        success, message = game_state.move("north")
                        # Banter still in message, but whisper is displayed via display_whisper
                        if "[Companion]" in message and mock_display.called:
                            found_both = True
                            break

        assert found_both, "Banter and whisper should be able to coexist in same move"


class TestBanterContextInMove:
    """Tests verifying banter receives correct context from GameState."""

    def test_banter_receives_location_category(self):
        """Test that banter service receives correct location category."""
        # Spec: Location-based comments about location category
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Mock the banter service to verify it receives correct category
        with patch.object(game_state.banter_service, "get_banter") as mock_get_banter:
            mock_get_banter.return_value = None  # Don't trigger banter
            game_state.move("north")

            # Verify get_banter was called with forest category
            mock_get_banter.assert_called()
            call_kwargs = mock_get_banter.call_args.kwargs
            assert call_kwargs["location_category"] == "forest"

    def test_banter_receives_weather_condition(self):
        """Test that banter service receives current weather."""
        # Spec: Weather-based - React to weather conditions
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Set specific weather
        game_state.weather.condition = "storm"

        # Patch weather transition random to prevent weather change during move
        with patch("cli_rpg.models.weather.random.random", return_value=0.50):
            with patch.object(game_state.banter_service, "get_banter") as mock_get_banter:
                mock_get_banter.return_value = None
                game_state.move("north")

                call_kwargs = mock_get_banter.call_args.kwargs
                assert call_kwargs["weather"] == "storm"

    def test_banter_receives_time_of_day(self):
        """Test that banter service receives night/day status."""
        # Spec: Time-based - Day/night observations
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Set to night time
        game_state.game_time.hour = 22  # 10 PM

        with patch.object(game_state.banter_service, "get_banter") as mock_get_banter:
            mock_get_banter.return_value = None
            game_state.move("north")

            call_kwargs = mock_get_banter.call_args.kwargs
            assert call_kwargs["is_night"] is True

    def test_banter_receives_dread_level(self):
        """Test that banter service receives current dread level."""
        # Spec: Dread-based - Nervous comments at high dread (50%+)
        world = create_test_world()
        character = create_test_character()
        game_state = GameState(character, world, "Town Square")

        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=50,
        )
        game_state.companions.append(companion)

        # Set high dread (but not in hallucination range to avoid combat)
        character.dread_meter.dread = 60

        with patch.object(game_state.banter_service, "get_banter") as mock_get_banter:
            mock_get_banter.return_value = None
            game_state.move("north")

            call_kwargs = mock_get_banter.call_args.kwargs
            # Dread may increase during move (forest adds dread), verify it's high
            assert call_kwargs["dread"] >= 60
