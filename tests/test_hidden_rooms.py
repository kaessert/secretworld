"""Tests for hidden rooms generated from secret doors.

Tests the integration of secret doors with SubGrid to create actual navigable rooms.
"""
import random
import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid
from cli_rpg.secrets import (
    generate_hidden_room,
    perform_active_search,
    apply_secret_rewards,
)


class TestHiddenRoomGeneration:
    """Test hidden room creation from secret doors."""

    def test_generate_hidden_room_creates_location(self):
        """generate_hidden_room creates a Location in the SubGrid."""
        # Spec: Hidden rooms are placed at empty adjacent coordinates
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry Hall", description="A hall.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")

        assert hidden is not None
        assert hidden.coordinates == (0, 1, 0)
        assert sub_grid.get_by_coordinates(0, 1, 0) == hidden

    def test_generate_hidden_room_fails_when_occupied(self):
        """generate_hidden_room returns None if target cell is occupied."""
        # Spec: Cannot overwrite existing rooms
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry Hall", description="A hall.")
        blocker = Location(name="Other Room", description="Another room.")
        sub_grid.add_location(origin, 0, 0)
        sub_grid.add_location(blocker, 0, 1)

        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")

        assert hidden is None

    def test_generate_hidden_room_fails_out_of_bounds(self):
        """generate_hidden_room returns None if target is out of bounds."""
        # Spec: Rooms must be within SubGrid bounds
        sub_grid = SubGrid(bounds=(0, 0, 0, 0, 0, 0), parent_name="Tiny")
        origin = Location(name="Only Room", description="The only room.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")

        assert hidden is None

    def test_hidden_room_uses_category_templates(self):
        """Hidden rooms use templates matching parent category."""
        # Spec: Rooms have thematic names based on parent category
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Cave")
        origin = Location(name="Cave Entry", description="A cave.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "east", "cave")

        assert hidden is not None
        # Cave templates have specific names
        assert any(
            word in hidden.name
            for word in ["Crystal", "Cavern", "Grotto", "Pool", "Hidden"]
        )

    def test_hidden_room_uses_default_template_for_unknown_category(self):
        """Hidden rooms fall back to default templates for unknown categories."""
        # Spec: Unknown categories use default template
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Unknown")
        origin = Location(name="Entry", description="An entry.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "west", "weird_category")

        assert hidden is not None
        assert any(
            word in hidden.name
            for word in ["Hidden", "Secret", "Concealed"]
        )

    def test_hidden_room_vertical_directions(self):
        """Hidden rooms can be created vertically (up/down)."""
        # Spec: Supports 3D navigation for multi-level dungeons
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, -1, 1), parent_name="Tower")
        origin = Location(name="Ground Floor", description="A floor.")
        sub_grid.add_location(origin, 0, 0, 0)

        hidden_up = generate_hidden_room(origin, sub_grid, "up", "tower")
        assert hidden_up is not None
        assert hidden_up.coordinates == (0, 0, 1)

    def test_hidden_room_may_contain_treasure(self):
        """Hidden rooms can contain treasure secrets."""
        # Spec: 50% chance of treasure in hidden rooms
        # Use fixed seed for deterministic test
        random.seed(42)
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry", description="Entry.")
        sub_grid.add_location(origin, 0, 0)

        # Generate multiple rooms to check treasure chance
        rooms_with_treasure = 0
        for i in range(10):
            test_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
            test_origin = Location(name=f"Entry{i}", description="Entry.")
            test_grid.add_location(test_origin, 0, 0)
            hidden = generate_hidden_room(test_origin, test_grid, "north", "dungeon")
            if hidden and hidden.hidden_secrets:
                rooms_with_treasure += 1

        # Should have some but not all rooms with treasure
        assert rooms_with_treasure > 0  # At least one room should have treasure


class TestHiddenDoorCreatesRoom:
    """Test that discovering hidden_door creates real rooms."""

    def test_search_creates_hidden_room_in_subgrid(self):
        """Discovering hidden_door via search creates navigable room."""
        # Spec: Hidden door discovery creates actual room in SubGrid
        char = Character(
            name="Scout",
            strength=10,
            dexterity=10,
            intelligence=10,
            perception=18,
        )
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        location = Location(
            name="Hall",
            description="A hall.",
            coordinates=(0, 0, 0),
            hidden_secrets=[
                {
                    "type": "hidden_door",
                    "description": "A hidden passage",
                    "threshold": 12,
                    "exit_direction": "north",
                }
            ],
        )
        sub_grid.add_location(location, 0, 0)

        found, message = perform_active_search(char, location, sub_grid)

        assert found
        assert "north" in message.lower()
        # Verify room was actually created
        hidden = sub_grid.get_by_coordinates(0, 1, 0)
        assert hidden is not None

    def test_search_falls_back_to_temporary_exits_outside_subgrid(self):
        """Hidden door adds temporary_exit when not in SubGrid."""
        # Spec: Fallback to cosmetic exits when no SubGrid
        char = Character(
            name="Scout",
            strength=10,
            dexterity=10,
            intelligence=10,
            perception=18,
        )
        location = Location(
            name="Overworld",
            description="Open area.",
            hidden_secrets=[
                {
                    "type": "hidden_door",
                    "description": "A hidden path",
                    "threshold": 12,
                    "exit_direction": "west",
                }
            ],
        )

        found, message = perform_active_search(char, location, sub_grid=None)

        assert found
        assert "west" in location.temporary_exits

    def test_apply_secret_rewards_creates_room_with_subgrid(self):
        """apply_secret_rewards creates room when SubGrid is provided."""
        # Spec: Room creation integrated into reward system
        char = Character(
            name="Scout",
            strength=10,
            dexterity=10,
            intelligence=10,
            perception=15,
        )
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        location = Location(
            name="Room",
            description="A room.",
            coordinates=(0, 0, 0),
            category="dungeon",
        )
        sub_grid.add_location(location, 0, 0)

        secret = {
            "type": "hidden_door",
            "description": "Hidden passage",
            "threshold": 12,
            "exit_direction": "south",
        }

        success, message = apply_secret_rewards(char, location, secret, sub_grid)

        assert success
        # Room should be created to the south
        hidden = sub_grid.get_by_coordinates(0, -1, 0)
        assert hidden is not None
        assert "south" in message.lower()


class TestHiddenRoomNavigation:
    """Test that hidden rooms are navigable after discovery."""

    def test_hidden_room_appears_in_available_directions(self):
        """Hidden room adds new direction to get_available_directions."""
        # Spec: Created room is navigable
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry", description="Entry.", coordinates=(0, 0, 0))
        sub_grid.add_location(origin, 0, 0)

        # Before hidden room
        directions_before = origin.get_available_directions(sub_grid=sub_grid)
        assert "north" not in directions_before

        # Create hidden room
        hidden = generate_hidden_room(origin, sub_grid, "north", "dungeon")
        assert hidden is not None

        # After hidden room
        directions_after = origin.get_available_directions(sub_grid=sub_grid)
        assert "north" in directions_after

    def test_hidden_room_has_parent_set(self):
        """Hidden room has parent_location set correctly."""
        # Spec: Room has correct parent for exit command
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Dungeon")
        origin = Location(name="Entry", description="Entry.")
        sub_grid.add_location(origin, 0, 0)

        hidden = generate_hidden_room(origin, sub_grid, "east", "dungeon")

        assert hidden is not None
        assert hidden.parent_location == "Dungeon"
