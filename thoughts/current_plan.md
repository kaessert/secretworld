# Implementation Plan: GameState System with Basic Gameplay Loop

## 1. SPECIFICATION

### 1.1 GameState Class Specification (src/cli_rpg/game_state.py)

**Attributes:**
- `current_character: Character` - The player's character
- `current_location: str` - Name of the current location
- `world: dict[str, Location]` - Dictionary mapping location names to Location objects

**Methods:**
- `__init__(character: Character, world: dict[str, Location], starting_location: str = "Town Square")` - Initialize game state
- `get_current_location() -> Location` - Return the current Location object
- `move(direction: str) -> tuple[bool, str]` - Move to connected location, return (success: bool, message: str)
- `look() -> str` - Return formatted description of current location
- `to_dict() -> dict` - Serialize game state for saving
- `from_dict(data: dict) -> GameState` - Deserialize game state from dict

**Validation:**
- Character must be valid Character instance
- World must be non-empty dict
- Starting location must exist in world
- All locations in connections must exist in world (validated during initialization)

### 1.2 World Module Specification (src/cli_rpg/world.py)

**Function:**
- `create_default_world() -> dict[str, Location]` - Create and return default world with 3 locations

**Default World Structure:**
- **Town Square**: Central hub
  - Description: "A bustling town square with a fountain in the center. People go about their daily business."
  - Connections: north -> Forest, east -> Cave
  
- **Forest**: Northern location
  - Description: "A dense forest with tall trees blocking most of the sunlight. Strange sounds echo in the distance."
  - Connections: south -> Town Square
  
- **Cave**: Eastern location
  - Description: "A dark cave with damp walls. You can hear water dripping somewhere deeper inside."
  - Connections: west -> Town Square

### 1.3 Command Parser Specification

**Command Format:**
- `look` - Display current location details
- `go <direction>` - Move in specified direction (north, south, east, west, up, down)
- `save` - Save game state
- `quit` - Exit to main menu

**Parser Function (in game_state.py):**
- `parse_command(command_str: str) -> tuple[str, list[str]]` - Return (command, args)
- Returns ("unknown", []) for invalid commands
- Normalizes to lowercase, strips whitespace
- Splits on spaces

### 1.4 Gameplay Loop Specification (in main.py)

**Flow:**
1. After character creation/load, call `start_game(character: Character)`
2. Initialize game state with default world
3. Display welcome message and current location
4. Enter command loop:
   - Display prompt
   - Get user input
   - Parse command
   - Execute command
   - Handle results (display messages, errors)
   - Continue until quit or error

**Commands Implementation:**
- `look`: Call game_state.look(), display result
- `go <direction>`: Call game_state.move(direction), display result message
- `save`: Call enhanced save function (save game state), display confirmation
- `quit`: Confirm save, exit to main menu
- Invalid command: Display error message with available commands

### 1.5 Enhanced Persistence Specification

**New Functions (persistence.py):**
- `save_game_state(game_state: GameState, save_dir: str = "saves") -> str`
  - Saves complete game state (character + location + world)
  - Returns filepath
  
- `load_game_state(filepath: str) -> GameState`
  - Loads complete game state
  - Returns GameState instance
  - Validates world consistency

**Save Format (JSON):**
```json
{
  "character": {Character.to_dict()},
  "current_location": "Town Square",
  "world": {
    "Town Square": {Location.to_dict()},
    "Forest": {Location.to_dict()},
    "Cave": {Location.to_dict()}
  }
}
```

## 2. TEST DEVELOPMENT (TDD - Tests Before Implementation)

### 2.1 Create tests/test_world.py

**Tests for create_default_world():**
- `test_default_world_has_three_locations` - Verify 3 locations returned
- `test_default_world_location_names` - Verify correct location names (Town Square, Forest, Cave)
- `test_default_world_all_valid_locations` - Verify all are Location instances
- `test_default_world_town_square_connections` - Verify Town Square has north->Forest, east->Cave
- `test_default_world_forest_connections` - Verify Forest has south->Town Square
- `test_default_world_cave_connections` - Verify Cave has west->Town Square
- `test_default_world_locations_have_descriptions` - Verify non-empty descriptions
- `test_default_world_immutable_returns` - Verify multiple calls return independent copies

### 2.2 Create tests/test_game_state.py

