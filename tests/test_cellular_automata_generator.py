"""Tests for CellularAutomataGenerator in procedural_interiors.py.

These tests verify the cellular automata algorithm for cave/mine layouts.
"""

import pytest

from cli_rpg.procedural_interiors import (
    CellularAutomataGenerator,
    RoomType,
    RoomTemplate,
    CATEGORY_GENERATORS,
    generate_interior_layout,
)


class TestCellularAutomataGeneratorCore:
    """Core algorithm tests for CellularAutomataGenerator."""

    # Spec: generate() returns list[RoomTemplate]
    def test_generator_returns_room_templates(self):
        """Verify generate() returns a list of RoomTemplate objects."""
        bounds = (-1, 1, -1, 1, 0, 0)  # 3x3 single level
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        assert isinstance(result, list)
        assert len(result) > 0
        for room in result:
            assert isinstance(room, RoomTemplate)

    # Spec: Layout has exactly one ENTRY room with is_entry=True
    def test_generator_has_entry_room(self):
        """Verify layout has exactly one ENTRY room with is_entry=True."""
        bounds = (-1, 1, -1, 1, 0, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) == 1
        assert entry_rooms[0].room_type == RoomType.ENTRY

    # Spec: Entry room z-coord equals max_z from bounds
    def test_entry_room_at_top_level(self):
        """Verify entry room is at max_z level."""
        bounds = (-1, 1, -1, 1, -2, 0)  # Multi-level
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        entry_rooms = [r for r in result if r.is_entry]
        assert len(entry_rooms) == 1
        assert entry_rooms[0].coords[2] == 0  # max_z

    # Spec: Same seed produces identical output
    def test_generator_deterministic(self):
        """Verify same seed produces identical layout."""
        bounds = (-2, 2, -2, 2, 0, 0)
        seed = 12345

        gen1 = CellularAutomataGenerator(bounds=bounds, seed=seed)
        gen2 = CellularAutomataGenerator(bounds=bounds, seed=seed)
        result1 = gen1.generate()
        result2 = gen2.generate()

        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.coords == r2.coords
            assert r1.room_type == r2.room_type
            assert r1.connections == r2.connections
            assert r1.is_entry == r2.is_entry

    # Spec: Different seeds produce different layouts
    def test_generator_different_seeds_differ(self):
        """Verify different seeds produce different layouts."""
        bounds = (-6, 6, -6, 6, 0, 0)  # 13x13 for variety (enough for cellular automata)

        gen1 = CellularAutomataGenerator(bounds=bounds, seed=111)
        gen2 = CellularAutomataGenerator(bounds=bounds, seed=222)
        result1 = gen1.generate()
        result2 = gen2.generate()

        # Collect coordinates to compare
        coords1 = set(r.coords for r in result1)
        coords2 = set(r.coords for r in result2)

        # Different seeds should generally produce different layouts
        assert coords1 != coords2 or len(result1) != len(result2)

    # Spec: All room coords within specified bounds
    def test_rooms_within_bounds(self):
        """Verify all rooms have coordinates within bounds."""
        bounds = (-2, 2, -2, 2, -1, 0)
        min_x, max_x, min_y, max_y, min_z, max_z = bounds

        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        for room in result:
            x, y, z = room.coords
            assert min_x <= x <= max_x, f"x={x} out of bounds [{min_x}, {max_x}]"
            assert min_y <= y <= max_y, f"y={y} out of bounds [{min_y}, {max_y}]"
            assert min_z <= z <= max_z, f"z={z} out of bounds [{min_z}, {max_z}]"


