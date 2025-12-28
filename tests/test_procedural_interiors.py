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


class TestGridSettlementGenerator:
    """Tests for GridSettlementGenerator for town/city layouts.

    Spec: Grid-based generator for settlement interiors using orthogonal
    street layouts with buildings along streets.
    """

    def test_generator_exists(self):
        """GridSettlementGenerator class is importable."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        assert GridSettlementGenerator is not None

    def test_implements_protocol(self):
        """GridSettlementGenerator follows GeneratorProtocol."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        bounds = (-5, 5, -5, 5, 0, 0)  # town size
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert isinstance(result, list)

    def test_returns_room_templates(self):
        """generate() returns list of RoomTemplate."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator, RoomTemplate

        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

    def test_has_entry_room(self):
        """Generated layout includes at least one entry room."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator, RoomType

        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) >= 1

    def test_entry_at_top_z_level(self):
        """Entry room is at z=0 (top level for settlements)."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        entry_rooms = [r for r in result if r.is_entry]
        assert all(r.coords[2] == 0 for r in entry_rooms)

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical layout."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        bounds = (-5, 5, -5, 5, 0, 0)
        gen1 = GridSettlementGenerator(bounds=bounds, seed=12345)
        gen2 = GridSettlementGenerator(bounds=bounds, seed=12345)
        result1 = gen1.generate()
        result2 = gen2.generate()
        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.coords == r2.coords
            assert r1.room_type == r2.room_type

    def test_different_seed_different_layout(self):
        """Different seeds produce different layouts."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        bounds = (-5, 5, -5, 5, 0, 0)
        gen1 = GridSettlementGenerator(bounds=bounds, seed=111)
        gen2 = GridSettlementGenerator(bounds=bounds, seed=222)
        result1 = gen1.generate()
        result2 = gen2.generate()
        coords1 = [r.coords for r in result1]
        coords2 = [r.coords for r in result2]
        # Very unlikely to be identical with different seeds
        assert coords1 != coords2 or len(result1) != len(result2)

    def test_has_connected_rooms(self):
        """Rooms have connections to adjacent rooms."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        # At least some rooms should have connections
        rooms_with_connections = [r for r in result if len(r.connections) > 0]
        assert len(rooms_with_connections) > 0

    def test_grid_pattern_has_corridors(self):
        """Grid layout produces CORRIDOR rooms (streets/intersections)."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator, RoomType

        bounds = (-5, 5, -5, 5, 0, 0)
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        corridors = [r for r in result if r.room_type == RoomType.CORRIDOR]
        # Grid should have some corridor/street tiles
        assert len(corridors) > 0

    def test_small_bounds_still_works(self):
        """Generator handles small bounds (village-sized)."""
        from cli_rpg.procedural_interiors import GridSettlementGenerator

        bounds = (-1, 1, -1, 1, 0, 0)  # 3x3
        gen = GridSettlementGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert len(result) >= 1  # At least entry room


class TestTowerGenerator:
    """Tests for TowerGenerator for vertical tower layouts.

    Spec: TowerGenerator generates vertical layouts for tower-type locations:
    - Extends upward (z > 0), opposite of dungeon behavior
    - Entry at ground level (z=0), boss/treasure at top (z=max)
    - Each floor is a single room connected by stairs (up/down)
    - Room types: ENTRY at z=0, CHAMBER for middle floors, BOSS_ROOM at top
    - 30% chance for treasure room on non-boss dead-end floors
    """

    def test_generator_exists(self):
        """TowerGenerator class is importable."""
        from cli_rpg.procedural_interiors import TowerGenerator

        assert TowerGenerator is not None

    def test_implements_protocol(self):
        """TowerGenerator follows GeneratorProtocol."""
        from cli_rpg.procedural_interiors import TowerGenerator

        # Tower bounds: 3x3 horizontal, z=0 to z=4 vertical
        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert isinstance(result, list)

    def test_returns_room_templates(self):
        """generate() returns list of RoomTemplate."""
        from cli_rpg.procedural_interiors import TowerGenerator, RoomTemplate

        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

    def test_has_entry_room(self):
        """Generated layout includes at least one entry room."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) >= 1

    def test_entry_at_ground_level(self):
        """Entry room is at z=0 (ground level)."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) >= 1
        # Entry must be at z=0 (ground level)
        assert all(r.coords[2] == 0 for r in entry_rooms)

    def test_boss_at_top_level(self):
        """BOSS_ROOM is at z=max_z (top level)."""
        from cli_rpg.procedural_interiors import TowerGenerator, RoomType

        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        boss_rooms = [r for r in result if r.room_type == RoomType.BOSS_ROOM]
        assert len(boss_rooms) >= 1
        # Boss room must be at max_z (top floor)
        assert all(r.coords[2] == 4 for r in boss_rooms)

    def test_extends_upward(self):
        """Rooms span z=0 to z=max_z (positive z only)."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        z_values = {r.coords[2] for r in result}
        # Should have rooms at multiple z levels
        assert min(z_values) == 0  # Ground floor
        assert max(z_values) == 4  # Top floor
        # All z values should be non-negative
        assert all(z >= 0 for z in z_values)

    def test_has_vertical_connections(self):
        """Floors are connected with up/down stairs."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 4)
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        # Find rooms with up/down connections
        rooms_with_up = [r for r in result if "up" in r.connections]
        rooms_with_down = [r for r in result if "down" in r.connections]
        # With 5 floors, we need up/down connections
        assert len(rooms_with_up) > 0
        assert len(rooms_with_down) > 0

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical layout."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 4)
        gen1 = TowerGenerator(bounds=bounds, seed=12345)
        gen2 = TowerGenerator(bounds=bounds, seed=12345)
        result1 = gen1.generate()
        result2 = gen2.generate()
        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.coords == r2.coords
            assert r1.room_type == r2.room_type

    def test_different_seed_different_layout(self):
        """Different seeds produce different layouts."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 4)
        gen1 = TowerGenerator(bounds=bounds, seed=111)
        gen2 = TowerGenerator(bounds=bounds, seed=222)
        result1 = gen1.generate()
        result2 = gen2.generate()
        # May differ in room types, positions, or count (due to treasure room randomness)
        room_types1 = [r.room_type for r in result1]
        room_types2 = [r.room_type for r in result2]
        coords1 = [r.coords for r in result1]
        coords2 = [r.coords for r in result2]
        # Either room counts, types, or coords should differ
        assert (
            room_types1 != room_types2
            or len(result1) != len(result2)
            or coords1 != coords2
        )

    def test_small_bounds_works(self):
        """Generator handles minimal 3x3x4 bounds."""
        from cli_rpg.procedural_interiors import TowerGenerator

        bounds = (-1, 1, -1, 1, 0, 3)  # 3x3 horizontal, 4 floors
        gen = TowerGenerator(bounds=bounds, seed=42)
        result = gen.generate()
        # Should have at least entry + boss rooms
        assert len(result) >= 2
