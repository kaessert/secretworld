"""Tests for the main entry point and package structure."""

import sys
from io import StringIO

import pytest


def test_package_importable():
    """Test that the cli_rpg package can be imported.
    
    Verifies: Package structure requirement from spec.
    """
    import cli_rpg
    
    assert cli_rpg is not None


def test_package_has_version():
    """Test that the cli_rpg package has a __version__ attribute.
    
    Verifies: Package metadata requirement from spec.
    """
    import cli_rpg
    
    assert hasattr(cli_rpg, "__version__")
    assert isinstance(cli_rpg.__version__, str)
    assert cli_rpg.__version__ == "0.1.0"


def test_main_function_exists():
    """Test that the main() function exists in cli_rpg.main.
    
    Verifies: CLI entry point existence requirement from spec.
    """
    from cli_rpg import main
    
    assert hasattr(main, "main")
    assert callable(main.main)


def test_main_function_callable():
    """Test that main() can be called without errors.
    
    Verifies: CLI entry point callable requirement from spec.
    """
    from cli_rpg.main import main
    from unittest.mock import patch
    
    # Mock input to exit immediately
    with patch('builtins.input', return_value="3"):
        # Capture stdout to avoid cluttering test output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main()
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should execute without raising exceptions
        assert output is not None
        assert "Welcome to CLI RPG!" in output


def test_main_returns_zero():
    """Test that main() returns 0 or None (success status).
    
    Verifies: CLI entry point success exit requirement from spec.
    """
    from cli_rpg.main import main
    from unittest.mock import patch
    
    # Mock input to exit immediately
    with patch('builtins.input', return_value="3"):
        # Capture stdout to avoid cluttering test output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main()
        finally:
            sys.stdout = old_stdout
        
        # Should return 0 for success (or None which is also acceptable)
        assert result == 0 or result is None
