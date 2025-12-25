"""Tests for AI location category generation.

Tests verify:
1. AI returns category field
2. AI validates category values
3. Category passed to Location in create_ai_world
4. Category passed to Location in expand_world
5. Area generation includes category
6. Prompt includes category instruction
"""

import json
import pytest
from unittest.mock import Mock, patch
from cli_rpg.ai_config import AIConfig, DEFAULT_LOCATION_PROMPT
from cli_rpg.ai_service import AIService, AIGenerationError


# Valid categories per spec
VALID_CATEGORIES = {
    "town", "dungeon", "wilderness", "settlement",
    "ruins", "cave", "forest", "mountain", "village"
}


@pytest.fixture
def basic_config(tmp_path):
    """Create a basic AIConfig for testing with isolated cache file."""
    return AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        max_retries=3,
        retry_delay=0.1,
        cache_file=str(tmp_path / "test_cache.json")
    )


@pytest.fixture
def config_no_cache():
    """Create AIConfig with caching disabled."""
    return AIConfig(
        api_key="test-key-123",
        enable_caching=False,
        retry_delay=0.1
    )


# Test 1: AI returns category field
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_location_returns_category_field(mock_openai_class, basic_config):
    """Test generate_location returns dict with category key."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response_with_category = {
        "name": "Ancient Temple",
        "description": "A weathered stone temple with mysterious carvings.",
        "connections": {"south": "Town Square"},
        "category": "ruins"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response_with_category)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    assert "category" in result
    assert result["category"] == "ruins"


# Test 2a: AI validates category values - valid categories accepted
@patch('cli_rpg.ai_service.OpenAI')
@pytest.mark.parametrize("category", list(VALID_CATEGORIES))
def test_valid_categories_accepted(mock_openai_class, basic_config, category):
    """Test all valid category values are accepted."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response = {
        "name": "Test Location",
        "description": "A test location for category validation.",
        "connections": {},
        "category": category
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    assert result["category"] == category


# Test 2b: Invalid/missing category defaults to None
@patch('cli_rpg.ai_service.OpenAI')
def test_invalid_category_defaults_to_none(mock_openai_class, basic_config):
    """Test invalid category values default to None."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response = {
        "name": "Test Location",
        "description": "A test location for category validation.",
        "connections": {},
        "category": "invalid_category"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    assert result["category"] is None


@patch('cli_rpg.ai_service.OpenAI')
def test_missing_category_defaults_to_none(mock_openai_class, basic_config):
    """Test missing category field defaults to None."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    response = {
        "name": "Test Location",
        "description": "A test location without category.",
        "connections": {}
        # No category field
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    assert result["category"] is None


