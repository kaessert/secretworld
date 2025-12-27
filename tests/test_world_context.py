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


class TestWorldContextLoreAndFactions:
    """Tests for new lore and faction fields added to WorldContext.

    Spec: Issue 1 - Expand WorldContext (Layer 1) with lore and faction fields.
    """

    def test_new_field_creation(self):
        """Test instantiation with all new fields.

        Spec: WorldContext stores lore and faction fields for richer world generation.
        """
        ctx = WorldContext(
            theme="fantasy",
            creation_myth="Forged by ancient gods from primordial chaos",
            major_conflicts=["The Great Mage War", "The Dragon Invasion"],
            legendary_artifacts=["The Sunblade", "The Crown of Stars"],
            prophecies=["The chosen one will rise when darkness falls"],
            major_factions=["The Crown", "The Mage's Circle", "The Merchant League"],
            faction_tensions={"The Crown": ["The Mage's Circle"]},
            economic_era="stable",
        )

        assert ctx.creation_myth == "Forged by ancient gods from primordial chaos"
        assert ctx.major_conflicts == ["The Great Mage War", "The Dragon Invasion"]
        assert ctx.legendary_artifacts == ["The Sunblade", "The Crown of Stars"]
        assert ctx.prophecies == ["The chosen one will rise when darkness falls"]
        assert ctx.major_factions == ["The Crown", "The Mage's Circle", "The Merchant League"]
        assert ctx.faction_tensions == {"The Crown": ["The Mage's Circle"]}
        assert ctx.economic_era == "stable"

    def test_new_field_defaults(self):
        """Test minimal instantiation still works with new field defaults.

        Spec: All new fields default to empty values for backward compatibility.
        """
        ctx = WorldContext(theme="fantasy")

        assert ctx.creation_myth == ""
        assert ctx.major_conflicts == []
        assert ctx.legendary_artifacts == []
        assert ctx.prophecies == []
        assert ctx.major_factions == []
        assert ctx.faction_tensions == {}
        assert ctx.economic_era == ""

    def test_to_dict_includes_new_fields(self):
        """Test serialization includes all 7 new fields.

        Spec: to_dict() serializes new lore and faction fields.
        """
        ctx = WorldContext(
            theme="cyberpunk",
            creation_myth="Built on the ashes of the old world",
            major_conflicts=["Corporate Wars", "AI Rebellion"],
            legendary_artifacts=["The God Chip"],
            prophecies=["The Net will become conscious"],
            major_factions=["MegaCorp", "The Resistance"],
            faction_tensions={"MegaCorp": ["The Resistance"]},
            economic_era="boom",
        )

        data = ctx.to_dict()

        assert data["creation_myth"] == "Built on the ashes of the old world"
        assert data["major_conflicts"] == ["Corporate Wars", "AI Rebellion"]
        assert data["legendary_artifacts"] == ["The God Chip"]
        assert data["prophecies"] == ["The Net will become conscious"]
        assert data["major_factions"] == ["MegaCorp", "The Resistance"]
        assert data["faction_tensions"] == {"MegaCorp": ["The Resistance"]}
        assert data["economic_era"] == "boom"

    def test_from_dict_restores_new_fields(self):
        """Test deserialization restores all 7 new fields.

        Spec: from_dict() deserializes new lore and faction fields.
        """
        data = {
            "theme": "horror",
            "creation_myth": "Born from the nightmares of a dead god",
            "major_conflicts": ["The Awakening", "The Purge"],
            "legendary_artifacts": ["The Necronomicon"],
            "prophecies": ["The stars will align"],
            "major_factions": ["The Cult", "The Order"],
            "faction_tensions": {"The Cult": ["The Order"]},
            "economic_era": "recession",
        }

        ctx = WorldContext.from_dict(data)

        assert ctx.creation_myth == "Born from the nightmares of a dead god"
        assert ctx.major_conflicts == ["The Awakening", "The Purge"]
        assert ctx.legendary_artifacts == ["The Necronomicon"]
        assert ctx.prophecies == ["The stars will align"]
        assert ctx.major_factions == ["The Cult", "The Order"]
        assert ctx.faction_tensions == {"The Cult": ["The Order"]}
        assert ctx.economic_era == "recession"

    def test_from_dict_backward_compatibility(self):
        """Test old saves without new fields still load.

        Spec: from_dict() handles missing new fields for backward compatibility.
        """
        # Simulate old save file that doesn't have new fields
        data = {
            "theme": "fantasy",
            "theme_essence": "classic high fantasy",
            "naming_style": "Old English",
            "tone": "heroic",
            "generated_at": None,
        }

        ctx = WorldContext.from_dict(data)

        # Old fields should load
        assert ctx.theme == "fantasy"
        assert ctx.theme_essence == "classic high fantasy"

        # New fields should default to empty
        assert ctx.creation_myth == ""
        assert ctx.major_conflicts == []
        assert ctx.legendary_artifacts == []
        assert ctx.prophecies == []
        assert ctx.major_factions == []
        assert ctx.faction_tensions == {}
        assert ctx.economic_era == ""

    def test_default_includes_new_field_defaults(self):
        """Test default() factory method provides sensible defaults for new fields.

        Spec: default() includes default values for new lore and faction fields.
        """
        ctx = WorldContext.default(theme="fantasy")

        # New fields should have sensible defaults for the theme
        assert ctx.creation_myth != ""  # Should have default creation myth
        assert isinstance(ctx.major_factions, list)  # Should be a list
        assert len(ctx.major_factions) >= 1  # Should have at least one faction
        assert ctx.economic_era != ""  # Should have default economic era

    def test_round_trip_with_new_fields(self):
        """Test all new fields survive serialization cycle.

        Spec: Round-trip serialization should preserve all new lore and faction fields.
        """
        original = WorldContext(
            theme="steampunk",
            theme_essence="Victorian brass and clockwork",
            creation_myth="The Great Gears were set in motion",
            major_conflicts=["The Gear Wars", "The Steam Revolution"],
            legendary_artifacts=["The First Engine", "The Clockwork Heart"],
            prophecies=["The gears will stop when the chosen one arrives"],
            major_factions=["The Engineers", "The Aristocracy", "The Workers"],
            faction_tensions={"The Workers": ["The Aristocracy"]},
            economic_era="boom",
        )

        restored = WorldContext.from_dict(original.to_dict())

        assert restored.creation_myth == original.creation_myth
        assert restored.major_conflicts == original.major_conflicts
        assert restored.legendary_artifacts == original.legendary_artifacts
        assert restored.prophecies == original.prophecies
        assert restored.major_factions == original.major_factions
        assert restored.faction_tensions == original.faction_tensions
        assert restored.economic_era == original.economic_era
