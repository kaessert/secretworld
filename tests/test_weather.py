"""Tests for weather system.

These tests verify the Weather model and its integration with GameState,
dread system, and movement mechanics.
"""

import pytest
import random
from cli_rpg.models.weather import Weather


class TestWeatherModel:
    """Tests for the Weather dataclass."""

    # Spec: Weather defaults to "clear"
    def test_weather_defaults_to_clear(self):
        """Weather condition defaults to 'clear'."""
        weather = Weather()
        assert weather.condition == "clear"

    # Spec: Display shows "Clear ☀"
    def test_weather_get_display_clear(self):
        """get_display returns 'Clear ☀' for clear weather."""
        weather = Weather(condition="clear")
        assert weather.get_display() == "Clear ☀"

    # Spec: Display shows "Rain ☔"
    def test_weather_get_display_rain(self):
        """get_display returns 'Rain ☔' for rain weather."""
        weather = Weather(condition="rain")
        assert weather.get_display() == "Rain ☔"

    # Spec: Display shows "Storm ⛈"
    def test_weather_get_display_storm(self):
        """get_display returns 'Storm ⛈' for storm weather."""
        weather = Weather(condition="storm")
        assert weather.get_display() == "Storm ⛈"

    # Spec: Display shows "Fog 🌫"
    def test_weather_get_display_fog(self):
        """get_display returns 'Fog 🌫' for fog weather."""
        weather = Weather(condition="fog")
        assert weather.get_display() == "Fog 🌫"

    # Spec: Serialization round-trips correctly
    def test_weather_serialization(self):
        """to_dict and from_dict round-trip correctly."""
        original = Weather(condition="storm")
        data = original.to_dict()
        restored = Weather.from_dict(data)
        assert restored.condition == original.condition

    # Spec: transition() can change weather state
    def test_weather_transition_changes_state(self):
        """transition() can change weather when probability triggers."""
        weather = Weather(condition="clear")

        # Force a change by using a fixed random seed that triggers transition
        random.seed(0)  # This seed will produce consistent results

        # Call transition many times to increase chance of change
        changed = False
        for _ in range(100):
            weather.condition = "clear"  # Reset
            result = weather.transition()
            if result is not None:
                changed = True
                assert result in Weather.WEATHER_STATES
                break

        # With 10% chance per call and 100 calls, should have changed
        assert changed, "Weather should have changed at least once in 100 attempts"

    # Spec: Caves always report clear weather
    def test_weather_stays_clear_in_caves(self):
        """get_effective_condition returns 'clear' for cave locations."""
        weather = Weather(condition="storm")
        assert weather.get_effective_condition("cave") == "clear"

    def test_weather_normal_in_non_caves(self):
        """get_effective_condition returns actual condition for non-cave locations."""
        weather = Weather(condition="storm")
        assert weather.get_effective_condition("wilderness") == "storm"
        assert weather.get_effective_condition("town") == "storm"
        assert weather.get_effective_condition("dungeon") == "storm"

    # Spec: Dread modifiers per weather type
    def test_weather_get_dread_modifier_clear(self):
        """Clear weather has no dread modifier."""
        weather = Weather(condition="clear")
        assert weather.get_dread_modifier() == 0

    def test_weather_get_dread_modifier_rain(self):
        """Rain adds +2 dread modifier."""
        weather = Weather(condition="rain")
        assert weather.get_dread_modifier() == 2

    def test_weather_get_dread_modifier_storm(self):
        """Storm adds +5 dread modifier."""
        weather = Weather(condition="storm")
        assert weather.get_dread_modifier() == 5

    def test_weather_get_dread_modifier_fog(self):
        """Fog adds +3 dread modifier."""
        weather = Weather(condition="fog")
        assert weather.get_dread_modifier() == 3

    # Spec: Travel time modifier for storm
    def test_weather_get_travel_modifier_storm(self):
        """Storm adds +1 hour travel time."""
        weather = Weather(condition="storm")
        assert weather.get_travel_modifier() == 1

    def test_weather_get_travel_modifier_clear(self):
        """Clear weather has no travel time modifier."""
        weather = Weather(condition="clear")
        assert weather.get_travel_modifier() == 0

    # Spec: Weather flavor text
    def test_weather_get_flavor_text(self):
        """get_flavor_text returns a string for each weather type."""
        for condition in Weather.WEATHER_STATES:
            weather = Weather(condition=condition)
            flavor = weather.get_flavor_text()
            assert isinstance(flavor, str)
            assert len(flavor) > 0


