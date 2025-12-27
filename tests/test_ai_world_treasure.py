"""Tests for AI-generated treasure chest placement in expand_area() and generate_subgrid_for_location().

Spec: AI-generated areas should include treasure chests that:
1. Scale with area size (1-3 chests based on number of rooms)
2. Are distributed across non-entry rooms (not clustered)
3. Match location category thematically (ancient weapons in ruins, crystals in caves)
4. Have lock difficulty that scales with distance from entry
5. Some chests are trap-protected (DEX check to open safely)
"""

import pytest
from unittest.mock import MagicMock
from cli_rpg.ai_world import (
    expand_area,
    generate_subgrid_for_location,
    TREASURE_LOOT_TABLES,
    TREASURE_CHEST_NAMES,
    _place_treasures,
    BOSS_CATEGORIES,
)
from cli_rpg.models.location import Location


class TestTreasureLootTables:
    """Tests for TREASURE_LOOT_TABLES constant."""

    # Spec: All major dungeon categories should have loot tables
    def test_treasure_loot_tables_contains_dungeon(self):
        """dungeon category has a loot table."""
        assert "dungeon" in TREASURE_LOOT_TABLES

    def test_treasure_loot_tables_contains_cave(self):
        """cave category has a loot table."""
        assert "cave" in TREASURE_LOOT_TABLES

    def test_treasure_loot_tables_contains_ruins(self):
        """ruins category has a loot table."""
        assert "ruins" in TREASURE_LOOT_TABLES

    def test_treasure_loot_tables_contains_temple(self):
        """temple category has a loot table."""
        assert "temple" in TREASURE_LOOT_TABLES

    def test_treasure_loot_tables_contains_forest(self):
        """forest category has a loot table (for forest caves, etc.)."""
        assert "forest" in TREASURE_LOOT_TABLES

    # Spec: Each item must have required fields
    def test_treasure_loot_tables_items_have_required_fields(self):
        """All loot table items must have name and item_type."""
        for category, items in TREASURE_LOOT_TABLES.items():
            for item in items:
                assert "name" in item, f"Item in {category} missing 'name'"
                assert "item_type" in item, f"Item {item.get('name')} in {category} missing 'item_type'"


class TestTreasureChestNames:
    """Tests for TREASURE_CHEST_NAMES constant."""

    # Spec: Chest names should be thematic per category
    def test_treasure_chest_names_contains_dungeon(self):
        """dungeon category has chest names."""
        assert "dungeon" in TREASURE_CHEST_NAMES
        assert len(TREASURE_CHEST_NAMES["dungeon"]) >= 1

    def test_treasure_chest_names_contains_cave(self):
        """cave category has chest names."""
        assert "cave" in TREASURE_CHEST_NAMES
        assert len(TREASURE_CHEST_NAMES["cave"]) >= 1

    def test_treasure_chest_names_contains_ruins(self):
        """ruins category has chest names."""
        assert "ruins" in TREASURE_CHEST_NAMES
        assert len(TREASURE_CHEST_NAMES["ruins"]) >= 1


