"""End-to-end tests for dynamic world expansion during gameplay.

These tests validate that dynamic world expansion works seamlessly in realistic
player session scenarios by verifying:
- Dangling connection detection
- AI-powered location generation
- World state updates
- Bidirectional connection creation
- Seamless move continuation
- Graceful failure handling
- No-AI fallback behavior
"""

import pytest
from unittest.mock import Mock
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.ai_service import AIService, AIServiceError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def basic_character():
    """Create a basic test character with standard stats."""
    return Character(name="Test Hero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def advanced_character():
    """Create a character with higher stats and level for state preservation tests."""
    char = Character(name="Veteran Hero", strength=15, dexterity=12, intelligence=14)
    char.level = 5
    char.xp = 50
    char.health = 150
    return char


@pytest.fixture
def mock_ai_service_success():
    """Create a mock AI service that successfully generates locations."""
    service = Mock(spec=AIService)
    
    def generate_location_side_effect(theme, context_locations, source_location, direction):
        """Generate unique location based on direction."""
        location_names = {
            "north": "Dark Forest",
            "south": "Sunny Meadow",
            "east": "Ancient Cave",
            "west": "Crystal Lake",
            "up": "Mountain Peak",
            "down": "Underground Cavern"
        }
        name = location_names.get(direction, "Mystery Location")
        
        # Get opposite direction for return connection
        opposites = {
            "north": "south", "south": "north",
            "east": "west", "west": "east",
            "up": "down", "down": "up"
        }
        opposite = opposites.get(direction, "north")
        
        return {
            "name": name,
            "description": f"A mysterious {name.lower()}.",
            "connections": {
                opposite: source_location if source_location else "Town Square"
            }
        }
    
    service.generate_location.side_effect = generate_location_side_effect
    return service


@pytest.fixture
def mock_ai_service_failure():
    """Create a mock AI service that fails generation."""
    service = Mock(spec=AIService)
    service.generate_location.side_effect = AIServiceError("Generation failed")
    return service


@pytest.fixture
def simple_world():
    """Create a simple world with one location."""
    town = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center.",
        connections={}
    )
    return {"Town Square": town}


@pytest.fixture
def simple_world_with_dangling():
    """Create a world with dangling connection (for expansion testing)."""
    town = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center."
    )
    # Add dangling connection after creation
    town.connections = {"north": "Forest"}
    return {"Town Square": town}


@pytest.fixture
def connected_world():
    """Create a world with 3 interconnected locations."""
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        connections={"east": "Market"}
    )
    market = Location(
        name="Market",
        description="A busy marketplace.",
        connections={"west": "Town Square", "south": "Harbor"}
    )
    harbor = Location(
        name="Harbor",
        description="A peaceful harbor with ships.",
        connections={"north": "Market"}
    )
    return {
        "Town Square": town,
        "Market": market,
        "Harbor": harbor
    }


@pytest.fixture
def connected_world_with_dangling():
    """Create a connected world with a dangling connection from Harbor."""
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        connections={"east": "Market"}
    )
    market = Location(
        name="Market",
        description="A busy marketplace.",
        connections={"west": "Town Square", "south": "Harbor"}
    )
    harbor = Location(
        name="Harbor",
        description="A peaceful harbor with ships.",
        connections={"north": "Market"}
    )
    # Add dangling connection
    harbor.connections["east"] = "Shipwreck"
    return {
        "Town Square": town,
        "Market": market,
        "Harbor": harbor
    }


# ============================================================================
# Helper Functions
# ============================================================================

def verify_bidirectional_connection(world, loc1_name, direction, loc2_name):
    """Verify that two locations have bidirectional connections.
    
    Args:
        world: World dictionary
        loc1_name: First location name
        direction: Direction from loc1 to loc2
        loc2_name: Second location name
    
    Raises:
        AssertionError: If connections are not bidirectional
    """
    opposites = {
        "north": "south", "south": "north",
        "east": "west", "west": "east",
        "up": "down", "down": "up"
    }
    
    # Check forward connection
    assert loc1_name in world, f"Location {loc1_name} not in world"
    assert world[loc1_name].has_connection(direction), \
        f"{loc1_name} has no connection in direction {direction}"
    assert world[loc1_name].get_connection(direction) == loc2_name, \
        f"{loc1_name} -> {direction} should point to {loc2_name}"
    
    # Check reverse connection
    opposite = opposites[direction]
    assert loc2_name in world, f"Location {loc2_name} not in world"
    assert world[loc2_name].has_connection(opposite), \
        f"{loc2_name} has no connection in direction {opposite}"
    assert world[loc2_name].get_connection(opposite) == loc1_name, \
        f"{loc2_name} -> {opposite} should point to {loc1_name}"


