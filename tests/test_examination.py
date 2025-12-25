"""Tests for multi-layered examination feature (environmental storytelling MVP).

Tests verify that players can reveal progressively more details about a location
by using the 'look' command multiple times.
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


# =============================================================================
# Character look tracking tests
# =============================================================================


class TestCharacterLookTracking:
    """Tests for Character look count tracking methods."""

    def test_character_look_counts_init_empty(self):
        """New character has no look counts."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        assert char.look_counts == {}

    def test_character_record_look_increments(self):
        """record_look increments the counter for a location."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        count = char.record_look("Town Square")
        assert count == 1
        count = char.record_look("Town Square")
        assert count == 2
        count = char.record_look("Town Square")
        assert count == 3

    def test_character_get_look_count_returns_zero_for_new(self):
        """get_look_count returns 0 for unknown locations."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        assert char.get_look_count("Unknown Place") == 0

    def test_character_get_look_count_returns_recorded_value(self):
        """get_look_count returns correct count after recording."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.record_look("Town Square")
        char.record_look("Town Square")
        assert char.get_look_count("Town Square") == 2

    def test_character_reset_look_count(self):
        """reset_look_count clears the count for a location."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.record_look("Town Square")
        char.record_look("Town Square")
        char.reset_look_count("Town Square")
        assert char.get_look_count("Town Square") == 0

    def test_character_reset_look_count_nonexistent(self):
        """reset_look_count does nothing for unknown locations."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # Should not raise
        char.reset_look_count("Nonexistent")
        assert char.get_look_count("Nonexistent") == 0

    def test_character_look_counts_serialization(self):
        """to_dict/from_dict preserves look_counts."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        char.record_look("Town Square")
        char.record_look("Town Square")
        char.record_look("Forest")

        data = char.to_dict()
        restored = Character.from_dict(data)

        assert restored.get_look_count("Town Square") == 2
        assert restored.get_look_count("Forest") == 1


# =============================================================================
# Location model tests with layer fields
# =============================================================================


class TestLocationLayers:
    """Tests for Location details and secrets fields."""

    def test_location_details_field_optional(self):
        """Location works without details field."""
        loc = Location(name="Test Place", description="A test location.")
        assert loc.details is None

    def test_location_secrets_field_optional(self):
        """Location works without secrets field."""
        loc = Location(name="Test Place", description="A test location.")
        assert loc.secrets is None

    def test_location_with_details(self):
        """Location can store details."""
        loc = Location(
            name="Test Place",
            description="A test location.",
            details="  - Some detail\n  - Another detail"
        )
        assert loc.details == "  - Some detail\n  - Another detail"

    def test_location_with_secrets(self):
        """Location can store secrets."""
        loc = Location(
            name="Test Place",
            description="A test location.",
            secrets="  - A hidden secret"
        )
        assert loc.secrets == "  - A hidden secret"

    def test_location_serialization_with_layers(self):
        """to_dict/from_dict preserves details and secrets."""
        loc = Location(
            name="Test Place",
            description="A test location.",
            details="  - A detail",
            secrets="  - A secret"
        )

        data = loc.to_dict()
        restored = Location.from_dict(data)

        assert restored.details == "  - A detail"
        assert restored.secrets == "  - A secret"

    def test_location_serialization_without_layers(self):
        """to_dict/from_dict handles missing details/secrets (backward compatibility)."""
        loc = Location(name="Test Place", description="A test location.")
        data = loc.to_dict()
        restored = Location.from_dict(data)
        assert restored.details is None
        assert restored.secrets is None