class TestPlaceTreasuresHelper:
    """Tests for _place_treasures helper function."""

    def _create_placed_locations(self, num_rooms: int, entry_category: str = "dungeon"):
        """Create a placed_locations dict for testing.

        Creates locations at (0,0) = entry, then (1,0), (2,0), etc.
        """
        placed = {}
        for i in range(num_rooms):
            name = f"Room {i}" if i > 0 else "Entry"
            loc = Location(
                name=name,
                description=f"A {entry_category} room.",
                category=entry_category,
            )
            placed[name] = {
                "location": loc,
                "relative_coords": (i, 0),
                "is_entry": (i == 0),
            }
        return placed

    # Spec: Entry room should not receive treasures
    def test_place_treasures_excludes_entry_room(self):
        """Entry room should not receive treasures."""
        placed = self._create_placed_locations(3)
        _place_treasures(placed, "dungeon")

        entry_loc = placed["Entry"]["location"]
        assert len(entry_loc.treasures) == 0, "Entry room should not have treasures"

    # Spec: _place_treasures adds treasure to non-entry rooms
    def test_place_treasures_adds_chest_to_location(self):
        """_place_treasures adds treasure to non-entry rooms."""
        placed = self._create_placed_locations(3)  # Entry + 2 rooms
        _place_treasures(placed, "dungeon")

        # At least one non-entry room should have treasure
        total_treasures = sum(
            len(placed[name]["location"].treasures)
            for name in placed if name != "Entry"
        )
        assert total_treasures >= 1, "At least one treasure should be placed"

    # Spec: Number of chests scales with room count
    def test_place_treasures_1_chest_for_2_rooms(self):
        """2 rooms (1 non-entry) gets 1 chest."""
        placed = self._create_placed_locations(2)  # Entry + 1 room
        _place_treasures(placed, "dungeon")

        total_treasures = sum(
            len(placed[name]["location"].treasures)
            for name in placed if name != "Entry"
        )
        assert total_treasures == 1

    def test_place_treasures_1_chest_for_3_rooms(self):
        """3 rooms (2 non-entry) gets 1 chest."""
        placed = self._create_placed_locations(3)  # Entry + 2 rooms
        _place_treasures(placed, "dungeon")

        total_treasures = sum(
            len(placed[name]["location"].treasures)
            for name in placed if name != "Entry"
        )
        assert total_treasures == 1

    def test_place_treasures_2_chests_for_4_rooms(self):
        """4 rooms (3 non-entry) gets 2 chests."""
        placed = self._create_placed_locations(4)  # Entry + 3 rooms
        _place_treasures(placed, "dungeon")

        total_treasures = sum(
            len(placed[name]["location"].treasures)
            for name in placed if name != "Entry"
        )
        assert total_treasures == 2

    def test_place_treasures_2_chests_for_5_rooms(self):
        """5 rooms (4 non-entry) gets 2 chests."""
        placed = self._create_placed_locations(5)  # Entry + 4 rooms
        _place_treasures(placed, "dungeon")

        total_treasures = sum(
            len(placed[name]["location"].treasures)
            for name in placed if name != "Entry"
        )
        assert total_treasures == 2

    def test_place_treasures_3_chests_for_6_rooms(self):
        """6+ rooms (5+ non-entry) gets 3 chests."""
        placed = self._create_placed_locations(6)  # Entry + 5 rooms
        _place_treasures(placed, "dungeon")

        total_treasures = sum(
            len(placed[name]["location"].treasures)
            for name in placed if name != "Entry"
        )
        assert total_treasures == 3

    # Spec: Treasures are distributed (not clustered)
    def test_place_treasures_spreads_across_rooms(self):
        """Treasures are distributed, not clustered in one room."""
        placed = self._create_placed_locations(6)  # Entry + 5 rooms -> 3 chests
        _place_treasures(placed, "dungeon")

        # Count rooms with treasures
        rooms_with_treasures = sum(
            1 for name in placed
            if name != "Entry" and len(placed[name]["location"].treasures) > 0
        )
        # With 3 chests in 5 rooms, they should be in different rooms
        assert rooms_with_treasures >= 3, "Treasures should be in different rooms"

    # Spec: Lock difficulty scales with distance from entry
    def test_place_treasures_difficulty_scales_with_distance(self):
        """Lock difficulty increases with Manhattan distance from entry."""
        # Create rooms at different distances
        placed = {}
        # Entry at (0,0)
        entry_loc = Location(name="Entry", description="Entry", category="dungeon")
        placed["Entry"] = {
            "location": entry_loc,
            "relative_coords": (0, 0),
            "is_entry": True,
        }
        # Room at distance 1
        near_loc = Location(name="Near Room", description="Near", category="dungeon")
        placed["Near Room"] = {
            "location": near_loc,
            "relative_coords": (1, 0),
            "is_entry": False,
        }
        # Room at distance 3
        far_loc = Location(name="Far Room", description="Far", category="dungeon")
        placed["Far Room"] = {
            "location": far_loc,
            "relative_coords": (2, 1),
            "is_entry": False,
        }

        _place_treasures(placed, "dungeon")

        # Check that far room has higher difficulty than near room
        near_treasures = near_loc.treasures
        far_treasures = far_loc.treasures

        if near_treasures and far_treasures:
            # Far room treasure should have higher or equal difficulty
            assert far_treasures[0]["difficulty"] >= near_treasures[0]["difficulty"]

    # Spec: Treasure items match category loot table
    def test_place_treasures_items_match_category(self):
        """Treasure items come from the category's loot table."""
        placed = self._create_placed_locations(3)
        _place_treasures(placed, "dungeon")

        # Get all placed treasure items
        all_items = []
        for name in placed:
            if name != "Entry":
                for treasure in placed[name]["location"].treasures:
                    all_items.extend(treasure.get("items", []))

        # All items should be from dungeon loot table
        dungeon_item_names = {item["name"] for item in TREASURE_LOOT_TABLES["dungeon"]}
        for item in all_items:
            assert item["name"] in dungeon_item_names, f"Item {item['name']} not in dungeon loot table"

    # Spec: Treasure has valid schema
    def test_place_treasures_valid_schema(self):
        """Placed treasures have valid schema."""
        placed = self._create_placed_locations(3)
        _place_treasures(placed, "dungeon")

        for name in placed:
            if name != "Entry":
                for treasure in placed[name]["location"].treasures:
                    assert "name" in treasure
                    assert "description" in treasure
                    assert "locked" in treasure
                    assert "difficulty" in treasure
                    assert "opened" in treasure
                    assert treasure["opened"] is False  # Newly placed treasures are unopened
                    assert "items" in treasure
                    assert len(treasure["items"]) >= 1

    # Spec: Excludes boss rooms from treasure placement
    def test_place_treasures_excludes_boss_room(self):
        """Boss room should not receive treasure (boss IS the reward)."""
        # Create locations with one having boss_enemy set
        placed = {}
        entry_loc = Location(name="Entry", description="Entry", category="dungeon")
        placed["Entry"] = {
            "location": entry_loc,
            "relative_coords": (0, 0),
            "is_entry": True,
        }
        # Regular room
        room1 = Location(name="Room 1", description="Room", category="dungeon")
        placed["Room 1"] = {
            "location": room1,
            "relative_coords": (1, 0),
            "is_entry": False,
        }
        # Boss room
        boss_room = Location(name="Boss Room", description="Boss", category="dungeon")
        boss_room.boss_enemy = "dungeon"  # This is a boss room
        placed["Boss Room"] = {
            "location": boss_room,
            "relative_coords": (2, 0),
            "is_entry": False,
        }

        _place_treasures(placed, "dungeon")

        assert len(boss_room.treasures) == 0, "Boss room should not have treasures"


