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
        assert location.connections == {}
    
    def test_location_creation_with_connections(self):
        """Test creating location with initial connections - verifies connections storage."""
        connections = {"north": "Market", "east": "Inn"}
        location = Location(
            name="Town Square",
            description="A bustling town square.",
            connections=connections
        )
        assert location.connections == connections
    
    def test_location_creation_defaults_empty_connections(self):
        """Test that connections defaults to empty dict - verifies default value."""
        location = Location(
            name="Town Square",
            description="A bustling town square."
        )
        assert location.connections == {}
    
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
    
    def test_location_connections_validation_invalid_direction(self):
        """Test connections validation fails for invalid direction key - spec: VALID_DIRECTIONS only."""
        with pytest.raises(ValueError) as exc_info:
            Location(
                name="Town Square",
                description="A description.",
                connections={"northwest": "Market"}
            )
        assert "Invalid direction" in str(exc_info.value)
    
    def test_location_connections_validation_empty_location_name(self):
        """Test connections validation fails for empty location name - spec: non-empty values."""
        with pytest.raises(ValueError) as exc_info:
            Location(
                name="Town Square",
                description="A description.",
                connections={"north": ""}
            )
        assert "cannot be empty" in str(exc_info.value)


class TestLocationConnectionMethods:
    """Test connection manipulation methods."""
    
    def test_add_connection_valid(self):
        """Test adding valid connection - verifies add_connection method."""
        location = Location(name="Town Square", description="A description.")
        location.add_connection("north", "Market")
        assert location.connections["north"] == "Market"
    
    def test_add_connection_invalid_direction(self):
        """Test adding connection with invalid direction fails - spec: VALID_DIRECTIONS only."""
        location = Location(name="Town Square", description="A description.")
        with pytest.raises(ValueError):
            location.add_connection("northwest", "Market")
    
    def test_add_connection_empty_location_name(self):
        """Test adding connection with empty location name fails - spec: non-empty required."""
        location = Location(name="Town Square", description="A description.")
        with pytest.raises(ValueError):
            location.add_connection("north", "")
    
    def test_add_connection_overwrites_existing(self):
        """Test adding connection overwrites existing one - verifies update behavior."""
        location = Location(name="Town Square", description="A description.")
        location.add_connection("north", "Market")
        location.add_connection("north", "Inn")
        assert location.connections["north"] == "Inn"
    
    def test_remove_connection_existing(self):
        """Test removing existing connection - verifies remove_connection method."""
        location = Location(
            name="Town Square",
            description="A description.",
            connections={"north": "Market"}
        )
        location.remove_connection("north")
        assert "north" not in location.connections
    
    def test_remove_connection_nonexistent(self):
        """Test removing non-existent connection doesn't raise error - spec: silent removal."""
        location = Location(name="Town Square", description="A description.")
        location.remove_connection("north")  # Should not raise
        assert "north" not in location.connections
    
    def test_get_connection_existing(self):
        """Test getting existing connection returns correct name - verifies get_connection method."""
        location = Location(
            name="Town Square",
            description="A description.",
            connections={"north": "Market"}
        )
        assert location.get_connection("north") == "Market"
    
    def test_get_connection_nonexistent(self):
        """Test getting non-existent connection returns None - spec: returns Optional[str]."""
        location = Location(name="Town Square", description="A description.")
        assert location.get_connection("north") is None
    
    def test_has_connection_existing(self):
        """Test has_connection returns True for existing connection - verifies has_connection method."""
        location = Location(
            name="Town Square",
            description="A description.",
            connections={"north": "Market"}
        )
        assert location.has_connection("north") is True
    
    def test_has_connection_nonexistent(self):
        """Test has_connection returns False for non-existent connection - verifies has_connection method."""
        location = Location(name="Town Square", description="A description.")
        assert location.has_connection("north") is False
    
    def test_get_available_directions_multiple(self):
        """Test get_available_directions with multiple connections - spec: returns sorted list."""
        location = Location(
            name="Town Square",
            description="A description.",
            connections={"north": "Market", "east": "Inn", "south": "Gate"}
        )
        directions = location.get_available_directions()
        assert directions == ["east", "north", "south"]
    
    def test_get_available_directions_empty(self):
        """Test get_available_directions with no connections - spec: returns empty list."""
        location = Location(name="Town Square", description="A description.")
        assert location.get_available_directions() == []


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
        assert data["connections"] == {}
    
    def test_location_to_dict_with_connections(self):
        """Test serializing location with connections to dict - verifies connections preservation."""
        location = Location(
            name="Town Square",
            description="A bustling square.",
            connections={"north": "Market", "east": "Inn"}
        )
        data = location.to_dict()
        assert data["connections"] == {"north": "Market", "east": "Inn"}
    
    def test_location_from_dict_basic(self):
        """Test deserializing basic location from dict - verifies from_dict classmethod."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
            "connections": {}
        }
        location = Location.from_dict(data)
        assert location.name == "Town Square"
        assert location.description == "A bustling square."
        assert location.connections == {}
    
    def test_location_from_dict_with_connections(self):
        """Test deserializing location with connections from dict - verifies connections restoration."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
            "connections": {"north": "Market", "east": "Inn"}
        }
        location = Location.from_dict(data)
        assert location.connections == {"north": "Market", "east": "Inn"}
    
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
            connections={"north": "Market", "south": "Gate"}
        )
        data = original.to_dict()
        restored = Location.from_dict(data)
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.connections == original.connections
    
    def test_location_str_representation(self):
        """Test __str__ output format - verifies human-readable representation."""
        location = Location(
            name="Town Square",
            description="A bustling square.",
            connections={"north": "Market", "east": "Inn"}
        )
        str_repr = str(location)
        assert "Town Square" in str_repr
        assert "A bustling square." in str_repr
        # Should show available directions
        assert "north" in str_repr or "Exits" in str_repr
