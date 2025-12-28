"""Tests for procedural_interiors.py foundational data structures."""

import pytest

from cli_rpg.procedural_interiors import (
    RoomType,
    RoomTemplate,
    CATEGORY_GENERATORS,
    generate_interior_layout,
)
from cli_rpg.world_tiles import ENTERABLE_CATEGORIES


class TestRoomType:
    """Test RoomType enum values exist."""

    # Spec: RoomType Enum - Room classifications for procedural layouts
    def test_room_type_entry_exists(self):
        """Verify ENTRY room type exists."""
        assert RoomType.ENTRY is not None

    def test_room_type_corridor_exists(self):
        """Verify CORRIDOR room type exists."""
        assert RoomType.CORRIDOR is not None

    def test_room_type_chamber_exists(self):
        """Verify CHAMBER room type exists."""
        assert RoomType.CHAMBER is not None

    def test_room_type_boss_room_exists(self):
        """Verify BOSS_ROOM room type exists."""
        assert RoomType.BOSS_ROOM is not None

    def test_room_type_treasure_exists(self):
        """Verify TREASURE room type exists."""
        assert RoomType.TREASURE is not None

    def test_room_type_puzzle_exists(self):
        """Verify PUZZLE room type exists."""
        assert RoomType.PUZZLE is not None

    def test_room_type_has_exactly_six_values(self):
        """Verify RoomType has exactly 6 members."""
        assert len(RoomType) == 6


class TestRoomTemplate:
    """Test RoomTemplate dataclass creation and defaults."""

    # Spec: RoomTemplate Dataclass - Procedural room blueprint
    def test_room_template_creation_with_required_fields(self):
        """Verify RoomTemplate can be created with required fields."""
        template = RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.CHAMBER,
            connections=["north", "south"],
        )
        assert template.coords == (0, 0, 0)
        assert template.room_type == RoomType.CHAMBER
        assert template.connections == ["north", "south"]

    def test_room_template_default_is_entry_false(self):
        """Verify is_entry defaults to False."""
        template = RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.CHAMBER,
            connections=[],
        )
        assert template.is_entry is False

    def test_room_template_default_suggested_hazards_empty(self):
        """Verify suggested_hazards defaults to empty list."""
        template = RoomTemplate(
            coords=(0, 0, 0),
            room_type=RoomType.CHAMBER,
            connections=[],
        )
        assert template.suggested_hazards == []

    def test_room_template_with_all_fields(self):
        """Verify RoomTemplate accepts all fields including optional ones."""
        template = RoomTemplate(
            coords=(1, 2, -1),
            room_type=RoomType.BOSS_ROOM,
            connections=["north", "east", "down"],
            is_entry=True,
            suggested_hazards=["poison_gas", "darkness"],
        )
        assert template.coords == (1, 2, -1)
        assert template.room_type == RoomType.BOSS_ROOM
        assert template.connections == ["north", "east", "down"]
        assert template.is_entry is True
        assert template.suggested_hazards == ["poison_gas", "darkness"]

    def test_room_template_3d_coordinates(self):
        """Verify coords supports 3D positions for multi-level dungeons."""
        # Dungeons extend downward (z < 0)
        dungeon_room = RoomTemplate(
            coords=(0, 0, -3),
            room_type=RoomType.TREASURE,
            connections=["up"],
        )
        assert dungeon_room.coords[2] == -3

        # Towers extend upward (z > 0)
        tower_room = RoomTemplate(
            coords=(0, 0, 5),
            room_type=RoomType.CHAMBER,
            connections=["down"],
        )
        assert tower_room.coords[2] == 5


class TestCategoryGenerators:
    """Test CATEGORY_GENERATORS mapping covers all enterable categories."""

    # Spec: Category Mapping - Maps categories to generator types
    def test_all_enterable_categories_mapped(self):
        """Verify every ENTERABLE_CATEGORY has a generator mapping."""
        for category in ENTERABLE_CATEGORIES:
            assert category in CATEGORY_GENERATORS, (
                f"Missing generator mapping for category: {category}"
            )

    def test_generator_values_are_strings(self):
        """Verify all generator mappings are string identifiers."""
        for category, generator in CATEGORY_GENERATORS.items():
            assert isinstance(generator, str), (
                f"Generator for {category} should be string, got {type(generator)}"
            )

    def test_expected_generator_types_exist(self):
        """Verify expected generator types are used in mappings."""
        generator_types = set(CATEGORY_GENERATORS.values())
        # At minimum, we expect BSP for dungeons and cellular automata for caves
        assert "BSPGenerator" in generator_types
        assert "CellularAutomataGenerator" in generator_types


class TestGenerateInteriorLayout:
    """Test generate_interior_layout factory function."""

    # Spec: Factory Function - Entry point for procedural generation
    def test_returns_list_of_room_templates(self):
        """Verify generate_interior_layout returns list of RoomTemplate."""
        bounds = (-3, 3, -3, 3, -2, 0)  # Example 7x7x3 dungeon bounds
        result = generate_interior_layout("dungeon", bounds, seed=42)

        assert isinstance(result, list)
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

    def test_layout_has_at_least_one_entry_point(self):
        """Verify generated layout includes at least one entry room."""
        bounds = (-3, 3, -3, 3, -2, 0)
        result = generate_interior_layout("dungeon", bounds, seed=42)

        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) >= 1

    def test_determinism_same_seed_same_output(self):
        """Verify same seed produces identical layout."""
        bounds = (-3, 3, -3, 3, -2, 0)
        seed = 12345

        result1 = generate_interior_layout("dungeon", bounds, seed=seed)
        result2 = generate_interior_layout("dungeon", bounds, seed=seed)

        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.coords == r2.coords
            assert r1.room_type == r2.room_type
            assert r1.connections == r2.connections
            assert r1.is_entry == r2.is_entry
            assert r1.suggested_hazards == r2.suggested_hazards

    def test_determinism_different_seed_different_output(self):
        """Verify different seeds produce different layouts."""
        bounds = (-3, 3, -3, 3, -2, 0)

        result1 = generate_interior_layout("dungeon", bounds, seed=111)
        result2 = generate_interior_layout("dungeon", bounds, seed=222)

        # Different seeds should generally produce different layouts
        # (though not guaranteed, very unlikely to be identical)
        coords1 = [r.coords for r in result1]
        coords2 = [r.coords for r in result2]
        assert coords1 != coords2 or len(result1) != len(result2)

    def test_works_with_all_enterable_categories(self):
        """Verify generate_interior_layout handles all enterable categories."""
        bounds = (-1, 1, -1, 1, 0, 0)  # Small 3x3 bounds for quick test

        for category in ENTERABLE_CATEGORIES:
            result = generate_interior_layout(category, bounds, seed=42)
            assert isinstance(result, list)
            # Should return at least an entry point
            assert len(result) >= 1
