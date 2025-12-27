"""Tests for interior events system (cave-ins).

Tests verify:
- InteriorEvent model creation and serialization (spec: dataclass with fields)
- Cave-in spawning (spec: 5% chance, valid categories, blocked direction updates)
- Cave-in clearing (spec: time-based expiry, manual clearing)
- Integration with SubGrid and movement (spec: blocked directions, messages)
"""

import pytest
from unittest.mock import MagicMock, patch

from cli_rpg.interior_events import (
    InteriorEvent,
    CAVE_IN_SPAWN_CHANCE,
    CAVE_IN_DURATION_RANGE,
    CAVE_IN_CATEGORIES,
    check_for_cave_in,
    progress_interior_events,
    clear_cave_in,
    get_active_cave_ins,
    get_cave_in_at_location,
)
from cli_rpg.world_grid import SubGrid
from cli_rpg.models.location import Location


class TestInteriorEventModel:
    """Tests for InteriorEvent dataclass model."""

    def test_event_creation(self):
        """Test: InteriorEvent can be created with required fields."""
        event = InteriorEvent(
            event_id="cave_in_1_2_0_1234",
            event_type="cave_in",
            location_coords=(1, 2, 0),
            blocked_direction="north",
            start_hour=10,
            duration_hours=6,
        )

        assert event.event_id == "cave_in_1_2_0_1234"
        assert event.event_type == "cave_in"
        assert event.location_coords == (1, 2, 0)
        assert event.blocked_direction == "north"
        assert event.start_hour == 10
        assert event.duration_hours == 6
        assert event.is_active is True  # Default

    def test_event_expiry(self):
        """Test: is_expired correctly checks event duration."""
        event = InteriorEvent(
            event_id="test",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="east",
            start_hour=10,
            duration_hours=5,
        )

        # Before expiry
        assert event.is_expired(10) is False
        assert event.is_expired(14) is False

        # At and after expiry
        assert event.is_expired(15) is True
        assert event.is_expired(20) is True

    def test_time_remaining(self):
        """Test: get_time_remaining returns correct hours left."""
        event = InteriorEvent(
            event_id="test",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="west",
            start_hour=10,
            duration_hours=8,
        )

        assert event.get_time_remaining(10) == 8
        assert event.get_time_remaining(14) == 4
        assert event.get_time_remaining(18) == 0
        assert event.get_time_remaining(20) == 0  # Never negative

    def test_serialization(self):
        """Test: InteriorEvent serializes to/from dict correctly."""
        event = InteriorEvent(
            event_id="cave_in_0_1_2_5678",
            event_type="cave_in",
            location_coords=(0, 1, -2),
            blocked_direction="south",
            start_hour=50,
            duration_hours=10,
            is_active=False,
        )

        # Serialize
        data = event.to_dict()
        assert data["event_id"] == "cave_in_0_1_2_5678"
        assert data["event_type"] == "cave_in"
        assert data["location_coords"] == [0, 1, -2]
        assert data["blocked_direction"] == "south"
        assert data["start_hour"] == 50
        assert data["duration_hours"] == 10
        assert data["is_active"] is False

        # Deserialize
        restored = InteriorEvent.from_dict(data)
        assert restored.event_id == event.event_id
        assert restored.location_coords == event.location_coords
        assert restored.blocked_direction == event.blocked_direction
        assert restored.is_active == event.is_active


