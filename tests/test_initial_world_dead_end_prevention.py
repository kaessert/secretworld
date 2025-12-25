"""Tests for initial world generation dead-end prevention.

Spec: Initial world generation must create sufficient exits and dangling connections
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

        assert len(starting_loc.connections) >= 2, \
            "Starting location must have at least 2 exits"

    def test_default_world_all_exits_are_valid(self):
        """Spec: All exits must point to existing locations (no dangling exits).

        Note: This test replaces previous tests that required dangling exits.
        Dangling exits cause "Destination 'X' not found in world" errors which
        appear as bugs to users. The default world without AI should have a
        complete, navigable set of locations.
        """
        world, starting_location = create_default_world()

        for name, location in world.items():
            for direction, destination in location.connections.items():
                assert destination in world, (
                    f"Location '{name}' has invalid exit '{direction}' to "
                    f"non-existent '{destination}'"
                )


class TestAIWorldDeadEndPrevention:
    """Tests ensuring AI-generated world has no dead-ends."""

    @pytest.fixture
    def mock_ai_service_minimal(self):
        """Mock AI that returns locations with only back-connections."""
        service = Mock()
        call_count = [0]

        def generate_location_side_effect(theme, context_locations, source_location, direction):
            call_count[0] += 1
            opposites = {
                "north": "south", "south": "north",
                "east": "west", "west": "east",
                "up": "down", "down": "up"
            }

            if source_location is None:
                # Starting location - only back connection to next location
                return {
                    "name": "Central Hub",
                    "description": "The central hub.",
                    "connections": {"north": "North Wing"}  # Only one exit
                }
            else:
                # Generated location - only back connection
                opposite = opposites.get(direction, "south")
                return {
                    "name": f"Location {call_count[0]}",
                    "description": "A generated location.",
                    "connections": {opposite: source_location}  # Only back
                }

        service.generate_location.side_effect = generate_location_side_effect
        return service

    def test_ai_world_starting_location_has_multiple_exits(self, mock_ai_service_minimal):
        """Spec: AI starting location must have multiple exits."""
        world, starting_location = create_ai_world(
            mock_ai_service_minimal, theme="fantasy", initial_size=3
        )

        starting_loc = world[starting_location]
        assert len(starting_loc.connections) >= 2, \
            "AI starting location must have at least 2 exits"

    def test_ai_world_generated_locations_have_forward_exits(self, mock_ai_service_minimal):
        """Spec: Every AI-generated location must have forward exit for expansion."""
        world, starting_location = create_ai_world(
            mock_ai_service_minimal, theme="fantasy", initial_size=3
        )

        for name, location in world.items():
            # Every location needs at least 2 connections (or 1 if it's connected to multiple)
            assert len(location.connections) >= 2, \
                f"Location '{name}' must have at least 2 exits (back + dangling)"

    def test_ai_world_no_isolated_dead_ends(self, mock_ai_service_minimal):
        """Spec: No location should be a dead-end with only one exit."""
        world, starting_location = create_ai_world(
            mock_ai_service_minimal, theme="fantasy", initial_size=3
        )

        for name, location in world.items():
            exits = len(location.connections)
            assert exits >= 2, \
                f"Location '{name}' is a dead-end with only {exits} exit(s)"


class TestCreateWorldDeadEndPrevention:
    """Tests for create_world() dead-end prevention."""

    def test_create_world_without_ai_all_exits_are_valid(self):
        """Spec: Default world via create_world() has no dangling exits.

        Note: This test replaces the previous test that required >= 2 connections.
        Without AI service, dangling exits cause errors. All exits must point
        to valid locations.
        """
        world, starting_location = create_world(ai_service=None)

        for name, location in world.items():
            for direction, destination in location.connections.items():
                assert destination in world, (
                    f"Location '{name}' has invalid exit '{direction}' to "
                    f"non-existent '{destination}'"
                )

    def test_create_world_starting_location_expandable(self):
        """Spec: Starting location must be expandable in multiple directions."""
        world, starting_location = create_world(ai_service=None)
        starting_loc = world[starting_location]

        # Starting location should have paths to explore
        assert len(starting_loc.connections) >= 2, \
            "Starting location must provide multiple exploration paths"
