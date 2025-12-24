"""Tests for AI-powered world generation."""

import pytest
from unittest.mock import Mock, patch
from cli_rpg.ai_config import AIConfig
from cli_rpg.ai_service import AIService
from cli_rpg.ai_world import (
    create_ai_world,
    expand_world,
    create_world_with_fallback,
    get_opposite_direction
)
from cli_rpg.models.location import Location


# Fixtures

@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock(spec=AIService)
    return service


@pytest.fixture
def basic_world():
    """Create a basic world with one location."""
    town_square = Location(
        name="Town Square",
        description="A bustling town square."
    )
    return {"Town Square": town_square}


# Test: Create AI world generates locations
def test_create_ai_world_generates_location(mock_ai_service):
    """Test create_ai_world generates at least a starting location."""
    # Mock generate_location to return a valid location
    mock_ai_service.generate_location.return_value = {
        "name": "Town Square",
        "description": "A bustling town square with a fountain.",
        "connections": {
            "north": "Forest Path",
            "east": "Market District"
        }
    }
    
    world = create_ai_world(mock_ai_service, theme="fantasy")
    
    # Verify world is created
    assert len(world) > 0
    assert "Town Square" in world
    assert isinstance(world["Town Square"], Location)


# Test: Create AI world with starting location
def test_create_ai_world_with_starting_location(mock_ai_service):
    """Test create_ai_world creates world with specified starting location."""
    mock_ai_service.generate_location.return_value = {
        "name": "Space Station Alpha",
        "description": "A large orbital station.",
        "connections": {
            "north": "Docking Bay"
        }
    }
    
    world = create_ai_world(
        mock_ai_service,
        theme="sci-fi",
        starting_location_name="Space Station Alpha"
    )
    
    assert "Space Station Alpha" in world
    assert world["Space Station Alpha"].name == "Space Station Alpha"


# Test: Create AI world generates connected locations
def test_create_ai_world_generates_connected_locations(mock_ai_service):
    """Test create_ai_world generates connected locations based on initial location."""
    # First call: starting location
    # Subsequent calls: connected locations
    def mock_generate(theme, context_locations=None, source_location=None, direction=None):
        if source_location is None:
            # Starting location
            return {
                "name": "Town Square",
                "description": "A bustling town square.",
                "connections": {
                    "north": "Forest",
                    "east": "Market"
                }
            }
        elif direction == "north":
            return {
                "name": "Forest",
                "description": "A dark forest.",
                "connections": {
                    "south": "Town Square"
                }
            }
        else:  # east
            return {
                "name": "Market",
                "description": "A busy marketplace.",
                "connections": {
                    "west": "Town Square"
                }
            }
    
    mock_ai_service.generate_location.side_effect = mock_generate
    
    world = create_ai_world(mock_ai_service, theme="fantasy", initial_size=3)
    
    # Verify multiple locations created
    assert len(world) >= 2
    assert "Town Square" in world


# Test: Create AI world expands from seed
def test_create_ai_world_expands_from_seed(mock_ai_service):
    """Test create_ai_world expands world from initial seed location."""
    call_count = [0]
    
    def mock_generate(theme, context_locations=None, source_location=None, direction=None):
        call_count[0] += 1
        if call_count[0] == 1:
            # First location
            return {
                "name": "Central Hub",
                "description": "The central hub.",
                "connections": {"north": "North Wing"}
            }
        else:
            # Expanded location
            return {
                "name": "North Wing",
                "description": "The northern wing.",
                "connections": {"south": "Central Hub"}
            }
    
    mock_ai_service.generate_location.side_effect = mock_generate
    
    world = create_ai_world(mock_ai_service, theme="fantasy", initial_size=2)
    
    # Should have called generate_location multiple times
    assert mock_ai_service.generate_location.call_count >= 2


# Test: Create AI world respects theme
def test_create_ai_world_respects_theme(mock_ai_service):
    """Test create_ai_world passes theme to AI service."""
    mock_ai_service.generate_location.return_value = {
        "name": "Cyberpunk Street",
        "description": "Neon-lit streets.",
        "connections": {}
    }
    
    world = create_ai_world(mock_ai_service, theme="cyberpunk")
    
    # Verify theme was passed
    call_args = mock_ai_service.generate_location.call_args
    assert call_args[1]["theme"] == "cyberpunk"


