"""Tests for fast travel functionality.

Tests the `travel` command that allows players to teleport to
previously-visited named overworld locations.
"""
import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.location import Location
from cli_rpg.combat import CombatEncounter


def create_test_character() -> Character:
    """Create a test character with all required attributes."""
    char = Character(
        name="Test Hero",
        strength=10,
        dexterity=10,
        intelligence=10,
        character_class=CharacterClass.WARRIOR
    )
    return char


def create_test_world() -> dict[str, Location]:
    """Create a minimal world with named and unnamed locations."""
    return {
        "Town Square": Location(
            name="Town Square",
            description="A bustling town center.",
            coordinates=(0, 0),
            category="town",
            is_named=True,
            is_safe_zone=True,
        ),
        "Forest Clearing": Location(
            name="Forest Clearing",
            description="A peaceful forest clearing.",
            coordinates=(4, 0),
            category="wilderness",
            is_named=True,
        ),
        "Mountain Pass": Location(
            name="Mountain Pass",
            description="A treacherous mountain path.",
            coordinates=(8, 8),
            category="wilderness",
            is_named=True,
        ),
        # Unnamed terrain filler location
        "Plains (1,0)": Location(
            name="Plains (1,0)",
            description="Rolling plains.",
            coordinates=(1, 0),
            category="wilderness",
            is_named=False,
        ),
        # Sub-location (inside a building)
        "Tavern Interior": Location(
            name="Tavern Interior",
            description="Inside the tavern.",
            coordinates=(0, 0),
            category="town",
            is_named=True,
            parent_location="Town Square",
        ),
    }


class TestGetFastTravelDestinations:
    """Tests for get_fast_travel_destinations() method.

    Spec: Only named overworld locations should appear.
    """

    def test_returns_only_named_locations(self):
        """Unnamed terrain filler locations should not appear."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        destinations = game_state.get_fast_travel_destinations()

        # "Plains (1,0)" has is_named=False, should not appear
        assert "Plains (1,0)" not in destinations
        # Named locations should appear (except current)
        assert "Forest Clearing" in destinations

    def test_returns_only_overworld_locations(self):
        """Sub-locations (with parent_location) should not appear."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        destinations = game_state.get_fast_travel_destinations()

        # Tavern Interior has parent_location, should not appear
        assert "Tavern Interior" not in destinations

    def test_excludes_current_location(self):
        """Current location should not be in destinations."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        destinations = game_state.get_fast_travel_destinations()

        # Current location (Town Square) should not appear
        assert "Town Square" not in destinations

    def test_excludes_locations_without_coordinates(self):
        """Locations missing coordinates are filtered out."""
        character = create_test_character()
        world = create_test_world()
        # Add location without coordinates
        world["Mysterious Void"] = Location(
            name="Mysterious Void",
            description="A place with no position.",
            coordinates=None,
            is_named=True,
        )
        game_state = GameState(character, world, "Town Square")

        destinations = game_state.get_fast_travel_destinations()

        assert "Mysterious Void" not in destinations

    def test_returns_sorted_list(self):
        """Destinations should be alphabetically sorted."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        destinations = game_state.get_fast_travel_destinations()

        assert destinations == sorted(destinations)

    def test_empty_when_no_valid_destinations(self):
        """Returns empty list when no named locations exist."""
        character = create_test_character()
        # World with only unnamed locations and current location
        world = {
            "Town Square": Location(
                name="Town Square",
                description="Start.",
                coordinates=(0, 0),
                is_named=True,
            ),
        }
        game_state = GameState(character, world, "Town Square")

        destinations = game_state.get_fast_travel_destinations()

        assert destinations == []


class TestFastTravelBlocks:
    """Tests for conditions that block fast travel.

    Spec: Cannot travel during combat, conversation, or from inside sub-location.
    """

    def test_blocked_during_combat(self):
        """Cannot travel while in active combat."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        # Mock active combat
        mock_combat = MagicMock(spec=CombatEncounter)
        mock_combat.is_active = True
        game_state.current_combat = mock_combat

        success, message = game_state.fast_travel("Forest Clearing")

        assert success is False
        assert "combat" in message.lower()

    def test_blocked_during_conversation(self):
        """Cannot travel while talking to NPC."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        # Set NPC to simulate conversation
        game_state.current_npc = MagicMock()

        success, message = game_state.fast_travel("Forest Clearing")

        assert success is False
        assert "conversation" in message.lower()

    def test_blocked_inside_subgrid(self):
        """Cannot travel from inside a sub-location."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        # Set sub-location state
        game_state.in_sub_location = True

        success, message = game_state.fast_travel("Forest Clearing")

        assert success is False
        assert "exit" in message.lower()

    def test_error_for_unknown_destination(self):
        """Clear error for destination not in list."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        success, message = game_state.fast_travel("Nonexistent Place")

        assert success is False
        assert "Unknown destination" in message


