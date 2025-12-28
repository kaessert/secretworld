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

        # Save the random state before seeding
        old_state = random.getstate()

        # Force a change by using a fixed random seed that triggers transition
        random.seed(0)  # This seed will produce consistent results

        # Call transition many times to increase chance of change
        changed = False
        try:
            for _ in range(100):
                weather.condition = "clear"  # Reset
                result = weather.transition()
                if result is not None:
                    changed = True
                    assert result in Weather.WEATHER_STATES
                    break
        finally:
            # Restore the random state to avoid affecting other tests
            random.setstate(old_state)

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
        # Locations at adjacent coordinates are connected via coordinate adjacency
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0))
        loc2 = Location(name="End", description="End area", coordinates=(0, 1))
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
        # Locations at adjacent coordinates are connected via coordinate adjacency
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0), category="wilderness")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1), category="wilderness")
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
        # Locations at adjacent coordinates are connected via coordinate adjacency
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0), category="wilderness")
        loc2 = Location(name="End", description="End area", coordinates=(0, 1), category="wilderness")
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
        # Locations at adjacent coordinates are connected via coordinate adjacency
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0))
        loc2 = Location(name="End", description="End area", coordinates=(0, 1))
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
        # Locations at adjacent coordinates are connected via coordinate adjacency
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0), category="wilderness")
        loc2 = Location(name="Cave", description="A dark cave", coordinates=(0, 1), category="cave")
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
        # Locations at adjacent coordinates are connected via coordinate adjacency
        loc1 = Location(name="Start", description="Start area", coordinates=(0, 0))
        loc2 = Location(name="End", description="End area", coordinates=(0, 1))
        world = {"Start": loc1, "End": loc2}

        game_state = GameState(char, world, starting_location="Start")
        game_state.weather.condition = "rain"

        _, message = game_state.move("north")

        # Should contain some weather-related text
        # Check for any of the rain flavor texts
        rain_indicators = ["rain", "mud", "wet", "patters", "drizzle"]
        has_weather_flavor = any(word.lower() in message.lower() for word in rain_indicators)
        assert has_weather_flavor, f"Expected weather flavor in message: {message}"


class TestWeatherVisibility:
    """Tests for weather visibility effects on location descriptions.

    Spec: Weather affects what players can see when looking at locations:
    - Fog: Hides some exits (50% chance each exit hidden)
    - Storm: Reduces description detail (truncates to first sentence), hides details/secrets layers
    - Rain/Clear: No visibility effects
    - Cave locations (underground) are unaffected by weather
    """

    # Spec: get_visibility_level returns "full" for clear weather
    def test_weather_visibility_level_clear(self):
        """Clear weather returns 'full' visibility."""
        weather = Weather(condition="clear")
        assert weather.get_visibility_level() == "full"

    # Spec: get_visibility_level returns "full" for rain weather
    def test_weather_visibility_level_rain(self):
        """Rain weather returns 'full' visibility."""
        weather = Weather(condition="rain")
        assert weather.get_visibility_level() == "full"

    # Spec: get_visibility_level returns "reduced" for storm weather
    def test_weather_visibility_level_storm(self):
        """Storm weather returns 'reduced' visibility."""
        weather = Weather(condition="storm")
        assert weather.get_visibility_level() == "reduced"

    # Spec: get_visibility_level returns "obscured" for fog weather
    def test_weather_visibility_level_fog(self):
        """Fog weather returns 'obscured' visibility."""
        weather = Weather(condition="fog")
        assert weather.get_visibility_level() == "obscured"

    # Spec: Caves always return "full" visibility regardless of weather
    def test_weather_visibility_level_cave_always_full(self):
        """Cave locations always return 'full' visibility."""
        for condition in Weather.WEATHER_STATES:
            weather = Weather(condition=condition)
            assert weather.get_visibility_level("cave") == "full"


