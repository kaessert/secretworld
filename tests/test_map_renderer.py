"""Tests for player-centered map display (5x5 grid).

These tests verify that render_map() displays a 5x5 grid centered on the player's
current location, rather than calculating bounds from all explored locations.
"""

from cli_rpg.map_renderer import render_map
from cli_rpg.models.location import Location


class TestPlayerCenteredMap:
    """Tests for 5x5 player-centered map viewport."""

    def test_map_centered_on_player(self):
        """Verify player position is always at grid center regardless of absolute coordinates.

        Spec: Player should always be at the center of the 5x5 viewport (relative 0,0)
        """
        # Player at (5, 5) with locations scattered around
        world = {
            "Player Location": Location(
                "Player Location", "Current location", {}, coordinates=(5, 5)
            ),
            "Far North": Location("Far North", "Far north", {}, coordinates=(5, 10)),
            "Far East": Location("Far East", "Far east", {}, coordinates=(10, 5)),
        }
        result = render_map(world, "Player Location")

        # The map should show coordinates 3-7 on x-axis (5-2 to 5+2)
        # The map should show coordinates 3-7 on y-axis (5-2 to 5+2)
        # Player @ should be at the center position
        lines = result.split("\n")

        # Find the row with the player's y-coordinate (5)
        player_row = None
        for line in lines:
            if line.strip().startswith("5 ") or line.strip().startswith(" 5 "):
                player_row = line
                break

        assert player_row is not None, "Player's y-coordinate row (5) should be visible"
        assert "@" in player_row, "Player marker @ should be in the row with y=5"

    def test_map_shows_5x5_viewport(self):
        """Verify exactly 5 columns (-2 to +2) and 5 rows (-2 to +2) are displayed.

        Spec: Map should display fixed 5x5 area centered on player
        """
        # Player at origin
        world = {
            "Center": Location("Center", "Center location", {}, coordinates=(0, 0)),
        }
        result = render_map(world, "Center")

        lines = result.split("\n")

        # The map format is:
        # === MAP ===
        #     -2 -1  0  1  2    <- header with x-coordinates
        #  2                     <- data rows with y-coord prefix
        #  1
        #  0         @
        # -1
        # -2
        #
        # Legend: ...

        # Find header line with x-coordinates (has multiple numbers)
        header_line = lines[1]  # Header is always second line after "=== MAP ==="
        assert "-2" in header_line, "Header should contain x-coordinate -2"
        assert "2" in header_line, "Header should contain x-coordinate 2"
        # Check all 5 x-coordinates are present
        for x in range(-2, 3):
            assert str(x) in header_line, f"X-coordinate {x} should be in header"

        # Data rows are lines 2-6 (y from 2 down to -2)
        # Verify we have exactly 5 data rows between header and legend
        data_rows = lines[2:7]  # Lines 2,3,4,5,6
        assert len(data_rows) == 5, f"Should have exactly 5 data rows, got {len(data_rows)}"

        # Verify y-coordinates 2, 1, 0, -1, -2 are present as row labels
        expected_y = [2, 1, 0, -1, -2]
        for i, expected in enumerate(expected_y):
            row = data_rows[i]
            # Each row should start with the y-coordinate
            assert row.strip().startswith(str(expected)), (
                f"Row {i} should start with y={expected}, got: {row}"
            )

    def test_map_clips_locations_outside_viewport(self):
        """Verify locations >2 tiles away are not shown on map grid.

        Spec: Locations more than 2 tiles away from player should not appear in grid
        """
        # Player at (0,0), with a location far away at (10, 10)
        world = {
            "Center": Location("Center", "Center location", {}, coordinates=(0, 0)),
            "Far Away": Location("Far Away", "Very far location", {}, coordinates=(10, 10)),
        }
        result = render_map(world, "Center")

        # The "F" marker for "Far Away" should NOT appear in the map grid
        # (though it may appear in legend if we include explored locations)
        lines = result.split("\n")

        # Find the data rows (before legend)
        map_section = []
        in_map = False
        for line in lines:
            if "===" in line:
                in_map = True
                continue
            if "Legend" in line:
                break
            if in_map:
                map_section.append(line)

        map_content = "\n".join(map_section)

        # F for "Far Away" should not appear in the map grid portion
        # The grid only shows -2 to 2 on both axes
        assert (
            "F" not in map_content
        ), "Far Away location (F) should not appear in 5x5 viewport"

    def test_map_handles_player_at_origin(self):
        """Player at (0,0) shows grid from (-2,-2) to (2,2).

        Spec: When player is at origin, viewport spans -2 to +2 on both axes
        """
        world = {
            "Origin": Location("Origin", "The origin", {}, coordinates=(0, 0)),
            "NorthEast": Location("NorthEast", "NE corner", {}, coordinates=(2, 2)),
            "SouthWest": Location("SouthWest", "SW corner", {}, coordinates=(-2, -2)),
        }
        result = render_map(world, "Origin")

        lines = result.split("\n")

        # Verify x-axis shows -2 to 2
        header = None
        for line in lines:
            if "-2" in line and "-1" in line and "0" in line and "1" in line and "2" in line:
                header = line
                break
        assert header is not None, "Header should contain all x-coordinates from -2 to 2"

        # Verify y-axis shows -2 to 2 (check for rows with these y-values)
        y_coords_found = set()
        for line in lines:
            stripped = line.strip()
            if stripped:
                parts = stripped.split()
                if parts:
                    try:
                        y = int(parts[0])
                        if -2 <= y <= 2:
                            y_coords_found.add(y)
                    except ValueError:
                        pass

        expected_y_coords = {-2, -1, 0, 1, 2}
        assert y_coords_found == expected_y_coords, (
            f"Should have y-coordinates {expected_y_coords}, got {y_coords_found}"
        )

    def test_map_handles_player_at_large_coordinates(self):
        """Player at (100,50) shows grid from (98,48) to (102,52).

        Spec: Viewport should be relative to player position at large coordinates
        """
        world = {
            "Distant": Location("Distant", "A distant place", {}, coordinates=(100, 50)),
            "Nearby": Location("Nearby", "Close by", {}, coordinates=(101, 51)),
        }
        result = render_map(world, "Distant")

        lines = result.split("\n")

        # Verify x-axis shows 98 to 102
        header = None
        for line in lines:
            if "98" in line and "102" in line:
                header = line
                break
        assert header is not None, "Header should contain x-coordinates 98 to 102"

        # Verify specific coordinates are present
        for x in [98, 99, 100, 101, 102]:
            assert str(x) in header, f"X-coordinate {x} should be in header"

        # Verify y-axis shows 48 to 52
        y_coords_found = set()
        for line in lines:
            stripped = line.strip()
            if stripped:
                parts = stripped.split()
                if parts:
                    try:
                        y = int(parts[0])
                        if 48 <= y <= 52:
                            y_coords_found.add(y)
                    except ValueError:
                        pass

        expected_y_coords = {48, 49, 50, 51, 52}
        assert y_coords_found == expected_y_coords, (
            f"Should have y-coordinates {expected_y_coords}, got {y_coords_found}"
        )

        # Verify both @ (player) and N (Nearby) are visible
        assert "@" in result, "Player marker @ should be visible"
        assert "N" in result, "Nearby location N should be visible"

    def test_colored_marker_alignment(self):
        """Verify colored @ marker aligns correctly with uncolored markers.

        Spec: ANSI color codes in the player marker should not break column alignment.
        The @ marker with color codes should occupy the same visual width as other markers.
        """
        # Player at (0,0) with a nearby location at (1,0) - same row
        world = {
            "Center": Location("Center", "Center location", {}, coordinates=(0, 0)),
            "East": Location("East", "East location", {}, coordinates=(1, 0)),
        }
        result = render_map(world, "Center")

        lines = result.split("\n")

        # Find the row with y=0 (both markers should be on this row)
        row_y0 = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("0 ") or stripped.startswith(" 0 "):
                row_y0 = line
                break

        assert row_y0 is not None, "Row with y=0 should exist"

        # Strip ANSI codes to get the visual representation
        import re

        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        clean_row = ansi_escape.sub("", row_y0)

        # In the clean row, @ and E should be properly spaced
        # With cell_width=3, markers should be right-aligned in their cells
        # The pattern should be consistent spacing between markers

        # Find positions of @ and E in the cleaned row
        at_pos = clean_row.find("@")
        e_pos = clean_row.find("E")

        assert at_pos >= 0, "@ marker should be in the row"
        assert e_pos >= 0, "E marker should be in the row"

        # E is at x=1 (one cell to the right of @)
        # With cell_width=3, E should be exactly 3 characters after @
        assert e_pos - at_pos == 3, (
            f"E should be 3 characters after @, but gap is {e_pos - at_pos}. "
            f"Row: '{clean_row}'"
        )

    def test_exits_displayed_on_map(self):
        """Verify available exits are shown on the map below the legend.

        Spec: The map should display "Exits: north, east" etc. showing available
        directions from the current location.
        """
        world = {
            "Center": Location(
                "Center",
                "Center location",
                {"north": "North", "east": "East"},
                coordinates=(0, 0),
            ),
            "North": Location("North", "North location", {}, coordinates=(0, 1)),
            "East": Location("East", "East location", {}, coordinates=(1, 0)),
        }
        result = render_map(world, "Center")

        # Check that exits line is present
        assert "Exits:" in result, "Map should display exits"
        # Check that specific exits are shown
        assert "east" in result.lower(), "Map should show 'east' exit"
        assert "north" in result.lower(), "Map should show 'north' exit"

    def test_exits_displayed_when_no_connections(self):
        """Verify exits line shows when location has no connections.

        Spec: Even with no exits, the map should display "Exits: None"
        """
        world = {
            "Isolated": Location(
                "Isolated", "An isolated location", {}, coordinates=(0, 0)
            ),
        }
        result = render_map(world, "Isolated")

        # Should show exits line even with no connections
        assert "Exits:" in result, "Map should display exits line"
        assert "none" in result.lower(), "Map should indicate no exits available"
