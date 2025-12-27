"""Tests for multi-level dungeon navigation with z-coordinate support.

Tests vertical navigation (up/down commands) in SubGrid locations,
with z-coordinate support for multi-level dungeons.
"""

import pytest
from cli_rpg.models.location import Location
from cli_rpg.world_grid import (
    SubGrid,
    SUBGRID_DIRECTION_OFFSETS,
    SUBGRID_BOUNDS,
    OPPOSITE_DIRECTIONS,
    get_subgrid_bounds,
)


# =============================================================================
# Location model tests
# =============================================================================


class TestLocationCoordinates:
    """Test Location model z-coordinate support."""

    def test_location_coordinates_can_have_z_component(self):
        """Location coordinates can be (x, y, z) 3-tuple."""
        loc = Location(
            name="Basement",
            description="A dark basement.",
            coordinates=(0, 0, -1),
        )
        assert loc.coordinates == (0, 0, -1)
        assert len(loc.coordinates) == 3

    def test_location_coordinates_default_to_2d(self):
        """Backward compat: (x, y) stays (x, y) without auto-upgrade."""
        loc = Location(
            name="Surface",
            description="The surface level.",
            coordinates=(5, 3),
        )
        assert loc.coordinates == (5, 3)
        assert len(loc.coordinates) == 2

    def test_location_serialization_includes_z(self):
        """to_dict includes 3rd element when z is present."""
        loc = Location(
            name="Tower Top",
            description="High above.",
            coordinates=(1, 2, 3),
        )
        data = loc.to_dict()
        assert "coordinates" in data
        assert data["coordinates"] == [1, 2, 3]
        assert len(data["coordinates"]) == 3

    def test_location_serialization_preserves_2d(self):
        """to_dict keeps 2 elements for 2D coordinates."""
        loc = Location(
            name="Ground Floor",
            description="On the ground.",
            coordinates=(4, 5),
        )
        data = loc.to_dict()
        assert data["coordinates"] == [4, 5]
        assert len(data["coordinates"]) == 2

    def test_location_deserialization_preserves_2d(self):
        """from_dict keeps (x, y) as 2-tuple (no auto-upgrade to 3D)."""
        data = {
            "name": "Old Save Location",
            "description": "From an old save file.",
            "coordinates": [10, 20],
        }
        loc = Location.from_dict(data)
        assert loc.coordinates == (10, 20)
        assert len(loc.coordinates) == 2

    def test_location_deserialization_loads_3d(self):
        """from_dict correctly loads (x, y, z) 3-tuple."""
        data = {
            "name": "Deep Dungeon",
            "description": "Far underground.",
            "coordinates": [0, 0, -5],
        }
        loc = Location.from_dict(data)
        assert loc.coordinates == (0, 0, -5)
        assert len(loc.coordinates) == 3

    def test_location_get_z_helper(self):
        """get_z() returns z or 0 for 2D coordinates."""
        loc_3d = Location(name="3D", description="Has z.", coordinates=(1, 2, -3))
        loc_2d = Location(name="2D", description="No z.", coordinates=(1, 2))
        loc_none = Location(name="None", description="No coords.")

        assert loc_3d.get_z() == -3
        assert loc_2d.get_z() == 0
        assert loc_none.get_z() == 0


# =============================================================================
# Direction offset tests
# =============================================================================