class TestLocationVisibilityEffects:
    """Tests for Location.get_layered_description visibility parameter."""

    # Spec: Storm visibility truncates description to first sentence
    def test_location_reduced_visibility_truncates_description(self):
        """Reduced visibility (storm) truncates description to first sentence."""
        from cli_rpg.models.location import Location

        loc = Location(
            name="Dark Forest",
            description="The trees loom overhead. Strange sounds echo through the branches. A cold wind blows."
        )

        result = loc.get_layered_description(look_count=1, visibility="reduced")

        # Should only contain first sentence
        assert "The trees loom overhead." in result
        assert "Strange sounds echo through the branches" not in result
        assert "A cold wind blows" not in result

    # Spec: Storm hides details and secrets layers
    def test_location_reduced_visibility_hides_details_secrets(self):
        """Reduced visibility (storm) hides details and secrets layers."""
        from cli_rpg.models.location import Location

        loc = Location(
            name="Dark Forest",
            description="The trees loom overhead.",
            details="You notice scratch marks on the bark.",
            secrets="A hidden path leads deeper into the woods."
        )

        # With full visibility, look_count 3 should show all layers
        full_result = loc.get_layered_description(look_count=3, visibility="full")
        assert "scratch marks" in full_result
        assert "hidden path" in full_result

        # With reduced visibility, even look_count 3 should not show details/secrets
        reduced_result = loc.get_layered_description(look_count=3, visibility="reduced")
        assert "scratch marks" not in reduced_result
        assert "hidden path" not in reduced_result

    # Spec: Fog hides ~50% of exits (seeded by location name for consistency)
    def test_location_obscured_visibility_hides_some_exits(self):
        """Obscured visibility (fog) hides some exits (deterministic based on location name)."""
        from cli_rpg.models.location import Location

        # Create a crossroads with 4 adjacent locations for 4 exits
        loc = Location(
            name="Foggy Crossroads",
            description="You stand at a crossroads.",
            coordinates=(0, 0),
        )
        # Create adjacent locations in all 4 directions
        north_loc = Location(name="North Path", description="Path north", coordinates=(0, 1))
        south_loc = Location(name="South Path", description="Path south", coordinates=(0, -1))
        east_loc = Location(name="East Path", description="Path east", coordinates=(1, 0))
        west_loc = Location(name="West Path", description="Path west", coordinates=(-1, 0))
        world = {
            "Foggy Crossroads": loc,
            "North Path": north_loc,
            "South Path": south_loc,
            "East Path": east_loc,
            "West Path": west_loc,
        }

        # Run multiple times - should be consistent due to seeding by location name
        result1 = loc.get_layered_description(look_count=1, visibility="obscured", world=world)
        result2 = loc.get_layered_description(look_count=1, visibility="obscured", world=world)

        # Results should be identical (deterministic)
        assert result1 == result2

        # Should have fewer than 4 exits showing (some hidden)
        # Count direction mentions in Exits line
        exits_line = [line for line in result1.split("\n") if line.startswith("Exits:")]
        assert len(exits_line) == 1
        exits_text = exits_line[0]

        # At least one exit should remain visible
        directions = ["north", "south", "east", "west"]
        visible_count = sum(1 for d in directions if d in exits_text)
        assert visible_count >= 1, "At least one exit should remain visible in fog"
        # Some exits should be hidden (not all 4 visible)
        assert visible_count < 4 or "???" in exits_text, "Fog should hide some exits"

    # Spec: NPCs at player's current location are always visible, even in fog
    def test_location_obscured_visibility_shows_npc_names(self):
        """Obscured visibility (fog) still shows NPC names at player's current location."""
        from cli_rpg.models.location import Location
        from cli_rpg.models.npc import NPC

        loc = Location(
            name="Misty Square",
            description="A foggy town square."
        )
        loc.npcs = [
            NPC(name="Marcus the Blacksmith", description="A burly blacksmith", dialogue="Hello!"),
            NPC(name="Elena the Baker", description="A friendly baker", dialogue="Fresh bread!")
        ]

        result = loc.get_layered_description(look_count=1, visibility="obscured")

        # NPC names should be visible at the player's current location
        assert "Marcus" in result
        assert "Elena" in result
        # Should NOT show ???
        assert "???" not in result

    # Spec: Full visibility shows everything normally
    def test_location_full_visibility_unchanged(self):
        """Full visibility shows everything normally."""
        from cli_rpg.models.location import Location
        from cli_rpg.models.npc import NPC

        loc = Location(
            name="Town Square",
            description="A bustling town square.",
            details="You notice the cobblestones are worn smooth.",
            secrets="A secret door hides behind the fountain.",
            coordinates=(0, 0),
        )
        loc.npcs = [NPC(name="Guard Captain", description="A stern captain", dialogue="Halt!")]

        # Create adjacent locations for exits
        north_loc = Location(name="North Road", description="Road north", coordinates=(0, 1))
        south_loc = Location(name="South Road", description="Road south", coordinates=(0, -1))
        world = {
            "Town Square": loc,
            "North Road": north_loc,
            "South Road": south_loc,
        }

        result = loc.get_layered_description(look_count=3, visibility="full", world=world)

        # All exits should be visible
        assert "north" in result
        assert "south" in result
        # NPC names should be visible
        assert "Guard Captain" in result
        # Details and secrets should be visible at look_count 3
        assert "cobblestones are worn smooth" in result
        assert "secret door" in result


