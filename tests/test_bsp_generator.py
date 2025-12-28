"""Tests for BSPGenerator procedural dungeon layout generation.

Tests the Binary Space Partitioning generator for dungeons, temples, ruins, tombs,
crypts, monasteries, and shrines.
"""

import pytest

from cli_rpg.procedural_interiors import (
    BSPNode,
    BSPGenerator,
    RoomTemplate,
    RoomType,
    generate_interior_layout,
    CATEGORY_GENERATORS,
)


# =============================================================================
# BSPNode Tests (Tests 1-4 from spec)
# =============================================================================


class TestBSPNodeCreation:
    """Test BSPNode stores x, y, width, height correctly."""

    def test_bsp_node_creation(self):
        """Node stores x, y, width, height correctly."""
        node = BSPNode(x=5, y=10, width=20, height=15)
        assert node.x == 5
        assert node.y == 10
        assert node.width == 20
        assert node.height == 15
        assert node.left is None
        assert node.right is None
        assert node.room is None


class TestBSPNodeSplit:
    """Tests for BSPNode split operations."""

    def test_bsp_node_split_horizontal(self):
        """Horizontal split creates two children."""
        import random

        node = BSPNode(x=0, y=0, width=10, height=20)
        rng = random.Random(42)
        result = node.split(rng, horizontal=True, min_size=4)

        assert result is True
        assert node.left is not None
        assert node.right is not None
        # Horizontal split: children have same width, heights add up
        assert node.left.width == node.width
        assert node.right.width == node.width
        assert node.left.height + node.right.height == node.height
        # Left child starts at same position
        assert node.left.x == node.x
        assert node.left.y == node.y
        # Right child is offset by left height
        assert node.right.x == node.x
        assert node.right.y == node.y + node.left.height

    def test_bsp_node_split_vertical(self):
        """Vertical split creates two children."""
        import random

        node = BSPNode(x=0, y=0, width=20, height=10)
        rng = random.Random(42)
        result = node.split(rng, horizontal=False, min_size=4)

        assert result is True
        assert node.left is not None
        assert node.right is not None
        # Vertical split: children have same height, widths add up
        assert node.left.height == node.height
        assert node.right.height == node.height
        assert node.left.width + node.right.width == node.width
        # Left child starts at same position
        assert node.left.x == node.x
        assert node.left.y == node.y
        # Right child is offset by left width
        assert node.right.x == node.x + node.left.width
        assert node.right.y == node.y

    def test_bsp_node_is_leaf(self):
        """Leaf detection (no children)."""
        import random

        leaf_node = BSPNode(x=0, y=0, width=10, height=10)
        assert leaf_node.is_leaf is True

        # After splitting, node is no longer a leaf
        rng = random.Random(42)
        leaf_node.split(rng, horizontal=True, min_size=4)
        assert leaf_node.is_leaf is False

        # Children are leaves
        assert leaf_node.left.is_leaf is True
        assert leaf_node.right.is_leaf is True


# =============================================================================
# BSPGenerator Tests (Tests 5-14 from spec)
# =============================================================================


class TestBSPGeneratorBasics:
    """Basic tests for BSPGenerator."""

    def test_generator_returns_room_templates(self):
        """generate() returns list[RoomTemplate]."""
        bounds = (0, 6, 0, 6, 0, 0)  # 7x7 single level
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        assert isinstance(result, list)
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

    def test_generator_has_entry_room(self):
        """Layout has exactly one ENTRY room with is_entry=True."""
        bounds = (0, 6, 0, 6, 0, 0)
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        entry_rooms = [r for r in result if r.room_type == RoomType.ENTRY]
        assert len(entry_rooms) == 1
        assert entry_rooms[0].is_entry is True

    def test_entry_room_at_top_level(self):
        """Entry room z-coord equals max_z from bounds."""
        bounds = (0, 6, 0, 6, -2, 0)  # 3 levels deep
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        entry_rooms = [r for r in result if r.room_type == RoomType.ENTRY]
        assert len(entry_rooms) == 1
        # Entry should be at max_z (top level)
        assert entry_rooms[0].coords[2] == 0  # max_z


class TestBSPGeneratorDeterminism:
    """Tests for deterministic generation."""

    def test_generator_deterministic(self):
        """Same seed produces identical output."""
        bounds = (0, 6, 0, 6, 0, 0)

        gen1 = BSPGenerator(bounds=bounds, seed=12345)
        result1 = gen1.generate()

        gen2 = BSPGenerator(bounds=bounds, seed=12345)
        result2 = gen2.generate()

        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.coords == r2.coords
            assert r1.room_type == r2.room_type
            assert r1.connections == r2.connections
            assert r1.is_entry == r2.is_entry

    def test_generator_different_seeds_differ(self):
        """Different seeds produce different layouts."""
        bounds = (0, 10, 0, 10, 0, 0)  # Larger for more variation

        gen1 = BSPGenerator(bounds=bounds, seed=11111)
        result1 = gen1.generate()

        gen2 = BSPGenerator(bounds=bounds, seed=99999)
        result2 = gen2.generate()

        # Layouts should differ in some way (coords, room count, or types)
        coords1 = {r.coords for r in result1}
        coords2 = {r.coords for r in result2}

        # Different seeds should produce different layouts
        # (at least coords or types should differ)
        layouts_differ = coords1 != coords2 or len(result1) != len(result2)
        if not layouts_differ and len(result1) == len(result2):
            types1 = [r.room_type for r in sorted(result1, key=lambda x: x.coords)]
            types2 = [r.room_type for r in sorted(result2, key=lambda x: x.coords)]
            layouts_differ = types1 != types2

        assert layouts_differ, "Different seeds should produce different layouts"