class TestCaveInSpawning:
    """Tests for cave-in spawn logic."""

    @pytest.fixture
    def dungeon_sub_grid(self):
        """Create a simple SubGrid with connected rooms for testing."""
        sub_grid = SubGrid(
            bounds=(-1, 1, -1, 1, 0, 0),
            parent_name="Test Dungeon",
        )

        # Center room
        center = Location(name="Center Room", description="A central room.")
        sub_grid.add_location(center, 0, 0, 0)

        # North room
        north = Location(name="North Room", description="Northern passage.")
        sub_grid.add_location(north, 0, 1, 0)

        # East room
        east = Location(name="East Room", description="Eastern passage.")
        sub_grid.add_location(east, 1, 0, 0)

        return sub_grid

    @pytest.fixture
    def mock_game_state(self, dungeon_sub_grid):
        """Create mock game state for testing."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 100

        # Current location is center room
        center = dungeon_sub_grid.get_by_coordinates(0, 0, 0)
        game_state.get_current_location.return_value = center

        # Parent location is a dungeon (valid cave-in category)
        parent = MagicMock()
        parent.category = "dungeon"
        game_state.world = {"Test Dungeon": parent}

        return game_state

    def test_spawn_in_valid_category(self, mock_game_state, dungeon_sub_grid):
        """Test: Cave-ins can spawn in dungeon category (spec: CAVE_IN_CATEGORIES)."""
        # Force spawn with 100% chance
        with patch("cli_rpg.interior_events.random.random", return_value=0.01):
            with patch("cli_rpg.interior_events.random.choice", return_value="north"):
                with patch(
                    "cli_rpg.interior_events.random.randint",
                    return_value=6,  # Duration
                ):
                    message = check_for_cave_in(mock_game_state, dungeon_sub_grid)

        assert message is not None
        assert "cave-in" in message.lower()
        assert "north" in message.lower()

        # Verify event was added
        assert len(dungeon_sub_grid.interior_events) == 1
        event = dungeon_sub_grid.interior_events[0]
        assert event.event_type == "cave_in"
        assert event.blocked_direction == "north"

        # Verify direction is blocked
        center = dungeon_sub_grid.get_by_coordinates(0, 0, 0)
        assert "north" in center.blocked_directions

    def test_no_spawn_in_invalid_category(self, mock_game_state, dungeon_sub_grid):
        """Test: Cave-ins don't spawn in non-cave categories (spec: CAVE_IN_CATEGORIES)."""
        # Change parent to town (not in CAVE_IN_CATEGORIES)
        parent = mock_game_state.world["Test Dungeon"]
        parent.category = "town"

        with patch("cli_rpg.interior_events.random.random", return_value=0.01):
            message = check_for_cave_in(mock_game_state, dungeon_sub_grid)

        assert message is None
        assert len(dungeon_sub_grid.interior_events) == 0

    def test_spawn_chance(self, mock_game_state, dungeon_sub_grid):
        """Test: Cave-ins respect 5% spawn chance (spec: CAVE_IN_SPAWN_CHANCE)."""
        assert CAVE_IN_SPAWN_CHANCE == 0.05

        # Roll above chance - no spawn
        with patch("cli_rpg.interior_events.random.random", return_value=0.10):
            message = check_for_cave_in(mock_game_state, dungeon_sub_grid)

        assert message is None
        assert len(dungeon_sub_grid.interior_events) == 0

    def test_duration_range(self, mock_game_state, dungeon_sub_grid):
        """Test: Cave-in duration is within spec range (spec: 4-12 hours)."""
        assert CAVE_IN_DURATION_RANGE == (4, 12)

        with patch("cli_rpg.interior_events.random.random", return_value=0.01):
            with patch("cli_rpg.interior_events.random.choice", return_value="north"):
                with patch(
                    "cli_rpg.interior_events.random.randint",
                    return_value=8,
                ) as mock_randint:
                    check_for_cave_in(mock_game_state, dungeon_sub_grid)

        # Verify randint was called with duration range
        mock_randint.assert_called_with(4, 12)

    def test_no_spawn_when_already_blocked(self, mock_game_state, dungeon_sub_grid):
        """Test: Don't spawn cave-in if all directions are already blocked."""
        center = dungeon_sub_grid.get_by_coordinates(0, 0, 0)
        # Block all available directions
        center.blocked_directions = ["north", "east"]

        with patch("cli_rpg.interior_events.random.random", return_value=0.01):
            message = check_for_cave_in(mock_game_state, dungeon_sub_grid)

        # No new cave-in since all directions blocked
        assert message is None


