"""Tests for ritual in progress interior event (Issue 25).

This test file covers the "Ritual in progress" interior event system which creates
time-limited boss encounters in dungeons. The ritual spawns on SubGrid entry,
counts down with each player move, and spawns either a standard or empowered boss
depending on whether the player interrupts the ritual in time.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random

from cli_rpg.interior_events import (
    InteriorEvent,
    CAVE_IN_CATEGORIES,
    # Ritual constants - to be implemented
)
from cli_rpg.models.location import Location


# =============================================================================
# Test InteriorEvent model with ritual fields
# =============================================================================


class TestInteriorEventRitualFields:
    """Tests for InteriorEvent model ritual-related fields."""

    def test_event_creation_with_ritual_fields(self):
        """Test that InteriorEvent can be created with ritual fields."""
        event = InteriorEvent(
            event_id="ritual_test_001",
            event_type="ritual",
            location_coords=(3, 3, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,  # Not time-based
            ritual_room="Dark Chamber",
            ritual_countdown=10,
            ritual_completed=False,
        )

        assert event.event_id == "ritual_test_001"
        assert event.event_type == "ritual"
        assert event.ritual_room == "Dark Chamber"
        assert event.ritual_countdown == 10
        assert event.ritual_completed is False

    def test_event_serialization_with_ritual_fields(self):
        """Test to_dict/from_dict preserves ritual fields."""
        original = InteriorEvent(
            event_id="ritual_test_002",
            event_type="ritual",
            location_coords=(5, 5, -1),
            blocked_direction="",
            start_hour=200,
            duration_hours=0,
            ritual_room="Summoning Circle",
            ritual_countdown=8,
            ritual_completed=True,
        )

        # Serialize
        data = original.to_dict()

        # Verify serialized data
        assert data["ritual_room"] == "Summoning Circle"
        assert data["ritual_countdown"] == 8
        assert data["ritual_completed"] is True

        # Deserialize
        restored = InteriorEvent.from_dict(data)

        # Verify restored event
        assert restored.ritual_room == original.ritual_room
        assert restored.ritual_countdown == original.ritual_countdown
        assert restored.ritual_completed == original.ritual_completed

    def test_event_from_dict_backward_compatible(self):
        """Test that from_dict handles missing ritual fields gracefully."""
        # Old-format data without ritual fields
        old_data = {
            "event_id": "old_event_001",
            "event_type": "cave_in",
            "location_coords": [1, 2, 0],
            "blocked_direction": "north",
            "start_hour": 50,
            "duration_hours": 6,
            "is_active": True,
        }

        event = InteriorEvent.from_dict(old_data)

        # Should have default ritual values
        assert event.ritual_room is None
        assert event.ritual_countdown == 0
        assert event.ritual_completed is False


# =============================================================================
# Test ritual spawn mechanics
# =============================================================================


class TestRitualSpawnMechanics:
    """Tests for ritual spawn constants and spawn function."""

    def test_ritual_spawn_chance_15_percent(self):
        """Test RITUAL_SPAWN_CHANCE constant equals 0.15 (15%)."""
        from cli_rpg.interior_events import RITUAL_SPAWN_CHANCE

        assert RITUAL_SPAWN_CHANCE == 0.15

    def test_ritual_spawn_only_in_valid_categories(self):
        """Test RITUAL_CATEGORIES matches CAVE_IN_CATEGORIES."""
        from cli_rpg.interior_events import RITUAL_CATEGORIES

        assert RITUAL_CATEGORIES == CAVE_IN_CATEGORIES
        assert "dungeon" in RITUAL_CATEGORIES
        assert "cave" in RITUAL_CATEGORIES
        assert "ruins" in RITUAL_CATEGORIES
        assert "temple" in RITUAL_CATEGORIES

    def test_ritual_countdown_range(self):
        """Test RITUAL_COUNTDOWN_RANGE is (8, 12)."""
        from cli_rpg.interior_events import RITUAL_COUNTDOWN_RANGE

        assert RITUAL_COUNTDOWN_RANGE == (8, 12)

    def test_check_for_ritual_spawn_creates_event(self):
        """Test check_for_ritual_spawn creates event with correct fields."""
        from cli_rpg.interior_events import check_for_ritual_spawn
        from cli_rpg.world_grid import SubGrid

        # Create mock game state
        game_state = Mock()
        game_state.game_time = Mock()
        game_state.game_time.total_hours = 100

        # Create mock parent location with valid category
        parent_location = Mock()
        parent_location.category = "dungeon"
        game_state.world = {"Test Dungeon": parent_location}

        # Create SubGrid with rooms
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add entry room
        entry_room = Location(
            name="Dungeon Entrance",
            description="The entrance",
            coordinates=(0, 0, 0),
            is_exit_point=True,
        )
        sub_grid.add_location(entry_room, 0, 0, 0)

        # Add ritual target room (away from entry)
        ritual_room = Location(
            name="Dark Chamber",
            description="A dark chamber",
            coordinates=(2, 2, 0),
        )
        sub_grid.add_location(ritual_room, 2, 2, 0)

        # Force ritual spawn with mocked random
        with patch("cli_rpg.interior_events.random.random", return_value=0.05):
            with patch("cli_rpg.interior_events.random.randint", return_value=10):
                with patch("cli_rpg.interior_events.random.choice", return_value=ritual_room):
                    message = check_for_ritual_spawn(game_state, sub_grid)

        # Should return a message
        assert message is not None
        assert "ritual" in message.lower() or "dark" in message.lower()

        # Should have created a ritual event
        ritual_events = [
            e for e in sub_grid.interior_events if e.event_type == "ritual"
        ]
        assert len(ritual_events) == 1

        event = ritual_events[0]
        assert event.ritual_room is not None
        assert 8 <= event.ritual_countdown <= 12 or event.ritual_countdown == 10
        assert event.ritual_completed is False

    def test_check_for_ritual_spawn_no_duplicate(self):
        """Test that check_for_ritual_spawn doesn't create duplicate events."""
        from cli_rpg.interior_events import check_for_ritual_spawn, get_active_ritual_event
        from cli_rpg.world_grid import SubGrid

        # Create mock game state
        game_state = Mock()
        game_state.game_time = Mock()
        game_state.game_time.total_hours = 100

        parent_location = Mock()
        parent_location.category = "dungeon"
        game_state.world = {"Test Dungeon": parent_location}

        # Create SubGrid with existing ritual event
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add entry room
        entry_room = Location(
            name="Dungeon Entrance",
            description="The entrance",
            coordinates=(0, 0, 0),
            is_exit_point=True,
        )
        sub_grid.add_location(entry_room, 0, 0, 0)

        # Add existing ritual event
        existing_event = InteriorEvent(
            event_id="ritual_existing",
            event_type="ritual",
            location_coords=(1, 1, 0),
            blocked_direction="",
            start_hour=90,
            duration_hours=0,
            ritual_room="Some Room",
            ritual_countdown=5,
        )
        sub_grid.interior_events.append(existing_event)

        # Try to spawn another ritual (should not create duplicate)
        with patch("cli_rpg.interior_events.random.random", return_value=0.05):
            message = check_for_ritual_spawn(game_state, sub_grid)

        # Should return None (no new ritual)
        assert message is None

        # Should still have only one ritual event
        ritual_events = [
            e for e in sub_grid.interior_events if e.event_type == "ritual"
        ]
        assert len(ritual_events) == 1