**Tests for GameState.__init__():**
- `test_game_state_creation_valid` - Create with valid character, world, location
- `test_game_state_creation_defaults_to_town_square` - Verify default starting location
- `test_game_state_creation_custom_starting_location` - Custom starting location works
- `test_game_state_creation_invalid_character` - Raise TypeError for non-Character
- `test_game_state_creation_empty_world` - Raise ValueError for empty world dict
- `test_game_state_creation_invalid_starting_location` - Raise ValueError if starting location not in world
- `test_game_state_creation_validates_world_connections` - Raise ValueError if location connection points to non-existent location

**Tests for GameState.get_current_location():**
- `test_get_current_location_returns_location` - Returns Location instance
- `test_get_current_location_returns_correct_location` - Returns current location object

**Tests for GameState.look():**
- `test_look_returns_string` - Returns string
- `test_look_contains_location_info` - Contains name, description, exits
- `test_look_format_matches_location_str` - Format matches Location.__str__()

**Tests for GameState.move():**
- `test_move_valid_direction_success` - Returns (True, success_message)
- `test_move_valid_direction_updates_location` - current_location changes
- `test_move_invalid_direction_failure` - Returns (False, error_message)
- `test_move_invalid_direction_no_change` - current_location unchanged
- `test_move_nonexistent_direction_failure` - Returns (False, error) for direction with no connection
- `test_move_chain_navigation` - Multiple moves work correctly

**Tests for GameState serialization:**
- `test_game_state_to_dict` - Verify dict structure
- `test_game_state_to_dict_contains_all_data` - Contains character, location, world
- `test_game_state_from_dict` - Deserialize successfully
- `test_game_state_from_dict_validates_data` - Raises errors for invalid data
- `test_game_state_roundtrip_serialization` - to_dict -> from_dict preserves state

**Tests for parse_command():**
- `test_parse_command_look` - Returns ("look", [])
- `test_parse_command_go_with_direction` - Returns ("go", ["north"])
- `test_parse_command_save` - Returns ("save", [])
- `test_parse_command_quit` - Returns ("quit", [])
- `test_parse_command_unknown` - Returns ("unknown", [])
- `test_parse_command_case_insensitive` - "LOOK" -> ("look", [])
- `test_parse_command_strips_whitespace` - "  look  " -> ("look", [])
- `test_parse_command_go_missing_direction` - "go" -> ("go", [])

### 2.3 Create tests/test_persistence_game_state.py

**Tests for save_game_state():**
- `test_save_game_state_creates_file` - File created
- `test_save_game_state_returns_filepath` - Returns string path
- `test_save_game_state_creates_directory` - Creates save_dir if missing
- `test_save_game_state_valid_json` - Contains valid JSON
- `test_save_game_state_contains_complete_data` - Contains character, location, world
- `test_save_game_state_custom_directory` - Respects save_dir parameter

**Tests for load_game_state():**
- `test_load_game_state_success` - Loads valid file
- `test_load_game_state_returns_game_state` - Returns GameState instance
- `test_load_game_state_restores_character` - Character matches original
- `test_load_game_state_restores_location` - Location matches original
- `test_load_game_state_restores_world` - World matches original
- `test_load_game_state_file_not_found` - Raises FileNotFoundError
- `test_load_game_state_invalid_json` - Raises ValueError
- `test_load_game_state_missing_fields` - Raises ValueError
- `test_load_game_state_roundtrip` - save -> load preserves complete state

### 2.4 Create tests/test_gameplay_integration.py

**Integration tests for gameplay loop:**
- `test_gameplay_initialization` - Game state created from character
- `test_gameplay_look_command` - Look displays location
- `test_gameplay_move_command_success` - Move to valid direction works
- `test_gameplay_move_command_failure` - Move to invalid direction shows error
- `test_gameplay_navigation_sequence` - Multiple moves in sequence
- `test_gameplay_save_during_game` - Save preserves current location
- `test_gameplay_load_continues_from_saved_location` - Load restores position
- `test_gameplay_full_session` - Complete session: create, move, save, load, continue

## 3. IMPLEMENTATION

### 3.1 Implement src/cli_rpg/world.py

**Step 1:** Create world.py file
**Step 2:** Import Location from models
**Step 3:** Implement create_default_world():
- Create Town Square location with description
- Create Forest location with description
- Create Cave location with description
- Add connections: Town Square north->Forest, east->Cave
- Add connections: Forest south->Town Square
- Add connections: Cave west->Town Square
- Return dict with location name keys

**Step 4:** Run tests: `pytest tests/test_world.py -v`
**Step 5:** Fix any failures

### 3.2 Implement src/cli_rpg/game_state.py

