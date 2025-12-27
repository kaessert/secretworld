"""Tests for RegionContext model.

Tests the creation, serialization, and deserialization of RegionContext,
which caches region-level theme information for consistent AI generation.
"""

from datetime import datetime

import pytest

from cli_rpg.models.region_context import RegionContext


class TestRegionContextCreation:
    """Tests for RegionContext creation."""

    def test_create_with_all_fields(self):
        """Test creation with all fields specified."""
        now = datetime.now()
        ctx = RegionContext(
            name="Industrial District",
            theme="factory smoke, rust, labor",
            danger_level="moderate",
            landmarks=["Rust Tower", "The Vats"],
            coordinates=(5, 10),
            generated_at=now,
        )

        assert ctx.name == "Industrial District"
        assert ctx.theme == "factory smoke, rust, labor"
        assert ctx.danger_level == "moderate"
        assert ctx.landmarks == ["Rust Tower", "The Vats"]
        assert ctx.coordinates == (5, 10)
        assert ctx.generated_at == now

    def test_create_with_minimal_fields(self):
        """Test creation with only required fields (defaults applied)."""
        ctx = RegionContext(
            name="Dark Forest",
            theme="twisted trees, shadow",
            danger_level="dangerous",
            landmarks=["The Old Oak"],
            coordinates=(0, 0),
        )

        assert ctx.name == "Dark Forest"
        assert ctx.theme == "twisted trees, shadow"
        assert ctx.danger_level == "dangerous"
        assert ctx.landmarks == ["The Old Oak"]
        assert ctx.coordinates == (0, 0)
        assert ctx.generated_at is None

    def test_create_with_empty_landmarks(self):
        """Test creation with no landmarks."""
        ctx = RegionContext(
            name="Barren Wastes",
            theme="sand, desolation",
            danger_level="deadly",
            landmarks=[],
            coordinates=(-3, 7),
        )

        assert ctx.landmarks == []


class TestRegionContextSerialization:
    """Tests for RegionContext to_dict serialization."""

    def test_to_dict_with_all_fields(self):
        """Test serialization includes all fields."""
        now = datetime(2025, 1, 15, 12, 30, 45)
        ctx = RegionContext(
            name="Industrial District",
            theme="factory smoke, rust, labor",
            danger_level="moderate",
            landmarks=["Rust Tower", "The Vats"],
            coordinates=(5, 10),
            generated_at=now,
        )

        data = ctx.to_dict()

        assert data["name"] == "Industrial District"
        assert data["theme"] == "factory smoke, rust, labor"
        assert data["danger_level"] == "moderate"
        assert data["landmarks"] == ["Rust Tower", "The Vats"]
        assert data["coordinates"] == [5, 10]  # Tuple converted to list for JSON
        assert data["generated_at"] == "2025-01-15T12:30:45"

    def test_to_dict_with_none_generated_at(self):
        """Test serialization with no generated_at timestamp."""
        ctx = RegionContext(
            name="Dark Forest",
            theme="twisted trees",
            danger_level="dangerous",
            landmarks=[],
            coordinates=(0, 0),
            generated_at=None,
        )

        data = ctx.to_dict()

        assert data["generated_at"] is None


class TestRegionContextDeserialization:
    """Tests for RegionContext from_dict deserialization."""

    def test_from_dict_with_all_fields(self):
        """Test deserialization with all fields present."""
        data = {
            "name": "Industrial District",
            "theme": "factory smoke, rust, labor",
            "danger_level": "moderate",
            "landmarks": ["Rust Tower", "The Vats"],
            "coordinates": [5, 10],
            "generated_at": "2025-01-15T12:30:45",
        }

        ctx = RegionContext.from_dict(data)

        assert ctx.name == "Industrial District"
        assert ctx.theme == "factory smoke, rust, labor"
        assert ctx.danger_level == "moderate"
        assert ctx.landmarks == ["Rust Tower", "The Vats"]
        assert ctx.coordinates == (5, 10)
        assert ctx.generated_at == datetime(2025, 1, 15, 12, 30, 45)

    def test_from_dict_with_missing_generated_at(self):
        """Test deserialization when generated_at is missing."""
        data = {
            "name": "Dark Forest",
            "theme": "twisted trees",
            "danger_level": "dangerous",
            "landmarks": [],
            "coordinates": [0, 0],
        }

        ctx = RegionContext.from_dict(data)

        assert ctx.generated_at is None

    def test_from_dict_with_null_generated_at(self):
        """Test deserialization when generated_at is null."""
        data = {
            "name": "Dark Forest",
            "theme": "twisted trees",
            "danger_level": "dangerous",
            "landmarks": [],
            "coordinates": [0, 0],
            "generated_at": None,
        }

        ctx = RegionContext.from_dict(data)

        assert ctx.generated_at is None