class TestGameStateLookVisibility:
    """Tests for GameState.look() visibility integration."""

    # Spec: look in storm uses reduced visibility
    def test_look_in_storm_reduces_visibility(self):
        """look() in storm weather uses reduced visibility."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(
            name="Stormy Plains",
            description="A vast open plain. The grass sways in the wind. Lightning flashes overhead.",
            coordinates=(0, 0),
            category="wilderness",
            details="You spot animal tracks in the mud."
        )
        world = {"Stormy Plains": loc}

        game_state = GameState(char, world, starting_location="Stormy Plains")
        game_state.weather.condition = "storm"

        # Look twice to normally see details
        game_state.look()  # First look
        result = game_state.look()  # Second look (would normally show details)

        # Storm should truncate description and hide details
        assert "A vast open plain." in result
        assert "The grass sways in the wind" not in result  # Truncated
        assert "animal tracks" not in result  # Details hidden

    # Spec: look in fog shows NPCs at player's location, hides some exits
    def test_look_in_fog_shows_npcs_at_current_location(self):
        """look() in fog weather still shows NPC names at player's current location."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.npc import NPC

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(
            name="Foggy Hamlet",
            description="A small hamlet shrouded in mist.",
            coordinates=(0, 0),
            category="town"
        )
        loc.npcs = [NPC(name="Old Farmer", description="An elderly farmer", dialogue="Greetings!")]
        world = {"Foggy Hamlet": loc}

        game_state = GameState(char, world, starting_location="Foggy Hamlet")
        game_state.weather.condition = "fog"

        result = game_state.look()

        # NPC names should be visible at player's current location
        assert "Old Farmer" in result
        # Should NOT show ??? for NPCs
        assert "???" not in result

    # Spec: Caves are unaffected by weather
    def test_look_in_cave_unaffected_by_weather(self):
        """look() in cave location always uses full visibility regardless of weather."""
        from cli_rpg.game_state import GameState
        from cli_rpg.models.character import Character
        from cli_rpg.models.location import Location
        from cli_rpg.models.npc import NPC

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(
            name="Crystal Cave",
            description="A cave filled with glowing crystals. Water drips from stalactites.",
            coordinates=(0, 0),
            category="cave",
            details="The crystals hum with magical energy."
        )
        loc.npcs = [NPC(name="Cave Hermit", description="A mysterious hermit", dialogue="Who goes there?")]
        world = {"Crystal Cave": loc}

        game_state = GameState(char, world, starting_location="Crystal Cave")

        # Test with both storm and fog
        for condition in ["storm", "fog"]:
            game_state.weather.condition = condition

            # Reset look count for fresh test
            char.look_counts.clear()
            game_state.look()  # First look
            result = game_state.look()  # Second look

            # Full description should be shown (not truncated)
            assert "glowing crystals" in result
            assert "Water drips" in result
            # NPC name should be visible (not obscured)
            assert "Cave Hermit" in result
            # Details should be visible at look_count 2
            assert "magical energy" in result