def verify_world_integrity(world, allow_dangling=True):
    """Verify all connections point to existing locations.

    Args:
        world: World dictionary
        allow_dangling: If True, allows intentional dangling connections
            (those starting with "Unexplored ") for future expansion

    Raises:
        AssertionError: If any connection points to non-existent location
            (except allowed dangling connections)
    """
    for location_name, location in world.items():
        for direction, target in location.connections.items():
            # Allow intentional dangling connections for future expansion
            if allow_dangling and target.startswith("Unexplored "):
                continue
            assert target in world, \
                f"Connection from {location_name} via {direction} points to non-existent {target}"


# ============================================================================
# E2E Test Scenarios
# ============================================================================

def test_basic_single_expansion(basic_character, simple_world_with_dangling, mock_ai_service_success):
    """Test: Basic Single Expansion
    
    Spec: Verifies single location expansion works end-to-end
    - Dangling connection detection
    - AI-powered generation called with correct parameters
    - World state update with new location
    - Bidirectional connection creation
    - Seamless move continuation
    """
    # Setup GameState with dangling connection
    game_state = GameState(
        character=basic_character,
        world=simple_world_with_dangling,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Verify initial state
    assert game_state.current_location == "Town Square"
    assert "Forest" not in game_state.world
    
    # Execute move to trigger expansion
    success, message = game_state.move("north")
    
    # Spec: Move succeeds
    assert success is True, f"Move should succeed, got: {message}"
    
    # Spec: New location generated and added to world
    assert "Dark Forest" in game_state.world, "Generated location should be added to world"
    
    # Spec: Current location updated to new location
    assert game_state.current_location == "Dark Forest", "Should move to generated location"
    
    # Spec: Bidirectional connections created
    verify_bidirectional_connection(game_state.world, "Town Square", "north", "Dark Forest")
    
    # Spec: AI service called once with correct parameters
    mock_ai_service_success.generate_location.assert_called_once()
    call_kwargs = mock_ai_service_success.generate_location.call_args[1]
    assert call_kwargs["theme"] == "fantasy"
    assert call_kwargs["source_location"] == "Town Square"
    assert call_kwargs["direction"] == "north"
    assert "Town Square" in call_kwargs["context_locations"]


def test_multi_step_expansion_chain(basic_character, mock_ai_service_success):
    """Test: Multi-Step Expansion Chain
    
    Spec: Verifies multiple consecutive expansions work
    - Multiple expansions in sequence
    - Each location properly added to world
    - All connections are bidirectional
    - Context passed correctly for each generation
    """
    # Setup with single starting location
    town = Location(
        name="Town Square",
        description="A town square."
    )
    town.connections = {
        "north": "Forest",
        "east": "Cave",
        "down": "Dungeon"
    }
    world = {"Town Square": town}
    
    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Spec: Execute multiple moves to trigger expansion chain
    success1, _ = game_state.move("north")
    assert success1 is True, "First expansion should succeed"
    assert game_state.current_location == "Dark Forest"
    assert len(game_state.world) == 2
    
    # Add dangling connection from Dark Forest for next expansion
    game_state.world["Dark Forest"].connections["east"] = "Cave"
    
    success2, _ = game_state.move("east")
    assert success2 is True, "Second expansion should succeed"
    assert game_state.current_location == "Ancient Cave"
    assert len(game_state.world) == 3
    
    # Add dangling connection from Ancient Cave for third expansion
    game_state.world["Ancient Cave"].connections["down"] = "Dungeon"
    
    success3, _ = game_state.move("down")
    assert success3 is True, "Third expansion should succeed"
    assert game_state.current_location == "Underground Cavern"
    
    # Spec: All four locations exist in world
    assert len(game_state.world) == 4
    assert "Town Square" in game_state.world
    assert "Dark Forest" in game_state.world
    assert "Ancient Cave" in game_state.world
    assert "Underground Cavern" in game_state.world
    
    # Spec: All connections are bidirectional
    verify_bidirectional_connection(game_state.world, "Town Square", "north", "Dark Forest")
    verify_bidirectional_connection(game_state.world, "Dark Forest", "east", "Ancient Cave")
    verify_bidirectional_connection(game_state.world, "Ancient Cave", "down", "Underground Cavern")
    
    # Spec: AI service called three times (once per expansion)
    assert mock_ai_service_success.generate_location.call_count == 3


def test_expansion_with_existing_location(basic_character, mock_ai_service_success):
    """Test: Expansion with Existing Location
    
    Spec: Verifies expansion doesn't break when destination already exists
    - Move succeeds without calling AI
    - No duplicate locations created
    """
    # Setup world with both locations already present
    town = Location(
        name="Town Square",
        description="A town square.",
        connections={"north": "Forest"}
    )
    forest = Location(
        name="Forest",
        description="A dark forest.",
        connections={"south": "Town Square"}
    )
    world = {"Town Square": town, "Forest": forest}
    
    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Execute move to existing location
    success, message = game_state.move("north")
    
    # Spec: Move succeeds without calling AI
    assert success is True
    assert game_state.current_location == "Forest"
    
    # Spec: AI service never called
    mock_ai_service_success.generate_location.assert_not_called()
    
    # Spec: No duplicate locations created
    assert len(game_state.world) == 2


def test_expansion_after_movement_through_existing_world(
    basic_character, connected_world_with_dangling, mock_ai_service_success
):
    """Test: Expansion After Movement Through Existing World
    
    Spec: Verifies expansion works mid-game after exploring existing areas
    - Move through existing locations works normally
    - Expansion triggered from mid-game location
    - All existing locations remain unchanged
    - Context includes all previous locations
    """
    game_state = GameState(
        character=basic_character,
        world=connected_world_with_dangling,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Spec: Move through existing world
    success1, _ = game_state.move("east")
    assert success1 is True
    assert game_state.current_location == "Market"
    
    success2, _ = game_state.move("south")
    assert success2 is True
    assert game_state.current_location == "Harbor"
    
    # Verify no AI calls yet
    mock_ai_service_success.generate_location.assert_not_called()
    
    # Spec: Trigger expansion from Harbor
    success3, _ = game_state.move("east")
    assert success3 is True
    assert game_state.current_location == "Ancient Cave"
    
    # Spec: New location added
    assert "Ancient Cave" in game_state.world
    assert len(game_state.world) == 4
    
    # Spec: Context includes all three previous locations
    call_kwargs = mock_ai_service_success.generate_location.call_args[1]
    context = call_kwargs["context_locations"]
    assert "Town Square" in context
    assert "Market" in context
    assert "Harbor" in context
    
    # Spec: All existing locations remain unchanged
    assert game_state.world["Town Square"].description == "A bustling town square."
    assert game_state.world["Market"].description == "A busy marketplace."
    assert game_state.world["Harbor"].description == "A peaceful harbor with ships."


def test_expansion_failure_handling(basic_character, simple_world_with_dangling, mock_ai_service_failure):
    """Test: Expansion Failure Handling
    
    Spec: Verifies graceful handling when AI generation fails
    - Move fails with appropriate error message
    - Current location unchanged
    - World state unchanged (no partial location added)
    """
    game_state = GameState(
        character=basic_character,
        world=simple_world_with_dangling,
        starting_location="Town Square",
        ai_service=mock_ai_service_failure,
        theme="fantasy"
    )
    
    initial_world_size = len(game_state.world)
    
    # Attempt move that triggers failed expansion
    success, message = game_state.move("north")
    
    # Spec: Move fails
    assert success is False, "Move should fail when AI generation fails"
    
    # Spec: Error message contains failure indication
    assert "failed" in message.lower() or "error" in message.lower(), \
        f"Error message should indicate failure, got: {message}"
    
    # Spec: Current location unchanged
    assert game_state.current_location == "Town Square", \
        "Current location should not change on failed expansion"
    
    # Spec: World state unchanged
    assert len(game_state.world) == initial_world_size, \
        "No partial locations should be added on failure"
    assert "Forest" not in game_state.world
    assert "Dark Forest" not in game_state.world


def test_no_ai_service_fallback(basic_character):
    """Test: No AI Service Fallback
    
    Spec: Verifies behavior without AI service
    - Move to missing destination fails
    - Clear error message provided
    - No crashes or exceptions
    
    Note: GameState doesn't allow creating worlds with dangling connections
    when there's no AI service. This test creates a valid world with AI service,
    then removes it and adds a dangling connection to simulate runtime scenario.
    """
    # Create valid world first
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        connections={}
    )
    world = {"Town Square": town}
    
    # Create GameState with AI service initially to pass validation
    mock_ai_service = Mock(spec=AIService)
    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy"
    )
    
    # Add dangling connection after creation (simulates dynamic scenario)
    game_state.world["Town Square"].connections["north"] = "Forest"
    
    # Remove AI service to test fallback behavior
    game_state.ai_service = None
    
    # Attempt move to missing destination
    success, message = game_state.move("north")
    
    # Spec: Move fails
    assert success is False, "Move should fail without AI service"
    
    # Spec: Clear error message
    assert "destination" in message.lower() or "not found" in message.lower(), \
        f"Error message should be clear, got: {message}"
    
    # Spec: Current location unchanged
    assert game_state.current_location == "Town Square"