class TestCaveInClearing:
    """Tests for cave-in clearing logic."""

    @pytest.fixture
    def sub_grid_with_cave_in(self):
        """Create a SubGrid with an active cave-in."""
        sub_grid = SubGrid(
            bounds=(-1, 1, -1, 1, 0, 0),
            parent_name="Test Cave",
        )

        # Add rooms
        center = Location(name="Center", description="Center room.")
        center.blocked_directions = ["north"]  # Pre-blocked by cave-in
        sub_grid.add_location(center, 0, 0, 0)

        north = Location(name="North", description="North room.")
        sub_grid.add_location(north, 0, 1, 0)

        # Add cave-in event
        event = InteriorEvent(
            event_id="cave_in_test",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="north",
            start_hour=100,
            duration_hours=5,
        )
        sub_grid.interior_events.append(event)

        return sub_grid

    def test_time_based_expiry(self, sub_grid_with_cave_in):
        """Test: Cave-ins clear after duration expires (spec: time-based expiry)."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 106  # After expiry (100 + 5 = 105)

        messages = progress_interior_events(game_state, sub_grid_with_cave_in)

        assert len(messages) == 1
        # Message contains ANSI escape codes for color, check content is present
        assert "cleared" in messages[0]

        # Verify event is no longer active
        event = sub_grid_with_cave_in.interior_events[0]
        assert event.is_active is False

        # Verify direction is unblocked
        center = sub_grid_with_cave_in.get_by_coordinates(0, 0, 0)
        assert "north" not in center.blocked_directions

    def test_no_clear_before_expiry(self, sub_grid_with_cave_in):
        """Test: Cave-ins don't clear before duration expires."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 103  # Before expiry

        messages = progress_interior_events(game_state, sub_grid_with_cave_in)

        assert len(messages) == 0

        # Event still active
        event = sub_grid_with_cave_in.interior_events[0]
        assert event.is_active is True

        # Direction still blocked
        center = sub_grid_with_cave_in.get_by_coordinates(0, 0, 0)
        assert "north" in center.blocked_directions

    def test_manual_clearing(self, sub_grid_with_cave_in):
        """Test: clear_cave_in removes blocked direction (spec: manual clearing)."""
        result = clear_cave_in(sub_grid_with_cave_in, (0, 0, 0), "north")

        assert result is True

        center = sub_grid_with_cave_in.get_by_coordinates(0, 0, 0)
        assert "north" not in center.blocked_directions

    def test_clear_nonexistent_location(self, sub_grid_with_cave_in):
        """Test: clear_cave_in returns False for nonexistent location."""
        result = clear_cave_in(sub_grid_with_cave_in, (5, 5, 5), "north")
        assert result is False

    def test_clear_nonexistent_direction(self, sub_grid_with_cave_in):
        """Test: clear_cave_in returns False if direction not blocked."""
        result = clear_cave_in(sub_grid_with_cave_in, (0, 0, 0), "south")
        assert result is False


