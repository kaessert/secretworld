"""Tests for GameState integration with AI world generation."""

import pytest
from unittest.mock import Mock
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.ai_service import AIService


# Fixtures

@pytest.fixture
def test_character():
    """Create a test character."""
    return Character(name="Test Hero", strength=10, dexterity=10, intelligence=10)


@pytest.fixture
def basic_world():
    """Create a basic world with missing connection (for AI generation tests)."""
    town = Location(
        name="Town Square",
        description="A town square."
    )
    # Add connection after creation to avoid Location validation
    town.connections = {"north": "Forest"}
    # Note: Forest doesn't exist yet - will test dynamic generation
    return {"Town Square": town}


@pytest.fixture
def complete_world():
    """Create a complete world with all locations present."""
    town = Location(
        name="Town Square",
        description="A town square.",
        connections={}
    )
    return {"Town Square": town}


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock(spec=AIService)
    return service


# Test: GameState with AI world
def test_game_state_with_ai_world(test_character, complete_world):
    """Test GameState works with AI-generated world."""
    game_state = GameState(
        character=test_character,
        world=complete_world,
        starting_location="Town Square"
    )
    
    assert game_state.current_location == "Town Square"
    assert game_state.current_character == test_character
    assert game_state.world == complete_world


# Test: GameState accepts AI service and theme
def test_game_state_accepts_ai_service_and_theme(test_character, complete_world, mock_ai_service):
    """Test GameState accepts optional ai_service and theme parameters."""
    game_state = GameState(
        character=test_character,
        world=complete_world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy"
    )
    
    assert game_state.ai_service == mock_ai_service
    assert game_state.theme == "fantasy"


# Test: GameState move triggers expansion when destination missing
def test_game_state_move_triggers_expansion(test_character, basic_world, mock_ai_service):
    """Test moving to non-existent location triggers AI generation."""
    # Mock generate_location to return a new location
    # NOTE: The generated location name should match what expand_world creates
    mock_ai_service.generate_location.return_value = {
        "name": "Dark Forest",
        "description": "A dark and mysterious forest.",
        "connections": {
            "south": "Town Square"
        }
    }
    
    game_state = GameState(
        character=test_character,
        world=basic_world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy"
    )
    
    # Try to move north (connection exists but destination "Forest" doesn't)
    success, message = game_state.move("north")
    
    # Should succeed and generate the location
    assert success is True
    # The location gets generated with whatever name expand_world creates
    assert "Dark Forest" in game_state.world
    # Current location should be the generated location name
    assert game_state.current_location == "Dark Forest"


# Test: GameState move without AI service handles missing destination
def test_game_state_move_without_ai_service_missing_destination(test_character):
    """Test move to missing destination fails gracefully without AI service."""
    # Create world with connection but AI service to allow incomplete connections
    town = Location(
        name="Town Square",
        description="A town square."
    )
    town.connections = {"north": "Forest"}  # Forest doesn't exist
    world = {"Town Square": town}
    
    # Create with AI service first to allow incomplete connections
    game_state = GameState(
        character=test_character,
        world=world,
        starting_location="Town Square",
        ai_service=Mock(spec=AIService)  # Has AI service initially
    )
    
    # Remove AI service to simulate no AI available
    game_state.ai_service = None
    
    # Try to move north (connection exists but destination doesn't, no AI to generate)
    success, message = game_state.move("north")
    
    # Should fail
    assert success is False
    assert "destination" in message.lower() or "not found" in message.lower()


# Test: GameState AI generation failure handling
def test_game_state_ai_generation_failure_handling(test_character, basic_world, mock_ai_service):
    """Test GameState handles AI generation failures gracefully."""
    from cli_rpg.ai_service import AIGenerationError
    
    # Mock AI service to fail
    mock_ai_service.generate_location.side_effect = AIGenerationError("Generation failed")
    
    game_state = GameState(
        character=test_character,
        world=basic_world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy"
    )
    
    # Try to move north (should fail due to generation error)
    success, message = game_state.move("north")
    
    # Should fail gracefully
    assert success is False
    assert "failed" in message.lower() or "error" in message.lower()


