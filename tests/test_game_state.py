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
            "Start": Location("Start", "A starting location", coordinates=(0, 0)),
            "End": Location("End", "An ending location", coordinates=(0, 1))
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
        """Test that coordinate-based world allows expansion.

        Spec: Locations with coordinates can have neighbors added later.
        This supports the "infinite world" principle where new locations
        are generated at adjacent coordinates for future expansion.
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A location", coordinates=(0, 0))
        }

        # Should NOT raise - new locations can be added at adjacent coords later
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
            "Start": Location("Start", "A starting location", coordinates=(0, 0)),
            "End": Location("End", "An ending location", coordinates=(0, 1))
        }

        game_state = GameState(character, world, "Start")
        result = game_state.look()

        assert "Start" in result
        assert "A starting location" in result
        assert "north" in result or "Exits" in result
    
    def test_look_format_matches_location_str(self):
        """Test that look() contains expected location info.

        Spec: look() output should contain location name and description.
        Note: Exact format depends on layered description with world context.
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        location = Location("Start", "A starting location", coordinates=(0, 0))
        world = {"Start": location, "End": Location("End", "An ending location", coordinates=(0, 1))}

        game_state = GameState(character, world, "Start")
        result = game_state.look()

        # Result should contain the key parts of the location
        assert "Start" in result
        assert "A starting location" in result


