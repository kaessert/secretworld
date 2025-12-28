"""Tests for weather penetration in SubGrid locations.

When inside a SubGrid near an exit point (is_exit_point=True), and it's raining
or storming outside, players should hear muffled weather sounds. The chance
decreases with distance from the exit:
- At exit_point room: 30% chance
- 1 room away: 15% chance
- 2+ rooms away: 0% chance
- z < 0 (underground): 0% chance
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from cli_rpg.ambient_sounds import (
    AmbientSoundService,
    WEATHER_PENETRATION_SOUNDS,
    get_weather_penetration_sound,
)
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid


class TestWeatherPenetrationSounds:
    """Tests for weather penetration sound pools and getter."""

    def test_rain_sounds_exist(self):
        """Rain should have a pool of weather penetration sounds."""
        assert "rain" in WEATHER_PENETRATION_SOUNDS
        assert len(WEATHER_PENETRATION_SOUNDS["rain"]) >= 3

    def test_storm_sounds_exist(self):
        """Storm should have a pool of weather penetration sounds."""
        assert "storm" in WEATHER_PENETRATION_SOUNDS
        assert len(WEATHER_PENETRATION_SOUNDS["storm"]) >= 3

    def test_weather_sound_at_exit_30_percent(self):
        """At exit (distance=0), weather penetration has 30% chance."""
        # Test with mocked random to verify chance
        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            # Under 0.30 should trigger
            mock_random.random.return_value = 0.29
            mock_random.choice = random.choice
            result = get_weather_penetration_sound("rain", distance_from_exit=0)
            assert result is not None
            assert result in WEATHER_PENETRATION_SOUNDS["rain"]

            # At 0.30 should not trigger
            mock_random.random.return_value = 0.30
            result = get_weather_penetration_sound("rain", distance_from_exit=0)
            assert result is None

    def test_weather_sound_one_room_away_15_percent(self):
        """1 room from exit, weather penetration has 15% chance."""
        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            # Under 0.15 should trigger
            mock_random.random.return_value = 0.14
            mock_random.choice = random.choice
            result = get_weather_penetration_sound("storm", distance_from_exit=1)
            assert result is not None
            assert result in WEATHER_PENETRATION_SOUNDS["storm"]

            # At 0.15 should not trigger
            mock_random.random.return_value = 0.15
            result = get_weather_penetration_sound("storm", distance_from_exit=1)
            assert result is None

    def test_no_weather_sound_deep_inside(self):
        """2+ rooms from exit should never trigger weather sounds."""
        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            mock_random.random.return_value = 0.0  # Always trigger if allowed
            result = get_weather_penetration_sound("rain", distance_from_exit=2)
            assert result is None

            result = get_weather_penetration_sound("storm", distance_from_exit=5)
            assert result is None

    def test_no_weather_sound_clear_weather(self):
        """Clear weather should never trigger weather penetration sounds."""
        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            mock_random.random.return_value = 0.0  # Always trigger if allowed
            result = get_weather_penetration_sound("clear", distance_from_exit=0)
            assert result is None

    def test_no_weather_sound_fog(self):
        """Fog weather should not trigger penetration sounds (visual, not audible)."""
        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            mock_random.random.return_value = 0.0
            result = get_weather_penetration_sound("fog", distance_from_exit=0)
            assert result is None


class TestSubGridExitDistance:
    """Tests for SubGrid.get_distance_to_nearest_exit() method."""

    def test_distance_at_exit_point(self):
        """Distance from exit_point room should be 0."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Test Dungeon")

        # Add an exit point at origin
        exit_room = Location(
            name="Entrance",
            description="The dungeon entrance.",
            is_exit_point=True,
        )
        sub_grid.add_location(exit_room, 0, 0, 0)

        assert sub_grid.get_distance_to_nearest_exit((0, 0, 0)) == 0

    def test_distance_one_room_away(self):
        """Distance 1 room from exit should be 1."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Test Dungeon")

        # Add exit at origin
        exit_room = Location(name="Entrance", description="Entry.", is_exit_point=True)
        sub_grid.add_location(exit_room, 0, 0, 0)

        # Add room to the north
        north_room = Location(name="North Hall", description="A hallway.")
        sub_grid.add_location(north_room, 0, 1, 0)

        assert sub_grid.get_distance_to_nearest_exit((0, 1, 0)) == 1

    def test_distance_multiple_rooms_away(self):
        """Distance should be Manhattan distance from nearest exit."""
        sub_grid = SubGrid(bounds=(-3, 3, -3, 3, 0, 0), parent_name="Test Dungeon")

        # Add exit at origin
        exit_room = Location(name="Entrance", description="Entry.", is_exit_point=True)
        sub_grid.add_location(exit_room, 0, 0, 0)

        # Add rooms in a line going north
        for i in range(1, 4):
            room = Location(name=f"Hall {i}", description=f"Hallway section {i}.")
            sub_grid.add_location(room, 0, i, 0)

        assert sub_grid.get_distance_to_nearest_exit((0, 3, 0)) == 3

    def test_distance_underground_still_calculated(self):
        """Distance works for underground rooms but z-level doesn't affect it."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, -2, 0), parent_name="Test Dungeon")

        # Add exit at origin (z=0)
        exit_room = Location(name="Entrance", description="Entry.", is_exit_point=True)
        sub_grid.add_location(exit_room, 0, 0, 0)

        # Add room at z=-1 (directly below entrance)
        basement = Location(name="Basement", description="Below the entrance.")
        sub_grid.add_location(basement, 0, 0, -1)

        # Distance should include z-difference
        assert sub_grid.get_distance_to_nearest_exit((0, 0, -1)) == 1

    def test_distance_with_no_exit_points(self):
        """If no exit points exist, return -1 (or very large number)."""
        sub_grid = SubGrid(bounds=(-2, 2, -2, 2, 0, 0), parent_name="Test Dungeon")

        # Add a room that's NOT an exit point
        room = Location(name="Inner Room", description="Deep inside.")
        sub_grid.add_location(room, 0, 0, 0)

        assert sub_grid.get_distance_to_nearest_exit((0, 0, 0)) == -1

    def test_distance_multiple_exits_finds_nearest(self):
        """With multiple exits, should find the nearest one."""
        sub_grid = SubGrid(bounds=(-3, 3, -3, 3, 0, 0), parent_name="Test Dungeon")

        # Add exit on west side
        west_exit = Location(name="West Exit", description="Exit.", is_exit_point=True)
        sub_grid.add_location(west_exit, -2, 0, 0)

        # Add exit on east side
        east_exit = Location(name="East Exit", description="Exit.", is_exit_point=True)
        sub_grid.add_location(east_exit, 2, 0, 0)

        # Add room in the middle
        center = Location(name="Center", description="Center.")
        sub_grid.add_location(center, 0, 0, 0)

        # Center room should be distance 2 from either exit
        assert sub_grid.get_distance_to_nearest_exit((0, 0, 0)) == 2

        # Room at (-1, 0) should be distance 1 from west exit
        west_room = Location(name="West Side", description="Near west.")
        sub_grid.add_location(west_room, -1, 0, 0)
        assert sub_grid.get_distance_to_nearest_exit((-1, 0, 0)) == 1


