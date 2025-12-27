"""Tests for Tiredness system.

Tests cover:
- Tiredness model (increase/decrease, clamping, thresholds, penalties)
- Character integration (attack power penalty, perception penalty, serialization)
- GameState integration (movement increases tiredness)
- Dream integration (tiredness affects sleep/dream availability)
"""

import pytest
from cli_rpg.models.tiredness import Tiredness, TIREDNESS_THRESHOLDS


# =============================================================================
# Tiredness Model Tests
# =============================================================================


class TestTirednessModel:
    """Tests for the Tiredness dataclass."""

    def test_tiredness_defaults_to_zero(self):
        """Tiredness should default to 0 (fully rested)."""
        tiredness = Tiredness()
        assert tiredness.current == 0

    def test_tiredness_increase_clamps_at_100(self):
        """Tiredness should not exceed 100."""
        tiredness = Tiredness(current=95)
        tiredness.increase(10)
        assert tiredness.current == 100

    def test_tiredness_decrease_clamps_at_zero(self):
        """Tiredness should not go below 0."""
        tiredness = Tiredness(current=5)
        tiredness.decrease(10)
        assert tiredness.current == 0

    def test_tiredness_increase_returns_warning_at_60(self):
        """Crossing 60 threshold should return a warning."""
        tiredness = Tiredness(current=55)
        result = tiredness.increase(10)
        assert result == TIREDNESS_THRESHOLDS[60]

    def test_tiredness_increase_returns_warning_at_80(self):
        """Crossing 80 threshold should return a warning."""
        tiredness = Tiredness(current=75)
        result = tiredness.increase(10)
        assert result == TIREDNESS_THRESHOLDS[80]

    def test_tiredness_increase_returns_exhausted_warning_at_100(self):
        """Crossing 100 threshold should return exhausted warning."""
        tiredness = Tiredness(current=95)
        result = tiredness.increase(10)
        assert result == TIREDNESS_THRESHOLDS[100]

    def test_tiredness_increase_no_warning_within_same_tier(self):
        """No warning when staying within the same tier."""
        tiredness = Tiredness(current=65)
        result = tiredness.increase(5)
        assert result is None


class TestTirednessSleepability:
    """Tests for sleep availability based on tiredness."""

    def test_can_sleep_false_below_30(self):
        """Player should not be able to sleep when tiredness < 30."""
        tiredness = Tiredness(current=29)
        assert tiredness.can_sleep() is False

    def test_can_sleep_true_at_30(self):
        """Player should be able to sleep at tiredness == 30."""
        tiredness = Tiredness(current=30)
        assert tiredness.can_sleep() is True

    def test_can_sleep_true_at_100(self):
        """Player should be able to sleep at tiredness == 100."""
        tiredness = Tiredness(current=100)
        assert tiredness.can_sleep() is True


class TestTirednessSleepQuality:
    """Tests for sleep quality based on tiredness level."""

    def test_sleep_quality_light_below_60(self):
        """Sleep quality should be 'light' when tiredness < 60."""
        tiredness = Tiredness(current=45)
        assert tiredness.sleep_quality() == "light"

    def test_sleep_quality_normal_60_to_79(self):
        """Sleep quality should be 'normal' when tiredness 60-79."""
        tiredness = Tiredness(current=65)
        assert tiredness.sleep_quality() == "normal"

    def test_sleep_quality_deep_80_plus(self):
        """Sleep quality should be 'deep' when tiredness >= 80."""
        tiredness = Tiredness(current=85)
        assert tiredness.sleep_quality() == "deep"


class TestTirednessPenalties:
    """Tests for gameplay penalties from tiredness."""

    def test_get_attack_penalty_none_below_80(self):
        """No attack penalty when tiredness < 80."""
        tiredness = Tiredness(current=79)
        assert tiredness.get_attack_penalty() == 1.0

    def test_get_attack_penalty_0_9_at_80_plus(self):
        """10% attack penalty when tiredness >= 80."""
        tiredness = Tiredness(current=80)
        assert tiredness.get_attack_penalty() == 0.9

    def test_get_perception_penalty_none_below_80(self):
        """No perception penalty when tiredness < 80."""
        tiredness = Tiredness(current=79)
        assert tiredness.get_perception_penalty() == 1.0

    def test_get_perception_penalty_0_9_at_80_plus(self):
        """10% perception penalty when tiredness >= 80."""
        tiredness = Tiredness(current=80)
        assert tiredness.get_perception_penalty() == 0.9


class TestTirednessSerialization:
    """Tests for Tiredness serialization."""

    def test_to_dict_serialization(self):
        """to_dict should serialize current tiredness value."""
        tiredness = Tiredness(current=42)
        result = tiredness.to_dict()
        assert result == {"current": 42}

    def test_from_dict_deserialization(self):
        """from_dict should restore tiredness value."""
        data = {"current": 75}
        tiredness = Tiredness.from_dict(data)
        assert tiredness.current == 75

    def test_from_dict_default_zero(self):
        """from_dict should default to 0 if 'current' is missing."""
        data = {}
        tiredness = Tiredness.from_dict(data)
        assert tiredness.current == 0


class TestTirednessDisplay:
    """Tests for tiredness display bar."""

    def test_get_display_format(self):
        """get_display should return formatted bar string."""
        tiredness = Tiredness(current=50)
        display = tiredness.get_display()
        assert "TIREDNESS:" in display
        assert "50%" in display


