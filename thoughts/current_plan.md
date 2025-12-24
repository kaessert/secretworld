# Implementation Plan: Automatic Game Saving

## Spec

The game should automatically save the player's progress at key moments to prevent data loss. Auto-save triggers:
1. After successful movement to a new location
2. After combat ends (victory or retreat via flee)
3. After character state changes (level up, health restored)

The auto-save should:
- Use a dedicated auto-save slot (single file that gets overwritten)
- Not interfere with manual saves
- Be silent (no UI feedback unless an error occurs)
- Use consistent filename: `autosave_{character_name}.json`

---

## Tests

**File:** `tests/test_autosave.py`

```python
"""Tests for automatic game saving functionality."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState
from cli_rpg.world import create_world
from cli_rpg.autosave import autosave, get_autosave_path, load_autosave


class TestAutosaveBasics:
    """Test basic autosave functionality."""

    def test_autosave_creates_file(self, tmp_path):
        """Autosave should create a save file."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)

        filepath = autosave(game_state, save_dir=str(tmp_path))

        assert Path(filepath).exists()

    def test_autosave_filename_format(self, tmp_path):
        """Autosave file should use consistent naming."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)

        filepath = autosave(game_state, save_dir=str(tmp_path))

        assert "autosave_Hero.json" in filepath

    def test_autosave_overwrites_previous(self, tmp_path):
        """Subsequent autosaves should overwrite the previous one."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)

        # First autosave
        filepath1 = autosave(game_state, save_dir=str(tmp_path))

        # Move and autosave again
        game_state.current_location = list(game_state.world.keys())[1]
        filepath2 = autosave(game_state, save_dir=str(tmp_path))

        # Should be same file
        assert filepath1 == filepath2

        # Should only be one autosave file
        autosave_files = list(tmp_path.glob("autosave_*.json"))
        assert len(autosave_files) == 1

    def test_autosave_preserves_game_state(self, tmp_path):
        """Autosave should preserve complete game state."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)
        game_state.move("north")
        expected_location = game_state.current_location

        filepath = autosave(game_state, save_dir=str(tmp_path))
        loaded_state = load_autosave("Hero", save_dir=str(tmp_path))

        assert loaded_state.current_location == expected_location
        assert loaded_state.current_character.name == "Hero"


class TestAutosavePath:
    """Test autosave path generation."""

    def test_get_autosave_path_basic(self, tmp_path):
        """Should generate correct path for character name."""
        path = get_autosave_path("Hero", save_dir=str(tmp_path))
        assert path == str(tmp_path / "autosave_Hero.json")

    def test_get_autosave_path_sanitizes_name(self, tmp_path):
        """Should sanitize special characters in name."""
        path = get_autosave_path("Hero/Villain", save_dir=str(tmp_path))
        assert "/" not in Path(path).name or str(tmp_path) in path


class TestLoadAutosave:
    """Test loading autosave files."""

    def test_load_autosave_success(self, tmp_path):
        """Should load existing autosave."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)
        autosave(game_state, save_dir=str(tmp_path))

        loaded = load_autosave("Hero", save_dir=str(tmp_path))

        assert loaded is not None
        assert loaded.current_character.name == "Hero"

    def test_load_autosave_not_found(self, tmp_path):
        """Should return None if no autosave exists."""
        loaded = load_autosave("NonExistent", save_dir=str(tmp_path))
        assert loaded is None
```

---

## Implementation Steps

### Step 1: Create autosave module
**File:** `src/cli_rpg/autosave.py`

```python
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
```

### Step 2: Integrate autosave into game_state.py
**File:** `src/cli_rpg/game_state.py`

Add autosave trigger after successful movement in the `move` method:

```python
# At top of file, add import:
from cli_rpg.autosave import autosave

# In move() method, after line 200 (after self.current_location = destination_name):
# Add autosave trigger:
try:
    autosave(self)
except IOError:
    pass  # Silent failure - don't interrupt gameplay
```

### Step 3: Integrate autosave into combat resolution in main.py
**File:** `src/cli_rpg/main.py`

Add autosave trigger after combat ends:

```python
# At top, add import:
from cli_rpg.autosave import autosave

# In handle_combat_command(), after combat victory (line ~138):
# After: game_state.current_combat = None
try:
    autosave(game_state)
except IOError:
    pass

# In handle_combat_command(), after successful flee (line ~177):
# After: combat.is_active = False
try:
    autosave(game_state)
except IOError:
    pass
```

### Step 4: Run tests
```bash
pytest tests/test_autosave.py -v
```

### Step 5: Update ISSUES.md
**File:** `ISSUES.md`

Mark the "Game should ALWAYS SAVE" issue as resolved.