def test_theme_consistency_in_expansion(basic_character, simple_world_with_dangling, mock_ai_service_success):
    """Test: Theme Consistency in Expansion
    
    Spec: Verifies generated locations match theme
    - AI service called with correct theme parameter
    """
    game_state = GameState(
        character=basic_character,
        world=simple_world_with_dangling,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="cyberpunk"
    )
    
    # Trigger expansion
    game_state.move("north")
    
    # Spec: AI service called with correct theme
    call_kwargs = mock_ai_service_success.generate_location.call_args[1]
    assert call_kwargs["theme"] == "cyberpunk", \
        "AI service should receive correct theme parameter"


def test_connection_update_after_expansion(basic_character, simple_world_with_dangling, mock_ai_service_success):
    """Test: Connection Update After Expansion
    
    Spec: Verifies connections from source location are correctly updated
    - Source location's connection updated to actual generated name
    - get_connection returns correct destination
    """
    game_state = GameState(
        character=basic_character,
        world=simple_world_with_dangling,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Initial connection points to "Forest"
    assert game_state.world["Town Square"].get_connection("north") == "Forest"
    
    # Trigger expansion
    game_state.move("north")
    
    # Spec: Connection updated to actual generated name
    actual_name = game_state.world["Town Square"].get_connection("north")
    assert actual_name == "Dark Forest", \
        "Connection should be updated to actual generated location name"
    
    # Spec: get_connection returns correct destination
    assert game_state.world["Town Square"].get_connection("north") == "Dark Forest"


def test_multiple_paths_to_same_expansion_point(basic_character, mock_ai_service_success):
    """Test: Multiple Paths to Same Expansion Point
    
    Spec: Verifies expansion works when multiple locations could lead to same missing destination
    - First expansion creates the location
    - Second move to same location succeeds without regeneration
    - Location has connections to both sources (if appropriate)
    """
    # Setup world with two locations that could expand to same destination
    loc_a = Location(
        name="Location A",
        description="First location."
    )
    loc_a.connections = {"north": "Missing", "east": "Location B"}
    
    loc_b = Location(
        name="Location B",
        description="Second location."
    )
    loc_b.connections = {"west": "Location A"}
    
    world = {"Location A": loc_a, "Location B": loc_b}
    
    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Location A",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Spec: First move triggers expansion
    success1, _ = game_state.move("north")
    assert success1 is True
    assert game_state.current_location == "Dark Forest"
    assert "Dark Forest" in game_state.world
    
    # AI service should have been called once
    assert mock_ai_service_success.generate_location.call_count == 1
    
    # Go back to Location A, then to Location B
    game_state.current_location = "Location A"
    game_state.move("east")
    assert game_state.current_location == "Location B"
    
    # Add connection from Location B to the already-generated location
    game_state.world["Location B"].connections["north"] = "Dark Forest"
    
    # Spec: Second move to same location succeeds without regeneration
    success2, _ = game_state.move("north")
    assert success2 is True
    assert game_state.current_location == "Dark Forest"
    
    # AI service should still only have been called once (no regeneration)
    assert mock_ai_service_success.generate_location.call_count == 1


def test_expansion_preserves_game_state(advanced_character, simple_world_with_dangling, mock_ai_service_success):
    """Test: Expansion Preserves Game State
    
    Spec: Verifies character state, inventory, etc. preserved during expansion
    - Character HP, level, stats unchanged
    - XP preserved
    - Only world dictionary modified
    """
    game_state = GameState(
        character=advanced_character,
        world=simple_world_with_dangling,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Capture initial character state
    initial_name = game_state.current_character.name
    initial_level = game_state.current_character.level
    initial_health = game_state.current_character.health
    initial_max_health = game_state.current_character.max_health
    initial_strength = game_state.current_character.strength
    initial_dexterity = game_state.current_character.dexterity
    initial_intelligence = game_state.current_character.intelligence
    initial_xp = game_state.current_character.xp
    
    # Trigger expansion
    game_state.move("north")
    
    # Spec: Character state unchanged
    assert game_state.current_character.name == initial_name
    assert game_state.current_character.level == initial_level
    assert game_state.current_character.health == initial_health
    assert game_state.current_character.max_health == initial_max_health
    assert game_state.current_character.strength == initial_strength
    assert game_state.current_character.dexterity == initial_dexterity
    assert game_state.current_character.intelligence == initial_intelligence
    assert game_state.current_character.xp == initial_xp
    
    # Spec: Only world modified
    assert len(game_state.world) == 2  # Original + expanded location
    assert game_state.current_location == "Dark Forest"  # Location changed is expected


def test_world_integrity_after_multiple_expansions(basic_character, simple_world, mock_ai_service_success):
    """Test: World Integrity After Multiple Expansions
    
    Additional test to ensure world remains valid after multiple expansions
    - All connections point to existing locations
    - No orphaned connections
    - World is navigable
    """
    # Start with single location, add dangling connections dynamically
    game_state = GameState(
        character=basic_character,
        world=simple_world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )
    
    # Add first dangling connection
    game_state.world["Town Square"].connections["north"] = "Forest"
    game_state.move("north")
    
    # Add second dangling connection
    game_state.world["Dark Forest"].connections["east"] = "Cave"
    game_state.move("east")
    
    # Add third dangling connection
    game_state.world["Ancient Cave"].connections["south"] = "Valley"
    game_state.move("south")
    
    # Verify world integrity
    verify_world_integrity(game_state.world)

    # Verify we can navigate back
    game_state.world["Sunny Meadow"].connections["west"] = "Ancient Cave"  # Add explicit connection
    success, _ = game_state.move("west")
    assert success is True


def test_expanded_location_never_dead_end(basic_character, mock_ai_service_success):
    """Test: Expanded locations never become dead-ends.

    Spec: Newly expanded locations always have at least one exit besides
    the back-connection, preventing dead-end scenarios like Chrome Canyon.
    """
    # Override mock to return only back-connection
    def generate_dead_end(theme, context_locations, source_location, direction):
        opposites = {"north": "south", "south": "north", "east": "west",
                     "west": "east", "up": "down", "down": "up"}
        return {
            "name": "Chrome Canyon",
            "description": "A canyon with chrome walls.",
            "connections": {opposites[direction]: source_location}  # Only back
        }

    mock_ai_service_success.generate_location.side_effect = generate_dead_end

    town = Location(name="Town Square", description="A town square.")
    town.connections = {"south": "Chrome Canyon"}
    world = {"Town Square": town}

    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="cyberpunk"
    )

    # Trigger expansion
    success, _ = game_state.move("south")
    assert success is True

    # Verify Chrome Canyon has more than just the back exit
    chrome_canyon = game_state.world["Chrome Canyon"]
    assert len(chrome_canyon.connections) >= 2, \
        "Expanded location should have at least 2 exits (back + dangling)"

    # Verify at least one non-back exit exists
    non_back = [d for d in chrome_canyon.connections if d != "north"]
    assert len(non_back) >= 1, \
        "Expanded location must have at least one forward exit for exploration"