# =============================================================================
# Character Integration Tests
# =============================================================================


class TestCharacterTirednessIntegration:
    """Tests for Tiredness integration with Character model."""

    def test_character_has_tiredness_attribute(self):
        """Character should have a tiredness attribute."""
        from cli_rpg.models.character import Character
        char = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        assert hasattr(char, "tiredness")
        assert isinstance(char.tiredness, Tiredness)

    def test_character_to_dict_includes_tiredness(self):
        """Character.to_dict() should include tiredness."""
        from cli_rpg.models.character import Character
        char = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        char.tiredness.increase(50)
        data = char.to_dict()
        assert "tiredness" in data
        assert data["tiredness"]["current"] == 50

    def test_character_from_dict_restores_tiredness(self):
        """Character.from_dict() should restore tiredness."""
        from cli_rpg.models.character import Character
        char = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        char.tiredness.increase(65)
        data = char.to_dict()
        restored = Character.from_dict(data)
        assert restored.tiredness.current == 65

    def test_character_from_dict_defaults_tiredness_zero(self):
        """Character.from_dict() should default tiredness to 0 for old saves."""
        from cli_rpg.models.character import Character
        # Simulate old save without tiredness
        data = {
            "name": "Test",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "level": 1,
        }
        char = Character.from_dict(data)
        assert char.tiredness.current == 0

    def test_character_get_attack_power_applies_tiredness_penalty(self):
        """Attack power should be reduced by 10% at high tiredness."""
        from cli_rpg.models.character import Character
        char = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        # Store baseline attack power at low tiredness
        char.tiredness = Tiredness(current=0)
        base_attack = char.get_attack_power()

        # Increase tiredness to 80+
        char.tiredness = Tiredness(current=85)
        penalized_attack = char.get_attack_power()

        # Should be 90% of base attack (10% reduction)
        expected = int(base_attack * 0.9)
        assert penalized_attack == expected


# =============================================================================
# GameState Integration Tests
# =============================================================================


class TestGameStateTiredness:
    """Tests for tiredness integration with GameState."""

    def _create_game_state(self):
        """Helper to create a minimal GameState for testing."""
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.game_state import GameState

        char = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        start = Location(
            name="Start",
            description="Starting area",
            coordinates=(0, 0),
        )
        east = Location(
            name="East Area",
            description="East of start",
            coordinates=(1, 0),
        )
        world = {"Start": start, "East Area": east}
        return GameState(char, world, "Start")

    def test_move_increases_tiredness(self):
        """Movement should increase tiredness."""
        gs = self._create_game_state()
        initial_tiredness = gs.current_character.tiredness.current
        gs.move("east")
        assert gs.current_character.tiredness.current > initial_tiredness


# =============================================================================
# Combat Integration Tests
# =============================================================================


class TestCombatTiredness:
    """Tests for tiredness increase from combat."""

    def test_combat_victory_increases_tiredness(self):
        """Combat victory should increase tiredness based on turn count.

        Formula: 5 base + 1 per turn
        """
        from cli_rpg.models.character import Character
        from cli_rpg.models.enemy import Enemy
        from cli_rpg.combat import CombatEncounter

        char = Character(
            name="Test",
            strength=10,
            dexterity=10,
            intelligence=10,
        )
        enemy = Enemy(
            name="Test Enemy",
            level=1,
            health=1,  # Will die in one hit
            max_health=1,
            attack_power=1,
            defense=0,
            xp_reward=10,
        )

        combat = CombatEncounter(player=char, enemy=enemy)
        combat.is_active = True
        combat.turn_count = 3  # Simulate 3 turns of combat

        initial_tiredness = char.tiredness.current
        combat.end_combat(victory=True)

        # Should increase by 5 base + 3 turns = 8
        expected_increase = 8
        assert char.tiredness.current == initial_tiredness + expected_increase


# =============================================================================
# Dream Integration Tests
# =============================================================================


class TestDreamTirednessIntegration:
    """Tests for tiredness affecting dream triggers."""

    def test_dream_blocked_when_tiredness_below_30(self):
        """Dreams should be blocked when tiredness < 30."""
        from cli_rpg.dreams import maybe_trigger_dream
        # With tiredness below 30, dreams should not trigger
        # Set dream_chance=1.0 to guarantee trigger if allowed
        result = maybe_trigger_dream(
            tiredness=20,
            dread=0,
            choices=None,
            theme="fantasy",
            dream_chance=1.0,
        )
        assert result is None

    def test_dream_allowed_when_tiredness_at_30(self):
        """Dreams should be allowed when tiredness >= 30."""
        from cli_rpg.dreams import maybe_trigger_dream
        import random
        # Fix random seed for reproducibility
        random.seed(42)
        result = maybe_trigger_dream(
            tiredness=50,
            dread=0,
            choices=None,
            theme="fantasy",
            dream_chance=1.0,  # Guarantee trigger
        )
        # Should get a dream (not None) when tired enough
        assert result is not None

    def test_deep_sleep_increases_vivid_dream_chance(self):
        """Deep sleep (tiredness >= 80) should increase dream likelihood."""
        # This is implicitly tested via dream_chance modification
        # At high tiredness, dream chance is 40% vs 5-20% at lower levels
        from cli_rpg.dreams import get_tiredness_dream_chance
        low_chance = get_tiredness_dream_chance(40)  # light sleep
        high_chance = get_tiredness_dream_chance(90)  # deep sleep
        assert high_chance > low_chance