class TestDirectionOffsets:
    """Test 3D direction offsets for SubGrid navigation."""

    def test_direction_up_offset_is_0_0_1(self):
        """up direction has offset (0, 0, 1)."""
        assert SUBGRID_DIRECTION_OFFSETS["up"] == (0, 0, 1)

    def test_direction_down_offset_is_0_0_minus1(self):
        """down direction has offset (0, 0, -1)."""
        assert SUBGRID_DIRECTION_OFFSETS["down"] == (0, 0, -1)

    def test_opposite_of_up_is_down(self):
        """up's opposite is down."""
        assert OPPOSITE_DIRECTIONS["up"] == "down"

    def test_opposite_of_down_is_up(self):
        """down's opposite is up."""
        assert OPPOSITE_DIRECTIONS["down"] == "up"

    def test_cardinal_directions_preserved(self):
        """Existing cardinal directions still have correct 3D offsets."""
        assert SUBGRID_DIRECTION_OFFSETS["north"] == (0, 1, 0)
        assert SUBGRID_DIRECTION_OFFSETS["south"] == (0, -1, 0)
        assert SUBGRID_DIRECTION_OFFSETS["east"] == (1, 0, 0)
        assert SUBGRID_DIRECTION_OFFSETS["west"] == (-1, 0, 0)


# =============================================================================
# SubGrid 3D tests
# =============================================================================


class TestSubGridBounds:
    """Test 6-tuple bounds format for SubGrid."""

    def test_subgrid_bounds_include_z_axis(self):
        """SUBGRID_BOUNDS has 6-tuple format (min_x, max_x, min_y, max_y, min_z, max_z)."""
        # Check that all bounds are 6-tuples
        for category, bounds in SUBGRID_BOUNDS.items():
            assert len(bounds) == 6, f"Category '{category}' should have 6 bounds, got {len(bounds)}"
            min_x, max_x, min_y, max_y, min_z, max_z = bounds
            assert min_x <= max_x, f"{category}: min_x > max_x"
            assert min_y <= max_y, f"{category}: min_y > max_y"
            assert min_z <= max_z, f"{category}: min_z > max_z"

    def test_dungeon_has_negative_z(self):
        """Dungeons go down (negative z)."""
        bounds = SUBGRID_BOUNDS["dungeon"]
        min_z, max_z = bounds[4], bounds[5]
        assert min_z < 0, "Dungeons should have negative min_z"
        assert max_z == 0, "Dungeons should have max_z = 0 (ground level)"

    def test_tower_has_positive_z(self):
        """Towers go up (positive z)."""
        bounds = SUBGRID_BOUNDS["tower"]
        min_z, max_z = bounds[4], bounds[5]
        assert min_z == 0, "Towers should start at ground level"
        assert max_z > 0, "Towers should have positive max_z"

    def test_get_subgrid_bounds_returns_6tuple(self):
        """get_subgrid_bounds() returns 6-tuple."""
        bounds = get_subgrid_bounds("dungeon")
        assert len(bounds) == 6


