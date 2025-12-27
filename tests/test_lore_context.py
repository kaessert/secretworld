"""Tests for LoreContext model.

Tests the creation, serialization, and deserialization of LoreContext,
which caches lore information (historical events, legendary items, legendary places,
prophecies, ancient civilizations, creation myths, deities) (Layer 6 in the hierarchy).
"""

from datetime import datetime

import pytest

from cli_rpg.models.lore_context import LoreContext


class TestLoreContextCreation:
    """Tests for LoreContext creation."""

    # Tests spec: test_create_with_all_fields - all fields specified
    def test_create_with_all_fields(self):
        """Test creation with all fields specified."""
        now = datetime.now()
        ctx = LoreContext(
            region_name="The Shadowlands",
            coordinates=(5, 10),
            generated_at=now,
            # Historical Events
            historical_events=[
                {
                    "name": "The Great Sundering",
                    "date": "First Age",
                    "description": "The world was split asunder",
                    "impact": "Created the rift between realms",
                }
            ],
            # Legendary Items
            legendary_items=[
                {
                    "name": "Sword of Dawn",
                    "description": "A blade forged in starlight",
                    "powers": "Banishes darkness",
                    "location_hint": "Hidden in the Crystal Caves",
                }
            ],
            # Legendary Places
            legendary_places=[
                {
                    "name": "The Forgotten Temple",
                    "description": "An ancient temple to a dead god",
                    "danger_level": "extreme",
                    "rumored_location": "Beyond the mountains",
                }
            ],
            # Prophecies
            prophecies=[
                {
                    "name": "The Prophecy of Stars",
                    "text": "When stars align, the chosen shall rise",
                    "interpretation": "Refers to a future hero",
                    "fulfilled": False,
                }
            ],
            # Ancient Civilizations
            ancient_civilizations=[
                {
                    "name": "The Eldrathi",
                    "era": "First Age",
                    "achievements": "Built the great towers",
                    "downfall": "Consumed by their own magic",
                }
            ],
            # Creation Myths
            creation_myths=[
                "In the beginning, there was only void...",
                "The first gods arose from the cosmic sea...",
            ],
            # Deities
            deities=[
                {
                    "name": "Solara",
                    "domain": "life",
                    "alignment": "good",
                    "worship_status": "active",
                }
            ],
        )

        assert ctx.region_name == "The Shadowlands"
        assert ctx.coordinates == (5, 10)
        assert ctx.generated_at == now
        assert len(ctx.historical_events) == 1
        assert ctx.historical_events[0]["name"] == "The Great Sundering"
        assert len(ctx.legendary_items) == 1
        assert ctx.legendary_items[0]["name"] == "Sword of Dawn"
        assert len(ctx.legendary_places) == 1
        assert ctx.legendary_places[0]["danger_level"] == "extreme"
        assert len(ctx.prophecies) == 1
        assert ctx.prophecies[0]["fulfilled"] is False
        assert len(ctx.ancient_civilizations) == 1
        assert ctx.ancient_civilizations[0]["era"] == "First Age"
        assert len(ctx.creation_myths) == 2
        assert "void" in ctx.creation_myths[0]
        assert len(ctx.deities) == 1
        assert ctx.deities[0]["domain"] == "life"

    # Tests spec: test_create_with_minimal_fields - only required, defaults applied
    def test_create_with_minimal_fields(self):
        """Test creation with only required fields (defaults applied)."""
        ctx = LoreContext(
            region_name="Empty Region",
            coordinates=(0, 0),
        )

        assert ctx.region_name == "Empty Region"
        assert ctx.coordinates == (0, 0)
        assert ctx.generated_at is None
        # All optional fields should have defaults
        assert ctx.historical_events == []
        assert ctx.legendary_items == []
        assert ctx.legendary_places == []
        assert ctx.prophecies == []
        assert ctx.ancient_civilizations == []
        assert ctx.creation_myths == []
        assert ctx.deities == []

    # Tests spec: test_create_empty_collections - empty lists work correctly
    def test_create_empty_collections(self):
        """Test creation with explicitly empty collections works."""
        ctx = LoreContext(
            region_name="Barren Lands",
            coordinates=(-3, 7),
            historical_events=[],
            legendary_items=[],
            legendary_places=[],
            prophecies=[],
            ancient_civilizations=[],
            creation_myths=[],
            deities=[],
        )

        assert ctx.historical_events == []
        assert ctx.legendary_items == []
        assert ctx.legendary_places == []
        assert ctx.prophecies == []
        assert ctx.ancient_civilizations == []
        assert ctx.creation_myths == []
        assert ctx.deities == []


