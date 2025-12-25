"""Tests for ASCII art feature in locations.

Tests cover:
1. Location model ascii_art field (storage and serialization)
2. Fallback ASCII art templates (by category and name)
3. Location __str__() displaying ASCII art
4. AI-generated ASCII art (mocked)
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.models.location import Location


class TestLocationModelAsciiArt:
    """Test Location model has ascii_art field."""

    def test_location_model_has_ascii_art_field(self):
        """Verify Location can store ascii_art."""
        ascii_art = r"""
    /\  /\
   /  \/  \
  |   ||   |
  |___||___|
"""
        location = Location(
            name="Test Town",
            description="A small test town",
            ascii_art=ascii_art,
        )

        assert location.ascii_art == ascii_art

    def test_location_default_ascii_art_is_empty(self):
        """Verify Location defaults ascii_art to empty string."""
        location = Location(
            name="Test Location",
            description="A test location",
        )

        assert location.ascii_art == ""

    def test_location_to_dict_includes_ascii_art_when_present(self):
        """Verify to_dict includes ascii_art when non-empty."""
        ascii_art = "  /\\\n / \\\n/___\\"
        location = Location(
            name="Test Location",
            description="A test location",
            ascii_art=ascii_art,
        )

        data = location.to_dict()
        assert "ascii_art" in data
        assert data["ascii_art"] == ascii_art

    def test_location_to_dict_excludes_ascii_art_when_empty(self):
        """Verify to_dict excludes ascii_art when empty (backward compatibility)."""
        location = Location(
            name="Test Location",
            description="A test location",
            ascii_art="",
        )

        data = location.to_dict()
        assert "ascii_art" not in data

    def test_location_from_dict_loads_ascii_art(self):
        """Verify from_dict loads ascii_art correctly."""
        ascii_art = "  ^^\n /||\\\n/____\\"
        data = {
            "name": "Test Location",
            "description": "A test location",
            "connections": {},
            "ascii_art": ascii_art,
        }

        location = Location.from_dict(data)
        assert location.ascii_art == ascii_art

    def test_location_from_dict_default_ascii_art(self):
        """Verify from_dict defaults ascii_art to empty string."""
        data = {
            "name": "Test Location",
            "description": "A test location",
            "connections": {},
        }

        location = Location.from_dict(data)
        assert location.ascii_art == ""


class TestLocationDisplayAsciiArt:
    """Test location __str__() displays ASCII art."""

    def test_str_includes_ascii_art_when_present(self):
        """Location __str__() includes ASCII art after name, before description."""
        ascii_art = r"""
    ___
   /   \
  |     |
  |_____|
"""
        location = Location(
            name="Castle Keep",
            description="A mighty fortress",
            ascii_art=ascii_art,
        )

        output = str(location)

        # Name should come first
        assert "Castle Keep" in output
        # ASCII art should be present
        assert "___" in output
        assert "|_____|" in output
        # Description should be present
        assert "A mighty fortress" in output

    def test_str_no_art_when_empty(self):
        """Location __str__() shows normal output when no ASCII art."""
        location = Location(
            name="Plain Town",
            description="A simple town",
        )

        output = str(location)

        assert "Plain Town" in output
        assert "A simple town" in output


class TestFallbackLocationAsciiArt:
    """Test fallback ASCII art templates for locations."""

    def test_get_fallback_art_by_category_town(self):
        """Town category returns town-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="town", location_name="Some Town")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3  # At least 3 lines
        assert max(len(line) for line in art.splitlines()) <= 50  # Max 50 chars wide

    def test_get_fallback_art_by_category_forest(self):
        """Forest category returns forest-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="forest", location_name="Dark Woods")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_dungeon(self):
        """Dungeon category returns dungeon-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="dungeon", location_name="Deep Dungeon")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_cave(self):
        """Cave category returns cave-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="cave", location_name="Dark Cave")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_ruins(self):
        """Ruins category returns ruins-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="ruins", location_name="Ancient Ruins")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_mountain(self):
        """Mountain category returns mountain-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="mountain", location_name="High Peak")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_village(self):
        """Village category returns village-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="village", location_name="Small Village")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_wilderness(self):
        """Wilderness category returns wilderness-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="wilderness", location_name="Wild Plains")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_by_category_settlement(self):
        """Settlement category returns settlement-themed art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category="settlement", location_name="Frontier Post")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_name_fallback_forest(self):
        """Name-based detection for forest locations."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category=None, location_name="Dark Forest")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_name_fallback_cave(self):
        """Name-based detection for cave locations."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art = get_fallback_location_ascii_art(category=None, location_name="Crystal Cavern")

        assert art  # Non-empty
        assert len(art.splitlines()) >= 3

    def test_get_fallback_art_default(self):
        """Unknown category/name gets default wilderness art."""
        from cli_rpg.location_art import get_fallback_location_ascii_art

        art1 = get_fallback_location_ascii_art(category=None, location_name="Unknown Place")
        art2 = get_fallback_location_ascii_art(category=None, location_name="Mystery Spot")

        assert art1  # Non-empty
        assert art2  # Non-empty
        assert art1 == art2  # Same default art


class TestAILocationAsciiArtGeneration:
    """Test AIService.generate_location_ascii_art method."""

    def test_ai_location_ascii_art_generation(self):
        """AIService.generate_location_ascii_art returns valid art (mocked)."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        with patch.object(AIService, "_call_llm") as mock_call:
            mock_call.return_value = r"""
      ___
     /   \
    /     \
   |  ___  |
   | |   | |
   |_|   |_|
"""
            service = AIService(config)
            art = service.generate_location_ascii_art(
                location_name="Castle Keep",
                location_description="A mighty fortress atop the hill",
                location_category="town",
                theme="fantasy",
            )

            # Should return non-empty art
            assert art
            # Should have multiple lines
            assert len(art.splitlines()) >= 3
            # Should be max 50 chars wide
            for line in art.splitlines():
                assert len(line) <= 50, f"Line too long: {line}"

    def test_ai_location_ascii_art_prompt_formatting(self):
        """Verify location ASCII art prompt is properly formatted."""
        from cli_rpg.ai_service import AIService
        from cli_rpg.ai_config import AIConfig

        config = AIConfig(
            api_key="test-key",
            provider="openai",
            enable_caching=False,
        )

        with patch.object(AIService, "_call_llm") as mock_call:
            mock_call.return_value = "  /\\\n /  \\\n/____\\"
            service = AIService(config)
            service.generate_location_ascii_art(
                location_name="Dark Cave",
                location_description="A foreboding entrance",
                location_category="cave",
                theme="dark fantasy",
            )

            # Check that prompt was called with location details
            call_args = mock_call.call_args[0][0]
            assert "Dark Cave" in call_args
            assert "cave" in call_args.lower()
            assert "dark fantasy" in call_args.lower()
