"""Tests for WFC-aware exit filtering (Bug #5 fix).

These tests verify that exits displayed to the player are filtered to only show
directions where WFC terrain is passable, preventing the "Can't go that way"
message when the map shows an exit exists.
"""

import pytest
from unittest.mock import Mock, MagicMock

from cli_rpg.models.location import Location
from cli_rpg.world import generate_fallback_location
from cli_rpg.map_renderer import render_map
from cli_rpg.world_tiles import TERRAIN_PASSABLE


class TestLocationExitFiltering:
    """Tests for Location.get_filtered_directions() method."""

    def test_get_filtered_directions_excludes_water_exits(self):
        """Exits blocked by water terrain should not be returned.

        Spec: get_filtered_directions() excludes directions where WFC terrain is impassable.
        """
        # Create a location with exits in all four directions
        location = Location(
            name="Test Location",
            description="A test location",
            connections={
                "north": "Northern Woods",
                "south": "Southern Plains",
                "east": "Eastern Shore",
                "west": "Western Hills"
            },
            coordinates=(5, 5)
        )

        # Create mock ChunkManager that returns water to the east
        chunk_manager = Mock()
        def get_tile_at(x, y):
            if x == 6 and y == 5:  # East of (5, 5)
                return "water"
            return "plains"
        chunk_manager.get_tile_at = get_tile_at

        # Get filtered directions
        filtered = location.get_filtered_directions(chunk_manager)

        # East should be excluded due to water
        assert "east" not in filtered
        assert "north" in filtered
        assert "south" in filtered
        assert "west" in filtered

    def test_get_filtered_directions_allows_passable_terrain(self):
        """Exits with passable terrain should be included.

        Spec: get_filtered_directions() includes directions where WFC terrain is passable.
        """
        location = Location(
            name="Test Location",
            description="A test location",
            connections={
                "north": "Forest North",
                "south": "Plains South",
            },
            coordinates=(0, 0)
        )

        # Create mock ChunkManager that returns passable terrain
        chunk_manager = Mock()
        chunk_manager.get_tile_at = Mock(return_value="forest")

        filtered = location.get_filtered_directions(chunk_manager)

        # All exits should be included
        assert "north" in filtered
        assert "south" in filtered

    def test_get_filtered_directions_without_chunk_manager_returns_all(self):
        """Without ChunkManager, all exits should be returned.

        Spec: get_filtered_directions(None) returns all directions (backward compatibility).
        """
        location = Location(
            name="Test Location",
            description="A test location",
            connections={
                "north": "Location A",
                "east": "Location B",
            },
            coordinates=(0, 0)
        )

        # Without chunk_manager, should return all
        filtered = location.get_filtered_directions(None)

        assert "north" in filtered
        assert "east" in filtered

    def test_get_filtered_directions_no_coordinates_returns_all(self):
        """Without coordinates, all exits should be returned (legacy locations).

        Spec: Locations without coordinates skip WFC filtering.
        """
        location = Location(
            name="Test Location",
            description="A test location",
            connections={
                "north": "Location A",
            },
            coordinates=None  # No coordinates
        )

        chunk_manager = Mock()
        chunk_manager.get_tile_at = Mock(return_value="water")

        # Should return all because we can't calculate target coords
        filtered = location.get_filtered_directions(chunk_manager)
        assert "north" in filtered


class TestLayeredDescriptionFiltering:
    """Tests for get_layered_description() with WFC filtering."""

    def test_layered_description_shows_only_passable_exits(self):
        """get_layered_description should show only passable exits when chunk_manager provided.

        Spec: Exits shown in description must exclude WFC-blocked directions.
        """
        location = Location(
            name="Test Location",
            description="A test location with several exits.",
            connections={
                "north": "Northern Pass",
                "east": "Eastern Lake",  # Will be water
            },
            coordinates=(10, 10)
        )

        # Mock ChunkManager - east is water
        chunk_manager = Mock()
        def get_tile_at(x, y):
            if x == 11 and y == 10:  # East of (10, 10)
                return "water"
            return "plains"
        chunk_manager.get_tile_at = get_tile_at

        description = location.get_layered_description(
            look_count=1,
            visibility="full",
            chunk_manager=chunk_manager
        )

        # Description should show north but not east
        assert "Exits:" in description
        assert "north" in description
        assert "east" not in description