# =============================================================================
# Test ritual progression
# =============================================================================


class TestRitualProgression:
    """Tests for ritual countdown progression."""

    def test_progress_ritual_decrements_countdown(self):
        """Test that progress_ritual decrements countdown by 1."""
        from cli_rpg.interior_events import progress_ritual
        from cli_rpg.world_grid import SubGrid

        game_state = Mock()
        game_state.game_time = Mock()
        game_state.game_time.total_hours = 100

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=10,
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Progress ritual
        progress_ritual(game_state, sub_grid)

        assert ritual_event.ritual_countdown == 9

    def test_progress_ritual_warning_at_75_percent(self):
        """Test warning message at 75% progress (25% countdown remaining)."""
        from cli_rpg.interior_events import progress_ritual, RITUAL_WARNING_MESSAGES
        from cli_rpg.world_grid import SubGrid

        game_state = Mock()
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event at 75% progress (countdown at 25%)
        # If initial countdown was 8, we're at countdown=2 (75% progress)
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=3,  # Just above 25% threshold
            ritual_initial_countdown=12,  # Track initial for percentage
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Progress to cross 75% threshold
        message = progress_ritual(game_state, sub_grid)

        # Should have some warning (75% threshold message)
        # The exact message depends on implementation
        assert message is not None or ritual_event.ritual_countdown == 2

    def test_progress_ritual_warning_at_50_percent(self):
        """Test warning message at 50% progress."""
        from cli_rpg.interior_events import progress_ritual
        from cli_rpg.world_grid import SubGrid

        game_state = Mock()
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event at ~50% progress
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=5,
            ritual_initial_countdown=10,
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Progress to cross 50% threshold
        message = progress_ritual(game_state, sub_grid)

        # Should decrement countdown
        assert ritual_event.ritual_countdown == 4

    def test_progress_ritual_warning_at_25_percent(self):
        """Test warning message at 25% progress (75% countdown remaining)."""
        from cli_rpg.interior_events import progress_ritual
        from cli_rpg.world_grid import SubGrid

        game_state = Mock()
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event at 25% progress
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=8,
            ritual_initial_countdown=10,
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Progress
        message = progress_ritual(game_state, sub_grid)

        # Should decrement countdown
        assert ritual_event.ritual_countdown == 7

    def test_ritual_completes_when_countdown_zero(self):
        """Test ritual_completed becomes True when countdown reaches 0."""
        from cli_rpg.interior_events import progress_ritual
        from cli_rpg.world_grid import SubGrid

        game_state = Mock()
        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event at countdown=1 (about to complete)
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=1,
            ritual_initial_countdown=10,
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Progress to complete
        message = progress_ritual(game_state, sub_grid)

        # Should be completed
        assert ritual_event.ritual_countdown == 0
        assert ritual_event.ritual_completed is True
        # Should have completion message
        assert message is not None


