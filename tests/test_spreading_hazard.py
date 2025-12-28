"""Tests for spreading hazard system (Issue 25).

Tests the spreading fire and flooding hazards that propagate through
dungeon tiles over time.
"""

import pytest
import random
from unittest.mock import MagicMock, patch

from cli_rpg.interior_events import (
    InteriorEvent,
    SPREADING_HAZARD_SPAWN_CHANCE,
    SPREADING_HAZARD_DURATION_RANGE,
    SPREADING_HAZARD_CATEGORIES,
    FIRE_DAMAGE_RANGE,
    FLOODING_TIREDNESS,
    MAX_SPREAD_RADIUS,
    check_for_spreading_hazard,
    spread_hazard,
    get_active_spreading_hazard_event,
    progress_interior_events,
)
from cli_rpg.hazards import (
    apply_spreading_fire,
    apply_spreading_flood,
    check_hazards_on_entry,
    HAZARD_TYPES,
)
from cli_rpg.models.location import Location


# ============================================================================
# Test 1: Test spreading hazard model fields
# ============================================================================


class TestSpreadingHazardModel:
    """Tests for InteriorEvent spreading hazard fields."""

    def test_interior_event_has_hazard_type_field(self):
        """InteriorEvent should have hazard_type field (default None)."""
        event = InteriorEvent(
            event_id="test_1",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=10,
        )
        assert hasattr(event, "hazard_type")
        assert event.hazard_type is None

    def test_interior_event_has_spread_rooms_field(self):
        """InteriorEvent should have spread_rooms field (default None)."""
        event = InteriorEvent(
            event_id="test_2",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=10,
        )
        assert hasattr(event, "spread_rooms")
        assert event.spread_rooms is None

    def test_interior_event_has_max_spread_radius_field(self):
        """InteriorEvent should have max_spread_radius field (default 3)."""
        event = InteriorEvent(
            event_id="test_3",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=10,
        )
        assert hasattr(event, "max_spread_radius")
        assert event.max_spread_radius == 3

    def test_interior_event_custom_hazard_values(self):
        """InteriorEvent should accept custom hazard values."""
        spread_rooms = {(0, 0, 0): 0, (1, 0, 0): 1}
        event = InteriorEvent(
            event_id="test_4",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=10,
            hazard_type="fire",
            spread_rooms=spread_rooms,
            max_spread_radius=5,
        )
        assert event.hazard_type == "fire"
        assert event.spread_rooms == spread_rooms
        assert event.max_spread_radius == 5


# ============================================================================
# Test 2-4: Test hazard spawning
# ============================================================================