class TestLoreContextSerialization:
    """Tests for LoreContext to_dict serialization."""

    # Tests spec: test_to_dict_with_all_fields - datetime->ISO, tuple->list conversions
    def test_to_dict_with_all_fields(self):
        """Test serialization includes all fields with proper conversions."""
        now = datetime(2025, 1, 15, 12, 30, 45)
        ctx = LoreContext(
            region_name="The Shadowlands",
            coordinates=(5, 10),
            generated_at=now,
            historical_events=[
                {"name": "War of Ages", "date": "100 AE", "description": "A great war", "impact": "devastation"}
            ],
            legendary_items=[
                {"name": "Holy Grail", "description": "A chalice", "powers": "healing", "location_hint": "unknown"}
            ],
            legendary_places=[
                {"name": "Lost City", "description": "Ancient city", "danger_level": "high", "rumored_location": "north"}
            ],
            prophecies=[
                {"name": "Doom Prophecy", "text": "All shall fall", "interpretation": "warning", "fulfilled": False}
            ],
            ancient_civilizations=[
                {"name": "Atlanteans", "era": "Bronze Age", "achievements": "architecture", "downfall": "flood"}
            ],
            creation_myths=["The world was born from fire"],
            deities=[{"name": "Zeus", "domain": "war", "alignment": "neutral", "worship_status": "active"}],
        )

        data = ctx.to_dict()

        assert data["region_name"] == "The Shadowlands"
        assert data["coordinates"] == [5, 10]  # Tuple converted to list for JSON
        assert data["generated_at"] == "2025-01-15T12:30:45"  # datetime to ISO string
        assert data["historical_events"] == [
            {"name": "War of Ages", "date": "100 AE", "description": "A great war", "impact": "devastation"}
        ]
        assert data["legendary_items"] == [
            {"name": "Holy Grail", "description": "A chalice", "powers": "healing", "location_hint": "unknown"}
        ]
        assert data["legendary_places"] == [
            {"name": "Lost City", "description": "Ancient city", "danger_level": "high", "rumored_location": "north"}
        ]
        assert data["prophecies"] == [
            {"name": "Doom Prophecy", "text": "All shall fall", "interpretation": "warning", "fulfilled": False}
        ]
        assert data["ancient_civilizations"] == [
            {"name": "Atlanteans", "era": "Bronze Age", "achievements": "architecture", "downfall": "flood"}
        ]
        assert data["creation_myths"] == ["The world was born from fire"]
        assert data["deities"] == [
            {"name": "Zeus", "domain": "war", "alignment": "neutral", "worship_status": "active"}
        ]

    # Tests spec: test_to_dict_with_none_generated_at - handles None timestamp
    def test_to_dict_with_none_generated_at(self):
        """Test serialization with no generated_at timestamp."""
        ctx = LoreContext(
            region_name="Unknown Region",
            coordinates=(0, 0),
            generated_at=None,
        )

        data = ctx.to_dict()

        assert data["generated_at"] is None


class TestLoreContextDeserialization:
    """Tests for LoreContext from_dict deserialization."""

    # Tests spec: test_from_dict_with_all_fields - restores all data correctly
    def test_from_dict_with_all_fields(self):
        """Test deserialization with all fields present."""
        data = {
            "region_name": "The Shadowlands",
            "coordinates": [5, 10],
            "generated_at": "2025-01-15T12:30:45",
            "historical_events": [
                {"name": "War of Ages", "date": "100 AE", "description": "A great war", "impact": "devastation"}
            ],
            "legendary_items": [
                {"name": "Holy Grail", "description": "A chalice", "powers": "healing", "location_hint": "unknown"}
            ],
            "legendary_places": [
                {"name": "Lost City", "description": "Ancient city", "danger_level": "high", "rumored_location": "north"}
            ],
            "prophecies": [
                {"name": "Doom Prophecy", "text": "All shall fall", "interpretation": "warning", "fulfilled": False}
            ],
            "ancient_civilizations": [
                {"name": "Atlanteans", "era": "Bronze Age", "achievements": "architecture", "downfall": "flood"}
            ],
            "creation_myths": ["The world was born from fire", "Dragons hatched the sun"],
            "deities": [{"name": "Zeus", "domain": "war", "alignment": "neutral", "worship_status": "active"}],
        }

        ctx = LoreContext.from_dict(data)

        assert ctx.region_name == "The Shadowlands"
        assert ctx.coordinates == (5, 10)  # List converted back to tuple
        assert ctx.generated_at == datetime(2025, 1, 15, 12, 30, 45)  # ISO string to datetime
        assert ctx.historical_events == [
            {"name": "War of Ages", "date": "100 AE", "description": "A great war", "impact": "devastation"}
        ]
        assert ctx.legendary_items == [
            {"name": "Holy Grail", "description": "A chalice", "powers": "healing", "location_hint": "unknown"}
        ]
        assert ctx.legendary_places == [
            {"name": "Lost City", "description": "Ancient city", "danger_level": "high", "rumored_location": "north"}
        ]
        assert ctx.prophecies == [
            {"name": "Doom Prophecy", "text": "All shall fall", "interpretation": "warning", "fulfilled": False}
        ]
        assert ctx.ancient_civilizations == [
            {"name": "Atlanteans", "era": "Bronze Age", "achievements": "architecture", "downfall": "flood"}
        ]
        assert ctx.creation_myths == ["The world was born from fire", "Dragons hatched the sun"]
        assert ctx.deities == [{"name": "Zeus", "domain": "war", "alignment": "neutral", "worship_status": "active"}]

    # Tests spec: test_from_dict_backward_compatible - old saves load with defaults
    def test_from_dict_backward_compatible(self):
        """Test old saves without optional fields load successfully with defaults."""
        # Simulates an old save file with only required fields
        old_save_data = {
            "region_name": "Old Region",
            "coordinates": [3, 4],
            "generated_at": None,
        }

        ctx = LoreContext.from_dict(old_save_data)

        # Required fields work
        assert ctx.region_name == "Old Region"
        assert ctx.coordinates == (3, 4)
        assert ctx.generated_at is None
        # All optional fields get defaults
        assert ctx.historical_events == []
        assert ctx.legendary_items == []
        assert ctx.legendary_places == []
        assert ctx.prophecies == []
        assert ctx.ancient_civilizations == []
        assert ctx.creation_myths == []
        assert ctx.deities == []

    # Tests spec: test_from_dict_with_null_generated_at - handles null timestamp
    def test_from_dict_with_null_generated_at(self):
        """Test deserialization when generated_at is null."""
        data = {
            "region_name": "Null Timestamp Region",
            "coordinates": [0, 0],
            "generated_at": None,
        }

        ctx = LoreContext.from_dict(data)

        assert ctx.generated_at is None


