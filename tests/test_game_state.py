"""Tests for GameState class."""

import pytest
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location


class TestParseCommand:
    """Tests for parse_command() function."""
    
    def test_parse_command_look(self):
        """Test parsing 'look' command.
        
        Spec: 'look' should return ("look", [])
        """
        cmd, args = parse_command("look")
        assert cmd == "look"
        assert args == []
    
    def test_parse_command_go_with_direction(self):
        """Test parsing 'go' command with direction.
        
        Spec: 'go north' should return ("go", ["north"])
        """
        cmd, args = parse_command("go north")
        assert cmd == "go"
        assert args == ["north"]
    
    def test_parse_command_save(self):
        """Test parsing 'save' command.
        
        Spec: 'save' should return ("save", [])
        """
        cmd, args = parse_command("save")
        assert cmd == "save"
        assert args == []
    
    def test_parse_command_quit(self):
        """Test parsing 'quit' command.
        
        Spec: 'quit' should return ("quit", [])
        """
        cmd, args = parse_command("quit")
        assert cmd == "quit"
        assert args == []
    
    def test_parse_command_unknown(self):
        """Test parsing unknown command.

        Spec: Unknown commands should return ("unknown", [original_command])
        to enable 'Did you mean?' suggestions
        """
        cmd, args = parse_command("invalid")
        assert cmd == "unknown"
        assert args == ["invalid"]
    
    def test_parse_command_case_insensitive(self):
        """Test that command parsing is case insensitive.
        
        Spec: 'LOOK' should be treated same as 'look'
        """
        cmd, args = parse_command("LOOK")
        assert cmd == "look"
        assert args == []
        
        cmd, args = parse_command("Go NORTH")
        assert cmd == "go"
        assert args == ["north"]
    
    def test_parse_command_strips_whitespace(self):
        """Test that whitespace is stripped from commands.
        
        Spec: '  look  ' should return ("look", [])
        """
        cmd, args = parse_command("  look  ")
        assert cmd == "look"
        assert args == []
    
    def test_parse_command_go_missing_direction(self):
        """Test parsing 'go' without direction.
        
        Spec: 'go' should return ("go", [])
        """
        cmd, args = parse_command("go")
        assert cmd == "go"
        assert args == []
    
    def test_parse_command_attack(self):
        """Test parsing 'attack' command.
        
        Spec: 'attack' should return ("attack", [])
        """
        cmd, args = parse_command("attack")
        assert cmd == "attack"
        assert args == []
    
    def test_parse_command_defend(self):
        """Test parsing 'defend' command.
        
        Spec: 'defend' should return ("defend", [])
        """
        cmd, args = parse_command("defend")
        assert cmd == "defend"
        assert args == []
    
    def test_parse_command_flee(self):
        """Test parsing 'flee' command.
        
        Spec: 'flee' should return ("flee", [])
        """
        cmd, args = parse_command("flee")
        assert cmd == "flee"
        assert args == []
    
    def test_parse_command_status(self):
        """Test parsing 'status' command.

        Spec: 'status' should return ("status", [])
        """
        cmd, args = parse_command("status")
        assert cmd == "status"
        assert args == []

    def test_parse_command_help(self):
        """Test parsing 'help' command.

        Spec: 'help' should return ("help", [])
        """
        cmd, args = parse_command("help")
        assert cmd == "help"
        assert args == []

    def test_parse_command_empty_string(self):
        """Test parsing empty string.

        Spec: Empty string should return ("unknown", [])
        """
        cmd, args = parse_command("")
        assert cmd == "unknown"
        assert args == []

    def test_parse_command_whitespace_only(self):
        """Test parsing whitespace-only string.

        Spec: Whitespace-only string should return ("unknown", [])
        """
        cmd, args = parse_command("   ")
        assert cmd == "unknown"
        assert args == []

    def test_parse_command_movement_shortcuts_two_char(self):
        """Test ultra-short movement shortcuts (gn, gs, ge, gw).

        Spec: 'gn', 'gs', 'ge', 'gw' should map to 'go <direction>'
        """
        for shortcut, direction in [("gn", "north"), ("gs", "south"), ("ge", "east"), ("gw", "west")]:
            cmd, args = parse_command(shortcut)
            assert cmd == "go"
            assert args == [direction]

    def test_parse_command_movement_shortcuts_single_char(self):
        """Test single-char movement shortcuts (n, w) - s/e have existing meanings.

        Spec: 'n' and 'w' should map to 'go north' and 'go west'
        """
        for shortcut, direction in [("n", "north"), ("w", "west")]:
            cmd, args = parse_command(shortcut)
            assert cmd == "go"
            assert args == [direction]

    def test_parse_command_s_still_means_status(self):
        """Confirm 's' still maps to 'status' (not 'go south').

        Spec: 's' should remain as 'status' alias, not become 'go south'
        """
        cmd, args = parse_command("s")
        assert cmd == "status"

    def test_parse_command_e_still_means_equip(self):
        """Confirm 'e' still maps to 'equip' (not 'go east').

        Spec: 'e' should remain as 'equip' alias, not become 'go east'
        """
        cmd, args = parse_command("e")
        assert cmd == "equip"