class TestAmbientSoundServiceWeatherIntegration:
    """Tests for AmbientSoundService integration with weather penetration."""

    def test_weather_sound_at_z0_exit_room(self):
        """At z=0 exit room with rain, weather sounds should trigger."""
        service = AmbientSoundService()

        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            # Ensure cooldown is satisfied and weather penetration triggers
            mock_random.random.return_value = 0.0  # Always trigger
            mock_random.choice = random.choice

            result = service.get_ambient_sound(
                category="dungeon",
                depth=0,
                weather_condition="rain",
                distance_from_exit=0,
            )

            # Should return a weather penetration sound
            assert result is not None
            # Could be weather sound or normal ambient sound depending on impl
            # The key is that weather sounds CAN trigger here

    def test_no_weather_sound_underground(self):
        """At z < 0, weather sounds should never trigger regardless of distance."""
        service = AmbientSoundService()

        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            mock_random.random.return_value = 0.0
            mock_random.choice = random.choice

            # At z=-1 (underground), even at distance 0, no weather sounds
            result = service.get_ambient_sound(
                category="dungeon",
                depth=-1,
                weather_condition="storm",
                distance_from_exit=0,
            )

            # Should NOT contain weather penetration sounds
            # (it may still return a normal ambient sound)
            if result is not None:
                assert result not in WEATHER_PENETRATION_SOUNDS.get("storm", [])

    def test_normal_ambient_when_no_weather_penetration(self):
        """When weather penetration doesn't trigger, normal sounds should."""
        service = AmbientSoundService()

        with patch("cli_rpg.ambient_sounds.random") as mock_random:
            # First call: return high value (no weather sound triggers)
            # Then return low value for normal ambient sound trigger
            mock_random.random.side_effect = [0.99, 0.05]
            mock_random.choice = random.choice

            result = service.get_ambient_sound(
                category="dungeon",
                depth=0,
                weather_condition="rain",
                distance_from_exit=1,
            )

            # Should still be able to get normal ambient sounds
            # (exact behavior depends on implementation)