class TestCaveInIntegration:
    """Integration tests for cave-in system."""

    @pytest.fixture
    def full_sub_grid(self):
        """Create a complete SubGrid with multiple rooms."""
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Deep Dungeon",
        )

        rooms = [
            ("Entrance Hall", 0, 0, 0),
            ("North Corridor", 0, 1, 0),
            ("South Chamber", 0, -1, 0),
            ("East Gallery", 1, 0, 0),
            ("West Tunnel", -1, 0, 0),
        ]

        for name, x, y, z in rooms:
            loc = Location(name=name, description=f"The {name}.")
            sub_grid.add_location(loc, x, y, z)

        return sub_grid

    def test_get_active_cave_ins(self, full_sub_grid):
        """Test: get_active_cave_ins returns only active cave-in events."""
        # Add two events, one active, one inactive
        active = InteriorEvent(
            event_id="active",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="north",
            start_hour=100,
            duration_hours=10,
            is_active=True,
        )
        inactive = InteriorEvent(
            event_id="inactive",
            event_type="cave_in",
            location_coords=(0, 1, 0),
            blocked_direction="south",
            start_hour=50,
            duration_hours=5,
            is_active=False,
        )
        full_sub_grid.interior_events = [active, inactive]

        result = get_active_cave_ins(full_sub_grid)

        assert len(result) == 1
        assert result[0].event_id == "active"

    def test_get_cave_in_at_location(self, full_sub_grid):
        """Test: get_cave_in_at_location finds specific cave-in."""
        event = InteriorEvent(
            event_id="specific",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="east",
            start_hour=100,
            duration_hours=8,
        )
        full_sub_grid.interior_events.append(event)

        # Find existing cave-in
        found = get_cave_in_at_location(full_sub_grid, (0, 0, 0), "east")
        assert found is not None
        assert found.event_id == "specific"

        # Don't find non-existent
        not_found = get_cave_in_at_location(full_sub_grid, (0, 0, 0), "west")
        assert not_found is None

    def test_valid_categories(self):
        """Test: CAVE_IN_CATEGORIES matches spec (dungeon, cave, ruins, temple)."""
        assert CAVE_IN_CATEGORIES == {"dungeon", "cave", "ruins", "temple"}

    def test_2d_coords_handling(self, full_sub_grid):
        """Test: Functions handle 2D coordinates correctly (converted to 3D)."""
        event = InteriorEvent(
            event_id="2d_test",
            event_type="cave_in",
            location_coords=(1, 0, 0),  # 3D coords
            blocked_direction="west",
            start_hour=100,
            duration_hours=5,
        )
        full_sub_grid.interior_events.append(event)

        # Test with 2D coords (should be converted internally)
        found = get_cave_in_at_location(full_sub_grid, (1, 0), "west")
        assert found is not None

        # Test clear_cave_in with 2D coords
        entrance = full_sub_grid.get_by_coordinates(0, 0, 0)
        entrance.blocked_directions.append("test_dir")
        result = clear_cave_in(full_sub_grid, (0, 0), "test_dir")
        assert result is True


class TestSubGridSerialization:
    """Tests for SubGrid interior_events serialization."""

    def test_subgrid_interior_events_serialization(self):
        """Test: SubGrid serializes interior_events correctly."""
        sub_grid = SubGrid(
            bounds=(-1, 1, -1, 1, 0, 0),
            parent_name="Test",
        )
        loc = Location(name="Room", description="A room.")
        sub_grid.add_location(loc, 0, 0, 0)

        # Add interior event
        event = InteriorEvent(
            event_id="test_event",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="north",
            start_hour=100,
            duration_hours=8,
        )
        sub_grid.interior_events.append(event)

        # Serialize
        data = sub_grid.to_dict()
        assert "interior_events" in data
        assert len(data["interior_events"]) == 1
        assert data["interior_events"][0]["event_id"] == "test_event"

        # Deserialize
        restored = SubGrid.from_dict(data)
        assert len(restored.interior_events) == 1
        assert restored.interior_events[0].event_id == "test_event"
        assert restored.interior_events[0].blocked_direction == "north"

    def test_backward_compatible_deserialization(self):
        """Test: SubGrid deserialization handles missing interior_events (backward compat)."""
        # Old save format without interior_events
        data = {
            "locations": [
                {
                    "name": "Old Room",
                    "description": "An old room.",
                    "coordinates": [0, 0, 0],
                }
            ],
            "bounds": [-1, 1, -1, 1, 0, 0],
            "parent_name": "Old Dungeon",
        }

        restored = SubGrid.from_dict(data)

        # Should have empty interior_events list
        assert restored.interior_events == []