# Test 3: Category passed to Location in create_ai_world
@patch('cli_rpg.ai_service.OpenAI')
def test_create_ai_world_passes_category_to_location(mock_openai_class, basic_config):
    """Test create_ai_world passes category from AI response to Location."""
    from cli_rpg.ai_world import create_ai_world

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Mock response with category
    starting_response = {
        "name": "Town Square",
        "description": "The central plaza of the village.",
        "connections": {},
        "category": "town"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(starting_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    world, starting_name = create_ai_world(
        ai_service=service,
        theme="fantasy",
        initial_size=1
    )

    # Verify the starting location has category set
    assert starting_name in world
    assert world[starting_name].category == "town"


# Test 4: Category passed to Location in expand_world
@patch('cli_rpg.ai_service.OpenAI')
def test_expand_world_passes_category_to_location(mock_openai_class, basic_config):
    """Test expand_world passes category from AI response to new Location."""
    from cli_rpg.ai_world import expand_world
    from cli_rpg.models.location import Location

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Create initial world with a starting location
    world = {
        "Town Square": Location(
            name="Town Square",
            description="Central plaza",
            connections={},
            coordinates=(0, 0)
        )
    }

    # Mock response for new location
    new_location_response = {
        "name": "Dark Forest",
        "description": "A shadowy forest with twisted trees.",
        "connections": {"south": "Town Square"},
        "category": "forest"
    }

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(new_location_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    updated_world = expand_world(
        world=world,
        ai_service=service,
        from_location="Town Square",
        direction="north",
        theme="fantasy"
    )

    # Verify the new location has category set
    assert "Dark Forest" in updated_world
    assert updated_world["Dark Forest"].category == "forest"


# Test 5: Area generation includes category
@patch('cli_rpg.ai_service.OpenAI')
def test_generate_area_includes_category(mock_openai_class, basic_config):
    """Test generate_area returns category for each location."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response = [
        {
            "name": "Dungeon Entrance",
            "description": "A dark entrance to the underground.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"},
            "category": "dungeon"
        },
        {
            "name": "Deep Cavern",
            "description": "A deep cavern with strange echoes.",
            "relative_coords": [0, 1],
            "connections": {"south": "Dungeon Entrance"},
            "category": "cave"
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="underground",
        entry_direction="north",
        context_locations=[],
        size=4
    )

    assert len(result) == 2
    assert result[0]["category"] == "dungeon"
    assert result[1]["category"] == "cave"


@patch('cli_rpg.ai_service.OpenAI')
def test_area_generation_missing_category_defaults_to_none(mock_openai_class, basic_config):
    """Test area locations without category default to None."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response = [
        {
            "name": "Mystery Location",
            "description": "A location with no category.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"}
            # No category field
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="mysterious",
        entry_direction="north",
        context_locations=[],
        size=4
    )

    assert len(result) == 1
    assert result[0]["category"] is None


@patch('cli_rpg.ai_service.OpenAI')
def test_area_generation_invalid_category_defaults_to_none(mock_openai_class, basic_config):
    """Test area locations with invalid category default to None and log warning."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    area_response = [
        {
            "name": "Weird Location",
            "description": "A location with an invalid category.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"},
            "category": "invalid_dungeon"  # Invalid category
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    result = service.generate_area(
        theme="fantasy",
        sub_theme_hint="mysterious",
        entry_direction="north",
        context_locations=[],
        size=4
    )

    assert len(result) == 1
    assert result[0]["category"] is None


# Test 6: Prompt includes category instruction
def test_location_prompt_includes_category_instruction():
    """Test DEFAULT_LOCATION_PROMPT asks for category field."""
    assert "category" in DEFAULT_LOCATION_PROMPT.lower()


def test_location_prompt_lists_valid_categories():
    """Test DEFAULT_LOCATION_PROMPT lists valid category values."""
    prompt_lower = DEFAULT_LOCATION_PROMPT.lower()
    # Check that at least some of the valid categories are mentioned
    categories_mentioned = sum(1 for cat in VALID_CATEGORIES if cat in prompt_lower)
    assert categories_mentioned >= 5, f"Expected at least 5 valid categories in prompt, found {categories_mentioned}"


@patch('cli_rpg.ai_service.OpenAI')
def test_area_prompt_includes_category_instruction(mock_openai_class, basic_config):
    """Test area generation prompt asks for category field."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # We'll capture the prompt by checking what's passed to the LLM
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps([
        {
            "name": "Test Location",
            "description": "A test location.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD"},
            "category": "town"
        }
    ])
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    service.generate_area(
        theme="fantasy",
        sub_theme_hint="test",
        entry_direction="north",
        context_locations=[],
        size=4
    )

    # Verify the prompt contains category instructions
    call_args = mock_client.chat.completions.create.call_args
    prompt = call_args.kwargs['messages'][0]['content']
    assert "category" in prompt.lower()


# Test expand_area passes category to Location
@patch('cli_rpg.ai_service.OpenAI')
def test_expand_area_passes_category_to_location(mock_openai_class, basic_config):
    """Test expand_area passes category from AI response to Location."""
    from cli_rpg.ai_world import expand_area
    from cli_rpg.models.location import Location

    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Create initial world
    world = {
        "Town Square": Location(
            name="Town Square",
            description="Central plaza",
            connections={},
            coordinates=(0, 0)
        )
    }

    # Mock area response
    area_response = [
        {
            "name": "Mountain Pass",
            "description": "A narrow mountain pass.",
            "relative_coords": [0, 0],
            "connections": {"south": "EXISTING_WORLD", "north": "Peak"},
            "category": "mountain"
        },
        {
            "name": "Peak",
            "description": "The mountain summit.",
            "relative_coords": [0, 1],
            "connections": {"south": "Mountain Pass"},
            "category": "mountain"
        }
    ]

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(area_response)
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService(basic_config)
    updated_world = expand_area(
        world=world,
        ai_service=service,
        from_location="Town Square",
        direction="north",
        theme="fantasy",
        target_coords=(0, 1),
        size=4
    )

    # Verify the new locations have category set
    assert "Mountain Pass" in updated_world
    assert updated_world["Mountain Pass"].category == "mountain"
    assert "Peak" in updated_world
    assert updated_world["Peak"].category == "mountain"
