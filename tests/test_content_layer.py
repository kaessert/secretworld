"""Tests for ContentLayer mediator class.

These tests verify that ContentLayer correctly bridges procedural layout
generators (RoomTemplate) with AI content generation to produce fully
populated SubGrid instances.

Spec: ContentLayer.populate_subgrid() transforms RoomTemplate list → SubGrid
with deterministic spatial structure and appropriate content.
"""

import pytest
from unittest.mock import Mock, patch

from cli_rpg.content_layer import ContentLayer
from cli_rpg.procedural_interiors import RoomTemplate, RoomType
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid


@pytest.fixture
def sample_room_templates():
    """Sample room templates for testing."""
    return [
        RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.ENTRY,
            connections=["north"],
            is_entry=True,
        ),
        RoomTemplate(
            coords=(0, 1, 0),
            room_type=RoomType.CORRIDOR,
            connections=["south", "north"],
        ),
        RoomTemplate(
            coords=(0, 2, 0),
            room_type=RoomType.CHAMBER,
            connections=["south", "east"],
        ),
        RoomTemplate(
            coords=(1, 2, 0),
            room_type=RoomType.TREASURE,
            connections=["west"],
        ),
        RoomTemplate(
            coords=(0, 3, 0),
            room_type=RoomType.BOSS_ROOM,
            connections=["south"],
        ),
    ]


@pytest.fixture
def parent_location():
    """Sample parent location (dungeon) for SubGrid context."""
    return Location(
        name="Test Dungeon",
        description="A dark and dangerous dungeon.",
        category="dungeon",
    )


@pytest.fixture
def content_layer():
    """Create a ContentLayer instance."""
    return ContentLayer()


# Test 1: RoomTemplate list → SubGrid with matching coordinates
def test_content_layer_transforms_templates_to_locations(
    content_layer, sample_room_templates, parent_location
):
    """Verify RoomTemplate list → SubGrid with matching coordinates.

    Spec: ContentLayer.populate_subgrid() creates Location for each RoomTemplate
    and places them at the correct coordinates in the SubGrid.
    """
    sub_grid = content_layer.populate_subgrid(
        room_templates=sample_room_templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=42,
    )

    # Verify SubGrid has correct number of locations
    assert len(sub_grid._by_name) == len(sample_room_templates)

    # Verify each template has a corresponding location at correct coordinates
    for template in sample_room_templates:
        x, y, z = template.coords
        loc = sub_grid.get_by_coordinates(x, y, z)
        assert loc is not None, f"No location at {template.coords}"
        # Location should have coordinates set
        assert loc.coordinates == template.coords


# Test 2: Entry template → Location with is_exit_point=True
def test_content_layer_entry_room_is_exit_point(
    content_layer, parent_location
):
    """Verify Entry template → Location with is_exit_point=True.

    Spec: RoomTemplate with is_entry=True produces Location with is_exit_point=True
    to allow player to exit back to overworld.
    """
    templates = [
        RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.ENTRY,
            connections=["north"],
            is_entry=True,
        ),
        RoomTemplate(
            coords=(0, 1, 0),
            room_type=RoomType.CHAMBER,
            connections=["south"],
            is_entry=False,
        ),
    ]

    sub_grid = content_layer.populate_subgrid(
        room_templates=templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=42,
    )

    # Entry location should have is_exit_point=True
    entry_loc = sub_grid.get_by_coordinates(0, 0, 0)
    assert entry_loc is not None
    assert entry_loc.is_exit_point is True

    # Non-entry location should NOT have is_exit_point=True
    other_loc = sub_grid.get_by_coordinates(0, 1, 0)
    assert other_loc is not None
    assert other_loc.is_exit_point is False


# Test 3: BOSS_ROOM template → Location with boss_enemy set
def test_content_layer_boss_room_gets_boss_enemy(
    content_layer, parent_location
):
    """Verify BOSS_ROOM template → Location with boss_enemy set.

    Spec: RoomTemplate with room_type=BOSS_ROOM produces Location with
    boss_enemy set based on parent category.
    """
    templates = [
        RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.ENTRY,
            connections=["north"],
            is_entry=True,
        ),
        RoomTemplate(
            coords=(0, 1, 0),
            room_type=RoomType.BOSS_ROOM,
            connections=["south"],
        ),
    ]

    sub_grid = content_layer.populate_subgrid(
        room_templates=templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=42,
    )

    # Boss room should have boss_enemy set
    boss_loc = sub_grid.get_by_coordinates(0, 1, 0)
    assert boss_loc is not None
    assert boss_loc.boss_enemy is not None
    assert boss_loc.boss_enemy == "dungeon"  # Based on parent category


