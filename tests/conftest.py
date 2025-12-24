"""Pytest configuration and fixtures for CLI RPG tests."""
import pytest
from unittest.mock import patch
import tempfile


@pytest.fixture(autouse=True)
def mock_autosave_directory():
    """Mock autosave to use a temporary directory instead of real saves/.

    This prevents tests from polluting the saves/ directory and ensures
    test isolation for autosave functionality.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            from cli_rpg import autosave as autosave_module
            original_autosave = autosave_module.autosave

            def patched_autosave(game_state, save_dir="saves"):
                # If using default saves dir, redirect to temp
                if save_dir == "saves":
                    save_dir = tmpdir
                return original_autosave(game_state, save_dir=save_dir)

            # Patch in both the module and where it's imported in game_state
            with patch.object(autosave_module, 'autosave', patched_autosave):
                with patch('cli_rpg.game_state.autosave', patched_autosave):
                    with patch('cli_rpg.main.autosave', patched_autosave):
                        yield tmpdir

        except ImportError:
            # If autosave module doesn't exist yet, just yield
            yield tmpdir
