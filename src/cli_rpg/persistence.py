"""Character and game state persistence system for CLI RPG."""
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from cli_rpg.models.character import Character

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


def _format_timestamp(ts: str) -> str:
    """Convert YYYYMMDD_HHMMSS to human-readable format.

    Args:
        ts: Timestamp string in format YYYYMMDD_HHMMSS

    Returns:
        Human-readable timestamp like "Dec 25, 2024 03:45 PM"
    """
    try:
        dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
        return dt.strftime("%b %d, %Y %I:%M %p")
    except ValueError:
        return ts


def _sanitize_filename(name: str) -> str:
    """Remove/replace invalid filesystem characters from name.
    
    Args:
        name: Character name to sanitize
        
    Returns:
        Sanitized filename-safe string
    """
    # Replace invalid filesystem characters
    invalid_chars = ['/', '\\', '*', '?', '<', '>', '|', ':', '"']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Limit length to reasonable max
    max_length = 50
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def _generate_filename(character_name: str) -> str:
    """Generate unique filename with timestamp.
    
    Args:
        character_name: Name of the character
        
    Returns:
        Filename in format: {sanitized_name}_{timestamp}.json
    """
    sanitized_name = _sanitize_filename(character_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitized_name}_{timestamp}.json"


def save_character(character: Character, save_dir: str = "saves") -> str:
    """Save character to JSON file.
    
    Args:
        character: Character instance to save
        save_dir: Directory to save character files (default: "saves")
        
    Returns:
        Full path to saved file
        
    Raises:
        IOError: If write operation fails
    """
    try:
        # Create directory if it doesn't exist
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        filename = _generate_filename(character.name)
        filepath = save_path / filename
        
        # Serialize character to dictionary
        character_data = character.to_dict()
        
        # Write JSON to file
        with open(filepath, 'w') as f:
            json.dump(character_data, f, indent=2)
        
        return str(filepath)
        
    except (OSError, PermissionError) as e:
        raise IOError(f"Failed to save character: {e}")


def load_character(filepath: str) -> Character:
    """Load character from JSON file.
    
    Args:
        filepath: Path to character save file
        
    Returns:
        Character instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid or character data is corrupted
    """
    # Check if file exists
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"Save file not found: {filepath}")
    
    try:
        # Load and parse JSON
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate required keys
        required_keys = ['name', 'strength', 'dexterity', 'intelligence']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required field: {key}")
        
        # Deserialize using Character.from_dict()
        character = Character.from_dict(data)
        return character
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in save file: {e}")
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid character data: {e}")
    except ValueError as e:
        # Re-raise validation errors from Character
        raise ValueError(f"Invalid character data: {e}")


def list_saves(save_dir: str = "saves") -> list[dict[str, Any]]:
    """List all available character saves.

    Args:
        save_dir: Directory containing save files (default: "saves")

    Returns:
        List of dicts with keys: name, filepath, timestamp, display_time, is_autosave
        Sorted by timestamp (most recent first)
    """
    save_path = Path(save_dir)

    # Return empty list if directory doesn't exist
    if not save_path.exists():
        return []

    # Find all JSON files
    json_files = list(save_path.glob("*.json"))

    saves = []
    for json_file in json_files:
        filename = json_file.stem  # Filename without extension

        # Detect autosave by filename prefix
        is_autosave = filename.startswith("autosave_")

        # Parse filename to extract character name and timestamp
        # Expected format: {name}_{timestamp}
        parts = filename.rsplit('_', 2)  # Split from right, max 2 splits

        if len(parts) >= 3:
            # Last two parts are date and time
            character_name = '_'.join(parts[:-2])
            timestamp = f"{parts[-2]}_{parts[-1]}"
        else:
            # Fallback if filename doesn't match expected format
            character_name = filename
            timestamp = "unknown"

        # Fallback timestamp from file mtime if unknown
        if timestamp == "unknown":
            mtime = json_file.stat().st_mtime
            timestamp = datetime.fromtimestamp(mtime).strftime("%Y%m%d_%H%M%S")

        saves.append({
            'name': character_name,
            'filepath': str(json_file),
            'timestamp': timestamp,
            'display_time': _format_timestamp(timestamp),
            'is_autosave': is_autosave,
        })

    # Sort by timestamp (most recent first)
    saves.sort(key=lambda x: x['timestamp'], reverse=True)

    return saves


def detect_save_type(filepath: str) -> str:
    """Detect whether save file is character-only or full game state.
    
    Args:
        filepath: Path to save file
        
    Returns:
        "character" for character-only saves
        "game_state" for full game state saves
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    # Check if file exists
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"Save file not found: {filepath}")
    
    try:
        # Load and parse JSON
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Check for presence of "world" key to determine save type
        if "world" in data:
            return "game_state"
        else:
            return "character"
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in save file: {e}")


def delete_save(filepath: str) -> bool:
    """Delete a save file.
    
    Args:
        filepath: Path to save file to delete
        
    Returns:
        True if successful, False if file doesn't exist
        
    Raises:
        OSError: On permission errors
    """
    file_path = Path(filepath)
    
    try:
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
        
    except FileNotFoundError:
        return False


def save_game_state(game_state: "GameState", save_dir: str = "saves") -> str:
    """Save complete game state to JSON file.
    
    Args:
        game_state: GameState instance to save
        save_dir: Directory to save game files (default: "saves")
        
    Returns:
        Full path to saved file
        
    Raises:
        IOError: If write operation fails
    """
    try:
        # Create directory if it doesn't exist
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        filename = _generate_filename(game_state.current_character.name)
        filepath = save_path / filename
        
        # Serialize game state to dictionary
        game_data = game_state.to_dict()
        
        # Write JSON to file
        with open(filepath, 'w') as f:
            json.dump(game_data, f, indent=2)
        
        return str(filepath)
        
    except (OSError, PermissionError) as e:
        raise IOError(f"Failed to save game state: {e}")


def load_game_state(filepath: str) -> "GameState":
    """Load complete game state from JSON file.
    
    Args:
        filepath: Path to game state save file
        
    Returns:
        GameState instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid or game state data is corrupted
    """
    # Import here to avoid circular dependency
    from cli_rpg.game_state import GameState
    
    # Check if file exists
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"Save file not found: {filepath}")
    
    try:
        # Load and parse JSON
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate required keys
        required_keys = ['character', 'current_location', 'world']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required field: {key}")
        
        # Deserialize using GameState.from_dict()
        game_state = GameState.from_dict(data)
        return game_state
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in save file: {e}")
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid game state data: {e}")
    except ValueError as e:
        # Re-raise validation errors from GameState
        raise ValueError(f"Invalid game state data: {e}")
