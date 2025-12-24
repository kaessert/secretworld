"""Tests for the colors module."""
import os
import pytest
from unittest.mock import patch

from cli_rpg import colors


class TestColorEnabled:
    """Tests for color_enabled function."""

    def test_color_enabled_default(self):
        """Colors should be enabled when CLI_RPG_NO_COLOR is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove CLI_RPG_NO_COLOR if it exists
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            # Clear the cache to force re-evaluation
            colors.color_enabled.cache_clear()
            assert colors.color_enabled() is True

    def test_color_disabled_via_env_true(self):
        """Colors should be disabled when CLI_RPG_NO_COLOR=true."""
        with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": "true"}):
            colors.color_enabled.cache_clear()
            assert colors.color_enabled() is False

    def test_color_disabled_via_env_one(self):
        """Colors should be disabled when CLI_RPG_NO_COLOR=1."""
        with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": "1"}):
            colors.color_enabled.cache_clear()
            assert colors.color_enabled() is False

    def test_color_enabled_with_empty_env(self):
        """Colors should be enabled when CLI_RPG_NO_COLOR is empty."""
        with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": ""}):
            colors.color_enabled.cache_clear()
            assert colors.color_enabled() is True

    def test_color_enabled_with_false_env(self):
        """Colors should be enabled when CLI_RPG_NO_COLOR=false."""
        with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": "false"}):
            colors.color_enabled.cache_clear()
            assert colors.color_enabled() is True


class TestColorize:
    """Tests for colorize function."""

    def test_colorize_returns_colored_when_enabled(self):
        """Verify ANSI codes are present when colors enabled."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.colorize("test", colors.RED)
            assert result.startswith(colors.RED)
            assert result.endswith(colors.RESET)
            assert "test" in result

    def test_colorize_returns_plain_when_disabled(self):
        """Verify no ANSI codes when colors disabled."""
        with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": "true"}):
            colors.color_enabled.cache_clear()
            result = colors.colorize("test", colors.RED)
            assert result == "test"
            assert "\x1b" not in result  # No escape sequences

    def test_reset_always_appended(self):
        """Ensure RESET code terminates colored text."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.colorize("test", colors.CYAN)
            assert result.endswith(colors.RESET)


class TestSemanticHelpers:
    """Tests for semantic color helper functions."""

    def setup_method(self):
        """Enable colors for each test."""
        os.environ.pop("CLI_RPG_NO_COLOR", None)
        colors.color_enabled.cache_clear()

    def test_enemy_uses_red(self):
        """enemy() should use red color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.enemy("Goblin")
            assert colors.RED in result
            assert "Goblin" in result

    def test_location_uses_cyan(self):
        """location() should use cyan color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.location("Town Square")
            assert colors.CYAN in result
            assert "Town Square" in result

    def test_npc_uses_yellow(self):
        """npc() should use yellow color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.npc("Merchant")
            assert colors.YELLOW in result
            assert "Merchant" in result

    def test_item_uses_green(self):
        """item() should use green color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.item("Sword")
            assert colors.GREEN in result
            assert "Sword" in result

    def test_gold_uses_yellow(self):
        """gold() should use yellow color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.gold("100 gold")
            assert colors.YELLOW in result
            assert "100 gold" in result

    def test_damage_uses_red(self):
        """damage() should use red color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.damage("10 damage")
            assert colors.RED in result
            assert "10 damage" in result

    def test_heal_uses_green(self):
        """heal() should use green color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.heal("15 HP")
            assert colors.GREEN in result
            assert "15 HP" in result

    def test_stat_header_uses_magenta(self):
        """stat_header() should use magenta color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.stat_header("Health")
            assert colors.MAGENTA in result
            assert "Health" in result


class TestColorConstants:
    """Tests for color constant values."""

    def test_color_constants_are_ansi_codes(self):
        """Color constants should be valid ANSI escape sequences."""
        assert colors.RESET == "\x1b[0m"
        assert colors.RED == "\x1b[31m"
        assert colors.GREEN == "\x1b[32m"
        assert colors.YELLOW == "\x1b[33m"
        assert colors.BLUE == "\x1b[34m"
        assert colors.MAGENTA == "\x1b[35m"
        assert colors.CYAN == "\x1b[36m"
        assert colors.BOLD == "\x1b[1m"


class TestBoldColorize:
    """Tests for bold color formatting."""

    def test_bold_colorize_applies_bold(self):
        """bold_colorize() should include BOLD code."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLI_RPG_NO_COLOR", None)
            colors.color_enabled.cache_clear()
            result = colors.bold_colorize("Player", colors.CYAN)
            assert colors.BOLD in result
            assert colors.CYAN in result
            assert "Player" in result

    def test_bold_colorize_plain_when_disabled(self):
        """bold_colorize() returns plain text when colors disabled."""
        with patch.dict(os.environ, {"CLI_RPG_NO_COLOR": "true"}):
            colors.color_enabled.cache_clear()
            result = colors.bold_colorize("Player", colors.CYAN)
            assert result == "Player"
            assert "\x1b" not in result
