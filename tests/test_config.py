"""Tests for config module."""

import os
import pytest
from unittest.mock import patch


class TestIsAIStrictMode:
    """Tests for is_ai_strict_mode() function.

    Spec: Add a configuration option CLI_RPG_REQUIRE_AI=true/false to control
    strict vs. fallback mode (default: strict when AI service is provided)
    """

    def test_strict_mode_true_by_default(self):
        """Test that strict mode is True when env var is not set.

        Spec: Returns True if CLI_RPG_REQUIRE_AI env var is not set
        """
        from cli_rpg.config import is_ai_strict_mode

        with patch.dict(os.environ, {}, clear=True):
            # Ensure the env var is not set
            os.environ.pop('CLI_RPG_REQUIRE_AI', None)
            assert is_ai_strict_mode() is True

    def test_strict_mode_true_when_set_to_true(self):
        """Test that strict mode is True when env var is 'true'.

        Spec: Returns True if CLI_RPG_REQUIRE_AI is "true"
        """
        from cli_rpg.config import is_ai_strict_mode

        with patch.dict(os.environ, {'CLI_RPG_REQUIRE_AI': 'true'}):
            assert is_ai_strict_mode() is True

    def test_strict_mode_true_when_set_to_TRUE_uppercase(self):
        """Test that strict mode is True when env var is 'TRUE' (case-insensitive).

        Spec: Returns True if CLI_RPG_REQUIRE_AI is "true" (case-insensitive)
        """
        from cli_rpg.config import is_ai_strict_mode

        with patch.dict(os.environ, {'CLI_RPG_REQUIRE_AI': 'TRUE'}):
            assert is_ai_strict_mode() is True

    def test_strict_mode_false_when_set_to_false(self):
        """Test that strict mode is False when env var is 'false'.

        Spec: Returns False only if explicitly set to "false"
        """
        from cli_rpg.config import is_ai_strict_mode

        with patch.dict(os.environ, {'CLI_RPG_REQUIRE_AI': 'false'}):
            assert is_ai_strict_mode() is False

    def test_strict_mode_false_when_set_to_FALSE_uppercase(self):
        """Test that strict mode is False when env var is 'FALSE' (case-insensitive).

        Spec: Returns False only if explicitly set to "false" (case-insensitive)
        """
        from cli_rpg.config import is_ai_strict_mode

        with patch.dict(os.environ, {'CLI_RPG_REQUIRE_AI': 'FALSE'}):
            assert is_ai_strict_mode() is False

    def test_strict_mode_true_for_invalid_values(self):
        """Test that strict mode is True for invalid env var values.

        Spec: Default to strict (True) for any value that isn't explicitly "false"
        """
        from cli_rpg.config import is_ai_strict_mode

        invalid_values = ['yes', 'no', '1', '0', '', 'foo', 'True', 'False']
        for value in invalid_values:
            with patch.dict(os.environ, {'CLI_RPG_REQUIRE_AI': value}):
                # Only "false" (case-insensitive) should return False
                expected = value.lower() == 'false'
                assert is_ai_strict_mode() is not expected or value.lower() == 'false', (
                    f"Expected strict mode for value '{value}'"
                )