class TestCellularAutomataCaveLayout:
    """Cave-specific layout tests."""

    # Spec: All rooms reachable from entry (flood fill works)
    def test_all_rooms_connected(self):
        """Verify all rooms are reachable from entry room."""
        bounds = (-3, 3, -3, 3, 0, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        if len(result) <= 1:
            return  # Trivial case, nothing to check

        # Build adjacency from connections
        coord_to_room = {r.coords: r for r in result}

        direction_offsets = {
            "north": (0, 1, 0),
            "south": (0, -1, 0),
            "east": (1, 0, 0),
            "west": (-1, 0, 0),
            "up": (0, 0, 1),
            "down": (0, 0, -1),
        }

        # Find entry room
        entry_room = next((r for r in result if r.is_entry), result[0])

        # BFS to find all reachable rooms
        visited = set()
        queue = [entry_room.coords]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            room = coord_to_room.get(current)
            if not room:
                continue

            for direction in room.connections:
                if direction in direction_offsets:
                    dx, dy, dz = direction_offsets[direction]
                    neighbor = (current[0] + dx, current[1] + dy, current[2] + dz)
                    if neighbor in coord_to_room and neighbor not in visited:
                        queue.append(neighbor)

        # All rooms should be reachable
        all_coords = set(r.coords for r in result)
        assert visited == all_coords, f"Unreachable rooms: {all_coords - visited}"

    # Spec: Layout has irregular shape (not grid-aligned)
    def test_organic_layout_not_rectangular(self):
        """Verify layout has organic, non-rectangular shape."""
        bounds = (-4, 4, -4, 4, 0, 0)  # 9x9 for clear organic shapes
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        # Get unique x and y values
        x_coords = sorted(set(r.coords[0] for r in result))
        y_coords = sorted(set(r.coords[1] for r in result))

        # If it were a perfect rectangle, every x,y combination would exist
        if len(x_coords) > 1 and len(y_coords) > 1:
            # Count actual rooms vs perfect rectangle rooms
            actual_count = len(result)
            perfect_rect_count = len(x_coords) * len(y_coords)

            # Organic shapes should not fill the bounding rectangle perfectly
            assert actual_count < perfect_rect_count, (
                "Layout appears to be a perfect rectangle - not organic"
            )

    # Spec: Connections reflect actual adjacent rooms
    def test_connections_based_on_adjacency(self):
        """Verify connections reflect actual adjacent rooms."""
        bounds = (-2, 2, -2, 2, 0, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        coord_to_room = {r.coords: r for r in result}
        direction_offsets = {
            "north": (0, 1, 0),
            "south": (0, -1, 0),
            "east": (1, 0, 0),
            "west": (-1, 0, 0),
            "up": (0, 0, 1),
            "down": (0, 0, -1),
        }

        for room in result:
            for direction in room.connections:
                if direction in direction_offsets:
                    dx, dy, dz = direction_offsets[direction]
                    neighbor_coord = (
                        room.coords[0] + dx,
                        room.coords[1] + dy,
                        room.coords[2] + dz,
                    )
                    # Every connection should point to an existing room
                    assert neighbor_coord in coord_to_room, (
                        f"Room at {room.coords} has '{direction}' connection "
                        f"but no room exists at {neighbor_coord}"
                    )

    # Spec: Caves have dead-end rooms (1 connection)
    def test_dead_ends_exist(self):
        """Verify caves have dead-end rooms with only 1 connection."""
        bounds = (-3, 3, -3, 3, 0, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        dead_ends = [r for r in result if len(r.connections) == 1]
        # Organic caves should have dead ends unless very small
        if len(result) > 3:
            assert len(dead_ends) >= 1, "Expected at least one dead end in organic cave"


class TestCellularAutomataMultiLevel:
    """Multi-level cave tests."""

    # Spec: Multi-level bounds produce "up"/"down" connections
    def test_multi_level_generates_stairs(self):
        """Verify multi-level caves have up/down connections."""
        bounds = (-2, 2, -2, 2, -2, 0)  # 3 levels
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        # Check for up/down connections
        has_up = any("up" in r.connections for r in result)
        has_down = any("down" in r.connections for r in result)

        # Multi-level should have vertical connections
        assert has_up or has_down, "Multi-level cave should have vertical connections"

    # Spec: BOSS_ROOM placed at min_z
    def test_boss_room_at_deepest_level(self):
        """Verify BOSS_ROOM is at the deepest z-level."""
        bounds = (-2, 2, -2, 2, -2, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        boss_rooms = [r for r in result if r.room_type == RoomType.BOSS_ROOM]
        if boss_rooms:
            # Boss should be at min_z (-2)
            assert boss_rooms[0].coords[2] == -2


class TestCellularAutomataRoomTypes:
    """Room type assignment tests."""

    # Spec: TREASURE rooms have 1-2 connections
    def test_treasure_rooms_at_dead_ends(self):
        """Verify TREASURE rooms are placed at dead ends (1-2 connections)."""
        bounds = (-3, 3, -3, 3, 0, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        treasure_rooms = [r for r in result if r.room_type == RoomType.TREASURE]
        for room in treasure_rooms:
            assert len(room.connections) <= 2, (
                f"TREASURE room at {room.coords} has {len(room.connections)} connections"
            )

    # Spec: All connections are valid directions
    def test_connections_are_valid_directions(self):
        """Verify all connections are valid direction strings."""
        valid_directions = {"north", "south", "east", "west", "up", "down"}

        bounds = (-2, 2, -2, 2, -1, 0)
        generator = CellularAutomataGenerator(bounds=bounds, seed=42)
        result = generator.generate()

        for room in result:
            for conn in room.connections:
                assert conn in valid_directions, (
                    f"Invalid connection '{conn}' in room at {room.coords}"
                )


class TestCellularAutomataIntegration:
    """Integration tests with generate_interior_layout factory."""

    # Spec: Factory uses CellularAutomataGenerator for "cave"
    def test_generate_interior_layout_uses_cellular(self):
        """Verify factory maps 'cave' to CellularAutomataGenerator."""
        assert CATEGORY_GENERATORS["cave"] == "CellularAutomataGenerator"
        assert CATEGORY_GENERATORS["mine"] == "CellularAutomataGenerator"

    # Spec: Cave category works end-to-end
    def test_category_cave_produces_valid_layout(self):
        """Verify generate_interior_layout works for 'cave' category."""
        bounds = (-1, 1, -1, 1, 0, 0)
        result = generate_interior_layout("cave", bounds, seed=42)

        assert isinstance(result, list)
        assert len(result) > 0
        assert any(r.is_entry for r in result)

    # Spec: Mine category works end-to-end
    def test_category_mine_produces_valid_layout(self):
        """Verify generate_interior_layout works for 'mine' category."""
        bounds = (-1, 1, -1, 1, 0, 0)
        result = generate_interior_layout("mine", bounds, seed=42)

        assert isinstance(result, list)
        assert len(result) > 0
        assert any(r.is_entry for r in result)


class TestCellularAutomataConstants:
    """Test class constants."""

    def test_initial_fill_probability_reasonable(self):
        """Verify INITIAL_FILL_PROBABILITY is between 0.4 and 0.6."""
        assert 0.4 <= CellularAutomataGenerator.INITIAL_FILL_PROBABILITY <= 0.6

    def test_automata_iterations_reasonable(self):
        """Verify AUTOMATA_ITERATIONS is between 3 and 6."""
        assert 3 <= CellularAutomataGenerator.AUTOMATA_ITERATIONS <= 6

    def test_birth_threshold_reasonable(self):
        """Verify BIRTH_THRESHOLD is 4-6 (standard 4-5 rule)."""
        assert 4 <= CellularAutomataGenerator.BIRTH_THRESHOLD <= 6

    def test_death_threshold_reasonable(self):
        """Verify DEATH_THRESHOLD is 3-5 (standard 4-5 rule)."""
        assert 3 <= CellularAutomataGenerator.DEATH_THRESHOLD <= 5