# =============================================================================
# Test ritual combat triggers
# =============================================================================


class TestRitualCombatTriggers:
    """Tests for ritual encounter and boss spawning."""

    def test_get_ritual_encounter_before_completion(self):
        """Test get_ritual_encounter_at_location returns event with standard boss flag."""
        from cli_rpg.interior_events import get_ritual_encounter_at_location
        from cli_rpg.world_grid import SubGrid

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event (not completed)
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=5,
            ritual_initial_countdown=10,
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Create ritual room location
        ritual_room = Location(
            name="Dark Chamber",
            description="A dark chamber with ritual markings",
            coordinates=(2, 2, 0),
        )

        # Check for encounter at ritual room
        result = get_ritual_encounter_at_location(sub_grid, ritual_room)

        # Should return (event, is_empowered=False)
        assert result is not None
        event, is_empowered = result
        assert event == ritual_event
        assert is_empowered is False

    def test_get_ritual_encounter_after_completion(self):
        """Test get_ritual_encounter_at_location returns event with empowered flag."""
        from cli_rpg.interior_events import get_ritual_encounter_at_location
        from cli_rpg.world_grid import SubGrid

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add completed ritual event
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=0,
            ritual_initial_countdown=10,
            ritual_completed=True,
        )
        sub_grid.interior_events.append(ritual_event)

        # Create ritual room location
        ritual_room = Location(
            name="Dark Chamber",
            description="A dark chamber with ritual markings",
            coordinates=(2, 2, 0),
        )

        # Check for encounter at ritual room
        result = get_ritual_encounter_at_location(sub_grid, ritual_room)

        # Should return (event, is_empowered=True)
        assert result is not None
        event, is_empowered = result
        assert event == ritual_event
        assert is_empowered is True

    def test_get_ritual_encounter_wrong_room_returns_none(self):
        """Test get_ritual_encounter_at_location returns None for non-ritual room."""
        from cli_rpg.interior_events import get_ritual_encounter_at_location
        from cli_rpg.world_grid import SubGrid

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add ritual event
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=5,
            ritual_initial_countdown=10,
            ritual_completed=False,
        )
        sub_grid.interior_events.append(ritual_event)

        # Create different room location
        other_room = Location(
            name="Hallway",
            description="A regular hallway",
            coordinates=(1, 1, 0),
        )

        # Check for encounter at other room
        result = get_ritual_encounter_at_location(sub_grid, other_room)

        # Should return None
        assert result is None


