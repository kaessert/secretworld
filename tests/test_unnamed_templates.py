"""Tests for the unnamed location template system.

Tests that:
- Each terrain type has templates defined
- get_unnamed_location_template returns valid (name, description) tuples
- Template names are 2-50 chars
- Template descriptions are 1-500 chars
"""

import pytest

from cli_rpg.world_tiles import (
    UNNAMED_LOCATION_TEMPLATES,
    get_unnamed_location_template,
    TerrainType,
)
from cli_rpg.models.location import Location


class TestUnnamedLocationTemplates:
    """Tests for the UNNAMED_LOCATION_TEMPLATES dictionary."""

    def test_all_terrains_have_templates(self):
        """Every passable terrain type should have templates defined."""
        # All terrains except water should have templates
        expected_terrains = {"forest", "mountain", "plains", "desert", "swamp", "hills", "beach", "foothills"}

        for terrain in expected_terrains:
            assert terrain in UNNAMED_LOCATION_TEMPLATES, f"Missing template for terrain: {terrain}"
            assert len(UNNAMED_LOCATION_TEMPLATES[terrain]) > 0, f"Empty template list for: {terrain}"

    def test_templates_are_tuples(self):
        """Each template should be a (name, description) tuple."""
        for terrain, templates in UNNAMED_LOCATION_TEMPLATES.items():
            for template in templates:
                assert isinstance(template, tuple), f"Template for {terrain} is not a tuple"
                assert len(template) == 2, f"Template for {terrain} should have 2 elements"
                name, description = template
                assert isinstance(name, str), f"Template name for {terrain} is not a string"
                assert isinstance(description, str), f"Template description for {terrain} is not a string"


class TestGetUnnamedLocationTemplate:
    """Tests for the get_unnamed_location_template function."""

    def test_get_unnamed_template_forest(self):
        """Returns a valid forest-themed template."""
        name, description = get_unnamed_location_template("forest")

        # Verify name length is valid for Location model
        assert len(name) >= Location.MIN_NAME_LENGTH
        assert len(name) <= Location.MAX_NAME_LENGTH

        # Verify description length is valid for Location model
        assert len(description) >= Location.MIN_DESCRIPTION_LENGTH
        assert len(description) <= Location.MAX_DESCRIPTION_LENGTH

        # Verify both are non-empty strings
        assert name.strip() != ""
        assert description.strip() != ""

    def test_get_unnamed_template_plains(self):
        """Returns a valid plains-themed template."""
        name, description = get_unnamed_location_template("plains")

        assert len(name) >= Location.MIN_NAME_LENGTH
        assert len(name) <= Location.MAX_NAME_LENGTH
        assert len(description) >= Location.MIN_DESCRIPTION_LENGTH
        assert len(description) <= Location.MAX_DESCRIPTION_LENGTH

    def test_get_unnamed_template_mountain(self):
        """Returns a valid mountain-themed template."""
        name, description = get_unnamed_location_template("mountain")

        assert len(name) >= Location.MIN_NAME_LENGTH
        assert len(name) <= Location.MAX_NAME_LENGTH
        assert len(description) >= Location.MIN_DESCRIPTION_LENGTH
        assert len(description) <= Location.MAX_DESCRIPTION_LENGTH

    def test_get_unnamed_template_unknown_terrain(self):
        """Unknown terrain falls back to plains templates."""
        name, description = get_unnamed_location_template("unknown_terrain_xyz")

        # Should still return valid values (defaulting to plains)
        assert len(name) >= Location.MIN_NAME_LENGTH
        assert len(name) <= Location.MAX_NAME_LENGTH
        assert len(description) >= Location.MIN_DESCRIPTION_LENGTH
        assert len(description) <= Location.MAX_DESCRIPTION_LENGTH

    def test_unnamed_template_has_valid_name(self):
        """All templates have names between 2-50 characters."""
        for terrain, templates in UNNAMED_LOCATION_TEMPLATES.items():
            for name, _ in templates:
                assert len(name) >= Location.MIN_NAME_LENGTH, f"Name too short in {terrain}: '{name}'"
                assert len(name) <= Location.MAX_NAME_LENGTH, f"Name too long in {terrain}: '{name}'"

    def test_unnamed_template_has_valid_description(self):
        """All templates have descriptions between 1-500 characters."""
        for terrain, templates in UNNAMED_LOCATION_TEMPLATES.items():
            for _, description in templates:
                assert len(description) >= Location.MIN_DESCRIPTION_LENGTH, f"Description too short in {terrain}"
                assert len(description) <= Location.MAX_DESCRIPTION_LENGTH, f"Description too long in {terrain}"

    def test_templates_can_create_valid_locations(self):
        """All templates can be used to create valid Location objects."""
        for terrain, templates in UNNAMED_LOCATION_TEMPLATES.items():
            for name, description in templates:
                # This should not raise any validation errors
                loc = Location(name=name, description=description)
                assert loc.name == name
                assert loc.description == description