class TestRegionContextDefaultFactory:
    """Tests for RegionContext.default() factory method."""

    def test_default_creates_valid_context(self):
        """Test default factory creates a valid RegionContext."""
        ctx = RegionContext.default("Unnamed Region", (5, 10))

        assert ctx.name == "Unnamed Region"
        assert ctx.coordinates == (5, 10)
        assert ctx.danger_level in ["safe", "moderate", "dangerous", "deadly"]
        assert isinstance(ctx.theme, str)
        assert len(ctx.theme) > 0
        assert isinstance(ctx.landmarks, list)
        assert ctx.generated_at is None

    def test_default_with_different_coordinates(self):
        """Test default factory works with various coordinates."""
        ctx1 = RegionContext.default("Region A", (0, 0))
        ctx2 = RegionContext.default("Region B", (-10, 20))

        assert ctx1.coordinates == (0, 0)
        assert ctx2.coordinates == (-10, 20)


class TestRegionContextRoundTrip:
    """Tests for serialization/deserialization round-trip."""

    def test_round_trip_preserves_all_data(self):
        """Test that to_dict/from_dict preserves all data."""
        now = datetime(2025, 1, 15, 12, 30, 45)
        original = RegionContext(
            name="Industrial District",
            theme="factory smoke, rust, labor",
            danger_level="moderate",
            landmarks=["Rust Tower", "The Vats", "Old Foundry"],
            coordinates=(5, 10),
            generated_at=now,
        )

        data = original.to_dict()
        restored = RegionContext.from_dict(data)

        assert restored.name == original.name
        assert restored.theme == original.theme
        assert restored.danger_level == original.danger_level
        assert restored.landmarks == original.landmarks
        assert restored.coordinates == original.coordinates
        assert restored.generated_at == original.generated_at

    def test_round_trip_without_generated_at(self):
        """Test round-trip when generated_at is None."""
        original = RegionContext(
            name="Dark Forest",
            theme="twisted trees",
            danger_level="dangerous",
            landmarks=[],
            coordinates=(0, 0),
            generated_at=None,
        )

        data = original.to_dict()
        restored = RegionContext.from_dict(data)

        assert restored.name == original.name
        assert restored.generated_at is None


class TestRegionContextEconomyFields:
    """Tests for RegionContext economy fields (primary_resources, scarce_resources, trade_goods, price_modifier)."""

    def test_create_with_economy_fields(self):
        """Test creation with all economy fields specified."""
        ctx = RegionContext(
            name="Mining District",
            theme="ore veins, pickaxe labor",
            danger_level="moderate",
            landmarks=["The Great Mine"],
            coordinates=(3, 4),
            primary_resources=["iron", "timber"],
            scarce_resources=["gold", "spices"],
            trade_goods=["iron ingots", "lumber"],
            price_modifier=1.2,
        )

        assert ctx.primary_resources == ["iron", "timber"]
        assert ctx.scarce_resources == ["gold", "spices"]
        assert ctx.trade_goods == ["iron ingots", "lumber"]
        assert ctx.price_modifier == 1.2

    def test_economy_fields_default_to_empty(self):
        """Test economy fields default to empty lists and 1.0 modifier."""
        ctx = RegionContext(
            name="Basic Region",
            theme="generic",
            danger_level="safe",
            landmarks=[],
            coordinates=(0, 0),
        )

        assert ctx.primary_resources == []
        assert ctx.scarce_resources == []
        assert ctx.trade_goods == []
        assert ctx.price_modifier == 1.0


