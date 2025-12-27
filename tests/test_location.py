"""Tests for the Location model."""

import pytest
from cli_rpg.models.location import Location


class TestLocationCreation:
    """Test location instantiation and validation."""

    def test_location_creation_valid(self):
        """Test creating location with valid attributes - verifies basic instantiation."""
        location = Location(
            name="Town Square",
            description="A bustling town square with a fountain in the center."
        )
        assert location.name == "Town Square"
        assert location.description == "A bustling town square with a fountain in the center."

    def test_location_name_validation_too_short(self):
        """Test name validation fails for name < 2 characters - spec: MIN_NAME_LENGTH = 2."""
        with pytest.raises(ValueError) as exc_info:
            Location(
                name="A",
                description="A description."
            )
        assert "at least 2 characters" in str(exc_info.value)

    def test_location_name_validation_too_long(self):
        """Test name validation fails for name > 50 characters - spec: MAX_NAME_LENGTH = 50."""
        long_name = "A" * 51
        with pytest.raises(ValueError) as exc_info:
            Location(
                name=long_name,
                description="A description."
            )
        assert "at most 50 characters" in str(exc_info.value)

    def test_location_name_validation_empty(self):
        """Test name validation fails for empty/whitespace name - spec: non-empty required."""
        with pytest.raises(ValueError) as exc_info:
            Location(
                name="   ",
                description="A description."
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_location_description_validation_empty(self):
        """Test description validation fails for empty description - spec: non-empty required."""
        with pytest.raises(ValueError) as exc_info:
            Location(
                name="Town Square",
                description="   "
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_location_description_validation_too_long(self):
        """Test description validation fails for description > 500 characters - spec: MAX_DESCRIPTION_LENGTH = 500."""
        long_description = "A" * 501
        with pytest.raises(ValueError) as exc_info:
            Location(
                name="Town Square",
                description=long_description
            )
        assert "at most 500 characters" in str(exc_info.value)


class TestLocationDirectionMethods:
    """Test direction-related methods."""

    def test_get_available_directions_with_world(self):
        """Test get_available_directions with world dict - spec: returns sorted list."""
        # Create a small world with coordinates
        town = Location(name="Town Square", description="A description.")
        town.coordinates = (0, 0)
        market = Location(name="Market", description="A market.")
        market.coordinates = (0, 1)  # north
        inn = Location(name="Inn", description="An inn.")
        inn.coordinates = (1, 0)  # east
        gate = Location(name="Gate", description="A gate.")
        gate.coordinates = (0, -1)  # south

        world = {
            "Town Square": town,
            "Market": market,
            "Inn": inn,
            "Gate": gate,
        }

        directions = town.get_available_directions(world=world)
        assert directions == ["east", "north", "south"]

    def test_get_available_directions_empty_when_no_context(self):
        """Test get_available_directions with no context returns empty list."""
        location = Location(name="Town Square", description="A description.")
        location.coordinates = (0, 0)
        assert location.get_available_directions() == []

    def test_get_available_directions_empty_when_no_coordinates(self):
        """Test get_available_directions with no coordinates returns empty list."""
        location = Location(name="Town Square", description="A description.")
        assert location.get_available_directions(world={}) == []


class TestLocationSerialization:
    """Test serialization/deserialization."""

    def test_location_to_dict(self):
        """Test serializing location to dict - verifies to_dict method."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        data = location.to_dict()
        assert data["name"] == "Town Square"
        assert data["description"] == "A bustling square."
        # Connections field should not exist
        assert "connections" not in data

    def test_location_from_dict_basic(self):
        """Test deserializing basic location from dict - verifies from_dict classmethod."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
        }
        location = Location.from_dict(data)
        assert location.name == "Town Square"
        assert location.description == "A bustling square."

    def test_location_from_dict_ignores_legacy_connections(self):
        """Test from_dict ignores legacy connections field - backward compatibility."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
            "connections": {"north": "Market", "east": "Inn"}  # Legacy field
        }
        location = Location.from_dict(data)
        assert location.name == "Town Square"
        # Location should still be created successfully

    def test_location_from_dict_missing_required_field(self):
        """Test from_dict fails with missing required field - spec: name and description required."""
        data = {"description": "A bustling square."}
        with pytest.raises((ValueError, KeyError)):
            Location.from_dict(data)

    def test_location_roundtrip_serialization(self):
        """Test to_dict -> from_dict preserves data - verifies serialization roundtrip."""
        original = Location(
            name="Town Square",
            description="A bustling square.",
            coordinates=(5, 10)
        )
        data = original.to_dict()
        restored = Location.from_dict(data)
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.coordinates == original.coordinates

    def test_location_str_representation(self):
        """Test __str__ output format - verifies human-readable representation."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        str_repr = str(location)
        assert "Town Square" in str_repr
        assert "A bustling square." in str_repr


class TestLocationCoordinates:
    """Tests for location coordinates (grid-based world system)."""

    def test_location_with_coordinates(self):
        """Test creating location with coordinates - spec: coordinates field added."""
        location = Location(
            name="Town Square",
            description="A bustling square.",
            coordinates=(0, 0)
        )
        assert location.coordinates == (0, 0)

    def test_location_without_coordinates_defaults_to_none(self):
        """Test location without coordinates defaults to None - spec: backward compat."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        assert location.coordinates is None

    def test_location_coordinates_in_to_dict(self):
        """Test coordinates included in to_dict when present - spec: serialization."""
        location = Location(
            name="Town Square",
            description="A bustling square.",
            coordinates=(5, -3)
        )
        data = location.to_dict()
        assert data["coordinates"] == [5, -3]

    def test_location_coordinates_not_in_to_dict_when_none(self):
        """Test coordinates excluded from to_dict when None - spec: backward compat."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        data = location.to_dict()
        assert "coordinates" not in data

    def test_location_coordinates_from_dict(self):
        """Test coordinates restored from dict - spec: deserialization."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
            "coordinates": [5, -3]
        }
        location = Location.from_dict(data)
        assert location.coordinates == (5, -3)

    def test_location_coordinates_from_dict_missing(self):
        """Test from_dict with missing coordinates defaults to None - spec: backward compat."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
        }
        location = Location.from_dict(data)
        assert location.coordinates is None

    def test_location_coordinates_roundtrip(self):
        """Test coordinates preserved through serialization roundtrip."""
        original = Location(
            name="Town Square",
            description="A bustling square.",
            coordinates=(10, 20)
        )
        data = original.to_dict()
        restored = Location.from_dict(data)
        assert restored.coordinates == (10, 20)