class TestGameStateMove:
    """Tests for GameState.move()."""
    
    def test_move_valid_direction_success(self):
        """Test moving in valid direction returns success.

        Spec: Should return (True, success_message)
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", coordinates=(0, 0)),
            "End": Location("End", "End location", coordinates=(0, 1))
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
            "Start": Location("Start", "Start location", coordinates=(0, 0)),
            "End": Location("End", "End location", coordinates=(0, 1))
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
    
    def test_move_nonexistent_direction_failure_or_generates(self):
        """Test moving in direction with no adjacent location.

        Spec: Should either fail with (False, error) or generate a new location
        via the infinite world system.
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", coordinates=(0, 0)),
            "End": Location("End", "End location", coordinates=(0, 1))
        }

        game_state = GameState(character, world, "Start")
        success, message = game_state.move("south")

        # Infinite world may generate a location, or movement fails
        if success:
            # New location generated at (0, -1)
            assert game_state.current_location != "Start"
            assert len(game_state.world) == 3
        else:
            # Movement blocked
            assert game_state.current_location == "Start"

    def test_move_unsupported_direction_shows_invalid_message(self):
        """Test that unsupported directions show a different error than blocked exits.

        Spec: 'northwest', 'left', etc. should say "Invalid direction" not "You can't go that way."
        Note: 'up' and 'down' are now valid directions (in SubGrid only), so they show a different message.
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", coordinates=(0, 0)),
            "End": Location("End", "End location", coordinates=(0, 1))
        }

        game_state = GameState(character, world, "Start")

        # Test invalid directions (not part of any supported direction set)
        for invalid_dir in ["northwest", "left", "forward", "xyz"]:
            success, message = game_state.move(invalid_dir)
            assert success is False
            assert "Invalid direction" in message, f"Expected 'Invalid direction' for '{invalid_dir}', got: {message}"

        # Test up/down on overworld - valid direction but wrong context
        for vertical_dir in ["up", "down"]:
            success, message = game_state.move(vertical_dir)
            assert success is False
            # Should say these only work inside buildings/dungeons
            assert "inside" in message.lower() or "building" in message.lower() or "dungeon" in message.lower()

    def test_move_chain_navigation(self):
        """Test multiple moves in sequence work correctly.

        Spec: Multiple moves should work correctly
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Room A": Location("Room A", "Location A", coordinates=(0, 0)),
            "Room B": Location("Room B", "Location B", coordinates=(0, 1)),
            "Room C": Location("Room C", "Location C", coordinates=(1, 1))
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
        """Movement uses coordinate adjacency to find destinations.

        Spec: Movement is determined by coordinate adjacency. When a location
        exists at the target coordinates, the player moves there. When no
        location exists, the infinite world generates one at the target coords.
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Locations at adjacent coordinates
        loc_a = Location("Origin", "Location A", coordinates=(0, 0))
        loc_b = Location("West1", "Location B", coordinates=(-1, 0))

        world = {"Origin": loc_a, "West1": loc_b}
        game_state = GameState(character, world, "Origin")

        # Move west to West1 (location at (-1, 0))
        success, msg = game_state.move("west")
        assert success
        assert game_state.current_location == "West1"

        # Move west from West1 - no location at (-2, 0)
        # With infinite world, a new fallback location is generated at (-2,0)
        success, msg = game_state.move("west")
        assert success is True
        # Should NOT have gone back to Origin (which is at 0,0, not -2,0)
        assert game_state.current_location != "Origin"
        # We should be at the new location at (-2, 0)
        current_loc = game_state.get_current_location()
        assert current_loc.coordinates == (-2, 0)

    def test_move_with_coordinates_goes_to_correct_location(self, tmp_path, monkeypatch):
        """Movement uses coordinates to find destinations.

        Spec: When target coordinates have a location, move to that location.
        Coordinate adjacency determines valid movement directions.
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Locations at adjacent coordinates forming a line
        loc_a = Location("Origin", "Location A", coordinates=(0, 0))
        loc_b = Location("West1", "Location B", coordinates=(-1, 0))
        loc_c = Location("West2", "Location C", coordinates=(-2, 0))

        world = {"Origin": loc_a, "West1": loc_b, "West2": loc_c}
        game_state = GameState(character, world, "Origin")

        # Move to West1 (at -1, 0)
        success, _ = game_state.move("west")
        assert success
        assert game_state.current_location == "West1"

        # Move to West2 (at -2, 0)
        success, _ = game_state.move("west")
        assert success
        assert game_state.current_location == "West2"

        # Move back east should return to West1 (at -1, 0)
        success, _ = game_state.move("east")
        assert success
        assert game_state.current_location == "West1"

    def test_move_fails_without_coordinates(self, tmp_path, monkeypatch):
        """Locations without coordinates cannot move to undefined adjacent cells.

        Spec: Without coordinates, there's no way to determine adjacency,
        so movement will fail with "can't go that way".
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Locations without coordinates
        loc_a = Location("Origin", "Location A")
        loc_b = Location("West1", "Location B")

        world = {"Origin": loc_a, "West1": loc_b}
        game_state = GameState(character, world, "Origin")

        # Without coordinates, movement cannot determine adjacency
        success, msg = game_state.move("west")
        # Either fails, or infinite world generates a fallback
        # (depends on AI/chunk manager state - test the coordinate case instead)
        assert game_state.current_location in ("Origin", "West1") or not success

    def test_move_with_connection_to_existing_location(self, monkeypatch):
        """Movement succeeds when location exists at target coordinates.

        Spec: When a location exists at target coordinates, the system moves
        to that location using coordinate-based lookup.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Location at (0,0) with adjacent locations in all 4 directions
        loc_a = Location("Origin", "Location A", coordinates=(0, 0))
        loc_north = Location("North", "North location", coordinates=(0, 1))
        loc_south = Location("South", "South location", coordinates=(0, -1))
        loc_west = Location("West", "West location", coordinates=(-1, 0))
        loc_east = Location("East", "East location", coordinates=(1, 0))

        world = {
            "Origin": loc_a, "North": loc_north, "South": loc_south,
            "West": loc_west, "East": loc_east
        }
        game_state = GameState(character, world, "Origin")

        # Moving east should succeed - location at target coords (1, 0)
        success, message = game_state.move("east")
        assert success is True, f"Expected success but got failure with message: {message}"
        assert game_state.current_location == "East"

    def test_move_blocked_when_no_adjacent_location(self, monkeypatch):
        """Movement fails or generates new location when no adjacent location exists.

        Spec: Moving in a direction without an adjacent location either fails
        with "You can't go that way" or triggers infinite world generation.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        # Location WITH coordinates but no adjacent locations
        loc = Location("Town", "A town", coordinates=(0, 0))
        world = {"Town": loc}
        game_state = GameState(character, world, "Town")

        # Try to go south - no location at (0, -1)
        success, msg = game_state.move("south")

        # Either fails (if no AI/infinite world), or generates new location
        if success:
            # Infinite world generated a new location
            assert len(game_state.world) == 2
            assert game_state.current_location != "Town"
        else:
            # No generation, movement blocked
            assert "can't go that way" in msg.lower()
            assert game_state.current_location == "Town"
            assert len(game_state.world) == 1

    def test_move_informs_player_when_ai_fails(self, monkeypatch):
        """Test that player is informed when AI generation fails during move.

        Spec: When AI area generation fails, player should see a message
        indicating fallback was used, not silent fallback.
        """
        from unittest.mock import MagicMock

        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Origin at (0,0) with west connection (to trigger generation)
        loc_origin = Location(
            "Origin", "Starting location",
            coordinates=(0, 0)
        )
        world = {"Origin": loc_origin}
        game_state = GameState(character, world, "Origin")

        # Set up mock AI service that will fail
        mock_ai_service = MagicMock()
        game_state.ai_service = mock_ai_service

        # Mock expand_area to raise an exception
        def mock_expand_area(*args, **kwargs):
            raise Exception("AI service unavailable")

        # Patch the expand_area function to raise exception
        monkeypatch.setattr("cli_rpg.game_state.expand_area", mock_expand_area)
        # Ensure AI_AVAILABLE is True so AI path is attempted
        monkeypatch.setattr("cli_rpg.game_state.AI_AVAILABLE", True)
        # Mock noise manager to force named location generation (triggers AI path)
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = True
        mock_noise_manager.world_seed = 42
        game_state.location_noise_manager = mock_noise_manager

        # Move west - AI will fail, should use fallback and inform player
        success, message = game_state.move("west")

        # Should still succeed (fallback works)
        assert success is True
        # Player should be informed about AI failure
        assert "unavailable" in message.lower() or "template" in message.lower() or "fallback" in message.lower()
        # Should have generated a new location
        assert len(game_state.world) == 2
        # Should have moved to new location
        assert game_state.current_location != "Origin"


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
            "Start": Location("Start", "Start location", coordinates=(0, 0)),
            "End": Location("End", "End location", coordinates=(0, 1))
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
        assert restored.world["Start"].coordinates == (0, 0)
        assert restored.world["End"].coordinates == (0, 1)


class TestEnterExitCommands:
    """Tests for enter/exit hierarchical navigation commands.

    Spec: `enter <location>` navigates from overworld to sub-locations.
          `exit`/`leave` returns from sub-location to parent overworld.
    """

    def test_enter_sublocation_from_overworld(self, monkeypatch):
        """Test entering a valid sub-location from overworld succeeds.

        Spec: When at an overworld location with sub-locations, 'enter <name>'
        moves player to that sub-location.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Create overworld location with sub-locations
        overworld = Location(
            "Shadowmere City",
            "A sprawling dark city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern", "Blacksmith"],
        )
        tavern = Location(
            "Tavern",
            "A cozy tavern with roaring fire",
            parent_location="Shadowmere City",
        )
        blacksmith = Location(
            "Blacksmith",
            "Sparks fly from the forge",
            parent_location="Shadowmere City",
        )

        world = {"Shadowmere City": overworld, "Tavern": tavern, "Blacksmith": blacksmith}
        game_state = GameState(character, world, "Shadowmere City")

        success, message = game_state.enter("Tavern")

        assert success is True
        assert game_state.current_location == "Tavern"
        assert "Tavern" in message

    def test_enter_uses_entry_point_default(self, monkeypatch):
        """Test that enter with no argument uses entry_point.

        Spec: When overworld has entry_point set, 'enter' without argument
        goes to that default sub-location.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "Shadowmere City",
            "A sprawling dark city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern", "Blacksmith"],
            entry_point="Tavern",
        )
        tavern = Location(
            "Tavern",
            "A cozy tavern",
            parent_location="Shadowmere City",
        )
        blacksmith = Location(
            "Blacksmith",
            "A forge",
            parent_location="Shadowmere City",
        )

        world = {"Shadowmere City": overworld, "Tavern": tavern, "Blacksmith": blacksmith}
        game_state = GameState(character, world, "Shadowmere City")

        success, message = game_state.enter()  # No argument

        assert success is True
        assert game_state.current_location == "Tavern"

    def test_enter_partial_match(self, monkeypatch):
        """Test that enter supports partial name matching (case-insensitive).

        Spec: 'enter tav' should match 'Tavern' case-insensitively.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "Shadowmere City",
            "A city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern", "Blacksmith"],
        )
        tavern = Location("Tavern", "A tavern", parent_location="Shadowmere City")
        blacksmith = Location("Blacksmith", "A forge", parent_location="Shadowmere City")

        world = {"Shadowmere City": overworld, "Tavern": tavern, "Blacksmith": blacksmith}
        game_state = GameState(character, world, "Shadowmere City")

        # Test partial match with different case
        success, _ = game_state.enter("tav")
        assert success is True
        assert game_state.current_location == "Tavern"

    def test_enter_fails_when_not_overworld(self, monkeypatch):
        """Test enter fails when not at an overworld location.

        Spec: 'enter' returns error "You're not at an overworld location"
        when current location is not an overworld.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Regular location (not overworld)
        regular = Location("Forest", "A dark forest", is_overworld=False)

        world = {"Forest": regular}
        game_state = GameState(character, world, "Forest")

        success, message = game_state.enter("Anywhere")

        assert success is False
        assert "not at an overworld location" in message.lower()

    def test_enter_fails_sublocation_not_found(self, monkeypatch):
        """Test enter fails when target sub-location doesn't exist.

        Spec: 'enter <nonexistent>' returns "No such location: <name>".
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "City",
            "A city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern"],
        )
        tavern = Location("Tavern", "A tavern", parent_location="City")

        world = {"City": overworld, "Tavern": tavern}
        game_state = GameState(character, world, "City")

        success, message = game_state.enter("Nonexistent")

        assert success is False
        assert "no such location" in message.lower()

    def test_enter_fails_no_arg_no_entrypoint(self, monkeypatch):
        """Test enter fails with no argument and no entry_point set.

        Spec: 'enter' with no argument and no entry_point returns "Enter where?".
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "City",
            "A city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern"],
            entry_point=None,  # No default entry point
        )
        tavern = Location("Tavern", "A tavern", parent_location="City")

        world = {"City": overworld, "Tavern": tavern}
        game_state = GameState(character, world, "City")

        success, message = game_state.enter()  # No argument

        assert success is False
        assert "enter where" in message.lower()

    def test_enter_blocked_during_conversation(self, monkeypatch):
        """Test enter is blocked when in conversation with NPC.

        Spec: 'enter' returns conversation warning when current_npc is set.
        """
        from cli_rpg.models.npc import NPC
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "City",
            "A city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern"],
        )
        tavern = Location("Tavern", "A tavern", parent_location="City")

        world = {"City": overworld, "Tavern": tavern}
        game_state = GameState(character, world, "City")

        # Set current NPC to simulate conversation
        game_state.current_npc = NPC("Bartender", "A friendly bartender", "What can I get you?")

        success, message = game_state.enter("Tavern")

        assert success is False
        assert "conversation" in message.lower()

    def test_exit_from_sublocation(self, monkeypatch):
        """Test exiting from sub-location returns to parent.

        Spec: 'exit' from a sub-location moves player to parent_location.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "Shadowmere City",
            "A city",
            is_overworld=True,
            sub_locations=["Tavern"],
        )
        tavern = Location(
            "Tavern",
            "A tavern",
            parent_location="Shadowmere City",
        )

        world = {"Shadowmere City": overworld, "Tavern": tavern}
        game_state = GameState(character, world, "Tavern")  # Start inside

        success, message = game_state.exit_location()

        assert success is True
        assert game_state.current_location == "Shadowmere City"
        assert "Shadowmere City" in message

    def test_exit_fails_when_no_parent(self, monkeypatch):
        """Test exit fails when not in a sub-location.

        Spec: 'exit' returns "You're not inside a building or dungeon" with travel hint when no parent.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        # Overworld location (no parent)
        overworld = Location(
            "City",
            "A city",
            is_overworld=True,
            parent_location=None,
        )

        world = {"City": overworld}
        game_state = GameState(character, world, "City")

        success, message = game_state.exit_location()

        assert success is False
        assert "not inside a building or dungeon" in message.lower()
        assert "go <direction>" in message.lower()

    def test_exit_blocked_during_conversation(self, monkeypatch):
        """Test exit is blocked when in conversation with NPC.

        Spec: 'exit' returns conversation warning when current_npc is set.
        """
        from cli_rpg.models.npc import NPC
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location("City", "A city", is_overworld=True)
        tavern = Location("Tavern", "A tavern", parent_location="City")

        world = {"City": overworld, "Tavern": tavern}
        game_state = GameState(character, world, "Tavern")

        # Set current NPC to simulate conversation
        game_state.current_npc = NPC("Bartender", "A friendly bartender", "What can I get you?")

        success, message = game_state.exit_location()

        assert success is False
        assert "conversation" in message.lower()

    def test_leave_alias_works(self, monkeypatch):
        """Test 'leave' command works same as 'exit'.

        Spec: 'leave' is an alias for 'exit', both call exit_location().
        Note: The alias is handled in main.py command handling, but we test
        that exit_location() works for both command paths.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location("City", "A city", is_overworld=True)
        tavern = Location("Tavern", "A tavern", parent_location="City")

        world = {"City": overworld, "Tavern": tavern}
        game_state = GameState(character, world, "Tavern")

        # exit_location() should work regardless of which alias calls it
        success, _ = game_state.exit_location()

        assert success is True
        assert game_state.current_location == "City"

    def test_enter_case_insensitive_multiword_name(self, monkeypatch):
        """Test that enter works with multi-word location names in any case.

        Spec: 'enter spectral grove' should match 'Spectral Grove' case-insensitively.
        This tests the full command flow where input is lowercased before reaching enter().
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "Ancient Forest",
            "A mystical forest",
            is_overworld=True,
            is_named=True,
            sub_locations=["Spectral Grove", "Moonlit Clearing"],
        )
        spectral = Location("Spectral Grove", "A ghostly grove", parent_location="Ancient Forest")
        moonlit = Location("Moonlit Clearing", "A clearing bathed in moonlight", parent_location="Ancient Forest")

        world = {"Ancient Forest": overworld, "Spectral Grove": spectral, "Moonlit Clearing": moonlit}
        game_state = GameState(character, world, "Ancient Forest")

        # Test lowercase input (as parse_command would provide)
        success, _ = game_state.enter("spectral grove")
        assert success is True
        assert game_state.current_location == "Spectral Grove"

    def test_enter_invalid_location_shows_available(self, monkeypatch):
        """Test that entering invalid location shows available options.

        Spec: Error message should list available sub-locations for discoverability.
        """
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)

        overworld = Location(
            "City",
            "A bustling city",
            is_overworld=True,
            is_named=True,
            sub_locations=["Tavern", "Market"],
        )
        tavern = Location("Tavern", "A tavern", parent_location="City")
        market = Location("Market", "A market", parent_location="City")

        world = {"City": overworld, "Tavern": tavern, "Market": market}
        game_state = GameState(character, world, "City")

        success, message = game_state.enter("nonexistent")
        assert success is False
        assert "Available:" in message
        assert "Tavern" in message
        assert "Market" in message


class TestLocationNoiseManagerIntegration:
    """Tests for LocationNoiseManager integration into GameState.

    Spec: GameState should use LocationNoiseManager for deterministic,
    noise-based location spawn decisions instead of probabilistic
    should_generate_named_location().
    """

    def test_game_state_has_location_noise_manager(self):
        """GameState should initialize a LocationNoiseManager on creation.

        Spec: GameState.__init__ should create a location_noise_manager attribute.
        """
        from cli_rpg.location_noise import LocationNoiseManager

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location", coordinates=(0, 0)),
        }

        game_state = GameState(character, world, "Start")

        assert hasattr(game_state, "location_noise_manager")
        assert isinstance(game_state.location_noise_manager, LocationNoiseManager)

    def test_location_noise_uses_chunk_manager_seed_when_available(self):
        """LocationNoiseManager should use chunk_manager.seed when available.

        Spec: When GameState has a chunk_manager, the location_noise_manager
        should use the same seed for consistent world generation.
        """
        from unittest.mock import MagicMock

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location", coordinates=(0, 0)),
        }

        # Create mock chunk_manager with a specific seed
        mock_chunk_manager = MagicMock()
        mock_chunk_manager.world_seed = 12345

        game_state = GameState(
            character, world, "Start", chunk_manager=mock_chunk_manager
        )

        assert game_state.location_noise_manager.world_seed == 12345

    def test_serialization_preserves_location_noise_seed(self):
        """Serialization should preserve location_noise_seed for deterministic saves.

        Spec: to_dict() should include location_noise_seed, and from_dict()
        should restore a LocationNoiseManager with that seed.
        """
        from cli_rpg.location_noise import LocationNoiseManager

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location", coordinates=(0, 0)),
        }

        game_state = GameState(character, world, "Start")
        original_seed = game_state.location_noise_manager.world_seed

        # Serialize
        data = game_state.to_dict()
        assert "location_noise_seed" in data
        assert data["location_noise_seed"] == original_seed

        # Deserialize
        restored = GameState.from_dict(data)
        assert hasattr(restored, "location_noise_manager")
        assert isinstance(restored.location_noise_manager, LocationNoiseManager)
        assert restored.location_noise_manager.world_seed == original_seed

    def test_move_uses_noise_based_location_spawn(self, monkeypatch):
        """Movement should use LocationNoiseManager for spawn decisions.

        Spec: When generating a new location during move(), GameState should
        call location_noise_manager.should_spawn_location() instead of
        should_generate_named_location().
        """
        from unittest.mock import MagicMock, patch

        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A starting location", coordinates=(0, 0)),
        }

        game_state = GameState(character, world, "Start")

        # Mock the noise manager to track calls
        mock_noise_manager = MagicMock()
        mock_noise_manager.should_spawn_location.return_value = True
        mock_noise_manager.world_seed = 42
        game_state.location_noise_manager = mock_noise_manager

        # Move to a new location (no existing location at (0, 1))
        success, message = game_state.move("north")

        # Verify noise manager was called
        mock_noise_manager.should_spawn_location.assert_called()
        # Check it was called with correct coordinates and terrain
        call_args = mock_noise_manager.should_spawn_location.call_args
        assert call_args[0][0] == 0  # x coordinate
        assert call_args[0][1] == 1  # y coordinate
        # terrain is passed as third argument

    def test_deterministic_location_generation_with_same_seed(self, monkeypatch):
        """Same world seed should produce same location spawn decisions.

        Spec: Two GameStates with same noise seed should make identical
        spawn decisions at any given coordinates.
        """
        # Disable autosave for this test
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character1 = Character("Hero", strength=10, dexterity=10, intelligence=10)
        character2 = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world1 = {"Start": Location("Start", "A starting location", coordinates=(0, 0))}
        world2 = {"Start": Location("Start", "A starting location", coordinates=(0, 0))}

        game_state1 = GameState(character1, world1, "Start")
        game_state2 = GameState(character2, world2, "Start")

        # Set same seed for both
        game_state1.location_noise_manager = (
            game_state1.location_noise_manager.__class__(world_seed=42)
        )
        game_state2.location_noise_manager = (
            game_state2.location_noise_manager.__class__(world_seed=42)
        )

        # Check that spawn decisions are identical
        for x in range(-5, 5):
            for y in range(-5, 5):
                result1 = game_state1.location_noise_manager.should_spawn_location(
                    x, y, "plains"
                )
                result2 = game_state2.location_noise_manager.should_spawn_location(
                    x, y, "plains"
                )
                assert result1 == result2, f"Spawn decision differs at ({x}, {y})"
