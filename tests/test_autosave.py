"""Tests for automatic game saving functionality.

Tests verify the spec:
1. Autosave creates a file at key moments
2. Autosave uses consistent naming: autosave_{character_name}.json
3. Autosave overwrites previous autosave (single slot)
4. Autosave preserves complete game state
5. Autosave handles missing files gracefully
"""
from pathlib import Path

from cli_rpg.models.character import Character
from cli_rpg.game_state import GameState
from cli_rpg.world import create_world
from cli_rpg.autosave import autosave, get_autosave_path, load_autosave


class TestAutosaveBasics:
    """Test basic autosave functionality.

    Spec: Auto-save should use a dedicated auto-save slot (single file that gets overwritten)
    """

    def test_autosave_creates_file(self, tmp_path):
        """Autosave should create a save file.

        Spec: The game should automatically save the player's progress
        """
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)

        filepath = autosave(game_state, save_dir=str(tmp_path))

        assert Path(filepath).exists()

    def test_autosave_filename_format(self, tmp_path):
        """Autosave file should use consistent naming.

        Spec: Use consistent filename: autosave_{character_name}.json
        """
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)

        filepath = autosave(game_state, save_dir=str(tmp_path))

        assert "autosave_Hero.json" in filepath

    def test_autosave_overwrites_previous(self, tmp_path):
        """Subsequent autosaves should overwrite the previous one.

        Spec: Use a dedicated auto-save slot (single file that gets overwritten)
        """
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
        """Autosave should preserve complete game state.

        Spec: Auto-save preserves player's progress (location, character state)
        """
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        world, starting_location = create_world()
        game_state = GameState(character, world, starting_location)
        game_state.move("north")
        expected_location = game_state.current_location

        autosave(game_state, save_dir=str(tmp_path))
        loaded_state = load_autosave("Hero", save_dir=str(tmp_path))

        assert loaded_state.current_location == expected_location
        assert loaded_state.current_character.name == "Hero"


class TestAutosavePath:
    """Test autosave path generation.

    Spec: Use consistent filename: autosave_{character_name}.json
    """

    def test_get_autosave_path_basic(self, tmp_path):
        """Should generate correct path for character name."""
        path = get_autosave_path("Hero", save_dir=str(tmp_path))
        assert path == str(tmp_path / "autosave_Hero.json")

    def test_get_autosave_path_sanitizes_name(self, tmp_path):
        """Should sanitize special characters in name.

        Spec: Filename should be safe for filesystem
        """
        path = get_autosave_path("Hero/Villain", save_dir=str(tmp_path))
        # The slash should be replaced with underscore
        assert "autosave_Hero_Villain.json" in path


class TestLoadAutosave:
    """Test loading autosave files.

    Spec: Autosave should preserve complete game state for loading
    """

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
        """Should return None if no autosave exists.

        Spec: Silent failure - don't interrupt gameplay
        """
        loaded = load_autosave("NonExistent", save_dir=str(tmp_path))
        assert loaded is None

    def test_load_autosave_corrupted_json(self, tmp_path):
        """Should return None for corrupted JSON file.

        Spec: Handle corrupted save files gracefully by returning None (line 73).
        """
        filepath = tmp_path / "autosave_Hero.json"
        filepath.write_text("not valid json{{{")
        loaded = load_autosave("Hero", save_dir=str(tmp_path))
        assert loaded is None

    def test_load_autosave_invalid_data_structure(self, tmp_path):
        """Should return None for valid JSON with invalid structure.

        Spec: Handle missing required fields gracefully by returning None (line 73-74).
        """
        filepath = tmp_path / "autosave_Hero.json"
        filepath.write_text('{"invalid": "structure"}')
        loaded = load_autosave("Hero", save_dir=str(tmp_path))
        assert loaded is None

    def test_load_autosave_missing_character_data(self, tmp_path):
        """Should return None when character data is malformed.

        Spec: Handle ValueError from GameState.from_dict gracefully (line 73-74).
        """
        filepath = tmp_path / "autosave_Hero.json"
        # Valid JSON structure but missing required character fields
        filepath.write_text('{"character": {"name": "Hero"}, "world": {}, "current_location": "Town"}')
        loaded = load_autosave("Hero", save_dir=str(tmp_path))
        assert loaded is None