class TestBSPGeneratorBounds:
    """Tests for bounds compliance."""

    def test_rooms_within_bounds(self):
        """All room coords within specified bounds."""
        bounds = (-3, 3, -3, 3, -2, 0)  # Asymmetric bounds
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        for room in result:
            x, y, z = room.coords
            assert min_x <= x <= max_x, f"x={x} out of bounds [{min_x}, {max_x}]"
            assert min_y <= y <= max_y, f"y={y} out of bounds [{min_y}, {max_y}]"
            assert min_z <= z <= max_z, f"z={z} out of bounds [{min_z}, {max_z}]"


class TestBSPGeneratorMultiLevel:
    """Tests for multi-level dungeon support."""

    def test_multi_level_generates_stairs(self):
        """Multi-level bounds produce 'up'/'down' connections."""
        bounds = (0, 6, 0, 6, -2, 0)  # 3 levels
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        all_connections = []
        for room in result:
            all_connections.extend(room.connections)

        # Should have some vertical connections
        vertical = [c for c in all_connections if c in ("up", "down")]
        assert len(vertical) > 0, "Multi-level should have up/down connections"

    def test_boss_room_at_lowest_level(self):
        """BOSS_ROOM placed at min_z."""
        bounds = (0, 10, 0, 10, -3, 0)  # 4 levels deep
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        boss_rooms = [r for r in result if r.room_type == RoomType.BOSS_ROOM]
        assert len(boss_rooms) >= 1, "Should have at least one boss room"

        # Boss room should be at the lowest level
        for boss in boss_rooms:
            assert boss.coords[2] == -3, "Boss room should be at min_z"


class TestBSPGeneratorConnections:
    """Tests for room connections."""

    def test_connections_are_valid_directions(self):
        """All connections are valid (north/south/east/west/up/down)."""
        bounds = (0, 6, 0, 6, -1, 0)
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        valid_directions = {"north", "south", "east", "west", "up", "down"}
        for room in result:
            for conn in room.connections:
                assert conn in valid_directions, f"Invalid connection: {conn}"

    def test_rooms_are_connected(self):
        """All rooms reachable from entry via connections."""
        bounds = (0, 6, 0, 6, 0, 0)
        generator = BSPGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        if len(result) <= 1:
            return  # Single room is trivially connected

        # Build adjacency map
        coord_to_room = {r.coords: r for r in result}

        # Direction offsets
        offsets = {
            "north": (0, 1, 0),
            "south": (0, -1, 0),
            "east": (1, 0, 0),
            "west": (-1, 0, 0),
            "up": (0, 0, 1),
            "down": (0, 0, -1),
        }

        # Find entry room
        entry = next((r for r in result if r.is_entry), result[0])

        # BFS from entry
        visited = {entry.coords}
        queue = [entry.coords]

        while queue:
            current_coords = queue.pop(0)
            current_room = coord_to_room[current_coords]

            for direction in current_room.connections:
                if direction in offsets:
                    dx, dy, dz = offsets[direction]
                    neighbor = (
                        current_coords[0] + dx,
                        current_coords[1] + dy,
                        current_coords[2] + dz,
                    )
                    if neighbor in coord_to_room and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

        assert len(visited) == len(result), (
            f"Not all rooms connected: visited {len(visited)}/{len(result)}"
        )


# =============================================================================
# Integration Tests (Tests 15-17 from spec)
# =============================================================================


class TestBSPIntegration:
    """Integration tests for BSPGenerator with generate_interior_layout."""

    def test_generate_interior_layout_uses_bsp(self):
        """Factory function uses BSPGenerator for 'dungeon'."""
        # Verify mapping exists
        assert CATEGORY_GENERATORS.get("dungeon") == "BSPGenerator"

        bounds = (0, 6, 0, 6, 0, 0)
        result = generate_interior_layout("dungeon", bounds, seed=42)

        # Should return room templates
        assert isinstance(result, list)
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

        # Should have entry room
        entry_rooms = [r for r in result if r.room_type == RoomType.ENTRY]
        assert len(entry_rooms) == 1

    def test_category_dungeon_produces_valid_layout(self):
        """Dungeon category works end-to-end."""
        bounds = (0, 6, 0, 6, -2, 0)
        result = generate_interior_layout("dungeon", bounds, seed=12345)

        # Has entry
        assert any(r.is_entry for r in result)

        # All within bounds
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        for room in result:
            x, y, z = room.coords
            assert min_x <= x <= max_x
            assert min_y <= y <= max_y
            assert min_z <= z <= max_z

    def test_category_temple_produces_valid_layout(self):
        """Temple category works end-to-end."""
        # Temple should also use BSPGenerator
        assert CATEGORY_GENERATORS.get("temple") == "BSPGenerator"

        bounds = (0, 6, 0, 6, 0, 0)
        result = generate_interior_layout("temple", bounds, seed=54321)

        # Has entry
        assert any(r.is_entry for r in result)
        assert len(result) > 0

        # All rooms have valid types
        for room in result:
            assert isinstance(room.room_type, RoomType)