# Test: GameState AI world persistence (serialization)
def test_game_state_ai_world_persistence(test_character, complete_world, mock_ai_service):
    """Test GameState with AI world can be saved and loaded."""
    original_game = GameState(
        character=test_character,
        world=complete_world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="cyberpunk"
    )
    
    # Serialize
    game_dict = original_game.to_dict()
    
    # Verify theme is included
    assert "theme" in game_dict
    assert game_dict["theme"] == "cyberpunk"
    
    # Deserialize (without ai_service - it's not serialized)
    restored_game = GameState.from_dict(game_dict)
    
    # Verify state is preserved
    assert restored_game.current_location == original_game.current_location
    assert restored_game.current_character.name == original_game.current_character.name
    assert restored_game.theme == "cyberpunk"
    assert restored_game.ai_service is None  # AI service not persisted


# Test: GameState from_dict accepts optional ai_service
def test_game_state_from_dict_accepts_ai_service(test_character, complete_world, mock_ai_service):
    """Test GameState.from_dict() can accept optional ai_service parameter."""
    original_game = GameState(
        character=test_character,
        world=complete_world,
        starting_location="Town Square",
        theme="fantasy"
    )
    
    game_dict = original_game.to_dict()
    
    # Restore with AI service
    restored_game = GameState.from_dict(game_dict, ai_service=mock_ai_service)
    
    # Verify AI service is set
    assert restored_game.ai_service == mock_ai_service


# Test: GameState theme defaults to fantasy
def test_game_state_theme_defaults_to_fantasy(test_character, complete_world):
    """Test GameState theme defaults to 'fantasy' if not specified."""
    game_state = GameState(
        character=test_character,
        world=complete_world,
        starting_location="Town Square"
    )
    
    assert game_state.theme == "fantasy"


# Test: GameState move to existing location works normally
def test_game_state_move_to_existing_location_works(test_character, mock_ai_service):
    """Test moving to existing location works normally with AI service."""
    # Create world with both locations
    town = Location(
        name="Town Square",
        description="A town square.",
        connections={"north": "Forest"}
    )
    forest = Location(
        name="Forest",
        description="A forest.",
        connections={"south": "Town Square"}
    )
    world = {"Town Square": town, "Forest": forest}
    
    game_state = GameState(
        character=test_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy"
    )
    
    # Move to existing location
    success, message = game_state.move("north")
    
    # Should succeed without calling AI
    assert success is True
    assert game_state.current_location == "Forest"
    # AI service should not be called since location exists
    mock_ai_service.generate_location.assert_not_called()


# Test: GameState dynamic expansion updates connections
def test_game_state_dynamic_expansion_updates_connections(test_character, basic_world, mock_ai_service):
    """Test dynamic expansion creates proper bidirectional connections."""
    mock_ai_service.generate_location.return_value = {
        "name": "Mysterious Cave",
        "description": "A dark cave entrance.",
        "connections": {
            "south": "Town Square"
        }
    }
    
    game_state = GameState(
        character=test_character,
        world=basic_world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy"
    )
    
    # Move north to trigger expansion
    game_state.move("north")
    
    # Verify bidirectional connections
    assert game_state.world["Town Square"].has_connection("north")
    assert game_state.world["Town Square"].get_connection("north") == "Mysterious Cave"
    assert game_state.world["Mysterious Cave"].has_connection("south")
    assert game_state.world["Mysterious Cave"].get_connection("south") == "Town Square"


# Test: GameState passes context to AI service
def test_game_state_passes_context_to_ai_service(test_character, basic_world, mock_ai_service):
    """Test GameState passes proper context when generating locations."""
    mock_ai_service.generate_location.return_value = {
        "name": "New Location",
        "description": "A new place.",
        "connections": {"south": "Town Square"}
    }
    
    game_state = GameState(
        character=test_character,
        world=basic_world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="steampunk"
    )
    
    # Trigger expansion
    game_state.move("north")
    
    # Verify context was passed
    call_args = mock_ai_service.generate_location.call_args
    assert call_args[1]["theme"] == "steampunk"
    assert call_args[1]["source_location"] == "Town Square"
    assert call_args[1]["direction"] == "north"
    assert "Town Square" in call_args[1]["context_locations"]


# ===== Tests for coordinate-based AI expansion (lines 254-275) =====


@pytest.fixture
def coord_world():
    """Create world with coordinates for testing coordinate-based movement."""
    town = Location(name="Town", description="A town with coordinates.", coordinates=(0, 0))
    town.connections = {"north": "Placeholder"}  # Exit exists but no destination
    return {"Town": town}