class TestGameStateInit:
    """Tests for GameState.__init__()."""
    
    def test_game_state_creation_valid(self):
        """Test creating GameState with valid parameters.
        
        Spec: Should accept character, world dict, and starting location
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location", {"north": "End"}),
            "End": Location("End", "An ending location", {"south": "Start"})
        }
        
        game_state = GameState(character, world, "Start")
        assert game_state.current_character == character
        assert game_state.world == world
        assert game_state.current_location == "Start"
    
    def test_game_state_creation_defaults_to_town_square(self):
        """Test that default starting location is Town Square.
        
        Spec: Default starting_location should be "Town Square"
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town Square": Location("Town Square", "A town square")
        }
        
        game_state = GameState(character, world)
        assert game_state.current_location == "Town Square"
    
    def test_game_state_creation_custom_starting_location(self):
        """Test creating GameState with custom starting location.
        
        Spec: Should accept custom starting location
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Custom": Location("Custom", "A custom location")
        }
        
        game_state = GameState(character, world, "Custom")
        assert game_state.current_location == "Custom"
    
    def test_game_state_creation_invalid_character(self):
        """Test that non-Character raises TypeError.
        
        Spec: Must raise TypeError if character is not Character instance
        """
        world = {
            "Start": Location("Start", "A location")
        }
        
        with pytest.raises(TypeError, match="character must be a Character instance"):
            GameState("not a character", world, "Start")
    
    def test_game_state_creation_empty_world(self):
        """Test that empty world dict raises ValueError.
        
        Spec: Must raise ValueError if world is empty
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        
        with pytest.raises(ValueError, match="world cannot be empty"):
            GameState(character, {})
    
    def test_game_state_creation_invalid_starting_location(self):
        """Test that invalid starting location raises ValueError.
        
        Spec: Must raise ValueError if starting_location not in world
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A location")
        }
        
        with pytest.raises(ValueError, match="starting_location.*not found in world"):
            GameState(character, world, "NonExistent")
    
    def test_game_state_creation_allows_dangling_connections(self):
        """Test that dangling connections are allowed for infinite world principle.

        Spec: Dangling connections (pointing to non-existent locations) are allowed
        to support the "infinite world" principle where all locations have forward
        paths for future expansion.
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A location", {"north": "NonExistent"})
        }

        # Should NOT raise - dangling connections are allowed
        game_state = GameState(character, world, "Start")
        assert game_state.current_location == "Start"


class TestGameStateGetCurrentLocation:
    """Tests for GameState.get_current_location()."""
    
    def test_get_current_location_returns_location(self):
        """Test that method returns a Location instance.
        
        Spec: Should return Location instance
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location")
        }
        
        game_state = GameState(character, world, "Start")
        location = game_state.get_current_location()
        assert isinstance(location, Location)
    
    def test_get_current_location_returns_correct_location(self):
        """Test that method returns the current location object.
        
        Spec: Should return the Location corresponding to current_location
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        start = Location("Start", "A starting location")
        world = {"Start": start}
        
        game_state = GameState(character, world, "Start")
        location = game_state.get_current_location()
        assert location == start