class TestSubGrid3D:
    """Test SubGrid 3D coordinate operations."""

    def test_subgrid_add_location_with_z_coordinate(self):
        """SubGrid.add_location works with z coordinate."""
        grid = SubGrid(bounds=(-1, 1, -1, 1, -2, 0))
        loc = Location(name="Deep Room", description="Far below.")
        grid.add_location(loc, 0, 0, -2)

        assert loc.coordinates == (0, 0, -2)
        assert grid.get_by_coordinates(0, 0, -2) == loc

    def test_subgrid_add_location_default_z(self):
        """SubGrid.add_location defaults z to 0."""
        grid = SubGrid(bounds=(-1, 1, -1, 1, 0, 0))
        loc = Location(name="Ground Room", description="On the ground.")
        grid.add_location(loc, 0, 0)  # No z specified

        assert loc.coordinates == (0, 0, 0)
        assert grid.get_by_coordinates(0, 0, 0) == loc

    def test_subgrid_get_by_coordinates_with_z(self):
        """SubGrid.get_by_coordinates works with z coordinate."""
        grid = SubGrid(bounds=(-1, 1, -1, 1, -1, 1))

        basement = Location(name="Basement", description="Below.")
        ground = Location(name="Ground", description="On ground.")
        upper = Location(name="Upper", description="Above.")

        grid.add_location(basement, 0, 0, -1)
        grid.add_location(ground, 0, 0, 0)
        grid.add_location(upper, 0, 0, 1)

        assert grid.get_by_coordinates(0, 0, -1) == basement
        assert grid.get_by_coordinates(0, 0, 0) == ground
        assert grid.get_by_coordinates(0, 0, 1) == upper

    def test_subgrid_is_within_bounds_checks_z(self):
        """SubGrid.is_within_bounds checks z coordinate."""
        grid = SubGrid(bounds=(-1, 1, -1, 1, -2, 1))

        # Within bounds
        assert grid.is_within_bounds(0, 0, 0) is True
        assert grid.is_within_bounds(0, 0, -2) is True
        assert grid.is_within_bounds(0, 0, 1) is True

        # Out of bounds on z
        assert grid.is_within_bounds(0, 0, -3) is False
        assert grid.is_within_bounds(0, 0, 2) is False

    def test_subgrid_serialization_preserves_z_bounds(self):
        """SubGrid serialization preserves 6-tuple bounds."""
        grid = SubGrid(bounds=(-2, 2, -2, 2, -3, 1), parent_name="Parent Tower")
        loc = Location(name="Room", description="A room.")
        grid.add_location(loc, 0, 0, -1)

        data = grid.to_dict()

        assert data["bounds"] == [-2, 2, -2, 2, -3, 1]
        assert len(data["bounds"]) == 6

    def test_subgrid_deserialization_loads_6tuple_bounds(self):
        """SubGrid.from_dict correctly loads 6-tuple bounds."""
        data = {
            "bounds": [-1, 1, -1, 1, -2, 2],
            "parent_name": "Test Parent",
            "locations": [
                {
                    "name": "Test Room",
                    "description": "A test room.",
                    "coordinates": [0, 0, -1],
                }
            ],
        }

        grid = SubGrid.from_dict(data)

        assert grid.bounds == (-1, 1, -1, 1, -2, 2)
        assert len(grid.bounds) == 6

        # Verify location was loaded with z coordinate
        loc = grid.get_by_name("Test Room")
        assert loc is not None
        assert loc.coordinates == (0, 0, -1)

    def test_subgrid_deserialization_upgrades_4tuple_to_6tuple(self):
        """SubGrid.from_dict upgrades old 4-tuple bounds to 6-tuple with z=0."""
        data = {
            "bounds": [-2, 2, -2, 2],  # Old 4-tuple format
            "parent_name": "Legacy Parent",
            "locations": [
                {
                    "name": "Legacy Room",
                    "description": "An old room.",
                    "coordinates": [0, 0],
                }
            ],
        }

        grid = SubGrid.from_dict(data)

        # Should be upgraded to 6-tuple with z bounds (0, 0)
        assert len(grid.bounds) == 6
        assert grid.bounds == (-2, 2, -2, 2, 0, 0)


# =============================================================================
# Movement tests
# =============================================================================