class TestRegionContextHistoryFields:
    """Tests for RegionContext history fields (founding_story, historical_events, ruined_civilizations, legendary_locations)."""

    def test_create_with_history_fields(self):
        """Test creation with all history fields specified."""
        ctx = RegionContext(
            name="Ancient Lands",
            theme="forgotten memories",
            danger_level="dangerous",
            landmarks=["Old Temple"],
            coordinates=(5, 5),
            founding_story="Founded by the First King in ages past",
            historical_events=["The Great War", "The Plague"],
            ruined_civilizations=["The Eldari", "The Dwarven Empire"],
            legendary_locations=["The Lost City", "The Hidden Valley"],
        )

        assert ctx.founding_story == "Founded by the First King in ages past"
        assert ctx.historical_events == ["The Great War", "The Plague"]
        assert ctx.ruined_civilizations == ["The Eldari", "The Dwarven Empire"]
        assert ctx.legendary_locations == ["The Lost City", "The Hidden Valley"]

    def test_history_fields_default_to_empty(self):
        """Test history fields default to empty strings and lists."""
        ctx = RegionContext(
            name="New Region",
            theme="fresh start",
            danger_level="safe",
            landmarks=[],
            coordinates=(0, 0),
        )

        assert ctx.founding_story == ""
        assert ctx.historical_events == []
        assert ctx.ruined_civilizations == []
        assert ctx.legendary_locations == []


class TestRegionContextAtmosphereFields:
    """Tests for RegionContext atmosphere fields (common_creatures, weather_tendency, ambient_sounds)."""

    def test_create_with_atmosphere_fields(self):
        """Test creation with all atmosphere fields specified."""
        ctx = RegionContext(
            name="Misty Swamp",
            theme="murky, damp",
            danger_level="dangerous",
            landmarks=["The Bog"],
            coordinates=(2, -3),
            common_creatures=["giant frogs", "will-o-wisps", "swamp trolls"],
            weather_tendency="foggy",
            ambient_sounds=["croaking", "bubbling", "distant howls"],
        )

        assert ctx.common_creatures == ["giant frogs", "will-o-wisps", "swamp trolls"]
        assert ctx.weather_tendency == "foggy"
        assert ctx.ambient_sounds == ["croaking", "bubbling", "distant howls"]

    def test_atmosphere_fields_default_to_empty(self):
        """Test atmosphere fields default to empty values."""
        ctx = RegionContext(
            name="Plain Region",
            theme="basic",
            danger_level="safe",
            landmarks=[],
            coordinates=(0, 0),
        )

        assert ctx.common_creatures == []
        assert ctx.weather_tendency == ""
        assert ctx.ambient_sounds == []


