"""Tests for AI-generated dungeon boss placement in expand_area().

Spec: When expand_area() generates a dungeon/cave/ruins category area,
the room furthest from entry (max Manhattan distance from (0,0)) should
have boss_enemy set to the entry location's category.
"""

import pytest
from unittest.mock import MagicMock, patch
from cli_rpg.ai_world import expand_area, BOSS_CATEGORIES, _find_furthest_room
from cli_rpg.models.location import Location


class TestBossCategories:
    """Tests for BOSS_CATEGORIES constant."""

    # Spec: dungeon, cave, ruins categories should have bosses
    def test_boss_categories_contains_dungeon(self):
        """dungeon is in BOSS_CATEGORIES."""
        assert "dungeon" in BOSS_CATEGORIES

    def test_boss_categories_contains_cave(self):
        """cave is in BOSS_CATEGORIES."""
        assert "cave" in BOSS_CATEGORIES

    def test_boss_categories_contains_ruins(self):
        """ruins is in BOSS_CATEGORIES."""
        assert "ruins" in BOSS_CATEGORIES

    # Spec: town, village, etc. should NOT have bosses
    def test_boss_categories_excludes_town(self):
        """town is NOT in BOSS_CATEGORIES."""
        assert "town" not in BOSS_CATEGORIES

    def test_boss_categories_excludes_village(self):
        """village is NOT in BOSS_CATEGORIES."""
        assert "village" not in BOSS_CATEGORIES

    def test_boss_categories_excludes_forest(self):
        """forest is NOT in BOSS_CATEGORIES (optional wilderness, not dungeon)."""
        assert "forest" not in BOSS_CATEGORIES


class TestFindFurthestRoom:
    """Tests for _find_furthest_room helper function."""

    # Spec: Entry rooms (is_entry=True) should be excluded
    def test_find_furthest_room_excludes_entry(self):
        """Entry room should be excluded from furthest room search."""
        placed_locations = {
            "Entry Hall": {"relative_coords": (0, 0), "is_entry": True},
            "Side Room": {"relative_coords": (1, 0), "is_entry": False},
        }
        result = _find_furthest_room(placed_locations)
        assert result == "Side Room"

    # Spec: Room with max Manhattan distance from (0,0) should be selected
    def test_find_furthest_room_manhattan_distance(self):
        """Room with highest Manhattan distance from (0,0) is selected."""
        placed_locations = {
            "Entry Hall": {"relative_coords": (0, 0), "is_entry": True},
            "Near Room": {"relative_coords": (1, 0), "is_entry": False},
            "Far Room": {"relative_coords": (2, 1), "is_entry": False},  # distance 3
            "Side Room": {"relative_coords": (0, 2), "is_entry": False},  # distance 2
        }
        result = _find_furthest_room(placed_locations)
        assert result == "Far Room"

    # Spec: If only entry exists, return None
    def test_find_furthest_room_only_entry_returns_none(self):
        """If only entry exists (no sub-rooms), return None."""
        placed_locations = {
            "Entry Hall": {"relative_coords": (0, 0), "is_entry": True},
        }
        result = _find_furthest_room(placed_locations)
        assert result is None

    # Spec: Empty dict returns None
    def test_find_furthest_room_empty_returns_none(self):
        """Empty placed_locations returns None."""
        result = _find_furthest_room({})
        assert result is None

    # Spec: Negative coordinates work correctly
    def test_find_furthest_room_negative_coords(self):
        """Negative coordinates are handled correctly (absolute values)."""
        placed_locations = {
            "Entry Hall": {"relative_coords": (0, 0), "is_entry": True},
            "Deep Room": {"relative_coords": (-2, -1), "is_entry": False},  # distance 3
            "Near Room": {"relative_coords": (1, 0), "is_entry": False},  # distance 1
        }
        result = _find_furthest_room(placed_locations)
        assert result == "Deep Room"