class TestLoreContextDefaultFactory:
    """Tests for LoreContext.default() factory method."""

    # Tests spec: test_default_creates_valid_context - creates valid instance
    def test_default_creates_valid_context(self):
        """Test default factory creates a valid LoreContext."""
        ctx = LoreContext.default("Unnamed Region", (5, 10))

        assert ctx.region_name == "Unnamed Region"
        assert ctx.coordinates == (5, 10)
        assert ctx.generated_at is None
        # Should have sensible defaults (empty lists)
        assert isinstance(ctx.historical_events, list)
        assert isinstance(ctx.legendary_items, list)
        assert isinstance(ctx.legendary_places, list)
        assert isinstance(ctx.prophecies, list)
        assert isinstance(ctx.ancient_civilizations, list)
        assert isinstance(ctx.creation_myths, list)
        assert isinstance(ctx.deities, list)

    # Tests spec: test_default_with_different_coordinates - works with various coords
    def test_default_with_different_coordinates(self):
        """Test default factory works with various coordinates."""
        ctx1 = LoreContext.default("Region A", (0, 0))
        ctx2 = LoreContext.default("Region B", (-10, 20))

        assert ctx1.coordinates == (0, 0)
        assert ctx2.coordinates == (-10, 20)


class TestLoreContextRoundTrip:
    """Tests for serialization/deserialization round-trip."""

    # Tests spec: test_round_trip_preserves_all_data - to_dict->from_dict preserves everything
    def test_round_trip_preserves_all_data(self):
        """Test that to_dict/from_dict preserves all data."""
        now = datetime(2025, 1, 15, 12, 30, 45)
        original = LoreContext(
            region_name="Complete Region",
            coordinates=(7, 8),
            generated_at=now,
            historical_events=[
                {"name": "The Cataclysm", "date": "Year Zero", "description": "End of an era", "impact": "reshaping"},
                {"name": "The Rebuilding", "date": "Year 100", "description": "New beginning", "impact": "hope"},
            ],
            legendary_items=[
                {"name": "Dragon Crown", "description": "Crown of fire", "powers": "fire control", "location_hint": "volcano"}
            ],
            legendary_places=[
                {"name": "Sky Citadel", "description": "Floating fortress", "danger_level": "extreme", "rumored_location": "clouds"}
            ],
            prophecies=[
                {"name": "Return of the King", "text": "He shall return", "interpretation": "hope", "fulfilled": True}
            ],
            ancient_civilizations=[
                {"name": "Sky People", "era": "Age of Flight", "achievements": "aviation", "downfall": "hubris"}
            ],
            creation_myths=["The sky was once the sea", "Stars are fallen gods"],
            deities=[
                {"name": "Aerion", "domain": "knowledge", "alignment": "good", "worship_status": "active"},
                {"name": "Noctis", "domain": "death", "alignment": "evil", "worship_status": "forgotten"},
            ],
        )

        data = original.to_dict()
        restored = LoreContext.from_dict(data)

        assert restored.region_name == original.region_name
        assert restored.coordinates == original.coordinates
        assert restored.generated_at == original.generated_at
        assert restored.historical_events == original.historical_events
        assert restored.legendary_items == original.legendary_items
        assert restored.legendary_places == original.legendary_places
        assert restored.prophecies == original.prophecies
        assert restored.ancient_civilizations == original.ancient_civilizations
        assert restored.creation_myths == original.creation_myths
        assert restored.deities == original.deities

    # Tests spec: test_round_trip_without_generated_at - round-trip with None timestamp
    def test_round_trip_without_generated_at(self):
        """Test round-trip when generated_at is None."""
        original = LoreContext(
            region_name="No Timestamp",
            coordinates=(0, 0),
            generated_at=None,
        )

        data = original.to_dict()
        restored = LoreContext.from_dict(data)

        assert restored.region_name == original.region_name
        assert restored.generated_at is None
