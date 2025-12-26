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