class TestFastTravelMechanics:
    """Tests for travel time and effects.

    Spec: Travel time = distance // 4, clamped 1-8 hours.
    """

    def test_travel_time_proportional_to_distance(self):
        """Travel time = distance // 4, clamped 1-8 hours."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")
        initial_hour = game_state.game_time.hour

        # Mountain Pass is at (8, 8), current at (0, 0)
        # Manhattan distance = 8 + 8 = 16
        # Travel time = 16 // 4 = 4 hours
        success, message = game_state.fast_travel("Mountain Pass")

        assert success is True
        # Verify time advanced by 4 hours (may wrap)
        expected_hours_passed = 4
        hours_passed = (game_state.game_time.hour - initial_hour) % 24
        assert hours_passed == expected_hours_passed

    def test_travel_time_minimum_1_hour(self):
        """Minimum travel time is 1 hour even for close destinations."""
        character = create_test_character()
        world = create_test_world()
        # Add a very close location
        world["Nearby Spot"] = Location(
            name="Nearby Spot",
            description="Very close.",
            coordinates=(1, 0),
            is_named=True,
        )
        game_state = GameState(character, world, "Town Square")
        initial_hour = game_state.game_time.hour

        success, message = game_state.fast_travel("Nearby Spot")

        assert success is True
        hours_passed = (game_state.game_time.hour - initial_hour) % 24
        assert hours_passed == 1

    def test_travel_time_maximum_8_hours(self):
        """Maximum travel time is 8 hours for far destinations."""
        character = create_test_character()
        world = create_test_world()
        # Add a very far location
        world["Distant Land"] = Location(
            name="Distant Land",
            description="Very far away.",
            coordinates=(50, 50),  # Distance 100, would be 25 hours
            is_named=True,
        )
        game_state = GameState(character, world, "Town Square")
        initial_hour = game_state.game_time.hour

        success, message = game_state.fast_travel("Distant Land")

        assert success is True
        hours_passed = (game_state.game_time.hour - initial_hour) % 24
        assert hours_passed == 8

    def test_tiredness_increases_per_hour(self):
        """Tiredness increases by 3 per hour traveled."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")
        initial_tiredness = game_state.current_character.tiredness.current

        # Travel to Mountain Pass (4 hours)
        game_state.fast_travel("Mountain Pass")

        expected_increase = 4 * 3  # 3 per hour, 4 hours
        expected_tiredness = min(100, initial_tiredness + expected_increase)
        assert game_state.current_character.tiredness.current == expected_tiredness

    def test_time_advances_correctly(self):
        """Game time advances by travel hours."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")
        initial_hour = game_state.game_time.hour

        # Forest Clearing is at (4, 0), distance = 4
        # Travel time = 4 // 4 = 1 hour
        game_state.fast_travel("Forest Clearing")

        hours_passed = (game_state.game_time.hour - initial_hour) % 24
        assert hours_passed == 1

    def test_player_arrives_at_destination(self):
        """current_location updated on success."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        success, message = game_state.fast_travel("Forest Clearing")

        assert success is True
        assert game_state.current_location == "Forest Clearing"

    def test_partial_name_matching(self):
        """Case-insensitive partial matching works."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        # Partial match
        success, message = game_state.fast_travel("forest")

        assert success is True
        assert game_state.current_location == "Forest Clearing"

    def test_case_insensitive_matching(self):
        """Case-insensitive matching works."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        success, message = game_state.fast_travel("FOREST CLEARING")

        assert success is True
        assert game_state.current_location == "Forest Clearing"


class TestFastTravelEncounters:
    """Tests for random encounters during travel.

    Spec: 15% per hour chance for encounter.
    """

    def test_encounter_can_interrupt_travel(self):
        """Combat encounter stops travel partway."""
        character = create_test_character()
        world = create_test_world()
        # Start from a non-safe-zone location to allow encounters
        game_state = GameState(character, world, "Forest Clearing")

        # Mock random to always trigger encounter (patch in game_state module)
        with patch('cli_rpg.game_state.random.random', return_value=0.10):  # < 0.15 triggers
            success, message = game_state.fast_travel("Mountain Pass")

        # Travel should still succeed (partial travel before encounter)
        assert success is True
        # Should be in combat
        assert game_state.is_in_combat()
        # Message should indicate ambush
        assert "Ambush" in message or "interrupted" in message.lower()

    def test_no_encounter_when_chance_fails(self):
        """No encounter when random check fails."""
        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        # Mock random to never trigger encounter (patch in game_state module)
        with patch('cli_rpg.game_state.random.random', return_value=0.99):  # > 0.15
            success, message = game_state.fast_travel("Forest Clearing")

        assert success is True
        assert not game_state.is_in_combat()
        assert game_state.current_location == "Forest Clearing"


class TestFastTravelCompletion:
    """Tests for tab completion."""

    def test_complete_travel_returns_destinations(self):
        """Completion returns valid destinations."""
        from cli_rpg.completer import CommandCompleter

        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        completer = CommandCompleter()
        completer.set_game_state(game_state)

        completions = completer._complete_travel("")

        # Should include named overworld locations except current
        assert "Forest Clearing" in completions
        assert "Mountain Pass" in completions
        # Should not include current location
        assert "Town Square" not in completions

    def test_partial_match_filters_destinations(self):
        """Only matching prefixes returned."""
        from cli_rpg.completer import CommandCompleter

        character = create_test_character()
        world = create_test_world()
        game_state = GameState(character, world, "Town Square")

        completer = CommandCompleter()
        completer.set_game_state(game_state)

        completions = completer._complete_travel("for")

        assert "Forest Clearing" in completions
        assert "Mountain Pass" not in completions
