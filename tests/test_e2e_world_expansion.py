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
    from cli_rpg.models.world_context import WorldContext
    from cli_rpg.models.region_context import RegionContext

    service = Mock(spec=AIService)

    def generate_location_side_effect(theme, context_locations, source_location, direction):
        """Generate unique location based on direction."""
        location_names = {
            "north": "Dark Forest",
            "south": "Sunny Meadow",
            "east": "Ancient Cave",
            "west": "Crystal Lake"
        }
        name = location_names.get(direction, "Mystery Location")

        # Get opposite direction for return connection
        opposites = {
            "north": "south", "south": "north",
            "east": "west", "west": "east"
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
    # Mock location ASCII art generation to return a string (fallback will be used)
    service.generate_location_ascii_art.return_value = "  /\\\n / \\\n/___\\"
    # Mock context generation to return proper serializable objects
    service.generate_world_context.return_value = WorldContext.default("fantasy")
    service.generate_region_context.return_value = RegionContext.default(
        "Test Region", (0, 0)
    )
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
        coordinates=(0, 0)
    )
    return {"Town Square": town}


@pytest.fixture
def simple_world_for_expansion():
    """Create a world ready for expansion testing (coordinate-based)."""
    town = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center.",
        coordinates=(0, 0)
    )
    # No location to the north - expansion will create one
    return {"Town Square": town}


@pytest.fixture
def connected_world():
    """Create a world with 3 interconnected locations via coordinates."""
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0)
    )
    market = Location(
        name="Market",
        description="A busy marketplace.",
        coordinates=(1, 0)  # East of town
    )
    harbor = Location(
        name="Harbor",
        description="A peaceful harbor with ships.",
        coordinates=(1, -1)  # South of market
    )
    return {
        "Town Square": town,
        "Market": market,
        "Harbor": harbor
    }


@pytest.fixture
def connected_world_for_expansion():
    """Create a connected world ready for expansion from Harbor."""
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0)
    )
    market = Location(
        name="Market",
        description="A busy marketplace.",
        coordinates=(1, 0)  # East of town
    )
    harbor = Location(
        name="Harbor",
        description="A peaceful harbor with ships.",
        coordinates=(1, -1)  # South of market
    )
    # No location to the east of harbor - expansion will create one
    return {
        "Town Square": town,
        "Market": market,
        "Harbor": harbor
    }


# ============================================================================
# Helper Functions
# ============================================================================

def verify_coordinate_adjacency(world, loc1_name, direction, loc2_name):
    """Verify that two locations are at adjacent coordinates in the given direction.

    Args:
        world: World dictionary
        loc1_name: First location name
        direction: Direction from loc1 to loc2
        loc2_name: Second location name

    Raises:
        AssertionError: If locations are not at adjacent coordinates
    """
    offsets = {
        "north": (0, 1), "south": (0, -1),
        "east": (1, 0), "west": (-1, 0)
    }

    # Check both locations exist
    assert loc1_name in world, f"Location {loc1_name} not in world"
    assert loc2_name in world, f"Location {loc2_name} not in world"

    loc1 = world[loc1_name]
    loc2 = world[loc2_name]

    # Check coordinates are set
    assert loc1.coordinates is not None, f"{loc1_name} has no coordinates"
    assert loc2.coordinates is not None, f"{loc2_name} has no coordinates"

    # Check adjacency
    dx, dy = offsets[direction]
    expected_coords = (loc1.coordinates[0] + dx, loc1.coordinates[1] + dy)
    assert loc2.coordinates == expected_coords, \
        f"{loc2_name} at {loc2.coordinates} is not {direction} of {loc1_name} at {loc1.coordinates}"


def verify_world_integrity(world):
    """Verify all locations have valid coordinates (no duplicates, all set).

    Args:
        world: World dictionary

    Raises:
        AssertionError: If coordinates are missing or duplicated
    """
    seen_coords = {}
    for location_name, location in world.items():
        if location.coordinates is not None:
            if location.coordinates in seen_coords:
                raise AssertionError(
                    f"Duplicate coordinates {location.coordinates}: "
                    f"{location_name} and {seen_coords[location.coordinates]}"
                )
            seen_coords[location.coordinates] = location_name


# ============================================================================
# E2E Test Scenarios
# ============================================================================