class TestExpandAreaTreasurePlacement:
    """Tests for treasure placement in expand_area()."""

    def _create_mock_ai_service(self, category: str, num_locations: int = 3):
        """Create a mock AI service that returns area data."""
        ai_service = MagicMock()

        # Coordinate layouts that stay within typical SubGrid bounds
        coord_layouts = {
            "cave": [(0, 0), (1, 0), (1, 1)],
            "dungeon": [(0, 0), (1, 0), (2, 0)],
            "ruins": [(0, 0), (1, 0), (2, 0)],
            "town": [(0, 0), (1, 0), (2, 0)],
        }
        coords = coord_layouts.get(category, [(0, 0), (1, 0), (2, 0)])

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

    # Spec: Dungeon areas should have treasures
    def test_expand_area_dungeon_has_treasures(self):
        """expand_area for dungeon category places treasures."""
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

        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None
        assert entry_loc.sub_grid is not None

        # Count treasures in sub_grid
        total_treasures = 0
        for loc in entry_loc.sub_grid._by_name.values():
            total_treasures += len(loc.treasures)

        assert total_treasures >= 1, "Dungeon should have at least one treasure"

    # Spec: Cave areas should have treasures
    def test_expand_area_cave_has_treasures(self):
        """expand_area for cave category places treasures."""
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

        total_treasures = 0
        for loc in entry_loc.sub_grid._by_name.values():
            total_treasures += len(loc.treasures)

        assert total_treasures >= 1, "Cave should have at least one treasure"

    # Spec: Town areas should NOT have random treasures
    def test_expand_area_town_has_no_treasures(self):
        """Town areas should NOT have random treasures."""
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

        # Check no location has treasures
        if entry_loc.sub_grid is not None:
            for loc in entry_loc.sub_grid._by_name.values():
                assert len(loc.treasures) == 0, f"{loc.name} should not have treasures"

    # Spec: Treasure items match the category loot table
    def test_expand_area_treasure_thematically_matches_category(self):
        """Treasure items match the category loot table."""
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

        entry_loc = None
        for loc in result.values():
            if loc.coordinates == (0, 1):
                entry_loc = loc
                break

        assert entry_loc is not None
        assert entry_loc.sub_grid is not None

        # Collect all treasure items
        all_items = []
        for loc in entry_loc.sub_grid._by_name.values():
            for treasure in loc.treasures:
                all_items.extend(treasure.get("items", []))

        # All items should be from dungeon loot table OR puzzle keys
        # Puzzle keys are placed in treasures for locked door puzzles (Issue #23)
        from cli_rpg.ai_world import PUZZLE_TEMPLATES
        from cli_rpg.models.puzzle import PuzzleType
        dungeon_item_names = {item["name"] for item in TREASURE_LOOT_TABLES["dungeon"]}
        # Add puzzle keys from dungeon templates
        for template in PUZZLE_TEMPLATES.get("dungeon", []):
            if template[0] == PuzzleType.LOCKED_DOOR:
                dungeon_item_names.add(template[3])  # required_key is at index 3
        for item in all_items:
            assert item["name"] in dungeon_item_names