class TestVerticalMovement:
    """Test up/down movement in SubGrid."""

    @pytest.fixture
    def multilevel_subgrid(self):
        """Create a multi-level SubGrid with rooms at different z levels."""
        grid = SubGrid(bounds=(-1, 1, -1, 1, -2, 2), parent_name="Test Dungeon")

        # Ground floor
        entrance = Location(name="Entrance", description="The dungeon entrance.", is_exit_point=True)
        grid.add_location(entrance, 0, 0, 0)

        # Basement levels
        basement1 = Location(name="Basement Level 1", description="First basement.")
        grid.add_location(basement1, 0, 0, -1)

        basement2 = Location(name="Basement Level 2", description="Deep basement.")
        grid.add_location(basement2, 0, 0, -2)

        # Upper levels
        upper1 = Location(name="Upper Level 1", description="First upper floor.")
        grid.add_location(upper1, 0, 0, 1)

        upper2 = Location(name="Upper Level 2", description="Top floor.")
        grid.add_location(upper2, 0, 0, 2)

        return grid

    def test_move_up_in_subgrid_increases_z(self, multilevel_subgrid):
        """Moving up increases z coordinate."""
        grid = multilevel_subgrid

        # Start at ground floor
        start = grid.get_by_coordinates(0, 0, 0)
        assert start.name == "Entrance"

        # Get location above
        above = grid.get_by_coordinates(0, 0, 1)
        assert above.name == "Upper Level 1"

    def test_move_down_in_subgrid_decreases_z(self, multilevel_subgrid):
        """Moving down decreases z coordinate."""
        grid = multilevel_subgrid

        # Start at ground floor
        start = grid.get_by_coordinates(0, 0, 0)
        assert start.name == "Entrance"

        # Get location below
        below = grid.get_by_coordinates(0, 0, -1)
        assert below.name == "Basement Level 1"

    def test_move_up_blocked_at_max_z(self, multilevel_subgrid):
        """Cannot move up beyond max_z bound."""
        grid = multilevel_subgrid

        # At top floor (z=2), trying to go up (z=3) should be out of bounds
        assert grid.is_within_bounds(0, 0, 2) is True
        assert grid.is_within_bounds(0, 0, 3) is False

    def test_move_down_blocked_at_min_z(self, multilevel_subgrid):
        """Cannot move down beyond min_z bound."""
        grid = multilevel_subgrid

        # At deepest level (z=-2), trying to go down (z=-3) should be out of bounds
        assert grid.is_within_bounds(0, 0, -2) is True
        assert grid.is_within_bounds(0, 0, -3) is False


class TestOverworldVerticalRestriction:
    """Test that up/down is blocked on overworld."""

    def test_up_direction_only_works_in_subgrid(self):
        """'up' direction offset should only be in SUBGRID_DIRECTION_OFFSETS."""
        from cli_rpg.world_grid import DIRECTION_OFFSETS

        # Overworld 2D directions should NOT include up/down
        assert "up" not in DIRECTION_OFFSETS
        assert "down" not in DIRECTION_OFFSETS

        # SubGrid 3D directions SHOULD include up/down
        assert "up" in SUBGRID_DIRECTION_OFFSETS
        assert "down" in SUBGRID_DIRECTION_OFFSETS

    def test_down_direction_only_works_in_subgrid(self):
        """'down' direction offset should only be in SUBGRID_DIRECTION_OFFSETS."""
        from cli_rpg.world_grid import DIRECTION_OFFSETS

        assert "down" not in DIRECTION_OFFSETS
        assert "down" in SUBGRID_DIRECTION_OFFSETS


# =============================================================================
# Command parsing tests
# =============================================================================


class TestGoCommandParsing:
    """Test 'go up' and 'go down' command parsing."""

    def test_go_up_command_parses(self):
        """'go up' is parsed correctly."""
        from cli_rpg.game_state import parse_command

        cmd, args = parse_command("go up")
        assert cmd == "go"
        assert args == ["up"]

    def test_go_down_command_parses(self):
        """'go down' is parsed correctly."""
        from cli_rpg.game_state import parse_command

        cmd, args = parse_command("go down")
        assert cmd == "go"
        assert args == ["down"]


# =============================================================================
# Integration tests with GameState
# =============================================================================