class TestLocationHierarchy:
    """Tests for location hierarchy fields (overworld/sub-location system)."""

    # Test Field Defaults
    def test_location_hierarchy_fields_default_values(self):
        """Test all 5 hierarchy fields have correct defaults - spec: backward compatible defaults."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        assert location.is_overworld is False
        assert location.parent_location is None
        assert location.sub_locations == []
        assert location.is_safe_zone is False
        assert location.entry_point is None

    def test_location_is_overworld_default_false(self):
        """Test is_overworld defaults to False - spec: is_overworld default is False."""
        location = Location(name="Town Square", description="A bustling square.")
        assert location.is_overworld is False

    def test_location_parent_location_default_none(self):
        """Test parent_location defaults to None - spec: parent_location default is None."""
        location = Location(name="Town Square", description="A bustling square.")
        assert location.parent_location is None

    def test_location_sub_locations_default_empty_list(self):
        """Test sub_locations defaults to empty list - spec: sub_locations default is []."""
        location = Location(name="Town Square", description="A bustling square.")
        assert location.sub_locations == []
        # Ensure it's a new list instance (not shared)
        location.sub_locations.append("Test")
        location2 = Location(name="Another Place", description="Another description.")
        assert location2.sub_locations == []

    def test_location_is_safe_zone_default_false(self):
        """Test is_safe_zone defaults to False - spec: is_safe_zone default is False."""
        location = Location(name="Town Square", description="A bustling square.")
        assert location.is_safe_zone is False

    def test_location_entry_point_default_none(self):
        """Test entry_point defaults to None - spec: entry_point default is None."""
        location = Location(name="Town Square", description="A bustling square.")
        assert location.entry_point is None

    # Test Field Assignment
    def test_location_creation_with_hierarchy_fields(self):
        """Test can create location with all 5 new hierarchy fields."""
        location = Location(
            name="Ancient Ruins",
            description="Mysterious ancient ruins.",
            is_overworld=True,
            parent_location=None,
            sub_locations=["Entrance Hall", "Inner Sanctum"],
            is_safe_zone=False,
            entry_point="Entrance Hall"
        )
        assert location.is_overworld is True
        assert location.parent_location is None
        assert location.sub_locations == ["Entrance Hall", "Inner Sanctum"]
        assert location.is_safe_zone is False
        assert location.entry_point == "Entrance Hall"

    def test_location_overworld_landmark_creation(self):
        """Test creating a typical overworld landmark."""
        landmark = Location(
            name="Crystal Tower",
            description="A towering spire of crystalline stone.",
            is_overworld=True,
            sub_locations=["Tower Base", "Crystal Chamber", "Observation Deck"],
            is_safe_zone=True,
            entry_point="Tower Base"
        )
        assert landmark.is_overworld is True
        assert landmark.parent_location is None  # Landmarks have no parent
        assert len(landmark.sub_locations) == 3
        assert landmark.is_safe_zone is True
        assert landmark.entry_point == "Tower Base"

    def test_location_sub_location_creation(self):
        """Test creating a sub-location with parent reference."""
        sub_location = Location(
            name="Tower Base",
            description="The base of the Crystal Tower.",
            parent_location="Crystal Tower",
            is_overworld=False,
            is_safe_zone=True
        )
        assert sub_location.is_overworld is False
        assert sub_location.parent_location == "Crystal Tower"
        assert sub_location.sub_locations == []  # Sub-locations typically don't have children
        assert sub_location.is_safe_zone is True

    # Test Serialization (to_dict)
    def test_location_to_dict_excludes_default_hierarchy_fields(self):
        """Test defaults not serialized - spec: backward compatibility."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        data = location.to_dict()
        assert "is_overworld" not in data
        assert "parent_location" not in data
        assert "sub_locations" not in data
        assert "is_safe_zone" not in data
        assert "entry_point" not in data

    def test_location_to_dict_includes_is_overworld_when_true(self):
        """Test is_overworld: true is serialized - spec: non-default values included."""
        location = Location(
            name="Landmark",
            description="An overworld landmark.",
            is_overworld=True
        )
        data = location.to_dict()
        assert data["is_overworld"] is True

    def test_location_to_dict_includes_parent_location_when_set(self):
        """Test parent_location serialized when not None - spec: non-default values included."""
        location = Location(
            name="Sub Area",
            description="A sub-location.",
            parent_location="Main Area"
        )
        data = location.to_dict()
        assert data["parent_location"] == "Main Area"

    def test_location_to_dict_includes_sub_locations_when_non_empty(self):
        """Test sub_locations serialized when not empty - spec: non-default values included."""
        location = Location(
            name="Main Area",
            description="A main area.",
            sub_locations=["Sub Area 1", "Sub Area 2"]
        )
        data = location.to_dict()
        assert data["sub_locations"] == ["Sub Area 1", "Sub Area 2"]

    def test_location_to_dict_includes_is_safe_zone_when_true(self):
        """Test is_safe_zone: true is serialized - spec: non-default values included."""
        location = Location(
            name="Safe Haven",
            description="A safe place.",
            is_safe_zone=True
        )
        data = location.to_dict()
        assert data["is_safe_zone"] is True

    def test_location_to_dict_includes_entry_point_when_set(self):
        """Test entry_point serialized when not None - spec: non-default values included."""
        location = Location(
            name="Dungeon",
            description="A dungeon.",
            entry_point="Dungeon Entrance"
        )
        data = location.to_dict()
        assert data["entry_point"] == "Dungeon Entrance"

    # Test Deserialization (from_dict)
    def test_location_from_dict_missing_hierarchy_fields_uses_defaults(self):
        """Test old saves load fine - spec: backward compatibility."""
        data = {
            "name": "Old Location",
            "description": "From an old save file.",
        }
        location = Location.from_dict(data)
        assert location.is_overworld is False
        assert location.parent_location is None
        assert location.sub_locations == []
        assert location.is_safe_zone is False
        assert location.entry_point is None

    def test_location_from_dict_with_is_overworld(self):
        """Test deserialize is_overworld - spec: deserialization."""
        data = {
            "name": "Landmark",
            "description": "An overworld landmark.",
            "is_overworld": True
        }
        location = Location.from_dict(data)
        assert location.is_overworld is True

    def test_location_from_dict_with_parent_location(self):
        """Test deserialize parent_location - spec: deserialization."""
        data = {
            "name": "Sub Area",
            "description": "A sub-location.",
            "parent_location": "Main Area"
        }
        location = Location.from_dict(data)
        assert location.parent_location == "Main Area"

    def test_location_from_dict_with_sub_locations(self):
        """Test deserialize sub_locations - spec: deserialization."""
        data = {
            "name": "Main Area",
            "description": "A main area.",
            "sub_locations": ["Sub 1", "Sub 2", "Sub 3"]
        }
        location = Location.from_dict(data)
        assert location.sub_locations == ["Sub 1", "Sub 2", "Sub 3"]

    def test_location_from_dict_with_is_safe_zone(self):
        """Test deserialize is_safe_zone - spec: deserialization."""
        data = {
            "name": "Safe Haven",
            "description": "A safe place.",
            "is_safe_zone": True
        }
        location = Location.from_dict(data)
        assert location.is_safe_zone is True

    def test_location_from_dict_with_entry_point(self):
        """Test deserialize entry_point - spec: deserialization."""
        data = {
            "name": "Dungeon",
            "description": "A dungeon.",
            "entry_point": "Dungeon Entrance"
        }
        location = Location.from_dict(data)
        assert location.entry_point == "Dungeon Entrance"

    # Test Roundtrip Serialization
    def test_location_hierarchy_roundtrip_serialization(self):
        """Test all hierarchy fields preserved through to_dict/from_dict - spec: roundtrip."""
        original = Location(
            name="Crystal Tower",
            description="A towering spire of crystalline stone.",
            coordinates=(5, 10),
            is_overworld=True,
            parent_location=None,
            sub_locations=["Tower Base", "Crystal Chamber"],
            is_safe_zone=True,
            entry_point="Tower Base"
        )
        data = original.to_dict()
        restored = Location.from_dict(data)

        assert restored.is_overworld == original.is_overworld
        assert restored.parent_location == original.parent_location
        assert restored.sub_locations == original.sub_locations
        assert restored.is_safe_zone == original.is_safe_zone
        assert restored.entry_point == original.entry_point
