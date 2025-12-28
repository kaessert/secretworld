"""Pytest configuration and fixtures for E2E tests.

E2E tests require live AI services (OpenAI or Anthropic) and are skipped
by default. Run with `pytest --e2e` to enable them.
"""
import os
import pytest

from cli_rpg.ai_config import AIConfig, AIConfigError


def pytest_configure(config):
    """Register custom markers for E2E tests."""
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests requiring live AI API key"
    )


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless --e2e flag is provided."""
    if not config.getoption("--e2e"):
        skip_e2e = pytest.mark.skip(reason="E2E tests skipped (use --e2e to run)")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)


@pytest.fixture
def ai_config():
    """Create AIConfig from environment variables for E2E testing.

    Requires OPENAI_API_KEY or ANTHROPIC_API_KEY to be set.

    Returns:
        AIConfig instance configured from environment variables

    Raises:
        pytest.skip: If no API key is available
    """
    try:
        config = AIConfig.from_env()
        return config
    except AIConfigError as e:
        pytest.skip(f"AI service not configured: {e}")


@pytest.fixture
def ai_service(ai_config):
    """Create a live AIService for E2E testing.

    Returns:
        AIService instance connected to real AI provider
    """
    from cli_rpg.ai_service import AIService
    return AIService(ai_config)


@pytest.fixture
def ai_game_state(ai_service):
    """Create GameState with live AI service for E2E testing.

    This creates a fresh game state with:
    - A new character
    - An empty world
    - The live AI service for location generation

    Returns:
        GameState instance with live AI integration
    """
    from cli_rpg.game_state import GameState
    from cli_rpg.models.character import Character
    from cli_rpg.models.location import Location
    from cli_rpg.wfc_chunks import ChunkManager

    # Create chunk manager for terrain generation
    chunk_manager = ChunkManager(seed=42)

    # Create a starting location
    starting_location = Location(
        name="Starting Point",
        description="A peaceful clearing where your adventure begins.",
        coordinates=(0, 0),
        category="wilderness",
        terrain="plains",
        is_named=True,
        is_overworld=True,
    )

    # Create the game state with AI service
    game_state = GameState(
        theme="dark fantasy",
        world={"Starting Point": starting_location},
        current_location="Starting Point",
        current_character=Character(name="Test Hero", character_class="warrior"),
        ai_service=ai_service,
        chunk_manager=chunk_manager,
    )

    return game_state
