"""Pytest configuration and fixtures for CLI RPG tests."""
import os
import pytest
from unittest.mock import patch
import tempfile


@pytest.fixture(autouse=True)
def disable_colors():
    """Disable colors during tests for consistent string comparisons.

    This fixture sets CLI_RPG_NO_COLOR=true to disable ANSI color codes
    in all test output, ensuring existing tests continue to pass.
    """
    # Clear the color_enabled cache before setting env var
    try:
        from cli_rpg import colors
        colors._check_env_color.cache_clear()
    except (ImportError, AttributeError):
        pass

    with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": "true"}):
        # Clear cache again after setting env var
        try:
            from cli_rpg import colors
            colors._check_env_color.cache_clear()
        except (ImportError, AttributeError):
            pass
        yield

    # Clear cache after test to restore default behavior
    try:
        from cli_rpg import colors
        colors._check_env_color.cache_clear()
    except (ImportError, AttributeError):
        pass


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