class TestExpandAreaBossPlacement:
    """Tests for boss placement in expand_area()."""

    def _create_mock_ai_service(self, category: str, num_locations: int = 3):
        """Create a mock AI service that returns area data.

        Note: Uses bounds-aware coordinates. Caves have 3x3 bounds (-1,1),
        dungeons have 7x7 bounds (-3,3), etc. We use diagonal coords to stay
        within bounds while maximizing distance.
        """
        ai_service = MagicMock()

        # Coordinate layouts that stay within typical SubGrid bounds
        # Cave: 3x3 = (-1, 1), Dungeon: 7x7 = (-3, 3), Ruins: 5x5 = (-2, 2)
        coord_layouts = {
            "cave": [(0, 0), (1, 0), (1, 1)],  # max distance 2 at (1,1)
            "dungeon": [(0, 0), (1, 0), (2, 0)],  # max distance 2 at (2,0)
            "ruins": [(0, 0), (1, 0), (2, 0)],  # max distance 2 at (2,0)
            "town": [(0, 0), (1, 0), (2, 0)],  # town uses default bounds
        }
        coords = coord_layouts.get(category, [(0, 0), (1, 0), (2, 0)])

        # Generate area data with entry at (0,0) and sub-locations
        area_data = [
            {
                "name": f"{category.title()} Entry",
                "description": f"The entrance to the {category}.",
                "category": category,
                "relative_coords": coords[0],
                "is_named": True,
                "npcs": [],
            }
        ]

        # Add sub-locations at valid coordinates
        for i in range(1, min(num_locations, len(coords))):
            area_data.append({
                "name": f"{category.title()} Room {i}",
                "description": f"A room deep in the {category}.",
                "category": category,
                "relative_coords": coords[i],
                "is_named": True,
                "npcs": [],
            })

        ai_service.generate_area.return_value = area_data
        ai_service.generate_area_with_context.return_value = area_data
        return ai_service

    # Spec: Dungeon areas should have boss in furthest room
    def test_expand_area_dungeon_places_boss_in_furthest_room(self):
        """expand_area for dungeon category places boss in furthest room."""
        world = {
            "Start": Location(name="Start", description="Starting location", coordinates=(0, 0))
        }
        ai_service = self._create_mock_ai_service("dungeon", num_locations=3)

        result = expand_area(
            world=world,
            ai_service=ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
        )

        # Find the entry location (at target coords)
        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None, "Entry location should exist"
        assert entry_loc.sub_grid is not None, "Entry should have sub_grid"

        # Find furthest room in sub_grid - should have boss_enemy set
        furthest_room = entry_loc.sub_grid.get_by_name("Dungeon Room 2")
        assert furthest_room is not None, "Furthest room should exist in sub_grid"
        assert furthest_room.boss_enemy == "dungeon", "Boss should be set to category"

    # Spec: Cave areas should have boss
    def test_expand_area_cave_places_boss(self):
        """expand_area for cave category places boss in furthest room."""
        world = {
            "Start": Location(name="Start", description="Starting location", coordinates=(0, 0))
        }
        ai_service = self._create_mock_ai_service("cave", num_locations=3)

        result = expand_area(
            world=world,
            ai_service=ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
        )

        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None
        assert entry_loc.sub_grid is not None

        # Cave Room 2 is at (1,1), distance 2 - furthest room
        furthest_room = entry_loc.sub_grid.get_by_name("Cave Room 2")
        assert furthest_room is not None, "Cave Room 2 should exist in sub_grid"
        assert furthest_room.boss_enemy == "cave"

    # Spec: Ruins areas should have boss
    def test_expand_area_ruins_places_boss(self):
        """expand_area for ruins category places boss in furthest room."""
        world = {
            "Start": Location(name="Start", description="Starting location", coordinates=(0, 0))
        }
        ai_service = self._create_mock_ai_service("ruins", num_locations=3)

        result = expand_area(
            world=world,
            ai_service=ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
        )

        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None
        assert entry_loc.sub_grid is not None

        furthest_room = entry_loc.sub_grid.get_by_name("Ruins Room 2")
        assert furthest_room is not None
        assert furthest_room.boss_enemy == "ruins"

    # Spec: Town areas should NOT have boss
    def test_expand_area_town_no_boss(self):
        """expand_area for town category does NOT place boss."""
        world = {
            "Start": Location(name="Start", description="Starting location", coordinates=(0, 0))
        }
        ai_service = self._create_mock_ai_service("town", num_locations=3)

        result = expand_area(
            world=world,
            ai_service=ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
        )

        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None

        # Check no location has boss_enemy set
        if entry_loc.sub_grid is not None:
            for name in ["Town Room 1", "Town Room 2"]:
                loc = entry_loc.sub_grid.get_by_name(name)
                if loc is not None:
                    assert loc.boss_enemy is None, f"{name} should not have boss"

    # Spec: Single location (no sub-locations) should NOT have boss
    def test_expand_area_single_location_no_boss(self):
        """expand_area with only entry location does NOT place boss."""
        world = {
            "Start": Location(name="Start", description="Starting location", coordinates=(0, 0))
        }
        ai_service = self._create_mock_ai_service("dungeon", num_locations=1)

        result = expand_area(
            world=world,
            ai_service=ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
        )

        # With only 1 location (entry), there's no sub_grid and no boss
        entry_loc = None
        for loc in result.values():
            if loc.name == "Dungeon Entry":
                entry_loc = loc
                break

        # Entry itself should not have boss_enemy
        if entry_loc is not None:
            assert entry_loc.boss_enemy is None, "Entry itself should not have boss"

    # Spec: Boss room is actually the furthest from entry
    def test_expand_area_boss_room_is_furthest_from_entry(self):
        """Boss is placed in room with maximum Manhattan distance from entry."""
        world = {
            "Start": Location(name="Start", description="Starting location", coordinates=(0, 0))
        }

        # Create mock with specific layout to verify distance calculation
        ai_service = MagicMock()
        area_data = [
            {"name": "Deep Dungeon Entry", "description": "Entry", "category": "dungeon",
             "relative_coords": (0, 0), "is_named": True, "npcs": []},
            {"name": "Near Chamber", "description": "Near", "category": "dungeon",
             "relative_coords": (1, 0), "is_named": True, "npcs": []},  # distance 1
            {"name": "Side Hall", "description": "Side", "category": "dungeon",
             "relative_coords": (0, 1), "is_named": True, "npcs": []},  # distance 1
            {"name": "Deep Sanctum", "description": "Deep", "category": "dungeon",
             "relative_coords": (2, 1), "is_named": True, "npcs": []},  # distance 3 - FURTHEST
        ]
        ai_service.generate_area.return_value = area_data
        ai_service.generate_area_with_context.return_value = area_data

        result = expand_area(
            world=world,
            ai_service=ai_service,
            from_location="Start",
            direction="north",
            theme="fantasy",
            target_coords=(0, 1),
        )

        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None
        assert entry_loc.sub_grid is not None

        # Deep Sanctum should have the boss (furthest at distance 3)
        deep_sanctum = entry_loc.sub_grid.get_by_name("Deep Sanctum")
        assert deep_sanctum is not None
        assert deep_sanctum.boss_enemy == "dungeon"

        # Other rooms should NOT have boss
        near_chamber = entry_loc.sub_grid.get_by_name("Near Chamber")
        side_hall = entry_loc.sub_grid.get_by_name("Side Hall")
        assert near_chamber is not None and near_chamber.boss_enemy is None
        assert side_hall is not None and side_hall.boss_enemy is None
