"""Tests for the WorldContext model.

Test cases verify the WorldContext dataclass for caching world theme information.
"""

from datetime import datetime

import pytest

from cli_rpg.models.world_context import WorldContext


class TestWorldContextCreation:
    """Tests for WorldContext instantiation."""

    def test_world_context_creation_all_fields(self):
        """Test basic instantiation with all fields.

        Spec: WorldContext stores cached world theme information with all required fields.
        """
        now = datetime.now()
        ctx = WorldContext(
            theme="cyberpunk",
            theme_essence="neon-lit dystopia with corporate warfare",
            naming_style="Japanese-English hybrid slang",
            tone="noir, cynical",
            generated_at=now,
        )

        assert ctx.theme == "cyberpunk"
        assert ctx.theme_essence == "neon-lit dystopia with corporate warfare"
        assert ctx.naming_style == "Japanese-English hybrid slang"
        assert ctx.tone == "noir, cynical"
        assert ctx.generated_at == now

    def test_world_context_creation_minimal(self):
        """Test instantiation with only required field (theme).

        Spec: Only theme is required; other fields have defaults.
        """
        ctx = WorldContext(theme="fantasy")

        assert ctx.theme == "fantasy"
        assert ctx.theme_essence == ""
        assert ctx.naming_style == ""
        assert ctx.tone == ""
        assert ctx.generated_at is None


class TestWorldContextSerialization:
    """Tests for WorldContext to_dict and from_dict methods."""

    def test_world_context_to_dict(self):
        """Test serialization includes all fields.

        Spec: to_dict() serializes all fields for save/load.
        """
        now = datetime(2024, 1, 15, 12, 30, 45)
        ctx = WorldContext(
            theme="fantasy",
            theme_essence="dark medieval fantasy with corrupted magic",
            naming_style="Old English with Norse influence",
            tone="gritty, morally ambiguous",
            generated_at=now,
        )

        data = ctx.to_dict()

        assert data["theme"] == "fantasy"
        assert data["theme_essence"] == "dark medieval fantasy with corrupted magic"
        assert data["naming_style"] == "Old English with Norse influence"
        assert data["tone"] == "gritty, morally ambiguous"
        assert data["generated_at"] == "2024-01-15T12:30:45"

    def test_world_context_to_dict_none_datetime(self):
        """Test serialization when generated_at is None.

        Spec: to_dict() handles None datetime gracefully.
        """
        ctx = WorldContext(theme="fantasy")
        data = ctx.to_dict()

        assert data["generated_at"] is None

    def test_world_context_from_dict(self):
        """Test deserialization restores all fields.

        Spec: from_dict() deserializes saved data back to WorldContext.
        """
        data = {
            "theme": "steampunk",
            "theme_essence": "Victorian-era with brass and clockwork",
            "naming_style": "British Victorian with mechanical terms",
            "tone": "adventurous, optimistic",
            "generated_at": "2024-03-20T14:45:00",
        }

        ctx = WorldContext.from_dict(data)

        assert ctx.theme == "steampunk"
        assert ctx.theme_essence == "Victorian-era with brass and clockwork"
        assert ctx.naming_style == "British Victorian with mechanical terms"
        assert ctx.tone == "adventurous, optimistic"
        assert ctx.generated_at == datetime(2024, 3, 20, 14, 45, 0)

    def test_world_context_from_dict_missing_fields(self):
        """Test backward compatibility with partial data.

        Spec: from_dict() handles missing optional fields for backward compatibility.
        """
        data = {
            "theme": "horror",
        }

        ctx = WorldContext.from_dict(data)

        assert ctx.theme == "horror"
        assert ctx.theme_essence == ""
        assert ctx.naming_style == ""
        assert ctx.tone == ""
        assert ctx.generated_at is None

    def test_world_context_from_dict_none_datetime(self):
        """Test deserialization when generated_at is None.

        Spec: from_dict() handles None datetime correctly.
        """
        data = {
            "theme": "fantasy",
            "theme_essence": "test",
            "naming_style": "test",
            "tone": "test",
            "generated_at": None,
        }

        ctx = WorldContext.from_dict(data)

        assert ctx.generated_at is None


class TestWorldContextDefault:
    """Tests for WorldContext.default() factory method."""

    def test_world_context_default(self):
        """Test default factory creates valid context.

        Spec: default() creates a fallback context when AI is unavailable.
        """
        ctx = WorldContext.default()

        assert ctx.theme == "fantasy"
        assert ctx.theme_essence != ""  # Should have default essence
        assert ctx.naming_style != ""  # Should have default naming style
        assert ctx.tone != ""  # Should have default tone
        assert ctx.generated_at is None  # Not AI-generated

    def test_world_context_default_custom_theme(self):
        """Test default factory with custom theme.

        Spec: default() accepts optional theme parameter.
        """
        ctx = WorldContext.default(theme="cyberpunk")

        assert ctx.theme == "cyberpunk"
        assert ctx.theme_essence != ""
        assert ctx.generated_at is None


class TestWorldContextRoundTrip:
    """Tests for serialization/deserialization round-trip."""

    def test_world_context_round_trip(self):
        """Test that to_dict/from_dict preserves all data.

        Spec: Round-trip serialization should preserve all context data.
        """
        now = datetime(2024, 6, 15, 10, 0, 0)
        original = WorldContext(
            theme="post-apocalyptic",
            theme_essence="wasteland survival",
            naming_style="rough, abbreviated",
            tone="desperate, hopeful",
            generated_at=now,
        )

        restored = WorldContext.from_dict(original.to_dict())

        assert restored.theme == original.theme
        assert restored.theme_essence == original.theme_essence
        assert restored.naming_style == original.naming_style
        assert restored.tone == original.tone
        assert restored.generated_at == original.generated_at