@pytest.mark.usefixtures("mock_ai_service")
def test_move_triggers_coordinate_based_ai_expansion(test_character, coord_world, mock_ai_service):
    """Test move triggers expand_area for coordinate-based worlds (lines 254-270)."""
    from unittest.mock import patch

    def mock_expand_area(world, ai_service, from_location, direction, theme, target_coords):
        """Mock expand_area that creates a location at target coords."""
        new_loc = Location(
            name="Northern Area",
            description="A generated area to the north.",
            coordinates=target_coords,
        )
        new_loc.connections = {"south": "Town"}
        world["Northern Area"] = new_loc

    with patch("cli_rpg.game_state.expand_area", side_effect=mock_expand_area) as mock_expand:
        game = GameState(
            character=test_character,
            world=coord_world,
            starting_location="Town",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        success, msg = game.move("north")

        assert success is True
        assert game.current_location == "Northern Area"
        mock_expand.assert_called_once()
        # Verify correct parameters were passed
        call_kwargs = mock_expand.call_args[1]
        assert call_kwargs["from_location"] == "Town"
        assert call_kwargs["direction"] == "north"
        assert call_kwargs["target_coords"] == (0, 1)


def test_move_coordinate_expansion_returns_failure_on_error(test_character, coord_world, mock_ai_service):
    """Test move returns failure when expand_area raises AIServiceError (lines 273-275)."""
    from unittest.mock import patch
    from cli_rpg.ai_service import AIServiceError

    with patch("cli_rpg.game_state.expand_area", side_effect=AIServiceError("API failed")):
        game = GameState(
            character=test_character,
            world=coord_world,
            starting_location="Town",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        success, msg = game.move("north")

        assert success is False
        assert "Failed to generate destination" in msg
        assert "API failed" in msg


def test_move_coordinate_expansion_fails_when_location_not_created(
    test_character, coord_world, mock_ai_service
):
    """Test move fails when expand_area runs but doesn't create location (lines 271-272)."""
    from unittest.mock import patch

    def mock_expand_area_no_create(world, ai_service, from_location, direction, theme, target_coords):
        """Mock expand_area that does not create any location."""
        pass  # Does nothing

    with patch("cli_rpg.game_state.expand_area", side_effect=mock_expand_area_no_create):
        game = GameState(
            character=test_character,
            world=coord_world,
            starting_location="Town",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        success, msg = game.move("north")

        assert success is False
        assert msg == "Failed to generate destination."


# ===== Test for autosave IOError silent failure (lines 311-312) =====


def test_move_autosave_ioerror_silent_failure(test_character, mock_ai_service):
    """Test move succeeds even when autosave raises IOError (lines 311-312)."""
    from unittest.mock import patch

    # Create world with existing destination (so move will succeed)
    town = Location(
        name="Town Square",
        description="A town square.",
        connections={"north": "Forest"},
    )
    forest = Location(
        name="Forest",
        description="A forest.",
        connections={"south": "Town Square"},
    )
    world = {"Town Square": town, "Forest": forest}

    with patch("cli_rpg.game_state.autosave", side_effect=IOError("Disk full")):
        game = GameState(
            character=test_character,
            world=world,
            starting_location="Town Square",
            ai_service=mock_ai_service,
            theme="fantasy",
        )

        success, msg = game.move("north")

        # Move should succeed despite autosave failure
        assert success is True
        assert game.current_location == "Forest"


# ===== Test for quest exploration messages (line 319) =====


def test_move_appends_exploration_quest_messages(test_character, mock_ai_service):
    """Test move appends quest progress messages when exploring (line 319)."""
    from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType

    # Create world with destination
    town = Location(
        name="Town Square",
        description="A town square.",
        connections={"north": "Ancient Ruins"},
    )
    ruins = Location(
        name="Ancient Ruins",
        description="Ancient ruins to explore.",
        connections={"south": "Town Square"},
    )
    world = {"Town Square": town, "Ancient Ruins": ruins}

    # Add exploration quest to character
    explore_quest = Quest(
        name="Find the Ruins",
        description="Explore the ancient ruins.",
        objective_type=ObjectiveType.EXPLORE,
        target="Ancient Ruins",
        status=QuestStatus.ACTIVE,
        target_count=1,
        current_count=0,
        quest_giver="Elder",
    )
    test_character.quests.append(explore_quest)

    game = GameState(
        character=test_character,
        world=world,
        starting_location="Town Square",
        ai_service=mock_ai_service,
        theme="fantasy",
    )

    success, msg = game.move("north")

    assert success is True
    # Quest should be marked as ready to turn in
    assert explore_quest.status == QuestStatus.READY_TO_TURN_IN
    # Message should include quest completion notification
    assert "Quest objectives complete" in msg
    assert "Find the Ruins" in msg
    assert "Elder" in msg
