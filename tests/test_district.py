"""Tests for District model.

Tests the District dataclass, DistrictType enum, and serialization.
"""

import pytest

from cli_rpg.models.district import District, DistrictType


class TestDistrictType:
    """Tests for DistrictType enum."""

    def test_district_type_enum_values(self):
        """DistrictType has expected values (MARKET, TEMPLE, etc.)."""
        # Spec: DistrictType enum should have 9 district types
        expected_types = {
            "MARKET",
            "TEMPLE",
            "RESIDENTIAL",
            "NOBLE",
            "SLUMS",
            "CRAFTSMEN",
            "DOCKS",
            "ENTERTAINMENT",
            "MILITARY",
        }
        actual_types = {member.name for member in DistrictType}
        assert actual_types == expected_types

    def test_district_type_string_values(self):
        """DistrictType values are human-readable strings."""
        # Spec: Each type should have a readable value
        assert DistrictType.MARKET.value == "Market"
        assert DistrictType.TEMPLE.value == "Temple"
        assert DistrictType.SLUMS.value == "Slums"


class TestDistrictCreation:
    """Tests for District dataclass creation."""

    def test_district_creation_with_required_fields(self):
        """District created with name, type, description, bounds."""
        # Spec: District requires name, district_type, description, bounds
        district = District(
            name="The Golden Market",
            district_type=DistrictType.MARKET,
            description="A bustling marketplace",
            bounds=(-4, 0, -4, 0),
        )

        assert district.name == "The Golden Market"
        assert district.district_type == DistrictType.MARKET
        assert district.description == "A bustling marketplace"
        assert district.bounds == (-4, 0, -4, 0)

    def test_district_creation_with_all_fields(self):
        """District created with all optional fields."""
        # Spec: District has optional atmosphere, prosperity, notable_features
        district = District(
            name="Temple District",
            district_type=DistrictType.TEMPLE,
            description="Sacred grounds of the city",
            bounds=(0, 4, 0, 4),
            atmosphere="serene",
            prosperity="wealthy",
            notable_features=["Grand Cathedral", "Holy Fountain"],
        )

        assert district.atmosphere == "serene"
        assert district.prosperity == "wealthy"
        assert district.notable_features == ["Grand Cathedral", "Holy Fountain"]

    def test_district_default_values(self):
        """District has sensible defaults for optional fields."""
        # Spec: atmosphere defaults to "neutral", prosperity to "modest"
        district = District(
            name="Test District",
            district_type=DistrictType.RESIDENTIAL,
            description="Test",
            bounds=(0, 0, 0, 0),
        )

        assert district.atmosphere == "neutral"
        assert district.prosperity == "modest"
        assert district.notable_features == []

    def test_district_bounds_is_tuple_of_four_ints(self):
        """Bounds tuple has 4 integers."""
        # Spec: bounds is (min_x, max_x, min_y, max_y)
        district = District(
            name="Test",
            district_type=DistrictType.MARKET,
            description="Test",
            bounds=(-8, 0, -8, 0),
        )

        assert len(district.bounds) == 4
        assert all(isinstance(b, int) for b in district.bounds)


class TestDistrictContains:
    """Tests for District.contains() coordinate check."""

    def test_contains_inside_bounds(self):
        """contains() returns True for coordinates inside bounds."""
        district = District(
            name="Test",
            district_type=DistrictType.MARKET,
            description="Test",
            bounds=(-4, 0, -4, 0),
        )

        assert district.contains(-2, -2) is True
        assert district.contains(-4, -4) is True  # Edge
        assert district.contains(0, 0) is True  # Edge

    def test_contains_outside_bounds(self):
        """contains() returns False for coordinates outside bounds."""
        district = District(
            name="Test",
            district_type=DistrictType.MARKET,
            description="Test",
            bounds=(-4, 0, -4, 0),
        )

        assert district.contains(1, 0) is False
        assert district.contains(-5, -2) is False
        assert district.contains(-2, 1) is False


class TestDistrictSerialization:
    """Tests for District serialization."""

    def test_district_to_dict(self):
        """to_dict() returns dictionary with all fields."""
        # Spec: to_dict serializes all fields
        district = District(
            name="The Docks",
            district_type=DistrictType.DOCKS,
            description="Harbor area",
            bounds=(-8, -4, -8, -4),
            atmosphere="bustling",
            prosperity="modest",
            notable_features=["Warehouse Row", "Sailor's Tavern"],
        )

        data = district.to_dict()

        assert data["name"] == "The Docks"
        assert data["district_type"] == "Docks"
        assert data["description"] == "Harbor area"
        assert data["bounds"] == [-8, -4, -8, -4]  # List for JSON
        assert data["atmosphere"] == "bustling"
        assert data["prosperity"] == "modest"
        assert data["notable_features"] == ["Warehouse Row", "Sailor's Tavern"]

    def test_district_from_dict(self):
        """from_dict() restores District from dictionary."""
        # Spec: from_dict deserializes back to District
        data = {
            "name": "Noble Quarter",
            "district_type": "Noble",
            "description": "Home of the aristocracy",
            "bounds": [0, 8, 0, 8],
            "atmosphere": "refined",
            "prosperity": "wealthy",
            "notable_features": ["Lord's Manor"],
        }

        district = District.from_dict(data)

        assert district.name == "Noble Quarter"
        assert district.district_type == DistrictType.NOBLE
        assert district.description == "Home of the aristocracy"
        assert district.bounds == (0, 8, 0, 8)
        assert district.atmosphere == "refined"
        assert district.prosperity == "wealthy"
        assert district.notable_features == ["Lord's Manor"]

    def test_district_serialization_roundtrip(self):
        """to_dict/from_dict preserves all fields."""
        # Spec: Roundtrip serialization preserves all data
        original = District(
            name="Craftsmen Quarter",
            district_type=DistrictType.CRAFTSMEN,
            description="Where artisans ply their trade",
            bounds=(-8, 0, 0, 8),
            atmosphere="industrious",
            prosperity="prosperous",
            notable_features=["Smithy Row", "Weavers Guild"],
        )

        data = original.to_dict()
        restored = District.from_dict(data)

        assert restored.name == original.name
        assert restored.district_type == original.district_type
        assert restored.description == original.description
        assert restored.bounds == original.bounds
        assert restored.atmosphere == original.atmosphere
        assert restored.prosperity == original.prosperity
        assert restored.notable_features == original.notable_features

    def test_district_from_dict_with_missing_optional_fields(self):
        """from_dict() uses defaults for missing optional fields."""
        # Spec: Backward compatibility for missing optional fields
        data = {
            "name": "Old District",
            "district_type": "Residential",
            "description": "An old area",
            "bounds": [0, 4, 0, 4],
        }

        district = District.from_dict(data)

        assert district.atmosphere == "neutral"
        assert district.prosperity == "modest"
        assert district.notable_features == []