class TestRegionContextNewFieldsSerialization:
    """Tests for serialization/deserialization of new economy, history, and atmosphere fields."""

    def test_to_dict_includes_new_fields(self):
        """Test serialization includes all 11 new fields."""
        ctx = RegionContext(
            name="Full Region",
            theme="complete theme",
            danger_level="moderate",
            landmarks=["Landmark"],
            coordinates=(1, 1),
            # Economy
            primary_resources=["iron", "timber"],
            scarce_resources=["gold"],
            trade_goods=["weapons"],
            price_modifier=0.9,
            # History
            founding_story="Long ago...",
            historical_events=["War"],
            ruined_civilizations=["Ancients"],
            legendary_locations=["Lost Temple"],
            # Atmosphere
            common_creatures=["wolves"],
            weather_tendency="rainy",
            ambient_sounds=["wind"],
        )

        data = ctx.to_dict()

        # Economy fields
        assert data["primary_resources"] == ["iron", "timber"]
        assert data["scarce_resources"] == ["gold"]
        assert data["trade_goods"] == ["weapons"]
        assert data["price_modifier"] == 0.9
        # History fields
        assert data["founding_story"] == "Long ago..."
        assert data["historical_events"] == ["War"]
        assert data["ruined_civilizations"] == ["Ancients"]
        assert data["legendary_locations"] == ["Lost Temple"]
        # Atmosphere fields
        assert data["common_creatures"] == ["wolves"]
        assert data["weather_tendency"] == "rainy"
        assert data["ambient_sounds"] == ["wind"]

    def test_from_dict_with_new_fields(self):
        """Test deserialization restores all 11 new fields."""
        data = {
            "name": "Full Region",
            "theme": "complete theme",
            "danger_level": "moderate",
            "landmarks": ["Landmark"],
            "coordinates": [1, 1],
            "generated_at": None,
            # Economy
            "primary_resources": ["iron", "timber"],
            "scarce_resources": ["gold"],
            "trade_goods": ["weapons"],
            "price_modifier": 0.9,
            # History
            "founding_story": "Long ago...",
            "historical_events": ["War"],
            "ruined_civilizations": ["Ancients"],
            "legendary_locations": ["Lost Temple"],
            # Atmosphere
            "common_creatures": ["wolves"],
            "weather_tendency": "rainy",
            "ambient_sounds": ["wind"],
        }

        ctx = RegionContext.from_dict(data)

        # Economy fields
        assert ctx.primary_resources == ["iron", "timber"]
        assert ctx.scarce_resources == ["gold"]
        assert ctx.trade_goods == ["weapons"]
        assert ctx.price_modifier == 0.9
        # History fields
        assert ctx.founding_story == "Long ago..."
        assert ctx.historical_events == ["War"]
        assert ctx.ruined_civilizations == ["Ancients"]
        assert ctx.legendary_locations == ["Lost Temple"]
        # Atmosphere fields
        assert ctx.common_creatures == ["wolves"]
        assert ctx.weather_tendency == "rainy"
        assert ctx.ambient_sounds == ["wind"]

    def test_from_dict_backward_compatible(self):
        """Test old saves without new fields load successfully with defaults."""
        # Simulates an old save file without any of the new fields
        old_save_data = {
            "name": "Old Region",
            "theme": "old theme",
            "danger_level": "safe",
            "landmarks": [],
            "coordinates": [0, 0],
            "generated_at": None,
        }

        ctx = RegionContext.from_dict(old_save_data)

        # Old fields work
        assert ctx.name == "Old Region"
        assert ctx.theme == "old theme"
        # New fields get defaults
        assert ctx.primary_resources == []
        assert ctx.scarce_resources == []
        assert ctx.trade_goods == []
        assert ctx.price_modifier == 1.0
        assert ctx.founding_story == ""
        assert ctx.historical_events == []
        assert ctx.ruined_civilizations == []
        assert ctx.legendary_locations == []
        assert ctx.common_creatures == []
        assert ctx.weather_tendency == ""
        assert ctx.ambient_sounds == []

    def test_default_factory_sets_empty_values(self):
        """Test RegionContext.default() works with new fields."""
        ctx = RegionContext.default("Default Region", (0, 0))

        # New economy fields
        assert ctx.primary_resources == []
        assert ctx.scarce_resources == []
        assert ctx.trade_goods == []
        assert ctx.price_modifier == 1.0
        # New history fields
        assert ctx.founding_story == ""
        assert ctx.historical_events == []
        assert ctx.ruined_civilizations == []
        assert ctx.legendary_locations == []
        # New atmosphere fields
        assert ctx.common_creatures == []
        assert ctx.weather_tendency == ""
        assert ctx.ambient_sounds == []

    def test_round_trip_with_new_fields(self):
        """Test full round-trip preserves all new data."""
        original = RegionContext(
            name="Complete Region",
            theme="full theme",
            danger_level="dangerous",
            landmarks=["Tower"],
            coordinates=(7, 8),
            generated_at=None,
            # Economy
            primary_resources=["copper", "fish"],
            scarce_resources=["diamonds"],
            trade_goods=["jewelry", "seafood"],
            price_modifier=1.5,
            # History
            founding_story="The settlers arrived...",
            historical_events=["Founding Day", "The Fire"],
            ruined_civilizations=["The Merfolk"],
            legendary_locations=["Sunken Palace"],
            # Atmosphere
            common_creatures=["seagulls", "crabs"],
            weather_tendency="stormy",
            ambient_sounds=["waves", "seabirds"],
        )

        data = original.to_dict()
        restored = RegionContext.from_dict(data)

        # All new economy fields preserved
        assert restored.primary_resources == original.primary_resources
        assert restored.scarce_resources == original.scarce_resources
        assert restored.trade_goods == original.trade_goods
        assert restored.price_modifier == original.price_modifier
        # All new history fields preserved
        assert restored.founding_story == original.founding_story
        assert restored.historical_events == original.historical_events
        assert restored.ruined_civilizations == original.ruined_civilizations
        assert restored.legendary_locations == original.legendary_locations
        # All new atmosphere fields preserved
        assert restored.common_creatures == original.common_creatures
        assert restored.weather_tendency == original.weather_tendency
        assert restored.ambient_sounds == original.ambient_sounds
