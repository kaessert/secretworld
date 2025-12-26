"""Tests for AI world hierarchy fields support.

These tests verify that AI-generated locations include proper hierarchy fields
(is_overworld, is_safe_zone, parent_location, sub_locations, entry_point)
to support hierarchical navigation with enter/exit commands.
"""

import pytest
from unittest.mock import Mock
from cli_rpg.ai_service import AIService
from cli_rpg.ai_world import (
    create_ai_world,
    expand_world,
    expand_area,
    _infer_hierarchy_from_category,
)
from cli_rpg.models.location import Location


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock(spec=AIService)
    return service


@pytest.fixture
def basic_world():
    """Create a basic world with one location at origin."""
    town_square = Location(
        name="Town Square",
        description="A bustling town square.",
        coordinates=(0, 0),
        category="town"
    )
    return {"Town Square": town_square}


class TestInferHierarchyFromCategory:
    """Tests for _infer_hierarchy_from_category() helper function.

    Spec: Category-to-Hierarchy Mapping
    - Safe zones: town, village, settlement -> is_safe_zone=True
    - Danger zones: dungeon, wilderness, ruins, cave, forest, mountain -> is_safe_zone=False
    - All AI-generated locations default to is_overworld=True
    """

    def test_town_is_safe_zone(self):
        """Verify town category maps to is_safe_zone=True.

        Spec: Safe zones: town -> is_safe_zone=True
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("town")
        assert is_overworld is True
        assert is_safe_zone is True

    def test_village_is_safe_zone(self):
        """Verify village category maps to is_safe_zone=True.

        Spec: Safe zones: village -> is_safe_zone=True
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("village")
        assert is_overworld is True
        assert is_safe_zone is True

    def test_settlement_is_safe_zone(self):
        """Verify settlement category maps to is_safe_zone=True.

        Spec: Safe zones: settlement -> is_safe_zone=True
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("settlement")
        assert is_overworld is True
        assert is_safe_zone is True

    def test_dungeon_is_danger_zone(self):
        """Verify dungeon category maps to is_safe_zone=False.

        Spec: Danger zones: dungeon -> is_safe_zone=False
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("dungeon")
        assert is_overworld is True
        assert is_safe_zone is False

    def test_wilderness_is_danger_zone(self):
        """Verify wilderness category maps to is_safe_zone=False.

        Spec: Danger zones: wilderness -> is_safe_zone=False
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("wilderness")
        assert is_overworld is True
        assert is_safe_zone is False

    def test_forest_is_danger_zone(self):
        """Verify forest category maps to is_safe_zone=False.

        Spec: Danger zones: forest -> is_safe_zone=False
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("forest")
        assert is_overworld is True
        assert is_safe_zone is False

    def test_cave_is_danger_zone(self):
        """Verify cave category maps to is_safe_zone=False.

        Spec: Danger zones: cave -> is_safe_zone=False
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("cave")
        assert is_overworld is True
        assert is_safe_zone is False

    def test_ruins_is_danger_zone(self):
        """Verify ruins category maps to is_safe_zone=False.

        Spec: Danger zones: ruins -> is_safe_zone=False
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("ruins")
        assert is_overworld is True
        assert is_safe_zone is False

    def test_mountain_is_danger_zone(self):
        """Verify mountain category maps to is_safe_zone=False.

        Spec: Danger zones: mountain -> is_safe_zone=False
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category("mountain")
        assert is_overworld is True
        assert is_safe_zone is False

    def test_none_category_defaults_to_unsafe(self):
        """Verify None category defaults to is_safe_zone=False.

        Spec: Graceful defaults when AI response omits hierarchy fields
        """
        is_overworld, is_safe_zone = _infer_hierarchy_from_category(None)
        assert is_overworld is True
        assert is_safe_zone is False


class TestCreateAIWorldHierarchy:
    """Tests for create_ai_world() hierarchy field support.

    Spec: Starting location hierarchy
    - Starting location has is_overworld=True
    - is_safe_zone based on category (town -> True)
    """

    def test_starting_location_is_overworld(self, mock_ai_service):
        """Verify starting location has is_overworld=True.

        Spec: Starting location defaults: is_overworld=True
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Town Square",
            "description": "A bustling town square with a fountain.",
            "connections": {},
            "category": "town"
        }

        world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

        location = world[starting_location]
        assert location.is_overworld is True

    def test_starting_location_town_is_safe_zone(self, mock_ai_service):
        """Verify starting location with town category has is_safe_zone=True.

        Spec: Starting location with town category -> is_safe_zone=True
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Town Square",
            "description": "A bustling town square with a fountain.",
            "connections": {},
            "category": "town"
        }

        world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

        location = world[starting_location]
        assert location.is_safe_zone is True

    def test_starting_location_forest_is_not_safe_zone(self, mock_ai_service):
        """Verify starting location with forest category has is_safe_zone=False.

        Spec: Starting location with forest category -> is_safe_zone=False
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Dark Forest Clearing",
            "description": "A shadowy clearing deep in the forest.",
            "connections": {},
            "category": "forest"
        }

        world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

        location = world[starting_location]
        assert location.is_safe_zone is False

    def test_starting_location_no_category_defaults_unsafe(self, mock_ai_service):
        """Verify starting location without category defaults to is_safe_zone=False.

        Spec: Graceful defaults when AI response omits hierarchy fields
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Mysterious Place",
            "description": "An enigmatic location.",
            "connections": {}
            # No category field
        }

        world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

        location = world[starting_location]
        assert location.is_overworld is True
        assert location.is_safe_zone is False


class TestExpandWorldHierarchy:
    """Tests for expand_world() hierarchy field support.

    Spec: Expanded locations inherit hierarchy from AI response
    """

    def test_expanded_location_is_overworld(self, mock_ai_service, basic_world):
        """Verify expanded location has is_overworld=True.

        Spec: All AI-generated locations are overworld by default
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Forest Path",
            "description": "A winding path through the woods.",
            "connections": {"south": "Town Square"},
            "category": "forest"
        }

        expand_world(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy"
        )

        forest = basic_world["Forest Path"]
        assert forest.is_overworld is True

    def test_expanded_village_is_safe_zone(self, mock_ai_service, basic_world):
        """Verify expanded village has is_safe_zone=True.

        Spec: village category -> is_safe_zone=True
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Riverdale Village",
            "description": "A peaceful village by the river.",
            "connections": {"south": "Town Square"},
            "category": "village"
        }

        expand_world(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy"
        )

        village = basic_world["Riverdale Village"]
        assert village.is_safe_zone is True

    def test_expanded_dungeon_is_not_safe_zone(self, mock_ai_service, basic_world):
        """Verify expanded dungeon has is_safe_zone=False.

        Spec: dungeon category -> is_safe_zone=False
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Dark Dungeon",
            "description": "A foreboding dungeon entrance.",
            "connections": {"south": "Town Square"},
            "category": "dungeon"
        }

        expand_world(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy"
        )

        dungeon = basic_world["Dark Dungeon"]
        assert dungeon.is_safe_zone is False


