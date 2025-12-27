"""Tests for enter command entry point restriction.

Spec:
- When a location has a sub_grid, only the entry_point should be shown in "Enter:" line
- The `enter` command should only allow entering the entry_point location
- Legacy sub_locations (without sub_grid) should still show all sub-locations
"""

import pytest

from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character
from cli_rpg.world_grid import SubGrid


def make_test_character() -> Character:
    """Create a test character."""
    return Character(
        name="Test Hero",
        strength=10,
        dexterity=10,
        intelligence=10,
        perception=10,
        charisma=10,
        level=1,
        gold=100,
    )


def make_overworld_with_sub_grid() -> tuple[Location, SubGrid]:
    """Create an overworld location with a sub_grid containing multiple rooms.

    Creates:
    - Entry Hall (entry point, exit point) at (0, 0)
    - Council Chamber (interior room) at (1, 0)
    - Treasury (interior room) at (0, 1)
    """
    # Create sub-locations
    entry_hall = Location(
        name="Entry Hall",
        description="The main entrance to the castle.",
        is_exit_point=True,
    )
    council_chamber = Location(
        name="Council Chamber",
        description="A grand chamber for meetings.",
        is_exit_point=False,
    )
    treasury = Location(
        name="Treasury",
        description="A vault full of treasures.",
        is_exit_point=False,
    )

    # Create sub_grid and add locations at coordinates
    sub_grid = SubGrid(parent_name="Castle Ruins")
    sub_grid.add_location(entry_hall, 0, 0)
    sub_grid.add_location(council_chamber, 1, 0)
    sub_grid.add_location(treasury, 0, 1)

    # Create overworld location with sub_grid
    castle = Location(
        name="Castle Ruins",
        description="An ancient castle stands here.",
        coordinates=(5, 5),
        is_overworld=True,
        entry_point="Entry Hall",
        sub_grid=sub_grid,
        sub_locations=["Entry Hall", "Council Chamber", "Treasury"],
    )

    return castle, sub_grid


class TestEnterShowsOnlyEntryPoint:
    """Tests that get_layered_description() shows only entry point for sub_grid locations."""

    def test_enter_shows_only_entry_point_with_sub_grid(self):
        """Spec: Display only entry_point in 'Enter:' line when sub_grid exists."""
        castle, sub_grid = make_overworld_with_sub_grid()

        # Get description (use sub_grid for exit calculation)
        description = castle.get_layered_description(sub_grid=sub_grid)

        # Should show only "Entry Hall", not all sub-locations
        assert "Enter: Entry Hall" in description or "Enter:" in description and "Entry Hall" in description
        assert "Council Chamber" not in description
        assert "Treasury" not in description

    def test_enter_shows_entry_point_from_is_exit_point_fallback(self):
        """Spec: When entry_point is None, find first is_exit_point location."""
        # Create sub-locations
        entrance = Location(
            name="Main Entrance",
            description="The entrance to the dungeon.",
            is_exit_point=True,
        )
        inner_room = Location(
            name="Inner Sanctum",
            description="A dark inner room.",
            is_exit_point=False,
        )

        sub_grid = SubGrid(parent_name="Dark Dungeon")
        sub_grid.add_location(entrance, 0, 0)
        sub_grid.add_location(inner_room, 1, 0)

        # Overworld without explicit entry_point
        dungeon = Location(
            name="Dark Dungeon",
            description="An ominous dungeon entrance.",
            coordinates=(3, 3),
            is_overworld=True,
            entry_point=None,  # Not set
            sub_grid=sub_grid,
            sub_locations=["Main Entrance", "Inner Sanctum"],
        )

        description = dungeon.get_layered_description(sub_grid=sub_grid)

        # Should find "Main Entrance" via is_exit_point=True
        assert "Main Entrance" in description
        assert "Inner Sanctum" not in description