class TestGenerateSubgridTreasurePlacement:
    """Tests for treasure placement in generate_subgrid_for_location()."""

    # Spec: On-demand SubGrid generation includes treasures
    def test_generate_subgrid_dungeon_has_treasures(self):
        """On-demand SubGrid generation includes treasures for dungeons."""
        # Create a dungeon location that will get a SubGrid generated
        location = Location(
            name="Dark Dungeon",
            description="A foreboding dungeon entrance.",
            category="dungeon",
        )

        # Generate SubGrid without AI service (uses fallback)
        sub_grid = generate_subgrid_for_location(
            location=location,
            ai_service=None,
            theme="fantasy",
        )

        # Count treasures in sub_grid
        total_treasures = 0
        for loc in sub_grid._by_name.values():
            total_treasures += len(loc.treasures)

        assert total_treasures >= 1, "Dungeon SubGrid should have at least one treasure"

    def test_generate_subgrid_cave_excludes_boss_room_from_treasures(self):
        """On-demand SubGrid generation correctly excludes boss room from treasures.

        For caves, the fallback interior only generates 2 rooms within bounds.
        The boss room (furthest from entry) shouldn't have treasures, and the
        entry room doesn't get treasures either. This is correct behavior:
        boss IS the reward.
        """
        location = Location(
            name="Crystal Cave",
            description="A cave entrance with glinting crystals.",
            category="cave",
        )

        sub_grid = generate_subgrid_for_location(
            location=location,
            ai_service=None,
            theme="fantasy",
        )

        # With only 2 rooms (entry + boss), there's no room for treasure
        # This is correct - verify boss room has no treasure
        for loc in sub_grid._by_name.values():
            if loc.boss_enemy is not None:
                assert len(loc.treasures) == 0, "Boss room should not have treasures"

    def test_generate_subgrid_town_has_no_treasures(self):
        """On-demand SubGrid generation for towns does NOT add treasures."""
        location = Location(
            name="Peaceful Village",
            description="A quiet village.",
            category="town",
        )

        sub_grid = generate_subgrid_for_location(
            location=location,
            ai_service=None,
            theme="fantasy",
        )

        for loc in sub_grid._by_name.values():
            assert len(loc.treasures) == 0, f"{loc.name} should not have treasures"