def test_basic_single_expansion(basic_character, simple_world_for_expansion, mock_ai_service_success):
    """Test: Basic Single Expansion

    Spec: Verifies single location expansion works end-to-end
    - Empty coordinate triggers location generation
    - World state update with new location at correct coordinates
    - Seamless move continuation
    """
    # Setup GameState with coordinate-based world
    game_state = GameState(
        character=basic_character,
        world=simple_world_for_expansion,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )

    # Verify initial state
    assert game_state.current_location == "Town Square"
    initial_world_size = len(game_state.world)

    # Execute move to trigger expansion (no location at (0,1) yet)
    success, message = game_state.move("north")

    # Spec: Move succeeds
    assert success is True, f"Move should succeed, got: {message}"

    # Spec: New location generated and added to world
    assert len(game_state.world) == initial_world_size + 1, "New location should be added"

    # Spec: Current location updated to new location at (0, 1)
    new_loc = game_state.get_current_location()
    assert new_loc.coordinates == (0, 1), "New location should be at (0, 1)"

    # Verify world integrity
    verify_world_integrity(game_state.world)


def test_multi_step_expansion_chain(basic_character, mock_ai_service_success):
    """Test: Multi-Step Expansion Chain

    Spec: Verifies multiple consecutive expansions work
    - Multiple expansions in sequence
    - Each location properly added to world at correct coordinates
    """
    # Setup with single starting location at (0, 0)
    town = Location(
        name="Town Square",
        description="A town square.",
        coordinates=(0, 0)
    )
    world = {"Town Square": town}

    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )

    # Spec: Execute multiple moves to trigger expansion chain
    # Move north to (0, 1)
    success1, _ = game_state.move("north")
    assert success1 is True, "First expansion should succeed"
    assert game_state.get_current_location().coordinates == (0, 1)
    assert len(game_state.world) == 2

    # Move east to (1, 1)
    success2, _ = game_state.move("east")
    assert success2 is True, "Second expansion should succeed"
    assert game_state.get_current_location().coordinates == (1, 1)
    assert len(game_state.world) == 3

    # Move south to (1, 0)
    success3, _ = game_state.move("south")
    assert success3 is True, "Third expansion should succeed"
    assert game_state.get_current_location().coordinates == (1, 0)

    # Spec: All four locations exist in world
    assert len(game_state.world) == 4

    # Verify world integrity (no duplicate coordinates)
    verify_world_integrity(game_state.world)


def test_expansion_with_existing_location(basic_character, mock_ai_service_success):
    """Test: Expansion with Existing Location

    Spec: Verifies expansion doesn't break when destination already exists
    - Move succeeds without calling AI
    - No duplicate locations created
    """
    # Setup world with both locations at adjacent coordinates
    town = Location(
        name="Town Square",
        description="A town square.",
        coordinates=(0, 0)
    )
    forest = Location(
        name="Forest",
        description="A dark forest.",
        coordinates=(0, 1)  # North of town
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
    basic_character, connected_world_for_expansion, mock_ai_service_success
):
    """Test: Expansion After Movement Through Existing World

    Spec: Verifies expansion works mid-game after exploring existing areas
    - Move through existing locations works normally
    - Expansion triggered from mid-game location
    - All existing locations remain unchanged
    """
    game_state = GameState(
        character=basic_character,
        world=connected_world_for_expansion,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )

    # Spec: Move through existing world (Town Square -> Market via east)
    success1, _ = game_state.move("east")
    assert success1 is True
    assert game_state.current_location == "Market"

    # Move south to Harbor
    success2, _ = game_state.move("south")
    assert success2 is True
    assert game_state.current_location == "Harbor"

    # Spec: Trigger expansion from Harbor (going east to empty (2, -1))
    success3, _ = game_state.move("east")
    assert success3 is True

    # New location generated at (2, -1)
    new_loc = game_state.get_current_location()
    assert new_loc.coordinates == (2, -1)

    # Spec: New location added
    assert len(game_state.world) == 4

    # Spec: All existing locations remain unchanged
    assert game_state.world["Town Square"].description == "A bustling town square."
    assert game_state.world["Market"].description == "A busy marketplace."
    assert game_state.world["Harbor"].description == "A peaceful harbor with ships."


