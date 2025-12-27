"""Test world fixture loading utilities for demo mode and testing.

This module provides functions to load pre-generated test world fixtures
for use in automated testing and demo mode gameplay.
"""

import json
from pathlib import Path
from typing import Optional

from cli_rpg.game_state import GameState


def get_fixture_path() -> Path:
    """Get the path to the test world fixture file.

    Returns:
        Path to tests/fixtures/test_world.json
    """
    # Navigate from src/cli_rpg to project root
    module_dir = Path(__file__).parent
    project_root = module_dir.parent.parent
    return project_root / "tests" / "fixtures" / "test_world.json"


def load_test_world() -> dict:
    """Load pre-generated test world from fixtures.

    Returns:
        Dictionary containing serialized game state

    Raises:
        FileNotFoundError: If fixture file doesn't exist
        json.JSONDecodeError: If fixture file is invalid JSON
    """
    fixture_path = get_fixture_path()
    with open(fixture_path, "r") as f:
        return json.load(f)


def create_demo_game_state(ai_service=None) -> GameState:
    """Create GameState from pre-generated test world.

    This creates a ready-to-play game state with:
    - A level 3 Warrior character with equipment and quests
    - 5 overworld locations including a village, forest, cave, ruins, and crossroads
    - NPCs with shops and quests
    - A cave SubGrid with boss encounter
    - Default factions

    Args:
        ai_service: Optional AIService instance (typically None for demo mode)

    Returns:
        GameState ready for gameplay

    Raises:
        FileNotFoundError: If fixture file doesn't exist
        KeyError: If fixture is missing required fields
    """
    data = load_test_world()
    return GameState.from_dict(data, ai_service=ai_service)