class TestSpreadingHazardSpawn:
    """Tests for spreading hazard spawn mechanics."""

    @pytest.fixture
    def mock_game_state(self):
        """Create a mock game state for testing."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 100
        return game_state

    @pytest.fixture
    def mock_sub_grid_dungeon(self):
        """Create a mock SubGrid in a dungeon."""
        sub_grid = MagicMock()
        sub_grid.parent_name = "Dark Dungeon"
        sub_grid.interior_events = []
        sub_grid._grid = {
            (0, 0, 0): MagicMock(coordinates=(0, 0, 0), is_exit_point=True, hazards=[]),
            (1, 0, 0): MagicMock(coordinates=(1, 0, 0), is_exit_point=False, hazards=[]),
            (2, 0, 0): MagicMock(coordinates=(2, 0, 0), is_exit_point=False, hazards=[]),
        }
        sub_grid.bounds = (-1, 3, -1, 1, -1, 1)
        sub_grid.is_within_bounds = MagicMock(return_value=True)
        sub_grid.get_by_coordinates = MagicMock(
            side_effect=lambda x, y, z: sub_grid._grid.get((x, y, z))
        )
        return sub_grid

    def test_fire_hazard_spawns_with_correct_chance(self, mock_game_state, mock_sub_grid_dungeon):
        """check_for_spreading_hazard() creates event with 5% chance."""
        # Mock the parent location lookup
        parent_loc = MagicMock()
        parent_loc.category = "dungeon"
        mock_game_state.world.get = MagicMock(return_value=parent_loc)

        # Force spawn by patching only the spawn roll check
        # The function calls random.random() twice: once for spawn check, once for hazard type
        with patch("cli_rpg.interior_events.random.random", side_effect=[0.01, 0.3]):  # Spawn check, fire type
            with patch("cli_rpg.interior_events.random.choice", return_value=(1, 0, 0)):  # Room selection
                with patch("cli_rpg.interior_events.random.randint", return_value=12):  # Duration
                    result = check_for_spreading_hazard(mock_game_state, mock_sub_grid_dungeon)

        assert result is not None  # Should return a message
        assert len(mock_sub_grid_dungeon.interior_events) == 1
        event = mock_sub_grid_dungeon.interior_events[0]
        assert event.event_type == "spreading_hazard"
        assert event.hazard_type in ("fire", "flooding")

    def test_hazard_does_not_spawn_on_failed_roll(self, mock_game_state, mock_sub_grid_dungeon):
        """Hazard should not spawn when roll > 5%."""
        parent_loc = MagicMock()
        parent_loc.category = "dungeon"
        mock_game_state.world.get = MagicMock(return_value=parent_loc)

        with patch("cli_rpg.interior_events.random.random", return_value=0.10):  # Above 0.05
            result = check_for_spreading_hazard(mock_game_state, mock_sub_grid_dungeon)

        assert result is None
        assert len(mock_sub_grid_dungeon.interior_events) == 0

    def test_fire_and_flooding_equal_chance(self, mock_game_state, mock_sub_grid_dungeon):
        """Fire and flooding have 50/50 selection."""
        parent_loc = MagicMock()
        parent_loc.category = "dungeon"
        mock_game_state.world.get = MagicMock(return_value=parent_loc)

        # Test fire when random < 0.5
        mock_sub_grid_dungeon.interior_events = []
        mock_sub_grid_dungeon._grid[(1, 0, 0)].hazards = []
        with patch("cli_rpg.interior_events.random.random", side_effect=[0.01, 0.3]):  # Spawn, Fire
            with patch("cli_rpg.interior_events.random.choice", return_value=(1, 0, 0)):
                with patch("cli_rpg.interior_events.random.randint", return_value=12):
                    result = check_for_spreading_hazard(mock_game_state, mock_sub_grid_dungeon)

        assert result is not None
        assert mock_sub_grid_dungeon.interior_events[0].hazard_type == "fire"

        # Test flooding when random >= 0.5
        mock_sub_grid_dungeon.interior_events = []
        mock_sub_grid_dungeon._grid[(1, 0, 0)].hazards = []
        with patch("cli_rpg.interior_events.random.random", side_effect=[0.01, 0.7]):  # Spawn, Flood
            with patch("cli_rpg.interior_events.random.choice", return_value=(1, 0, 0)):
                with patch("cli_rpg.interior_events.random.randint", return_value=12):
                    result = check_for_spreading_hazard(mock_game_state, mock_sub_grid_dungeon)

        assert result is not None
        assert mock_sub_grid_dungeon.interior_events[0].hazard_type == "flooding"

    def test_only_spawns_in_valid_categories(self, mock_game_state, mock_sub_grid_dungeon):
        """Hazard only spawns in dungeon/cave/ruins/temple."""
        # Test invalid category
        parent_loc = MagicMock()
        parent_loc.category = "town"
        mock_game_state.world.get = MagicMock(return_value=parent_loc)

        with patch("cli_rpg.interior_events.random.random", return_value=0.01):  # Force spawn attempt
            result = check_for_spreading_hazard(mock_game_state, mock_sub_grid_dungeon)

        assert result is None
        assert len(mock_sub_grid_dungeon.interior_events) == 0

    def test_spawns_in_all_valid_categories(self, mock_game_state, mock_sub_grid_dungeon):
        """Hazard spawns in all valid categories."""
        for category in SPREADING_HAZARD_CATEGORIES:
            mock_sub_grid_dungeon.interior_events = []
            mock_sub_grid_dungeon._grid[(1, 0, 0)].hazards = []

            parent_loc = MagicMock()
            parent_loc.category = category
            mock_game_state.world.get = MagicMock(return_value=parent_loc)

            with patch("cli_rpg.interior_events.random.random", side_effect=[0.01, 0.3]):  # Spawn check, fire type
                with patch("cli_rpg.interior_events.random.choice", return_value=(1, 0, 0)):  # Room
                    with patch("cli_rpg.interior_events.random.randint", return_value=12):  # Duration
                        result = check_for_spreading_hazard(mock_game_state, mock_sub_grid_dungeon)

            assert result is not None, f"Failed to spawn in category: {category}"


# ============================================================================
# Test 5-6: Test spread mechanics
# ============================================================================


class TestSpreadMechanics:
    """Tests for hazard spreading mechanics."""

    @pytest.fixture
    def mock_sub_grid_with_rooms(self):
        """Create a SubGrid with multiple rooms for spread testing."""
        sub_grid = MagicMock()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.interior_events = []
        sub_grid.bounds = (-5, 5, -5, 5, -1, 1)

        # Create a 3x3 grid of rooms
        rooms = {}
        for x in range(-1, 2):
            for y in range(-1, 2):
                rooms[(x, y, 0)] = MagicMock(
                    coordinates=(x, y, 0),
                    is_exit_point=(x == 0 and y == 0),
                    hazards=[],
                    name=f"Room_{x}_{y}",
                )
        sub_grid._grid = rooms

        def is_within_bounds(x, y, z):
            return -5 <= x <= 5 and -5 <= y <= 5 and -1 <= z <= 1

        sub_grid.is_within_bounds = is_within_bounds
        sub_grid.get_by_coordinates = MagicMock(
            side_effect=lambda x, y, z: rooms.get((x, y, z))
        )

        return sub_grid

    def test_spread_hazard_adds_adjacent_rooms(self, mock_sub_grid_with_rooms):
        """spread_hazard() adds adjacent rooms each hour."""
        # Create event at center (0, 0, 0)
        event = InteriorEvent(
            event_id="spread_test_1",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=16,
            hazard_type="fire",
            spread_rooms={(0, 0, 0): 0},
            max_spread_radius=3,
        )
        mock_sub_grid_with_rooms.interior_events.append(event)

        # Spread at hour 1
        messages = spread_hazard(mock_sub_grid_with_rooms, event, current_hour=1)

        # Should have spread to 4 adjacent rooms (N, S, E, W)
        assert len(event.spread_rooms) > 1
        # Check that at least some adjacent rooms were added
        adjacent_coords = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
        spread_count = sum(1 for c in adjacent_coords if c in event.spread_rooms)
        assert spread_count > 0

    def test_spread_stops_at_max_radius(self, mock_sub_grid_with_rooms):
        """Hazard stops spreading at max_spread_radius."""
        # Create event with radius 1
        event = InteriorEvent(
            event_id="spread_test_2",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=16,
            hazard_type="fire",
            spread_rooms={(0, 0, 0): 0},
            max_spread_radius=1,
        )
        mock_sub_grid_with_rooms.interior_events.append(event)

        # Spread multiple times
        for hour in range(1, 5):
            spread_hazard(mock_sub_grid_with_rooms, event, current_hour=hour)

        # All spread rooms should be within radius 1 of origin
        origin = (0, 0, 0)
        for coords in event.spread_rooms.keys():
            distance = abs(coords[0] - origin[0]) + abs(coords[1] - origin[1])
            assert distance <= 1, f"Room {coords} exceeds max radius 1"

    def test_spread_updates_location_hazards(self, mock_sub_grid_with_rooms):
        """Spread rooms have hazard added to location.hazards list."""
        event = InteriorEvent(
            event_id="spread_test_3",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=16,
            hazard_type="fire",
            spread_rooms={(0, 0, 0): 0},
            max_spread_radius=3,
        )
        # Add hazard to origin room
        mock_sub_grid_with_rooms._grid[(0, 0, 0)].hazards.append("spreading_fire")
        mock_sub_grid_with_rooms.interior_events.append(event)

        # Spread at hour 1
        spread_hazard(mock_sub_grid_with_rooms, event, current_hour=1)

        # Check that new rooms have hazard added
        for coords in event.spread_rooms.keys():
            if coords != (0, 0, 0):  # Skip origin
                room = mock_sub_grid_with_rooms._grid.get(coords)
                if room:
                    assert "spreading_fire" in room.hazards


# ============================================================================
# Test 7-8: Test hazard effects
# ============================================================================


class TestHazardEffects:
    """Tests for spreading hazard damage and effects."""

    @pytest.fixture
    def mock_character(self):
        """Create a mock character for testing."""
        char = MagicMock()
        char.health = 100
        char.max_health = 100
        char.tiredness.value = 0
        char.tiredness.increase = MagicMock()
        return char

    def test_fire_damage_in_range(self, mock_character):
        """apply_spreading_fire() deals 4-8 damage."""
        damages = []
        for _ in range(50):
            msg = apply_spreading_fire(mock_character)
            # Extract damage from message or call count
            damages.append(mock_character.take_damage.call_args[0][0])

        assert min(damages) >= FIRE_DAMAGE_RANGE[0]
        assert max(damages) <= FIRE_DAMAGE_RANGE[1]

    def test_flooding_causes_movement_penalty_and_tiredness(self, mock_character):
        """apply_spreading_flood() causes 50% movement fail + 3 tiredness."""
        msg, movement_blocked = apply_spreading_flood(mock_character)

        # Check tiredness increase was called with correct value
        mock_character.tiredness.increase.assert_called_with(FLOODING_TIREDNESS)

        # Check message mentions flooding
        assert "flood" in msg.lower() or "water" in msg.lower()

    def test_flooding_movement_penalty_is_50_percent(self, mock_character):
        """Flooding has 50% chance to block movement."""
        blocked_count = 0
        for _ in range(100):
            _, blocked = apply_spreading_flood(mock_character)
            if blocked:
                blocked_count += 1

        # Should be roughly 50% (allow 30-70 range for randomness)
        assert 30 <= blocked_count <= 70


# ============================================================================
# Test 9: Test hazard expiry
# ============================================================================


class TestHazardExpiry:
    """Tests for spreading hazard expiration."""

    @pytest.fixture
    def mock_sub_grid_with_hazard(self):
        """Create a SubGrid with an active spreading hazard."""
        sub_grid = MagicMock()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-5, 5, -5, 5, -1, 1)

        rooms = {
            (0, 0, 0): MagicMock(coordinates=(0, 0, 0), hazards=["spreading_fire"]),
            (1, 0, 0): MagicMock(coordinates=(1, 0, 0), hazards=["spreading_fire"]),
            (0, 1, 0): MagicMock(coordinates=(0, 1, 0), hazards=["spreading_fire"]),
        }
        sub_grid._grid = rooms
        sub_grid.get_by_coordinates = MagicMock(
            side_effect=lambda x, y, z: rooms.get((x, y, z))
        )

        event = InteriorEvent(
            event_id="expiry_test",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=10,
            hazard_type="fire",
            spread_rooms={(0, 0, 0): 0, (1, 0, 0): 1, (0, 1, 0): 2},
            max_spread_radius=3,
        )
        sub_grid.interior_events = [event]

        return sub_grid, event

    def test_hazard_clears_after_duration(self, mock_sub_grid_with_hazard):
        """Hazard clears after duration_hours, removes from all spread_rooms."""
        sub_grid, event = mock_sub_grid_with_hazard

        game_state = MagicMock()
        game_state.game_time.total_hours = 15  # Past expiry (start=0, duration=10)

        messages = progress_interior_events(game_state, sub_grid)

        # Event should be marked inactive
        assert not event.is_active

        # All rooms should have hazard removed
        for coords in [(0, 0, 0), (1, 0, 0), (0, 1, 0)]:
            room = sub_grid._grid.get(coords)
            assert "spreading_fire" not in room.hazards

        # Should return a message about the hazard dissipating
        assert any("dissipat" in msg.lower() or "clear" in msg.lower() for msg in messages)


# ============================================================================
# Test 10-11: Test serialization
# ============================================================================


class TestSpreadingHazardSerialization:
    """Tests for spreading hazard serialization."""

    def test_spread_rooms_serializes_correctly(self):
        """spread_rooms dict serializes and deserializes correctly."""
        original_spread = {(0, 0, 0): 0, (1, 0, 0): 1, (-1, 0, 0): 2}

        event = InteriorEvent(
            event_id="serialize_test",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=10,
            hazard_type="fire",
            spread_rooms=original_spread,
            max_spread_radius=5,
        )

        # Serialize
        data = event.to_dict()

        # Check serialization format
        assert "hazard_type" in data
        assert data["hazard_type"] == "fire"
        assert "spread_rooms" in data
        assert "max_spread_radius" in data
        assert data["max_spread_radius"] == 5

        # Deserialize
        restored = InteriorEvent.from_dict(data)

        assert restored.hazard_type == "fire"
        assert restored.max_spread_radius == 5
        assert restored.spread_rooms == original_spread

    def test_hazard_type_none_serializes_correctly(self):
        """Event with no hazard_type still serializes correctly."""
        event = InteriorEvent(
            event_id="normal_event",
            event_type="cave_in",
            location_coords=(0, 0, 0),
            blocked_direction="north",
            start_hour=0,
            duration_hours=10,
        )

        data = event.to_dict()
        restored = InteriorEvent.from_dict(data)

        assert restored.hazard_type is None
        assert restored.spread_rooms is None
        assert restored.max_spread_radius == 3  # Default


# ============================================================================
# Test 12: Test integration with progress_interior_events
# ============================================================================


class TestProgressInteriorEventsIntegration:
    """Tests for integration with progress_interior_events."""

    @pytest.fixture
    def mock_game_state_with_time(self):
        """Create a mock game state with controllable time."""
        game_state = MagicMock()
        game_state.game_time.total_hours = 5
        return game_state

    @pytest.fixture
    def mock_sub_grid_for_progress(self):
        """Create a SubGrid with a spreading hazard for progress testing."""
        sub_grid = MagicMock()
        sub_grid.parent_name = "Test Dungeon"
        sub_grid.bounds = (-5, 5, -5, 5, -1, 1)

        rooms = {}
        for x in range(-2, 3):
            for y in range(-2, 3):
                rooms[(x, y, 0)] = MagicMock(
                    coordinates=(x, y, 0),
                    hazards=[],
                    name=f"Room_{x}_{y}",
                )

        # Origin has hazard
        rooms[(0, 0, 0)].hazards = ["spreading_fire"]

        sub_grid._grid = rooms
        sub_grid.is_within_bounds = lambda x, y, z: -5 <= x <= 5 and -5 <= y <= 5
        sub_grid.get_by_coordinates = MagicMock(
            side_effect=lambda x, y, z: rooms.get((x, y, z))
        )

        event = InteriorEvent(
            event_id="progress_test",
            event_type="spreading_hazard",
            location_coords=(0, 0, 0),
            blocked_direction="",
            start_hour=0,
            duration_hours=16,
            hazard_type="fire",
            spread_rooms={(0, 0, 0): 0},
            max_spread_radius=3,
        )
        sub_grid.interior_events = [event]

        return sub_grid

    def test_spreading_occurs_during_time_progression(
        self, mock_game_state_with_time, mock_sub_grid_for_progress
    ):
        """Spreading occurs during progress_interior_events call."""
        initial_spread_count = len(
            mock_sub_grid_for_progress.interior_events[0].spread_rooms
        )

        # Progress events (simulating time passing)
        messages = progress_interior_events(
            mock_game_state_with_time, mock_sub_grid_for_progress, hours=1
        )

        # Check that spread occurred
        final_spread_count = len(
            mock_sub_grid_for_progress.interior_events[0].spread_rooms
        )
        assert final_spread_count > initial_spread_count


# ============================================================================
# Test for hazard types in hazards.py
# ============================================================================


class TestHazardTypesUpdated:
    """Tests for hazard types being properly registered."""

    def test_spreading_fire_in_hazard_types(self):
        """spreading_fire should be in HAZARD_TYPES."""
        assert "spreading_fire" in HAZARD_TYPES

    def test_spreading_flood_in_hazard_types(self):
        """spreading_flood should be in HAZARD_TYPES."""
        assert "spreading_flood" in HAZARD_TYPES