class TestLocationLayeredDescription:
    """Tests for Location.get_layered_description() method."""

    def test_first_look_returns_surface_only(self):
        """First look shows standard description without details/secrets."""
        loc = Location(
            name="Test Place",
            description="A basic description.",
            details="  - A detail",
            secrets="  - A secret"
        )
        result = loc.get_layered_description(look_count=1)

        assert "Test Place" in result
        assert "A basic description." in result
        assert "Upon closer inspection" not in result
        assert "Hidden secrets" not in result

    def test_second_look_reveals_details(self):
        """Second look includes details layer."""
        loc = Location(
            name="Test Place",
            description="A basic description.",
            details="  - A detail",
            secrets="  - A secret"
        )
        result = loc.get_layered_description(look_count=2)

        assert "Test Place" in result
        assert "A basic description." in result
        assert "Upon closer inspection, you notice:" in result
        assert "  - A detail" in result
        assert "Hidden secrets" not in result

    def test_third_look_reveals_secrets(self):
        """Third look includes both details and secrets layers."""
        loc = Location(
            name="Test Place",
            description="A basic description.",
            details="  - A detail",
            secrets="  - A secret"
        )
        result = loc.get_layered_description(look_count=3)

        assert "Test Place" in result
        assert "A basic description." in result
        assert "Upon closer inspection, you notice:" in result
        assert "  - A detail" in result
        assert "Hidden secrets reveal themselves:" in result
        assert "  - A secret" in result

    def test_fourth_look_repeats_full_description(self):
        """Additional looks continue to show full content."""
        loc = Location(
            name="Test Place",
            description="A basic description.",
            details="  - A detail",
            secrets="  - A secret"
        )
        result = loc.get_layered_description(look_count=5)

        assert "Upon closer inspection, you notice:" in result
        assert "Hidden secrets reveal themselves:" in result

    def test_look_without_details(self):
        """Second look without details shows nothing extra."""
        loc = Location(
            name="Test Place",
            description="A basic description.",
            secrets="  - A secret"
        )
        result = loc.get_layered_description(look_count=2)

        assert "Upon closer inspection" not in result

    def test_look_without_secrets(self):
        """Third look without secrets shows details but no secrets."""
        loc = Location(
            name="Test Place",
            description="A basic description.",
            details="  - A detail"
        )
        result = loc.get_layered_description(look_count=3)

        assert "Upon closer inspection, you notice:" in result
        assert "Hidden secrets" not in result


# =============================================================================
# GameState integration tests
# =============================================================================


class TestGameStateLookIntegration:
    """Tests for GameState.look() integration with layered examination."""

    @pytest.fixture
    def game_with_layers(self):
        """Create a game state with locations that have details and secrets."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        loc1 = Location(
            name="Town Square",
            description="A bustling town square.",
            connections={"north": "Market"},
            coordinates=(0, 0),
            details="  - Worn cobblestones\n  - Faded notice board",
            secrets="  - Hidden initials scratched behind a post"
        )
        loc2 = Location(
            name="Market",
            description="A busy marketplace.",
            connections={"south": "Town Square"},
            coordinates=(0, 1),
            details="  - Stalls with colorful awnings"
        )
        world = {"Town Square": loc1, "Market": loc2}
        return GameState(character=char, world=world, starting_location="Town Square")

    def test_gamestate_first_look_surface_only(self, game_with_layers):
        """First look shows only surface description."""
        result = game_with_layers.look()

        assert "Town Square" in result
        assert "A bustling town square." in result
        assert "Upon closer inspection" not in result
        assert "Hidden secrets" not in result

    def test_gamestate_second_look_reveals_details(self, game_with_layers):
        """Second look reveals details layer."""
        game_with_layers.look()  # First look
        result = game_with_layers.look()  # Second look

        assert "Upon closer inspection, you notice:" in result
        assert "Worn cobblestones" in result
        assert "Hidden secrets" not in result

    def test_gamestate_third_look_reveals_secrets(self, game_with_layers):
        """Third look reveals secrets layer."""
        game_with_layers.look()  # First look
        game_with_layers.look()  # Second look
        result = game_with_layers.look()  # Third look

        assert "Upon closer inspection, you notice:" in result
        assert "Hidden secrets reveal themselves:" in result
        assert "Hidden initials" in result

    def test_gamestate_look_increments_counter(self, game_with_layers):
        """look() method updates character's look count."""
        assert game_with_layers.current_character.get_look_count("Town Square") == 0
        game_with_layers.look()
        assert game_with_layers.current_character.get_look_count("Town Square") == 1
        game_with_layers.look()
        assert game_with_layers.current_character.get_look_count("Town Square") == 2

    def test_gamestate_move_resets_previous_look_count(self, game_with_layers):
        """Moving resets the look count for the previous location."""
        # Look at Town Square multiple times
        game_with_layers.look()
        game_with_layers.look()
        assert game_with_layers.current_character.get_look_count("Town Square") == 2

        # Move to Market
        success, _ = game_with_layers.move("north")
        assert success

        # Town Square count should be reset
        assert game_with_layers.current_character.get_look_count("Town Square") == 0

        # Market count should still be 0 (haven't looked yet)
        assert game_with_layers.current_character.get_look_count("Market") == 0

    def test_gamestate_returning_location_resets_look(self, game_with_layers):
        """Returning to a location starts look count fresh."""
        # Look at Town Square multiple times
        game_with_layers.look()
        game_with_layers.look()

        # Move away and back
        game_with_layers.move("north")
        game_with_layers.move("south")

        # First look at Town Square should be surface only again
        result = game_with_layers.look()
        assert "Upon closer inspection" not in result
        assert "Hidden secrets" not in result
