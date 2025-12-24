"""Automatic game saving functionality."""
import json
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from cli_rpg.persistence import _sanitize_filename

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


def get_autosave_path(character_name: str, save_dir: str = "saves") -> str:
    """Get the autosave file path for a character.

    Args:
        character_name: Name of the character
        save_dir: Directory for save files

    Returns:
        Full path to autosave file
    """
    sanitized_name = _sanitize_filename(character_name)
    return str(Path(save_dir) / f"autosave_{sanitized_name}.json")


def autosave(game_state: "GameState", save_dir: str = "saves") -> str:
    """Automatically save game state to dedicated autosave slot.

    Args:
        game_state: Current game state to save
        save_dir: Directory for save files

    Returns:
        Path to saved file

    Raises:
        IOError: If save fails
    """
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    filepath = get_autosave_path(game_state.current_character.name, save_dir)

    game_data = game_state.to_dict()

    with open(filepath, 'w') as f:
        json.dump(game_data, f, indent=2)

    return filepath


def load_autosave(character_name: str, save_dir: str = "saves") -> Optional["GameState"]:
    """Load autosave for a character if it exists.

    Args:
        character_name: Name of character to load autosave for
        save_dir: Directory containing save files

    Returns:
        GameState if autosave exists, None otherwise
    """
    from cli_rpg.game_state import GameState

    filepath = get_autosave_path(character_name, save_dir)

    if not Path(filepath).exists():
        return None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return GameState.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