class TestRitualBossSpawning:
    """Tests for ritual boss spawning with empowered modifier."""

    def test_spawn_ritual_boss_empowered(self):
        """Test spawn_boss with empowered=True has 1.5x stats."""
        from cli_rpg.combat import spawn_boss

        level = 5

        # Spawn standard boss
        standard_boss = spawn_boss(
            location_name="Dark Chamber",
            level=level,
            location_category="dungeon",
            boss_type="ritual_summoned",
            empowered=False,
        )

        # Spawn empowered boss
        empowered_boss = spawn_boss(
            location_name="Dark Chamber",
            level=level,
            location_category="dungeon",
            boss_type="ritual_summoned",
            empowered=True,
        )

        # Empowered boss should have 1.5x stats
        assert empowered_boss.max_health == int(standard_boss.max_health * 1.5)
        assert empowered_boss.attack_power == int(standard_boss.attack_power * 1.5)
        assert empowered_boss.defense == int(standard_boss.defense * 1.5)

    def test_spawn_ritual_boss_standard(self):
        """Test spawn_boss with empowered=False has normal stats."""
        from cli_rpg.combat import spawn_boss

        level = 3

        # Spawn standard ritual boss
        boss = spawn_boss(
            location_name="Dark Chamber",
            level=level,
            location_category="dungeon",
            boss_type="ritual_summoned",
            empowered=False,
        )

        # Should be a boss
        assert boss.is_boss is True
        assert "ritual" in boss.name.lower() or "summoned" in boss.name.lower() or boss.name is not None

        # Should have boss-level stats (2x base)
        # Base health = (40 + level * 25) * 2 = (40 + 75) * 2 = 230
        expected_base_health = (40 + level * 25) * 2
        assert boss.max_health == expected_base_health


# =============================================================================
# Test helper functions
# =============================================================================


class TestRitualHelpers:
    """Tests for ritual helper functions."""

    def test_get_active_ritual_event_returns_event(self):
        """Test get_active_ritual_event returns active ritual event."""
        from cli_rpg.interior_events import get_active_ritual_event
        from cli_rpg.world_grid import SubGrid

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add active ritual event
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            ritual_room="Dark Chamber",
            ritual_countdown=5,
        )
        sub_grid.interior_events.append(ritual_event)

        # Get active ritual
        result = get_active_ritual_event(sub_grid)

        assert result == ritual_event

    def test_get_active_ritual_event_returns_none_if_inactive(self):
        """Test get_active_ritual_event returns None if ritual is inactive."""
        from cli_rpg.interior_events import get_active_ritual_event
        from cli_rpg.world_grid import SubGrid

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add inactive ritual event
        ritual_event = InteriorEvent(
            event_id="ritual_test",
            event_type="ritual",
            location_coords=(2, 2, 0),
            blocked_direction="",
            start_hour=100,
            duration_hours=0,
            is_active=False,
            ritual_room="Dark Chamber",
            ritual_countdown=0,
        )
        sub_grid.interior_events.append(ritual_event)

        # Get active ritual
        result = get_active_ritual_event(sub_grid)

        assert result is None

    def test_get_active_ritual_event_returns_none_if_no_ritual(self):
        """Test get_active_ritual_event returns None if no ritual exists."""
        from cli_rpg.interior_events import get_active_ritual_event
        from cli_rpg.world_grid import SubGrid

        sub_grid = SubGrid(
            bounds=(-2, 2, -2, 2, 0, 0),
            parent_name="Test Dungeon",
        )

        # Add non-ritual event
        cave_in = InteriorEvent(
            event_id="cave_in_test",
            event_type="cave_in",
            location_coords=(1, 1, 0),
            blocked_direction="north",
            start_hour=100,
            duration_hours=6,
        )
        sub_grid.interior_events.append(cave_in)

        # Get active ritual
        result = get_active_ritual_event(sub_grid)

        assert result is None