class TestEnterLegacySubLocations:
    """Tests that legacy sub_locations (without sub_grid) still work."""

    def test_enter_legacy_sub_locations_shows_all(self):
        """Spec: Preserve backward compatibility for sub_locations without sub_grid."""
        # Legacy-style location with only sub_locations list, no sub_grid
        tavern = Location(
            name="Tavern",
            description="A cozy tavern.",
            coordinates=(2, 2),
            is_overworld=True,
            sub_locations=["Bar", "Kitchen", "Cellar"],
            sub_grid=None,  # No sub_grid
            entry_point=None,
        )

        description = tavern.get_layered_description()

        # Should show all sub-locations (legacy behavior)
        assert "Bar" in description
        assert "Kitchen" in description
        assert "Cellar" in description


class TestEnterStrShowsOnlyEntryPoint:
    """Tests that __str__() shows only entry point when sub_grid exists."""

    def test_str_shows_only_entry_point_with_sub_grid(self):
        """Spec: __str__() shows only entry point when sub_grid exists."""
        castle, sub_grid = make_overworld_with_sub_grid()

        str_output = str(castle)

        # Should show only entry point
        assert "Entry Hall" in str_output
        # Should NOT show other sub-locations
        assert "Council Chamber" not in str_output
        assert "Treasury" not in str_output

    def test_str_legacy_shows_all_sub_locations(self):
        """Spec: __str__() shows all sub_locations when no sub_grid."""
        tavern = Location(
            name="Tavern",
            description="A cozy tavern.",
            coordinates=(2, 2),
            sub_locations=["Bar", "Kitchen", "Cellar"],
            sub_grid=None,
        )

        str_output = str(tavern)

        # Legacy: should show all
        assert "Bar" in str_output
        assert "Kitchen" in str_output
        assert "Cellar" in str_output


class TestEnterCommandValidation:
    """Tests that the enter command validates entry_point access."""

    def test_enter_command_allows_entry_point(self):
        """Spec: enter() succeeds for entry_point location."""
        castle, sub_grid = make_overworld_with_sub_grid()
        character = make_test_character()
        world = {"Castle Ruins": castle}

        # Create game state with required arguments
        game = GameState(character=character, world=world, starting_location="Castle Ruins")

        # Try to enter the entry point
        success, message = game.enter("Entry Hall")

        assert success is True
        assert "Entry Hall" in message
        assert game.in_sub_location is True

    def test_enter_command_rejects_non_entry_point(self):
        """Spec: enter() fails for non-entry-point locations with helpful message."""
        castle, sub_grid = make_overworld_with_sub_grid()
        character = make_test_character()
        world = {"Castle Ruins": castle}

        # Create game state
        game = GameState(character=character, world=world, starting_location="Castle Ruins")

        # Try to enter Council Chamber directly (not entry point)
        success, message = game.enter("Council Chamber")

        assert success is False
        assert "Entry Hall" in message  # Should mention the entry point
        # Should NOT have entered the sub-location
        assert game.in_sub_location is False

    def test_enter_command_rejects_treasury_directly(self):
        """Spec: enter() fails for any non-entry-point room."""
        castle, sub_grid = make_overworld_with_sub_grid()
        character = make_test_character()
        world = {"Castle Ruins": castle}

        game = GameState(character=character, world=world, starting_location="Castle Ruins")

        # Try to enter Treasury directly
        success, message = game.enter("Treasury")

        assert success is False
        assert "Entry Hall" in message  # Should mention entry point
        assert game.in_sub_location is False

    def test_enter_no_argument_uses_entry_point(self):
        """Spec: enter() with no argument uses entry_point."""
        castle, sub_grid = make_overworld_with_sub_grid()
        character = make_test_character()
        world = {"Castle Ruins": castle}

        game = GameState(character=character, world=world, starting_location="Castle Ruins")

        # Enter with no argument
        success, message = game.enter(None)

        assert success is True
        assert "Entry Hall" in message
        assert game.in_sub_location is True