class TestGameStateLook:
    """Tests for GameState.look()."""
    
    def test_look_returns_string(self):
        """Test that look() returns a string.
        
        Spec: Should return string
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location")
        }
        
        game_state = GameState(character, world, "Start")
        result = game_state.look()
        assert isinstance(result, str)
    
    def test_look_contains_location_info(self):
        """Test that look() contains location name, description, and exits.
        
        Spec: Should contain name, description, exits
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location", {"north": "End"}),
            "End": Location("End", "An ending location")
        }
        
        game_state = GameState(character, world, "Start")
        result = game_state.look()
        
        assert "Start" in result
        assert "A starting location" in result
        assert "north" in result or "Exits" in result
    
    def test_look_format_matches_location_str(self):
        """Test that look() format matches Location.__str__().
        
        Spec: Format should match Location.__str__()
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        location = Location("Start", "A starting location", {"north": "End"})
        world = {"Start": location, "End": Location("End", "An ending location")}
        
        game_state = GameState(character, world, "Start")
        result = game_state.look()
        
        assert result == str(location)


class TestGameStateMove:
    """Tests for GameState.move()."""
    
    def test_move_valid_direction_success(self):
        """Test moving in valid direction returns success.
        
        Spec: Should return (True, success_message)
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }
        
        game_state = GameState(character, world, "Start")
        success, message = game_state.move("north")
        
        assert success is True
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_move_valid_direction_updates_location(self):
        """Test that moving updates current_location.
        
        Spec: current_location should change to destination
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }
        
        game_state = GameState(character, world, "Start")
        game_state.move("north")
        
        assert game_state.current_location == "End"
    
    def test_move_invalid_direction_failure(self):
        """Test moving in invalid direction returns failure.
        
        Spec: Should return (False, error_message)
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        
        game_state = GameState(character, world, "Start")
        success, message = game_state.move("north")
        
        assert success is False
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_move_invalid_direction_no_change(self):
        """Test that invalid move doesn't change location.
        
        Spec: current_location should remain unchanged
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        
        game_state = GameState(character, world, "Start")
        game_state.move("north")
        
        assert game_state.current_location == "Start"
    
    def test_move_nonexistent_direction_failure(self):
        """Test moving in direction with no connection fails.

        Spec: Should return (False, error) for direction with no connection
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }

        game_state = GameState(character, world, "Start")
        success, message = game_state.move("south")

        assert success is False

    def test_move_unsupported_direction_shows_invalid_message(self):
        """Test that unsupported directions show a different error than blocked exits.

        Spec: 'up', 'northwest', etc. should say "Invalid direction" not "You can't go that way."
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location")
        }

        game_state = GameState(character, world, "Start")

        # Test unsupported directions
        for invalid_dir in ["up", "northwest", "left", "forward", "xyz"]:
            success, message = game_state.move(invalid_dir)
            assert success is False
            assert "Invalid direction" in message, f"Expected 'Invalid direction' for '{invalid_dir}', got: {message}"

        # Verify blocked exit still shows original message
        success, message = game_state.move("south")  # valid direction, no exit
        assert success is False
        assert "can't go that way" in message.lower()

    def test_move_chain_navigation(self):
        """Test multiple moves in sequence work correctly.
        
        Spec: Multiple moves should work correctly
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Room A": Location("Room A", "Location A", {"north": "Room B"}),
            "Room B": Location("Room B", "Location B", {"south": "Room A", "east": "Room C"}),
            "Room C": Location("Room C", "Location C", {"west": "Room B"})
        }
        
        game_state = GameState(character, world, "Room A")
        
        # Move Room A -> Room B
        success, _ = game_state.move("north")
        assert success is True
        assert game_state.current_location == "Room B"
        
        # Move Room B -> Room C
        success, _ = game_state.move("east")
        assert success is True
        assert game_state.current_location == "Room C"
        
        # Move Room C -> Room B
        success, _ = game_state.move("west")
        assert success is True
        assert game_state.current_location == "Room B"