# Test 4: TREASURE template → Location with treasures list
def test_content_layer_treasure_room_gets_treasures(
    content_layer, parent_location
):
    """Verify TREASURE template → Location with treasures list.

    Spec: RoomTemplate with room_type=TREASURE produces Location with
    non-empty treasures list.
    """
    templates = [
        RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.ENTRY,
            connections=["east"],
            is_entry=True,
        ),
        RoomTemplate(
            coords=(1, 0, 0),
            room_type=RoomType.TREASURE,
            connections=["west"],
        ),
    ]

    sub_grid = content_layer.populate_subgrid(
        room_templates=templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=42,
    )

    # Treasure room should have treasures
    treasure_loc = sub_grid.get_by_coordinates(1, 0, 0)
    assert treasure_loc is not None
    assert len(treasure_loc.treasures) > 0


# Test 5: suggested_hazards → Location hazards
def test_content_layer_hazards_from_template(
    content_layer, parent_location
):
    """Verify suggested_hazards → Location hazards.

    Spec: RoomTemplate.suggested_hazards are transferred to Location.hazards.
    """
    templates = [
        RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.ENTRY,
            connections=["north"],
            is_entry=True,
        ),
        RoomTemplate(
            coords=(0, 1, 0),
            room_type=RoomType.CHAMBER,
            connections=["south"],
            suggested_hazards=["poison_gas", "darkness"],
        ),
    ]

    sub_grid = content_layer.populate_subgrid(
        room_templates=templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=42,
    )

    # Room with hazards should have them transferred
    hazard_loc = sub_grid.get_by_coordinates(0, 1, 0)
    assert hazard_loc is not None
    assert "poison_gas" in hazard_loc.hazards
    assert "darkness" in hazard_loc.hazards


# Test 6: Same seed → same output (determinism)
def test_content_layer_deterministic_with_seed(
    content_layer, sample_room_templates, parent_location
):
    """Verify same seed → same output (determinism).

    Spec: Given same inputs and seed, ContentLayer produces identical SubGrid.
    """
    sub_grid_1 = content_layer.populate_subgrid(
        room_templates=sample_room_templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=12345,
    )

    sub_grid_2 = content_layer.populate_subgrid(
        room_templates=sample_room_templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=12345,
    )

    # Both should have same locations with same names
    assert set(sub_grid_1._by_name.keys()) == set(sub_grid_2._by_name.keys())

    # Same locations at same coordinates
    for template in sample_room_templates:
        loc_1 = sub_grid_1.get_by_coordinates(*template.coords)
        loc_2 = sub_grid_2.get_by_coordinates(*template.coords)
        assert loc_1 is not None
        assert loc_2 is not None
        assert loc_1.name == loc_2.name


# Test 7: Fallback without AI
def test_content_layer_fallback_without_ai(
    content_layer, sample_room_templates, parent_location
):
    """Verify AI unavailable → fallback names/descriptions by room type.

    Spec: When ai_service=None, ContentLayer uses fallback content
    based on room type (e.g., "Entrance Chamber" for ENTRY).
    """
    sub_grid = content_layer.populate_subgrid(
        room_templates=sample_room_templates,
        parent_location=parent_location,
        ai_service=None,
        generation_context=None,
        seed=42,
    )

    # Check entry room has appropriate fallback name
    entry_loc = sub_grid.get_by_coordinates(0, 0, 0)
    assert entry_loc is not None
    # Fallback name should be descriptive (contains room type hint)
    assert entry_loc.name != ""
    assert entry_loc.description != ""

    # Boss room should have boss-related name
    boss_loc = sub_grid.get_by_coordinates(0, 3, 0)
    assert boss_loc is not None
    assert boss_loc.name != ""
    assert boss_loc.description != ""


# Test 8: AI content used when available
def test_content_layer_ai_content_used_when_available(
    content_layer, parent_location
):
    """Verify Mock AI → Location has AI-generated content.

    Spec: When ai_service is available, ContentLayer uses AI-generated
    names and descriptions instead of fallbacks.
    """
    templates = [
        RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.ENTRY,
            connections=["north"],
            is_entry=True,
        ),
    ]

    # Create mock AI service
    mock_ai = Mock()
    mock_ai.generate_room_content = Mock(return_value={
        "name": "The Grand Vestibule",
        "description": "An ornate entryway with gilded columns.",
    })

    sub_grid = content_layer.populate_subgrid(
        room_templates=templates,
        parent_location=parent_location,
        ai_service=mock_ai,
        generation_context=None,
        seed=42,
    )

    entry_loc = sub_grid.get_by_coordinates(0, 0, 0)
    assert entry_loc is not None

    # AI should have been called
    assert mock_ai.generate_room_content.called

    # Location should have AI-generated content
    assert entry_loc.name == "The Grand Vestibule"
    assert entry_loc.description == "An ornate entryway with gilded columns."