class TestExpandAreaHierarchy:
    """Tests for expand_area() hierarchy field support.

    Spec: Area locations hierarchy
    - Entry location (rel 0,0): is_overworld=True
    - Other locations: is_overworld=False, parent_location=entry_name
    - Entry location's sub_locations list contains child names
    - Entry location's entry_point set to first sub-location
    - is_safe_zone based on category
    """

    def test_area_entry_location_is_overworld(self, mock_ai_service, basic_world):
        """Verify area entry location has is_overworld=True.

        Spec: Entry location (rel 0,0): is_overworld=True
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Forest Entrance",
                "description": "The edge of a dark forest.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Deep Forest"},
                "category": "forest"
            },
            {
                "name": "Deep Forest",
                "description": "Deep within the forest.",
                "relative_coords": [0, 1],
                "connections": {"south": "Forest Entrance"},
                "category": "forest"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Forest Entrance"]
        assert entry.is_overworld is True

    def test_area_sub_location_is_not_overworld(self, mock_ai_service, basic_world):
        """Verify area sub-locations have is_overworld=False.

        Spec: Other locations: is_overworld=False
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Dungeon Gate",
                "description": "The entrance to a dark dungeon.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Dungeon Hall"},
                "category": "dungeon"
            },
            {
                "name": "Dungeon Hall",
                "description": "A dark hallway.",
                "relative_coords": [0, 1],
                "connections": {"south": "Dungeon Gate"},
                "category": "dungeon"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        sub_loc = basic_world["Dungeon Hall"]
        assert sub_loc.is_overworld is False

    def test_area_sub_location_has_parent(self, mock_ai_service, basic_world):
        """Verify area sub-locations have parent_location set to entry name.

        Spec: Other locations: parent_location=entry_name
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Cave Mouth",
                "description": "The entrance to a cave.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Cave Interior"},
                "category": "cave"
            },
            {
                "name": "Cave Interior",
                "description": "Deep inside the cave.",
                "relative_coords": [0, 1],
                "connections": {"south": "Cave Mouth"},
                "category": "cave"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        sub_loc = basic_world["Cave Interior"]
        assert sub_loc.parent_location == "Cave Mouth"

    def test_area_entry_has_sub_locations_list(self, mock_ai_service, basic_world):
        """Verify area entry location has sub_locations list populated.

        Spec: Entry location's sub_locations list contains child names
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Ruin Entrance",
                "description": "Ancient ruins entrance.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Inner Ruins", "east": "Ruin Chambers"},
                "category": "ruins"
            },
            {
                "name": "Inner Ruins",
                "description": "Deeper into the ruins.",
                "relative_coords": [0, 1],
                "connections": {"south": "Ruin Entrance"},
                "category": "ruins"
            },
            {
                "name": "Ruin Chambers",
                "description": "Hidden chambers.",
                "relative_coords": [1, 0],
                "connections": {"west": "Ruin Entrance"},
                "category": "ruins"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Ruin Entrance"]
        # Sub-locations list should contain all child location names
        assert "Inner Ruins" in entry.sub_locations
        assert "Ruin Chambers" in entry.sub_locations

    def test_area_entry_has_entry_point(self, mock_ai_service, basic_world):
        """Verify area entry location has entry_point set.

        Spec: Entry location's entry_point set to first sub-location
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Mountain Pass",
                "description": "A narrow mountain pass.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Mountain Peak"},
                "category": "mountain"
            },
            {
                "name": "Mountain Peak",
                "description": "The peak of the mountain.",
                "relative_coords": [0, 1],
                "connections": {"south": "Mountain Pass"},
                "category": "mountain"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Mountain Pass"]
        assert entry.entry_point is not None
        assert entry.entry_point in entry.sub_locations

    def test_area_safe_zone_for_settlement(self, mock_ai_service, basic_world):
        """Verify area locations with settlement category have is_safe_zone=True.

        Spec: settlement category -> is_safe_zone=True
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Camp Entrance",
                "description": "A traveler's camp.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Camp Center"},
                "category": "settlement"
            },
            {
                "name": "Camp Center",
                "description": "The heart of the camp.",
                "relative_coords": [0, 1],
                "connections": {"south": "Camp Entrance"},
                "category": "settlement"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Camp Entrance"]
        sub = basic_world["Camp Center"]
        assert entry.is_safe_zone is True
        assert sub.is_safe_zone is True

    def test_area_danger_zone_for_wilderness(self, mock_ai_service, basic_world):
        """Verify area locations with wilderness category have is_safe_zone=False.

        Spec: wilderness category -> is_safe_zone=False
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Wild Border",
                "description": "The edge of the wilderness.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD", "north": "Deep Wild"},
                "category": "wilderness"
            },
            {
                "name": "Deep Wild",
                "description": "Untamed wilderness.",
                "relative_coords": [0, 1],
                "connections": {"south": "Wild Border"},
                "category": "wilderness"
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Wild Border"]
        sub = basic_world["Deep Wild"]
        assert entry.is_safe_zone is False
        assert sub.is_safe_zone is False


class TestHierarchyFieldsDefaultsWhenMissing:
    """Tests for graceful defaults when AI response omits hierarchy fields.

    Spec: Verify graceful defaults when AI response omits hierarchy fields
    """

    def test_no_category_defaults_to_unsafe_overworld(self, mock_ai_service):
        """Verify locations without category default to is_safe_zone=False, is_overworld=True.

        Spec: Graceful defaults when AI response omits category
        """
        mock_ai_service.generate_location.return_value = {
            "name": "Unknown Location",
            "description": "A strange place.",
            "connections": {}
            # No category field
        }

        world, starting_location = create_ai_world(mock_ai_service, theme="fantasy")

        location = world[starting_location]
        assert location.is_overworld is True
        assert location.is_safe_zone is False

    def test_area_without_category_defaults_to_unsafe(self, mock_ai_service, basic_world):
        """Verify area locations without category default to is_safe_zone=False.

        Spec: Graceful defaults when AI response omits category in areas
        """
        mock_ai_service.generate_area.return_value = [
            {
                "name": "Strange Gate",
                "description": "An eerie entrance.",
                "relative_coords": [0, 0],
                "connections": {"south": "EXISTING_WORLD"}
                # No category field
            }
        ]

        expand_area(
            world=basic_world,
            ai_service=mock_ai_service,
            from_location="Town Square",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1)
        )

        entry = basic_world["Strange Gate"]
        assert entry.is_safe_zone is False