class TestMapRendererFiltering:
    """Tests for render_map() exit filtering with WFC."""

    def test_render_map_shows_only_passable_exits(self):
        """render_map should filter exits to only passable terrain.

        Spec: Map display's "Exits:" line excludes WFC-blocked directions.
        """
        # Create a location with multiple exits
        location = Location(
            name="Test Location",
            description="Test",
            connections={
                "north": "Northern Forest",
                "south": "Southern Water",  # Will be blocked by water
            },
            coordinates=(0, 0)
        )

        world = {"Test Location": location}

        # Mock ChunkManager - south is water
        chunk_manager = Mock()
        def get_tile_at(x, y):
            if y == -1:  # South of (0, 0)
                return "water"
            return "forest"
        chunk_manager.get_tile_at = get_tile_at

        map_output = render_map(
            world, "Test Location", chunk_manager=chunk_manager
        )

        # Find the exits line
        lines = map_output.split("\n")
        exits_line = next((l for l in lines if l.startswith("Exits:")), None)

        assert exits_line is not None
        assert "north" in exits_line
        assert "south" not in exits_line


class TestFallbackLocationGeneration:
    """Tests for generate_fallback_location() WFC-aware exit creation."""

    def test_fallback_location_no_water_exits(self):
        """Fallback location should not add exits pointing to water terrain.

        Spec: generate_fallback_location() checks WFC before adding dangling exits.
        """
        source = Location(
            name="Source Location",
            description="The source",
            coordinates=(0, 0)
        )

        # Mock ChunkManager where all directions except south are water
        chunk_manager = Mock()
        def get_tile_at(x, y):
            # East, west, and north are water; south is the return path
            if y >= 0:  # North and current row
                return "water"
            return "plains"
        chunk_manager.get_tile_at = get_tile_at

        # Generate fallback location going north to (0, 1)
        new_location = generate_fallback_location(
            direction="north",
            source_location=source,
            target_coords=(0, 1),
            terrain="plains",
            chunk_manager=chunk_manager
        )

        # Should have south (back to source) but no other exits to water
        assert "south" in new_location.connections
        # Check that no exit points to water terrain
        for exit_dir in ["north", "east", "west"]:
            if exit_dir in new_location.connections:
                # Calculate target coords for this exit
                offsets = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
                dx, dy = offsets[exit_dir]
                target_x = new_location.coordinates[0] + dx
                target_y = new_location.coordinates[1] + dy
                terrain = chunk_manager.get_tile_at(target_x, target_y)
                assert terrain != "water", f"Exit {exit_dir} points to impassable water"


class TestIntegration:
    """Integration tests for displayed exits matching traversable directions."""

    def test_displayed_exits_match_traversable_directions(self):
        """All displayed exits should be traversable (WFC-passable).

        Spec: If an exit is shown, movement in that direction should not fail
        due to impassable terrain (assuming the connection exists).
        """
        # Create a location with exits
        location = Location(
            name="Crossroads",
            description="A crossroads with paths in all directions.",
            connections={
                "north": "Northern Path",
                "south": "Southern Path",
                "east": "Eastern Path",
                "west": "Western Path",
            },
            coordinates=(5, 5)
        )

        # Create mock ChunkManager - north is water, others are passable
        chunk_manager = Mock()
        def get_tile_at(x, y):
            if y == 6 and x == 5:  # North of (5, 5)
                return "water"
            return "plains"
        chunk_manager.get_tile_at = get_tile_at

        # Get filtered directions
        filtered = location.get_filtered_directions(chunk_manager)

        # Verify each filtered direction has passable terrain
        offsets = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
        for direction in filtered:
            dx, dy = offsets[direction]
            target_x = location.coordinates[0] + dx
            target_y = location.coordinates[1] + dy
            terrain = chunk_manager.get_tile_at(target_x, target_y)
            is_passable = TERRAIN_PASSABLE.get(terrain, True)
            assert is_passable, f"Direction {direction} with terrain {terrain} should be passable"

        # Verify north was excluded
        assert "north" not in filtered