# Test: Create AI world with AI failure fallback
def test_create_ai_world_with_ai_failure_fallback(mock_ai_service):
    """Test create_world_with_fallback falls back to default world on AI failure."""
    from cli_rpg.ai_service import AIGenerationError
    
    # Mock AI service to fail
    mock_ai_service.generate_location.side_effect = AIGenerationError("Test failure")
    
    world = create_world_with_fallback(ai_service=mock_ai_service, theme="fantasy")
    
    # Should fall back to default world
    assert world is not None
    assert len(world) > 0
    # Default world has these locations
    assert "Town Square" in world or len(world) >= 1


# Test: Create AI world validates generated locations
def test_create_ai_world_validates_generated_locations(mock_ai_service):
    """Test create_ai_world validates that generated locations pass Location model validation."""
    # Return invalid location (name too long)
    mock_ai_service.generate_location.return_value = {
        "name": "A" * 51,  # Too long
        "description": "Valid description.",
        "connections": {}
    }
    
    # Should raise ValueError from Location model
    with pytest.raises(ValueError):
        create_ai_world(mock_ai_service, theme="fantasy")


# Test: Create AI world handles duplicate names
def test_create_ai_world_handles_duplicate_names(mock_ai_service):
    """Test create_ai_world handles duplicate location names appropriately."""
    # Always return same name
    mock_ai_service.generate_location.return_value = {
        "name": "Same Place",
        "description": "A place.",
        "connections": {}
    }
    
    world = create_ai_world(mock_ai_service, theme="fantasy", initial_size=2)
    
    # Should only have one location (duplicates handled)
    # Implementation may skip or overwrite duplicates
    assert "Same Place" in world


# Test: Expand world from location
def test_expand_world_from_location(mock_ai_service, basic_world):
    """Test expand_world generates new location in specified direction."""
    mock_ai_service.generate_location.return_value = {
        "name": "Dark Forest",
        "description": "A mysterious dark forest.",
        "connections": {
            "south": "Town Square"
        }
    }
    
    # Expand north from Town Square
    updated_world = expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )
    
    # Verify new location added
    assert "Dark Forest" in updated_world
    assert updated_world["Dark Forest"].name == "Dark Forest"


# Test: Expand world creates bidirectional connections
def test_expand_world_creates_bidirectional_connections(mock_ai_service, basic_world):
    """Test expand_world creates bidirectional connections between locations."""
    mock_ai_service.generate_location.return_value = {
        "name": "Ancient Ruins",
        "description": "Crumbling ancient ruins.",
        "connections": {
            "south": "Town Square"
        }
    }
    
    updated_world = expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )
    
    # Verify bidirectional connection
    assert updated_world["Town Square"].has_connection("north")
    assert updated_world["Town Square"].get_connection("north") == "Ancient Ruins"
    assert updated_world["Ancient Ruins"].has_connection("south")
    assert updated_world["Ancient Ruins"].get_connection("south") == "Town Square"


# Test: Get opposite direction
def test_get_opposite_direction():
    """Test get_opposite_direction returns correct opposite directions."""
    assert get_opposite_direction("north") == "south"
    assert get_opposite_direction("south") == "north"
    assert get_opposite_direction("east") == "west"
    assert get_opposite_direction("west") == "east"
    assert get_opposite_direction("up") == "down"
    assert get_opposite_direction("down") == "up"


# Test: Expand world with invalid source location
def test_expand_world_invalid_source_location(mock_ai_service, basic_world):
    """Test expand_world raises error when source location doesn't exist."""
    with pytest.raises(ValueError, match="not found in world"):
        expand_world(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Nonexistent Place",
            direction="north",
            theme="fantasy"
        )


# Test: Expand world with invalid direction
def test_expand_world_invalid_direction(mock_ai_service, basic_world):
    """Test expand_world raises error for invalid direction."""
    with pytest.raises(ValueError, match="Invalid direction"):
        expand_world(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="northeast",  # Invalid
            theme="fantasy"
        )


# Test: Create world with fallback when no AI service
def test_create_world_with_fallback_no_ai_service():
    """Test create_world_with_fallback uses default world when no AI service provided."""
    world = create_world_with_fallback(ai_service=None, theme="fantasy")
    
    # Should create default world
    assert world is not None
    assert len(world) > 0


# Test: Expand world context includes existing locations
def test_expand_world_context_includes_existing_locations(mock_ai_service, basic_world):
    """Test expand_world passes existing location names as context to AI."""
    mock_ai_service.generate_location.return_value = {
        "name": "New Place",
        "description": "A new place.",
        "connections": {"south": "Town Square"}
    }
    
    expand_world(
        world=basic_world,
        ai_service=mock_ai_service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )
    
    # Verify context_locations was passed
    call_args = mock_ai_service.generate_location.call_args
    context_locations = call_args[1]["context_locations"]
    assert "Town Square" in context_locations
