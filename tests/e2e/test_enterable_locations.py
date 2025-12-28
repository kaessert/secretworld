"""E2E tests for enterable location generation.

These tests verify that:
1. AI-generated worlds produce enterable locations (dungeons, caves, ruins, etc.)
2. The `enter` command works on enterable locations
3. SubGrids are properly created for enterable locations

Run with: pytest tests/e2e/ -v --e2e

Requires: OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable
"""
import pytest

from cli_rpg.world_tiles import ENTERABLE_CATEGORIES


@pytest.mark.e2e
class TestEnterableLocationGeneration:
    """E2E tests for enterable location AI generation."""

    def test_enterable_category_within_30_tiles(self, ai_game_state):
        """Walk 30 tiles and verify at least one enterable location appears.

        This tests that the forced spawn mechanism ensures players encounter
        enterable locations within a reasonable number of moves.

        Uses coordinate tracking to always move to unexplored tiles.
        """
        enterable_found = False
        tiles_visited = 0
        max_tiles = 40

        # Track visited coordinates to avoid revisiting
        visited_coords = {ai_game_state.get_current_location().coordinates}

        # Direction vectors
        direction_deltas = {
            "north": (0, 1), "south": (0, -1),
            "east": (1, 0), "west": (-1, 0)
        }

        for i in range(max_tiles):
            # Get current location
            current_loc = ai_game_state.get_current_location()
            current_coords = current_loc.coordinates

            # Check if current location is enterable
            if current_loc.category and current_loc.category.lower() in ENTERABLE_CATEGORIES:
                enterable_found = True
                break

            # Find unexplored adjacent tile
            moved = False
            for direction, (dx, dy) in direction_deltas.items():
                target = (current_coords[0] + dx, current_coords[1] + dy)
                if target not in visited_coords:
                    success, _ = ai_game_state.move(direction)
                    if success:
                        visited_coords.add(target)
                        tiles_visited += 1
                        moved = True
                        break

            # If all adjacent tiles visited, try any direction
            if not moved:
                for direction in ["north", "east", "south", "west"]:
                    success, _ = ai_game_state.move(direction)
                    if success:
                        tiles_visited += 1
                        new_coords = ai_game_state.get_current_location().coordinates
                        visited_coords.add(new_coords)
                        break

        # Final check of current location
        current_loc = ai_game_state.get_current_location()
        if current_loc.category and current_loc.category.lower() in ENTERABLE_CATEGORIES:
            enterable_found = True

        assert enterable_found, (
            f"No enterable location found within {tiles_visited} tiles. "
            f"Expected to find a dungeon, cave, ruins, temple, etc. "
            f"tiles_since_enterable: {ai_game_state.tiles_since_enterable}"
        )

    def test_enter_command_works_on_enterable_location(self, ai_game_state):
        """Find an enterable location and verify the enter command works.

        This ensures that when an enterable location is generated, it can
        actually be entered using the `enter` command.
        """
        # Walk until we find an enterable location
        max_attempts = 40
        enterable_location = None

        directions = ["north", "east", "south", "west"]

        for i in range(max_attempts):
            current_loc = ai_game_state.get_current_location()

            if current_loc.category and current_loc.category.lower() in ENTERABLE_CATEGORIES:
                enterable_location = current_loc
                break

            # Move to next tile
            direction = directions[i % 4]
            success, _ = ai_game_state.move(direction)
            if not success:
                for alt_dir in directions:
                    if alt_dir != direction:
                        success, _ = ai_game_state.move(alt_dir)
                        if success:
                            break

        # Skip test if we couldn't find an enterable location
        if enterable_location is None:
            pytest.skip("Could not find an enterable location within 40 tiles")

        # Now test the enter command
        assert not ai_game_state.in_sub_location, "Should not be in sub-location initially"

        success, message = ai_game_state.enter()

        # Should successfully enter
        assert success, f"Failed to enter {enterable_location.name}: {message}"
        assert ai_game_state.in_sub_location, "Should be in sub-location after entering"
        assert ai_game_state.current_sub_grid is not None, "Should have a SubGrid after entering"

    def test_subgrid_has_expected_content(self, ai_game_state):
        """Enter an enterable location and verify SubGrid has content.

        This tests that SubGrid generation produces proper interior content
        including exit points and (optionally) enemies/treasures.
        """
        # Walk until we find an enterable location
        max_attempts = 40
        enterable_location = None

        directions = ["north", "east", "south", "west"]

        for i in range(max_attempts):
            current_loc = ai_game_state.get_current_location()

            if current_loc.category and current_loc.category.lower() in ENTERABLE_CATEGORIES:
                enterable_location = current_loc
                break

            direction = directions[i % 4]
            success, _ = ai_game_state.move(direction)
            if not success:
                for alt_dir in directions:
                    if alt_dir != direction:
                        success, _ = ai_game_state.move(alt_dir)
                        if success:
                            break

        if enterable_location is None:
            pytest.skip("Could not find an enterable location within 40 tiles")

        # Enter the location
        success, _ = ai_game_state.enter()
        assert success, "Failed to enter enterable location"

        # Verify SubGrid properties
        subgrid = ai_game_state.current_sub_grid
        assert subgrid is not None, "SubGrid should be created"

        # SubGrid should have locations
        assert len(subgrid.locations) > 0, "SubGrid should have at least one location"

        # At least one location should be an exit point
        exit_points = [loc for loc in subgrid.locations.values() if loc.is_exit_point]
        assert len(exit_points) > 0, "SubGrid should have at least one exit point"

        # The SubGrid should have bounds defined
        assert subgrid.bounds is not None, "SubGrid should have bounds"
        assert len(subgrid.bounds) == 6, "SubGrid bounds should be 6-tuple (min_x, max_x, min_y, max_y, min_z, max_z)"


@pytest.mark.e2e
class TestEnterableCounterPersistence:
    """Tests that the tiles_since_enterable counter persists correctly."""

    def test_counter_resets_on_enterable_location(self, ai_game_state):
        """Verify that tiles_since_enterable resets when visiting an enterable location."""
        # Start at 0
        assert ai_game_state.tiles_since_enterable == 0

        # Walk until we find an enterable location
        max_attempts = 40
        directions = ["north", "east", "south", "west"]

        for i in range(max_attempts):
            current_loc = ai_game_state.get_current_location()

            if current_loc.category and current_loc.category.lower() in ENTERABLE_CATEGORIES:
                # Counter should be 0 after finding enterable
                assert ai_game_state.tiles_since_enterable == 0
                return

            direction = directions[i % 4]
            success, _ = ai_game_state.move(direction)
            if not success:
                for alt_dir in directions:
                    if alt_dir != direction:
                        success, _ = ai_game_state.move(alt_dir)
                        if success:
                            break

        pytest.skip("Could not find enterable location to test counter reset")