def test_ai_failure_uses_fallback(basic_character, simple_world_for_expansion, mock_ai_service_failure):
    """Test: AI Failure Uses Fallback

    Spec: Verifies graceful fallback when AI generation fails
    - Move succeeds via fallback generation
    - New location created with template content
    """
    game_state = GameState(
        character=basic_character,
        world=simple_world_for_expansion,
        starting_location="Town Square",
        ai_service=mock_ai_service_failure,
        theme="fantasy"
    )

    initial_world_size = len(game_state.world)

    # Attempt move that triggers AI failure -> fallback
    success, message = game_state.move("north")

    # Spec: Move succeeds via fallback generation
    assert success is True, "Move should succeed via fallback"

    # Spec: New location was added
    assert len(game_state.world) == initial_world_size + 1

    # Spec: Player moved to new location at (0, 1)
    new_loc = game_state.get_current_location()
    assert new_loc.coordinates == (0, 1)


def test_no_ai_service_uses_fallback(basic_character):
    """Test: No AI Service Uses Fallback

    Spec: Verifies fallback works without AI service
    - Move succeeds via fallback generation
    - No crashes or exceptions
    """
    # Create world with coordinates
    town = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0)
    )
    world = {"Town Square": town}

    # Create GameState without AI service
    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=None,  # No AI service
        theme="fantasy"
    )

    # Attempt move (should use fallback generation)
    success, message = game_state.move("north")

    # Spec: Move succeeds via fallback
    assert success is True, "Move should succeed via fallback"

    # Spec: New location at (0, 1)
    new_loc = game_state.get_current_location()
    assert new_loc.coordinates == (0, 1)
    assert game_state.current_location != "Town Square"


def test_multiple_paths_to_same_location(basic_character, mock_ai_service_success):
    """Test: Multiple Paths to Same Location

    Spec: Verifies existing locations can be reached from multiple places
    - Both locations can access the same target
    - No regeneration when location already exists
    """
    # Setup world with two locations that could access same third location
    loc_a = Location(
        name="Location A",
        description="First location.",
        coordinates=(0, 0)
    )
    loc_b = Location(
        name="Location B",
        description="Second location.",
        coordinates=(1, 0)  # East of A
    )
    # Create a location north that both can eventually reach
    north_loc = Location(
        name="Northern Area",
        description="Northern area.",
        coordinates=(0, 1)  # North of A
    )
    world = {"Location A": loc_a, "Location B": loc_b, "Northern Area": north_loc}

    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Location A",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )

    # Move north to existing location
    success1, _ = game_state.move("north")
    assert success1 is True
    assert game_state.current_location == "Northern Area"

    # AI should not have been called - location exists
    mock_ai_service_success.generate_location.assert_not_called()


def test_expansion_preserves_game_state(advanced_character, simple_world_for_expansion, mock_ai_service_success):
    """Test: Expansion Preserves Game State

    Spec: Verifies character state, inventory, etc. preserved during expansion
    - Character HP, level, stats unchanged
    - XP preserved
    - Only world dictionary modified
    """
    game_state = GameState(
        character=advanced_character,
        world=simple_world_for_expansion,
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

    # Spec: Only world modified (original + expanded location)
    assert len(game_state.world) == 2


def test_world_integrity_after_multiple_expansions(basic_character, simple_world, mock_ai_service_success):
    """Test: World Integrity After Multiple Expansions

    Additional test to ensure world remains valid after multiple expansions
    - All coordinates are unique
    - World is navigable
    """
    game_state = GameState(
        character=basic_character,
        world=simple_world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )

    # Move north to (0, 1)
    game_state.move("north")

    # Move east to (1, 1)
    game_state.move("east")

    # Move south to (1, 0)
    game_state.move("south")

    # Verify world integrity (no duplicate coordinates)
    verify_world_integrity(game_state.world)

    # Verify we can navigate back to (0, 0)
    success, _ = game_state.move("west")
    assert success is True
    assert game_state.get_current_location().coordinates == (0, 0)


def test_expansion_locations_are_navigable(basic_character, mock_ai_service_success):
    """Test: Expanded locations are navigable.

    Spec: Newly expanded locations can be navigated back to the source.
    """
    town = Location(
        name="Town Square",
        description="A town square.",
        coordinates=(0, 0)
    )
    world = {"Town Square": town}

    game_state = GameState(
        character=basic_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service_success,
        theme="fantasy"
    )

    # Move south to (0, -1) - expansion happens
    success, _ = game_state.move("south")
    assert success is True
    assert game_state.get_current_location().coordinates == (0, -1)

    # Verify we can navigate back north to Town Square
    success_back, _ = game_state.move("north")
    assert success_back is True
    assert game_state.current_location == "Town Square"