**Step 1:** Create game_state.py file
**Step 2:** Import Character, Location
**Step 3:** Implement parse_command() function:
- Strip and lowercase input
- Split on whitespace
- Match against known commands
- Return (command, args) tuple

**Step 4:** Implement GameState class:
- Define __init__ with validation
  - Validate character is Character instance
  - Validate world is non-empty dict
  - Validate starting_location exists in world
  - Validate all connection targets exist in world
  - Set attributes
- Implement get_current_location()
  - Return world[current_location]
- Implement look()
  - Get current location
  - Return str(location)
- Implement move(direction)
  - Get current location
  - Check if direction exists in connections
  - If yes: update current_location, return (True, "You head {direction} to {location_name}.")
  - If no: return (False, "You can't go that way.")
- Implement to_dict()
  - Return dict with character, current_location, world
  - Use character.to_dict() and location.to_dict()
- Implement from_dict() classmethod
  - Deserialize character
  - Deserialize world locations
  - Create and return GameState instance

**Step 5:** Run tests: `pytest tests/test_game_state.py -v`
**Step 6:** Fix any failures

### 3.3 Enhance src/cli_rpg/persistence.py

**Step 1:** Import GameState and world
**Step 2:** Implement save_game_state(game_state, save_dir):
- Create save directory
- Generate filename from character name
- Serialize game_state.to_dict()
- Write JSON to file
- Return filepath
- Handle IOError

**Step 3:** Implement load_game_state(filepath):
- Validate file exists
- Load and parse JSON
- Validate required fields
- Deserialize using GameState.from_dict()
- Return GameState instance
- Handle errors (FileNotFoundError, ValueError)

**Step 4:** Run tests: `pytest tests/test_persistence_game_state.py -v`
**Step 5:** Fix any failures

### 3.4 Implement gameplay loop in src/cli_rpg/main.py

**Step 1:** Import GameState, world, save_game_state, load_game_state, parse_command

**Step 2:** Implement start_game(character: Character) -> None:
- Create default world
- Create GameState(character, world)
- Display welcome message
- Display current location (look)
- Enter command loop:
  - Prompt for command
  - Parse command
  - Execute command (look/go/save/quit)
  - Display results
  - Continue until quit

**Step 3:** Implement command handlers within start_game():
- handle_look(game_state) - Call look(), print result
- handle_go(game_state, args) - Validate args, call move(), print result
- handle_save(game_state) - Call save_game_state(), print confirmation
- handle_quit() - Confirm, return to main menu

**Step 4:** Update main() function flow:
- After character creation (choice 1): Call start_game(character)
- After character load (choice 2): Create GameState from character, call start_game with loaded state

**Step 5:** Update show_main_menu() to remove redundant save prompt (saving now happens in-game)

**Step 6:** Run tests: `pytest tests/test_gameplay_integration.py -v`
**Step 7:** Fix any failures

### 3.5 Update main menu integration

**Step 1:** Modify main() to integrate gameplay:
- After character creation, call start_game()
- After loading, restore game state and call start_game()

**Step 2:** Modify save/load to use game state format:
- Update load to create GameState
- Remove standalone save prompt after creation (now in-game)

**Step 3:** Run all tests: `pytest -v`
**Step 4:** Fix integration issues

## 4. VERIFICATION

### 4.1 Run complete test suite
```bash
pytest -v
```

### 4.2 Run specific test files in order
```bash
pytest tests/test_world.py -v
pytest tests/test_game_state.py -v
pytest tests/test_persistence_game_state.py -v
pytest tests/test_gameplay_integration.py -v
```

### 4.3 Manual testing flow
1. Run `python -m cli_rpg.main`
2. Create new character
3. Test commands:
   - `look` - Verify location display
   - `go north` - Move to Forest
   - `look` - Verify in Forest
   - `go south` - Return to Town Square
   - `go east` - Move to Cave
   - `go nowhere` - Verify error message
   - `save` - Save game
   - `quit` - Return to menu
4. Load saved character
5. Verify location preserved
6. Test navigation continues correctly

### 4.4 Edge case verification
- Create character, move, save, load, continue - full cycle
- Invalid commands display helpful error messages
- Moving to non-existent direction shows available exits
- World connections are bidirectional where appropriate
- Save/load preserves exact game state including location

### 4.5 Test coverage check
```bash
pytest --cov=src/cli_rpg --cov-report=term-missing
```
- Ensure >90% coverage for new modules
- Identify untested code paths
