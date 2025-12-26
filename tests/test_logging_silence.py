"""Tests that log messages don't leak to stderr during normal operations.

This test verifies that the NullHandler added to cli_rpg's root logger
prevents warning messages from appearing on stderr during gameplay.
"""

import logging
import sys
from io import StringIO
from unittest.mock import patch

import pytest


class TestLoggingSilence:
    """Test that log messages are silenced by default."""

    def test_package_has_null_handler(self):
        """Verify NullHandler is attached to cli_rpg logger."""
        import cli_rpg

        logger = logging.getLogger("cli_rpg")
        handler_types = [type(h) for h in logger.handlers]
        assert logging.NullHandler in handler_types

    def test_warning_does_not_leak_to_stderr(self):
        """Verify that warning messages don't appear on stderr."""
        # Capture stderr
        captured = StringIO()

        with patch.object(sys, "stderr", captured):
            # Get a logger under cli_rpg namespace and emit a warning
            logger = logging.getLogger("cli_rpg.test_module")
            logger.warning("This warning should be silenced")

        # stderr should be empty
        assert captured.getvalue() == ""

    def test_debug_does_not_leak_to_stderr(self):
        """Verify that debug messages don't appear on stderr."""
        captured = StringIO()

        with patch.object(sys, "stderr", captured):
            logger = logging.getLogger("cli_rpg.another_module")
            logger.debug("This debug message should be silenced")

        assert captured.getvalue() == ""

    def test_error_does_not_leak_to_stderr(self):
        """Verify that error messages don't appear on stderr."""
        captured = StringIO()

        with patch.object(sys, "stderr", captured):
            logger = logging.getLogger("cli_rpg.error_module")
            logger.error("This error should be silenced")

        assert captured.getvalue() == ""