class TestWeatherGameStateIntegration:
    """Tests for Weather integration with GameState."""

    # Spec: GameState has weather attribute
    def test_game_state_has_weather(self):
        """GameState includes weather attribute."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0))
        world = {"Town": loc}

        game_state = GameState(char, world, starting_location="Town")
        assert hasattr(game_state, "weather")
        assert isinstance(game_state.weather, Weather)

    # Spec: Movement can trigger weather transitions
    def test_move_advances_weather(self):
        """Moving to a new location can trigger weather transitions."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0))
        loc1.add_connection("north", "End")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1))
        loc2.add_connection("south", "Start")
        world = {"Start": loc1, "End": loc2}

        game_state = GameState(char, world, starting_location="Start")

        # Transition is called on move (10% chance per hour)
        # We just verify the method is called without error
        game_state.move("north")
        assert game_state.weather.condition in Weather.WEATHER_STATES

    # Spec: Rain adds +2 dread on move
    def test_weather_affects_dread_rain(self):
        """Rain weather adds +2 extra dread on move."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        # Use wilderness category (normally adds 5 dread)
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0), category="wilderness")
        loc1.add_connection("north", "End")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1), category="wilderness")
        loc2.add_connection("south", "Start")
        world = {"Start": loc1, "End": loc2}

        game_state = GameState(char, world, starting_location="Start")
        game_state.weather.condition = "rain"
        game_state.game_time.hour = 12  # Daytime (no night bonus)
        initial_dread = game_state.current_character.dread_meter.dread

        game_state.move("north")

        # Should be wilderness (5) + rain (2) = 7 dread increase
        expected_dread = initial_dread + 5 + 2
        assert game_state.current_character.dread_meter.dread == expected_dread

    # Spec: Storm adds +5 dread on move
    def test_weather_affects_dread_storm(self):
        """Storm weather adds +5 extra dread on move."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0), category="wilderness")
        loc1.add_connection("north", "End")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1), category="wilderness")
        loc2.add_connection("south", "Start")
        world = {"Start": loc1, "End": loc2}

        game_state = GameState(char, world, starting_location="Start")
        game_state.weather.condition = "storm"
        game_state.game_time.hour = 12  # Daytime
        initial_dread = game_state.current_character.dread_meter.dread

        game_state.move("north")

        # Should be wilderness (5) + storm (5) = 10 dread increase
        expected_dread = initial_dread + 5 + 5
        assert game_state.current_character.dread_meter.dread == expected_dread

    # Spec: Storm adds +1 hour to travel
    def test_storm_adds_travel_time(self):
        """Storm weather adds +1 hour to travel time."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0))
        loc1.add_connection("north", "End")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1))
        loc2.add_connection("south", "Start")
        world = {"Start": loc1, "End": loc2}

        game_state = GameState(char, world, starting_location="Start")
        game_state.weather.condition = "storm"
        initial_hour = game_state.game_time.hour

        game_state.move("north")

        # Normal travel is 1 hour, storm adds +1 = 2 hours total
        assert game_state.game_time.hour == initial_hour + 2

    # Spec: Weather persists in save files
    def test_weather_persists_in_save(self):
        """Weather is saved and restored correctly."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0))
        world = {"Town": loc}

        game_state = GameState(char, world, starting_location="Town")
        game_state.weather.condition = "storm"

        # Serialize and deserialize
        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        assert restored.weather.condition == "storm"

    # Spec: Old saves without weather default to clear
    def test_weather_backward_compatibility(self):
        """Old saves without weather field default to clear."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0))
        world = {"Town": loc}

        game_state = GameState(char, world, starting_location="Town")

        # Create save data WITHOUT weather (simulating old save)
        data = game_state.to_dict()
        del data["weather"]

        restored = GameState.from_dict(data)
        assert restored.weather.condition == "clear"

    # Spec: Cave locations don't apply weather dread
    def test_cave_no_weather_dread(self):
        """Cave locations don't add weather-based dread."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0), category="wilderness")
        loc1.add_connection("north", "Cave")
        loc2 = Location(name="Cave", description="A dark cave", coordinates=(0, 1), category="cave")
        loc2.add_connection("south", "Start")
        world = {"Start": loc1, "Cave": loc2}

        game_state = GameState(char, world, starting_location="Start")
        game_state.weather.condition = "storm"
        game_state.game_time.hour = 12  # Daytime
        initial_dread = game_state.current_character.dread_meter.dread

        game_state.move("north")

        # Cave category adds 12 dread, but no weather bonus (underground)
        expected_dread = initial_dread + 12  # Just cave dread, no storm +5
        assert game_state.current_character.dread_meter.dread == expected_dread


class TestWeatherStatusDisplay:
    """Tests for weather display in status command."""

    # Spec: status command shows weather
    def test_status_shows_weather(self):
        """Status command includes weather display."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.main import handle_exploration_command

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0))
        world = {"Town": loc}

        game_state = GameState(char, world, starting_location="Town")
        game_state.weather.condition = "rain"

        _, message = handle_exploration_command(game_state, "status", [])

        assert "Weather:" in message
        assert "Rain" in message or "☔" in message

    # Spec: Move messages include weather flavor
    def test_move_message_includes_weather_flavor(self):
        """Movement messages include weather-related flavor text."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0))
        loc1.add_connection("north", "End")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1))
        loc2.add_connection("south", "Start")
        world = {"Start": loc1, "End": loc2}

        game_state = GameState(char, world, starting_location="Start")
        game_state.weather.condition = "rain"

        _, message = game_state.move("north")

        # Should contain some weather-related text
        # Check for any of the rain flavor texts
        rain_indicators = ["rain", "mud", "wet", "patters", "drizzle"]
        has_weather_flavor = any(word.lower() in message.lower() for word in rain_indicators)
        assert has_weather_flavor, f"Expected weather flavor in message: {message}"
