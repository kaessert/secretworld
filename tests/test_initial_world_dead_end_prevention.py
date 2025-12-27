"""Tests for initial world generation dead-end prevention.

Spec: Initial world generation must create sufficient exits based on coordinate adjacency
to ensure the "infinite world" principle. Players must never be stuck at game start.
"""

import pytest
from unittest.mock import Mock

from cli_rpg.world import create_default_world, create_world
from cli_rpg.ai_world import create_ai_world


class TestDefaultWorldDeadEndPrevention:
    """Tests ensuring default world has no dead-ends."""

    def test_default_world_starting_location_has_multiple_exits(self):
        """Spec: Starting location must have multiple exit directions."""
        world, starting_location = create_default_world()
        starting_loc = world[starting_location]

        # Use coordinate-based navigation
        exits = starting_loc.get_available_directions(world=world)
        assert len(exits) >= 2, \
            "Starting location must have at least 2 exits"

    def test_default_world_all_exits_are_valid(self):
        """Spec: All coordinate-adjacent locations must exist.

        Note: With coordinate-based navigation, exits are determined by
        adjacent coordinates. Every direction returned by get_available_directions
        must lead to a valid location.
        """
        world, starting_location = create_default_world()

        for name, location in world.items():
            exits = location.get_available_directions(world=world)
            for direction in exits:
                # Verify we can actually reach the target
                offsets = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
                if location.coordinates and direction in offsets:
                    dx, dy = offsets[direction]
                    target = (location.coordinates[0] + dx, location.coordinates[1] + dy)
                    # Find location at target coordinates
                    target_loc = next(
                        (loc for loc in world.values() if loc.coordinates == target),
                        None
                    )
                    assert target_loc is not None, (
                        f"Location '{name}' has exit '{direction}' but no location "
                        f"exists at {target}"
                    )


class TestAIWorldDeadEndPrevention:
    """Tests ensuring AI-generated world has no dead-ends."""

    @pytest.fixture
    def mock_ai_service_minimal(self):
        """Mock AI that returns locations with basic metadata."""
        service = Mock()
        call_count = [0]

        def generate_location_side_effect(theme, context_locations, source_location, direction):
            call_count[0] += 1

            if source_location is None:
                # Starting location
                return {
                    "name": "Central Hub",
                    "description": "The central hub.",
                    # No connections - coordinate-based navigation
                }
            else:
                # Generated location
                return {
                    "name": f"Location {call_count[0]}",
                    "description": "A generated location.",
                    # No connections - coordinate-based navigation
                }

        service.generate_location.side_effect = generate_location_side_effect
        return service

    def test_ai_world_starting_location_has_multiple_exits(self, mock_ai_service_minimal):
        """Spec: AI starting location must have multiple coordinate-adjacent locations."""
        world, starting_location = create_ai_world(
            mock_ai_service_minimal, theme="fantasy", initial_size=3
        )

        starting_loc = world[starting_location]
        # Use coordinate-based navigation
        exits = starting_loc.get_available_directions(world=world)
        assert len(exits) >= 2, \
            "AI starting location must have at least 2 exits"

    def test_ai_world_generated_locations_have_at_least_one_exit(self, mock_ai_service_minimal):
        """Spec: Every AI-generated location must have at least 1 adjacent location.

        Note: In coordinate-based navigation, edge/frontier locations naturally have
        fewer adjacent locations. The key requirement is that no location is completely
        isolated (0 exits).
        """
        world, starting_location = create_ai_world(
            mock_ai_service_minimal, theme="fantasy", initial_size=3
        )

        for name, location in world.items():
            # Use coordinate-based navigation
            exits = location.get_available_directions(world=world)
            assert len(exits) >= 1, \
                f"Location '{name}' is completely isolated with 0 exits"

    def test_ai_world_has_frontier_for_expansion(self, mock_ai_service_minimal):
        """Spec: AI world must have frontier locations that can be expanded.

        The infinite world principle requires that there are coordinates where
        new locations can be generated. We verify this by checking that at least
        one location has empty adjacent coordinates (potential for expansion).
        """
        world, starting_location = create_ai_world(
            mock_ai_service_minimal, theme="fantasy", initial_size=3
        )

        # Collect all coordinates that have locations
        occupied_coords = {loc.coordinates for loc in world.values() if loc.coordinates}

        # Check if there's room to expand (at least one location has empty adjacent coord)
        has_expansion_potential = False
        offsets = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}

        for location in world.values():
            if location.coordinates:
                for dx, dy in offsets.values():
                    adjacent = (location.coordinates[0] + dx, location.coordinates[1] + dy)
                    if adjacent not in occupied_coords:
                        has_expansion_potential = True
                        break
            if has_expansion_potential:
                break

        assert has_expansion_potential, \
            "AI world has no frontier for expansion (all adjacent coordinates occupied)"


class TestCreateWorldDeadEndPrevention:
    """Tests for create_world() dead-end prevention."""

    def test_create_world_without_ai_all_exits_are_valid(self):
        """Spec: Default world via create_world() has valid coordinate adjacency.

        Note: With coordinate-based navigation, all returned exits must
        lead to existing locations.
        """
        world, starting_location = create_world(ai_service=None)

        for name, location in world.items():
            exits = location.get_available_directions(world=world)
            for direction in exits:
                # Verify we can actually reach the target
                offsets = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
                if location.coordinates and direction in offsets:
                    dx, dy = offsets[direction]
                    target = (location.coordinates[0] + dx, location.coordinates[1] + dy)
                    target_loc = next(
                        (loc for loc in world.values() if loc.coordinates == target),
                        None
                    )
                    assert target_loc is not None, (
                        f"Location '{name}' has exit '{direction}' but no location "
                        f"exists at {target}"
                    )

    def test_create_world_starting_location_expandable(self):
        """Spec: Starting location must be expandable in multiple directions."""
        world, starting_location = create_world(ai_service=None)
        starting_loc = world[starting_location]

        # Starting location should have paths to explore via coordinate adjacency
        exits = starting_loc.get_available_directions(world=world)
        assert len(exits) >= 2, \
            "Starting location must provide multiple exploration paths"
