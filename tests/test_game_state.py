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
        
        Spec: Unknown commands should return ("unknown", [])
        """
        cmd, args = parse_command("invalid")
        assert cmd == "unknown"
        assert args == []
    
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
    
    def test_game_state_creation_validates_world_connections(self):
        """Test that invalid location connections raise ValueError.
        
        Spec: Must raise ValueError if connection points to non-existent location
        """
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "A location", {"north": "NonExistent"})
        }
        
        with pytest.raises(ValueError, match="Connection.*points to non-existent location"):
            GameState(character, world, "Start")


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