class TestGameStateVerticalMovement:
    """Test GameState vertical movement integration."""

    @pytest.fixture
    def game_with_multilevel_dungeon(self):
        """Create a game state with a multi-level dungeon."""
        from cli_rpg.models.character import Character, CharacterClass
        from cli_rpg.game_state import GameState

        # Create character with required stats
        char = Character(
            name="Test Hero",
            strength=12,
            dexterity=12,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )

        # Create overworld with a dungeon entrance
        dungeon_landmark = Location(
            name="Ancient Dungeon",
            description="A crumbling dungeon entrance.",
            coordinates=(0, 0),
            is_overworld=True,
            category="dungeon",
        )

        # Create multi-level SubGrid
        sub_grid = SubGrid(bounds=(-1, 1, -1, 1, -2, 1), parent_name="Ancient Dungeon")

        entrance = Location(
            name="Dungeon Entrance",
            description="The dungeon entrance hall.",
            is_exit_point=True,
        )
        sub_grid.add_location(entrance, 0, 0, 0)

        upper_room = Location(
            name="Guard Tower",
            description="A guard tower above the entrance.",
        )
        sub_grid.add_location(upper_room, 0, 0, 1)

        basement = Location(
            name="Dark Cellar",
            description="A dark cellar below.",
        )
        sub_grid.add_location(basement, 0, 0, -1)

        deep_basement = Location(
            name="Forgotten Crypt",
            description="An ancient crypt deep underground.",
        )
        sub_grid.add_location(deep_basement, 0, 0, -2)

        dungeon_landmark.sub_grid = sub_grid
        dungeon_landmark.entry_point = "Dungeon Entrance"

        world = {"Ancient Dungeon": dungeon_landmark}

        return GameState(char, world, starting_location="Ancient Dungeon")

    def test_move_up_in_subgrid_succeeds(self, game_with_multilevel_dungeon):
        """GameState.move('up') works inside SubGrid."""
        gs = game_with_multilevel_dungeon

        # Enter the dungeon
        success, _ = gs.enter()
        assert success
        assert gs.in_sub_location
        assert gs.current_location == "Dungeon Entrance"

        # Move up to guard tower
        success, message = gs.move("up")
        assert success, f"Move up failed: {message}"
        assert gs.current_location == "Guard Tower"

    def test_move_down_in_subgrid_succeeds(self, game_with_multilevel_dungeon):
        """GameState.move('down') works inside SubGrid."""
        gs = game_with_multilevel_dungeon

        # Enter the dungeon
        gs.enter()
        assert gs.current_location == "Dungeon Entrance"

        # Move down to cellar
        success, message = gs.move("down")
        assert success, f"Move down failed: {message}"
        assert gs.current_location == "Dark Cellar"

    def test_move_up_blocked_at_boundary(self, game_with_multilevel_dungeon):
        """Cannot move up past the SubGrid z boundary."""
        gs = game_with_multilevel_dungeon

        # Enter and go to top floor
        gs.enter()
        gs.move("up")
        assert gs.current_location == "Guard Tower"

        # Try to go higher - should fail
        success, message = gs.move("up")
        assert not success
        assert "no way" in message.lower() or "blocked" in message.lower() or "edge" in message.lower()

    def test_move_down_blocked_at_boundary(self, game_with_multilevel_dungeon):
        """Cannot move down past the SubGrid z boundary."""
        gs = game_with_multilevel_dungeon

        # Enter and go to deepest level
        gs.enter()
        gs.move("down")  # To Dark Cellar (z=-1)
        gs.move("down")  # To Forgotten Crypt (z=-2)
        assert gs.current_location == "Forgotten Crypt"

        # Try to go lower - should fail
        success, message = gs.move("down")
        assert not success
        assert "no way" in message.lower() or "blocked" in message.lower() or "edge" in message.lower()

    def test_up_blocked_on_overworld(self, game_with_multilevel_dungeon):
        """'go up' is blocked on the overworld."""
        gs = game_with_multilevel_dungeon

        # We're on the overworld
        assert not gs.in_sub_location

        # Try to go up
        success, message = gs.move("up")
        assert not success
        assert "inside" in message.lower() or "building" in message.lower() or "dungeon" in message.lower()

    def test_down_blocked_on_overworld(self, game_with_multilevel_dungeon):
        """'go down' is blocked on the overworld."""
        gs = game_with_multilevel_dungeon

        # We're on the overworld
        assert not gs.in_sub_location

        # Try to go down
        success, message = gs.move("down")
        assert not success
        assert "inside" in message.lower() or "building" in message.lower() or "dungeon" in message.lower()