class TestGameStateCoordinateBasedMovement:
    """Tests for coordinate-based movement to prevent circular wrapping.

    Spec: Movement should check coordinates to avoid circular wrapping caused
    by incorrect connections in Location objects.
    """

    def test_move_uses_coordinates_not_just_connections(self, tmp_path, monkeypatch):
        """Movement should check coordinates to avoid circular wrapping.

        Spec: When a location has a misleading connection that would violate
        coordinate consistency, the move should use coordinates to find the
        correct destination. With infinite world, a new location is generated
        if no location exists at target coords - but it should NOT follow a
        bad connection that points to the wrong coordinates.
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        loc_a = Location("Origin", "Location A", coordinates=(0, 0))
        loc_b = Location("West1", "Location B", coordinates=(-1, 0))

        # West1 has a west connection that would loop back to Origin (wrong!)
        loc_a.connections = {"west": "West1"}
        loc_b.connections = {"east": "Origin", "west": "Origin"}  # Bad: west should NOT point to Origin

        world = {"Origin": loc_a, "West1": loc_b}
        game_state = GameState(character, world, "Origin")

        # Move west to West1
        success, msg = game_state.move("west")
        assert success
        assert game_state.current_location == "West1"

        # Move west from West1 - should NOT go to Origin (that's at 0,0, not -2,0)
        # With infinite world, a new fallback location is generated at (-2,0)
        success, msg = game_state.move("west")
        assert success is True
        # Key: we should NOT have gone back to Origin (which is at 0,0, not -2,0)
        assert game_state.current_location != "Origin"
        # We should be at the new location at (-2, 0)
        current_loc = game_state.get_current_location()
        assert current_loc.coordinates == (-2, 0)

    def test_move_with_coordinates_goes_to_correct_location(self, tmp_path, monkeypatch):
        """Movement should follow coordinates even if connection name differs.

        Spec: When target coordinates have a location, move to that location
        regardless of what the connection says.
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        loc_a = Location("Origin", "Location A", coordinates=(0, 0))
        loc_b = Location("West1", "Location B", coordinates=(-1, 0))
        loc_c = Location("West2", "Location C", coordinates=(-2, 0))

        # Connection says "West1" but we add proper bidirectional connections
        loc_a.connections = {"west": "West1"}
        loc_b.connections = {"east": "Origin", "west": "West2"}
        loc_c.connections = {"east": "West1"}

        world = {"Origin": loc_a, "West1": loc_b, "West2": loc_c}
        game_state = GameState(character, world, "Origin")

        # Move to West1
        success, _ = game_state.move("west")
        assert success
        assert game_state.current_location == "West1"

        # Move to West2
        success, _ = game_state.move("west")
        assert success
        assert game_state.current_location == "West2"

        # Move back east should return to West1
        success, _ = game_state.move("east")
        assert success
        assert game_state.current_location == "West1"

    def test_move_falls_back_to_connection_for_legacy_locations(self, tmp_path, monkeypatch):
        """Locations without coordinates should use connection-based movement.

        Spec: Backward compatibility with legacy saves that don't have coordinates.
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Locations without coordinates (legacy)
        loc_a = Location("Origin", "Location A")
        loc_b = Location("West1", "Location B")

        loc_a.connections = {"west": "West1"}
        loc_b.connections = {"east": "Origin"}

        world = {"Origin": loc_a, "West1": loc_b}
        game_state = GameState(character, world, "Origin")

        # Should still work with connection-based movement
        success, _ = game_state.move("west")
        assert success
        assert game_state.current_location == "West1"

    def test_move_with_connection_to_existing_location(self, monkeypatch):
        """Movement with connection succeeds and finds location by coordinates.

        Spec: When a connection exists and a location exists at target coordinates,
        the system should move to that location by coordinate lookup (not by
        connection name), ensuring spatial consistency.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Location at (0,0) with connections to all 4 directions including east
        loc_a = Location(
            "Origin", "Location A",
            {"north": "North", "south": "South", "west": "West", "east": "East"},
            coordinates=(0, 0)
        )
        loc_north = Location("North", "North location", {"south": "Origin"}, coordinates=(0, 1))
        loc_south = Location("South", "South location", {"north": "Origin"}, coordinates=(0, -1))
        loc_west = Location("West", "West location", {"east": "Origin"}, coordinates=(-1, 0))
        loc_east = Location("East", "East location", {"west": "Origin"}, coordinates=(1, 0))

        world = {
            "Origin": loc_a, "North": loc_north, "South": loc_south,
            "West": loc_west, "East": loc_east
        }
        game_state = GameState(character, world, "Origin")

        # Moving east should succeed - connection exists and location at target coords
        success, message = game_state.move("east")
        assert success is True, f"Expected success but got failure with message: {message}"
        assert game_state.current_location == "East"

    def test_move_blocked_when_no_connection_coordinate_mode(self, monkeypatch):
        """Movement fails when no connection exists in coordinate-based mode.

        Spec: Moving in a direction without a connection should fail with
        "You can't go that way" even when the location has coordinates.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        # Location WITH coordinates but only north connection
        loc = Location("Town", "A town", connections={"north": "Forest"}, coordinates=(0, 0))
        world = {"Town": loc}
        game_state = GameState(character, world, "Town")

        # Try to go south - no connection exists
        success, msg = game_state.move("south")

        assert success is False
        assert "can't go that way" in msg.lower()
        assert game_state.current_location == "Town"
        # World should NOT have a new location generated
        assert len(game_state.world) == 1


class TestGameStateSerialization:
    """Tests for GameState serialization."""
    
    def test_game_state_to_dict(self):
        """Test that to_dict() returns a dictionary.
        
        Spec: Should return dict structure
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        
        game_state = GameState(character, world, "Start")
        data = game_state.to_dict()
        
        assert isinstance(data, dict)
    
    def test_game_state_to_dict_contains_all_data(self):
        """Test that to_dict() contains character, location, and world.
        
        Spec: Should contain character, current_location, world
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location")
        }
        
        game_state = GameState(character, world, "Start")
        data = game_state.to_dict()
        
        assert "character" in data
        assert "current_location" in data
        assert "world" in data
    
    def test_game_state_from_dict(self):
        """Test that from_dict() deserializes successfully.
        
        Spec: Should create GameState from dict
        """
        data = {
            "character": {
                "name": "Hero",
                "strength": 10,
                "dexterity": 10,
                "intelligence": 10,
                "level": 1,
                "health": 150,
                "max_health": 150
            },
            "current_location": "Start",
            "world": {
                "Start": {
                    "name": "Start",
                    "description": "Start location",
                    "connections": {}
                }
            }
        }
        
        game_state = GameState.from_dict(data)
        
        assert isinstance(game_state, GameState)
        assert game_state.current_location == "Start"
    
    def test_game_state_from_dict_validates_data(self):
        """Test that from_dict() validates data.
        
        Spec: Should raise errors for invalid data
        """
        # Missing character
        with pytest.raises(KeyError):
            GameState.from_dict({"current_location": "Start", "world": {}})
        
        # Missing world
        with pytest.raises(KeyError):
            GameState.from_dict({
                "character": {"name": "Hero", "strength": 10, "dexterity": 10, "intelligence": 10},
                "current_location": "Start"
            })
    
    def test_game_state_roundtrip_serialization(self):
        """Test that to_dict -> from_dict preserves state.
        
        Spec: Serialize and deserialize should preserve complete state
        """
        character = Character("Hero", strength=12, dexterity=15, intelligence=8)
        world = {
            "Start": Location("Start", "Start location", {"north": "End"}),
            "End": Location("End", "End location", {"south": "Start"})
        }
        
        game_state = GameState(character, world, "Start")
        
        # Move to test location preservation
        game_state.move("north")
        
        # Serialize and deserialize
        data = game_state.to_dict()
        restored = GameState.from_dict(data)
        
        # Verify character
        assert restored.current_character.name == "Hero"
        assert restored.current_character.strength == 12
        assert restored.current_character.dexterity == 15
        assert restored.current_character.intelligence == 8
        
        # Verify location
        assert restored.current_location == "End"
        
        # Verify world
        assert "Start" in restored.world
        assert "End" in restored.world
        assert restored.world["Start"].get_connection("north") == "End"
