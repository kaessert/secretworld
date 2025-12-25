"""Tests for player-centered map display (9x9 grid).

These tests verify that render_map() displays a 9x9 grid centered on the player's
current location, rather than calculating bounds from all explored locations.
"""

from cli_rpg.map_renderer import render_map
from cli_rpg.models.location import Location


class TestPlayerCenteredMap:
    """Tests for 9x9 player-centered map viewport."""

    def test_map_centered_on_player(self):
        """Verify player position is always at grid center regardless of absolute coordinates.

        Spec: Player should always be at the center of the 9x9 viewport (relative 0,0)
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

        # The map should show coordinates 1-9 on x-axis (5-4 to 5+4)
        # The map should show coordinates 1-9 on y-axis (5-4 to 5+4)
        # Player @ should be at the center position
        lines = result.split("\n")

        # Find the row with the player's y-coordinate (5)
        # Rows are inside box borders, so strip the │ characters
        player_row = None
        for line in lines:
            # Strip box border characters
            content = line.strip("│").strip()
            if content.startswith("5 ") or content.startswith(" 5 "):
                player_row = line
                break

        assert player_row is not None, "Player's y-coordinate row (5) should be visible"
        assert "@" in player_row, "Player marker @ should be in the row with y=5"

    def test_map_shows_9x9_viewport(self):
        """Verify exactly 9 columns (-4 to +4) and 9 rows (-4 to +4) are displayed.

        Spec: Map should display fixed 9x9 area centered on player
        """
        # Player at origin
        world = {
            "Center": Location("Center", "Center location", {}, coordinates=(0, 0)),
        }
        result = render_map(world, "Center")

        lines = result.split("\n")

        # Find header line with x-coordinates (inside box border)
        # Look for the line that has x-coordinates (should have -4 through 4)
        header_line = None
        for line in lines:
            content = line.strip("│").strip()
            if "-4" in content and "4" in content and "-3" in content:
                header_line = content
                break

        assert header_line is not None, "Header line with x-coordinates should exist"
        assert "-4" in header_line, "Header should contain x-coordinate -4"
        assert "4" in header_line, "Header should contain x-coordinate 4"
        # Check all 9 x-coordinates are present
        for x in range(-4, 5):
            assert str(x) in header_line, f"X-coordinate {x} should be in header"

        # Verify we have exactly 9 data rows (y from 4 down to -4)
        # Count rows that start with a y-coordinate number (inside box border)
        # Skip header line by checking that first part is a y-coordinate (not x-coordinates)
        data_rows = []
        for line in lines:
            # Strip box border characters
            content = line.strip("│").strip()
            if content:
                parts = content.split()
                if parts:
                    try:
                        y = int(parts[0])
                        # A y-coordinate row will have only one number at the start,
                        # while header has multiple x-coordinates
                        # Check that the rest of the content doesn't look like x-coordinates
                        if -4 <= y <= 4 and len(parts) == 1:
                            # This is a data row with only y-coord visible (empty cells)
                            data_rows.append(line)
                        elif -4 <= y <= 4 and not all(
                            p.lstrip("-").isdigit() for p in parts[1:4] if p
                        ):
                            # Data row with markers
                            data_rows.append(line)
                    except ValueError:
                        pass

        assert len(data_rows) == 9, f"Should have exactly 9 data rows, got {len(data_rows)}"

        # Verify y-coordinates 4, 3, 2, 1, 0, -1, -2, -3, -4 are present as row labels
        y_coords_found = set()
        for row in data_rows:
            content = row.strip("│").strip()
            parts = content.split()
            if parts:
                try:
                    y = int(parts[0])
                    y_coords_found.add(y)
                except ValueError:
                    pass

        expected_y = {4, 3, 2, 1, 0, -1, -2, -3, -4}
        assert y_coords_found == expected_y, (
            f"Should have y-coordinates {expected_y}, got {y_coords_found}"
        )

    def test_map_clips_locations_outside_viewport(self):
        """Verify locations >4 tiles away are not shown on map grid.

        Spec: Locations more than 4 tiles away from player should not appear in grid
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
            if "┌" in line:  # Top border of the box
                in_map = True
                continue
            if "└" in line:  # Bottom border
                break
            if in_map:
                map_section.append(line)

        map_content = "\n".join(map_section)

        # F for "Far Away" should not appear in the map grid portion
        # The grid only shows -4 to 4 on both axes
        assert (
            "F" not in map_content
        ), "Far Away location (F) should not appear in 9x9 viewport"

    def test_map_handles_player_at_origin(self):
        """Player at (0,0) shows grid from (-4,-4) to (4,4).

        Spec: When player is at origin, viewport spans -4 to +4 on both axes
        """
        world = {
            "Origin": Location("Origin", "The origin", {}, coordinates=(0, 0)),
            "NorthEast": Location("NorthEast", "NE corner", {}, coordinates=(4, 4)),
            "SouthWest": Location("SouthWest", "SW corner", {}, coordinates=(-4, -4)),
        }
        result = render_map(world, "Origin")

        lines = result.split("\n")

        # Verify x-axis shows -4 to 4 (inside box border)
        header = None
        for line in lines:
            content = line.strip("│").strip()
            if "-4" in content and "-3" in content and "0" in content and "3" in content and "4" in content:
                header = content
                break
        assert header is not None, "Header should contain all x-coordinates from -4 to 4"

        # Verify y-axis shows -4 to 4 (check for rows with these y-values, inside box border)
        y_coords_found = set()
        for line in lines:
            content = line.strip("│").strip()
            if content:
                parts = content.split()
                if parts:
                    try:
                        y = int(parts[0])
                        if -4 <= y <= 4:
                            y_coords_found.add(y)
                    except ValueError:
                        pass

        expected_y_coords = {-4, -3, -2, -1, 0, 1, 2, 3, 4}
        assert y_coords_found == expected_y_coords, (
            f"Should have y-coordinates {expected_y_coords}, got {y_coords_found}"
        )

    def test_map_handles_player_at_large_coordinates(self):
        """Player at (100,50) shows grid from (96,46) to (104,54).

        Spec: Viewport should be relative to player position at large coordinates
        """
        world = {
            "Distant": Location("Distant", "A distant place", {}, coordinates=(100, 50)),
            "Nearby": Location("Nearby", "Close by", {}, coordinates=(101, 51)),
        }
        result = render_map(world, "Distant")

        lines = result.split("\n")

        # Verify x-axis shows 96 to 104 (inside box border)
        header = None
        for line in lines:
            content = line.strip("│").strip()
            if "96" in content and "104" in content:
                header = content
                break
        assert header is not None, "Header should contain x-coordinates 96 to 104"

        # Verify specific coordinates are present
        for x in [96, 97, 98, 99, 100, 101, 102, 103, 104]:
            assert str(x) in header, f"X-coordinate {x} should be in header"

        # Verify y-axis shows 46 to 54 (inside box border)
        y_coords_found = set()
        for line in lines:
            content = line.strip("│").strip()
            if content:
                parts = content.split()
                if parts:
                    try:
                        y = int(parts[0])
                        if 46 <= y <= 54:
                            y_coords_found.add(y)
                    except ValueError:
                        pass

        expected_y_coords = {46, 47, 48, 49, 50, 51, 52, 53, 54}
        assert y_coords_found == expected_y_coords, (
            f"Should have y-coordinates {expected_y_coords}, got {y_coords_found}"
        )

        # Verify both @ (player) and • (Nearby - uncategorized) are visible
        assert "@" in result, "Player marker @ should be visible"

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

        # Find the row with y=0 (both markers should be on this row, inside box border)
        row_y0 = None
        for line in lines:
            content = line.strip("│").strip()
            if content.startswith("0 ") or content.startswith(" 0 "):
                row_y0 = line
                break

        assert row_y0 is not None, "Row with y=0 should exist"

        # Strip ANSI codes to get the visual representation
        import re

        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        clean_row = ansi_escape.sub("", row_y0)

        # In the clean row, @ and • (uncategorized marker) should be properly spaced
        # With cell_width=4, markers should be right-aligned in their cells
        # The pattern should be consistent spacing between markers

        # Find positions of @ and • in the cleaned row
        at_pos = clean_row.find("@")
        marker_pos = clean_row.find("•")

        assert at_pos >= 0, "@ marker should be in the row"
        assert marker_pos >= 0, "• marker should be in the row"

        # • is at x=1 (one cell to the right of @)
        # With cell_width=4, • should be exactly 4 characters after @
        assert marker_pos - at_pos == 4, (
            f"• should be 4 characters after @, but gap is {marker_pos - at_pos}. "
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


class TestMapVisualImprovements:
    """Tests for visual improvements: box border, category markers, vertical legend."""

    def test_map_has_box_border(self):
        """Verify map has box-drawing character border.

        Spec: Map should be enclosed in a box using ┌┐└┘─│ characters
        """
        world = {
            "Center": Location("Center", "Center location", {}, coordinates=(0, 0)),
        }
        result = render_map(world, "Center")

        # Check for box-drawing characters
        assert "┌" in result, "Map should have top-left corner (┌)"
        assert "┐" in result, "Map should have top-right corner (┐)"
        assert "└" in result, "Map should have bottom-left corner (└)"
        assert "┘" in result, "Map should have bottom-right corner (┘)"
        assert "─" in result, "Map should have horizontal borders (─)"
        assert "│" in result, "Map should have vertical borders (│)"

    def test_location_markers_show_category(self):
        """Verify locations show category-based markers instead of first letters.

        Spec: Each location type should show its category icon:
        - town: 🏠
        - shop: 🏪
        - dungeon: ⚔
        - forest: 🌲
        - cave: 🕳
        - water: 🌊
        - None/uncategorized: •
        """
        world = {
            "Town Square": Location(
                "Town Square", "A bustling town", {}, coordinates=(0, 0), category="town"
            ),
            "General Store": Location(
                "General Store", "A shop", {}, coordinates=(1, 0), category="shop"
            ),
            "Dark Dungeon": Location(
                "Dark Dungeon", "A dungeon", {}, coordinates=(2, 0), category="dungeon"
            ),
            "Forest Path": Location(
                "Forest Path", "A forest", {}, coordinates=(3, 0), category="forest"
            ),
        }
        result = render_map(world, "Town Square")

        # Player is at Town Square, so @ should be displayed for current location
        assert "@" in result, "Player marker @ should be visible"

        # Other locations should show their category icons
        assert "🏪" in result, "Shop should show 🏪 marker"
        assert "⚔" in result, "Dungeon should show ⚔ marker"
        assert "🌲" in result, "Forest should show 🌲 marker"

    def test_uncategorized_location_shows_default_marker(self):
        """Verify uncategorized locations show the default • marker.

        Spec: Locations without a category should show • instead of first letter
        """
        world = {
            "Center": Location("Center", "Center location", {}, coordinates=(0, 0)),
            "Nearby": Location(
                "Nearby", "A nearby location", {}, coordinates=(1, 0), category=None
            ),
        }
        result = render_map(world, "Center")

        # The Nearby location should show • marker (not "N")
        assert "•" in result, "Uncategorized location should show • marker"

    def test_legend_vertical_format(self):
        """Verify legend entries are displayed on separate lines.

        Spec: Each legend entry should be on its own line, not comma-separated
        """
        world = {
            "Town Square": Location(
                "Town Square", "A town", {}, coordinates=(0, 0), category="town"
            ),
            "Shop": Location(
                "Shop", "A shop", {}, coordinates=(1, 0), category="shop"
            ),
            "Forest": Location(
                "Forest", "A forest", {}, coordinates=(0, 1), category="forest"
            ),
        }
        result = render_map(world, "Town Square")

        # Find the legend section
        lines = result.split("\n")
        legend_start = None
        for i, line in enumerate(lines):
            if "Legend:" in line:
                legend_start = i
                break

        assert legend_start is not None, "Legend section should exist"

        # Legend should have multiple lines (not comma-separated on one line)
        # Count lines that contain location names after the Legend line
        legend_lines = []
        for i in range(legend_start, len(lines)):
            line = lines[i]
            if "Exits:" in line:
                break
            legend_lines.append(line)

        # Should have at least 3 legend lines (one for each location)
        assert len(legend_lines) >= 3, (
            f"Legend should have entries on separate lines, got: {legend_lines}"
        )

    def test_legend_shows_category_markers(self):
        """Verify legend entries show category markers next to location names.

        Spec: Legend format should be "  🏠 Town Name" for categorized locations
        """
        world = {
            "Town Square": Location(
                "Town Square", "A town", {}, coordinates=(0, 0), category="town"
            ),
            "Shop": Location(
                "Shop", "A shop", {}, coordinates=(1, 0), category="shop"
            ),
        }
        result = render_map(world, "Town Square")

        # Check that legend contains category markers
        # Current location (Town Square) shows with @ marker
        assert "@ = You (Town Square)" in result, "Legend should show player location with @"
        # Other locations show their category markers
        assert "🏪 = Shop" in result or "🏪  Shop" in result, (
            "Legend should show shop with 🏪 marker"
        )


class TestEmojiAlignment:
    """Tests for emoji marker alignment using wcwidth.

    These tests verify that emoji markers (which are display-width 2) align
    correctly with ASCII markers (display-width 1) in the map grid.

    Key insight: Each cell has a fixed visual width of 4. Markers are
    right-aligned within their cells. The visual gap between consecutive
    markers depends on their widths:
    - ASCII (width 1) to ASCII (width 1): gap = 4 (3 padding + 1 marker)
    - ASCII (width 1) to Emoji (width 2): gap = 3 (2 padding + next marker)
    - Emoji (width 2) to Emoji (width 2): gap = 4 (2 padding + 2 marker)
    """

    @staticmethod
    def get_display_width(text: str) -> int:
        """Get the display width of a string using wcwidth."""
        from wcwidth import wcswidth

        return wcswidth(text)

    def test_emoji_cell_visual_width(self):
        """Verify that emoji cells have correct visual width of 4.

        Spec: Use wcwidth to pad each cell to cell_width (4) based on actual
        display width. Each cell should occupy exactly 4 visual columns.
        """
        from cli_rpg.map_renderer import pad_marker

        # All markers should produce cells with visual width 4
        test_markers = ["@", "•", "🌲", "🏪", "🏠", "⚔", "🕳", "🌊"]
        for marker in test_markers:
            padded = pad_marker(marker, 4)
            visual_width = self.get_display_width(padded)
            assert visual_width == 4, (
                f"pad_marker('{marker}', 4) should have visual width 4, "
                f"got {visual_width}. Padded: '{padded}'"
            )

    def test_multiple_cells_accumulate_correctly(self):
        """Verify multiple cells in a row have consistent total visual width.

        Spec: When multiple cells are concatenated, the total visual width
        should be n_cells * cell_width.
        """
        from cli_rpg.map_renderer import pad_marker

        # Build a row with 4 cells of different markers
        markers = ["@", "🌲", "🏪", "⚔"]
        row = "".join(pad_marker(m, 4) for m in markers)

        # Total visual width should be 4 cells * 4 width = 16
        total_width = self.get_display_width(row)
        assert total_width == 16, (
            f"4 cells should have total visual width 16, got {total_width}. "
            f"Row: '{row}'"
        )

    def test_emoji_markers_align_with_header(self):
        """Verify emoji markers align with column numbers in header.

        Spec: Each marker should appear in the correct column position
        corresponding to its x-coordinate.
        """
        from wcwidth import wcswidth
        import re

        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0), category="town"),
            "Forest": Location("Forest", "A forest", {}, coordinates=(1, 0), category="forest"),
            "Shop": Location("Shop", "A shop", {}, coordinates=(2, 0), category="shop"),
        }
        result = render_map(world, "Town")
        lines = result.split("\n")

        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")

        # Find header line (contains column numbers like -4 -3 ... 0 1 2 ...)
        header = None
        data_row = None
        for line in lines:
            content = line.strip("│").strip()
            # Header has x-coordinates
            if "-4" in content and "0" in content and "4" in content:
                header = ansi_escape.sub("", line)
            # Data row for y=0
            if content.startswith("0 ") or content.startswith(" 0 "):
                data_row = ansi_escape.sub("", line)

        assert header is not None, "Header should exist"
        assert data_row is not None, "Data row y=0 should exist"

        # Find position of column "0" in header (where @ should align)
        # Look for " 0 " or " 0" at end of cell
        # The column number "0" should be right-aligned in its cell
        col_0_idx = header.find(" 0 ")
        if col_0_idx < 0:
            col_0_idx = header.find(" 0")
        assert col_0_idx >= 0, f"Column 0 not found in header: '{header}'"

        # Position of the "0" digit itself
        col_0_pos = wcswidth(header[: col_0_idx + 1])

        # Find @ in data row (should be in same visual column range as header "0")
        at_idx = data_row.find("@")
        at_pos = wcswidth(data_row[:at_idx])

        # The @ marker should be within cell_width of the column number
        # (both are right-aligned in their respective cells)
        assert abs(at_pos - col_0_pos) <= 3, (
            f"@ at visual pos {at_pos} should align with column 0 at pos {col_0_pos}. "
            f"Header: '{header}', Row: '{data_row}'"
        )

    def test_no_visual_overlap_between_cells(self):
        """Verify adjacent emoji cells don't visually overlap.

        Spec: Each cell should occupy exactly its allocated visual width
        without overflowing into adjacent cells.
        """
        import re

        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0), category="town"),
            "Forest": Location("Forest", "A forest", {}, coordinates=(1, 0), category="forest"),
        }
        result = render_map(world, "Town")
        lines = result.split("\n")

        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")

        # Find data row for y=0
        data_row = None
        for line in lines:
            content = line.strip("│").strip()
            if content.startswith("0 ") or content.startswith(" 0 "):
                data_row = ansi_escape.sub("", line)
                break

        assert data_row is not None, "Data row y=0 should exist"

        # Verify both markers are present (not garbled/overlapping)
        assert "@" in data_row, "@ marker should be visible"
        assert "🌲" in data_row, "🌲 marker should be visible"

        # Verify there's at least one space between markers (no overlap)
        at_idx = data_row.find("@")
        tree_idx = data_row.find("🌲")
        between = data_row[at_idx + 1 : tree_idx]
        assert " " in between, (
            f"Should have space between @ and 🌲 but got: '{between}'"
        )


class TestBlockedLocationMarkers:
    """Tests for showing blocked/impassable cells on the map.

    Blocked cells are adjacent to explored locations but have no connection
    (wall/barrier), and should show the █ marker.
    """

    def test_blocked_adjacent_cell_shows_marker(self):
        """Cell adjacent to player with no connection shows █ blocked marker.

        Spec: If a cell is adjacent to an explored location but no exit exists
        in that direction, it should show █ to indicate a wall/barrier.
        """
        import re

        # Player at (0,0) with only a north connection, so east/south/west are blocked
        world = {
            "Center": Location(
                "Center",
                "Center location",
                {"north": "North"},  # Only north exit, east/south/west are blocked
                coordinates=(0, 0),
            ),
            "North": Location("North", "North location", {}, coordinates=(0, 1)),
        }
        result = render_map(world, "Center")

        # Strip ANSI codes
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        clean_result = ansi_escape.sub("", result)

        # The blocked marker █ should appear for adjacent blocked cells
        assert "█" in clean_result, (
            "Blocked adjacent cells should show █ marker. "
            f"Result:\n{clean_result}"
        )

    def test_frontier_cell_shows_empty(self):
        """Cell with connection to it (unexplored frontier) shows blank.

        Spec: Adjacent cells that have a connection pointing to them should
        remain blank (not blocked), as they are pending exploration.
        """
        import re

        # Player at (0,0) with north connection - (0,1) is a frontier, not blocked
        world = {
            "Center": Location(
                "Center",
                "Center location",
                {"north": "North"},  # North has a connection
                coordinates=(0, 0),
            ),
        }
        result = render_map(world, "Center")

        lines = result.split("\n")
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")

        # Find the row with y=1 (north of player)
        # Look for row label "  1 " pattern in the line (inside box border)
        row_y1 = None
        for line in lines:
            clean_line = ansi_escape.sub("", line)
            # Match lines where y-coordinate is 1 (row label format: "│  1 ...")
            # The y-label is right-aligned in 3 chars, so " 1 " or "  1 "
            if "│" in clean_line:
                content = clean_line.split("│")[1] if "│" in clean_line else ""
                # Row label format: "  1 " (right-aligned to width 3, then space)
                if " 1 " in content[:5]:
                    row_y1 = clean_line
                    break

        assert row_y1 is not None, f"Row with y=1 should exist. Lines:\n{result}"
        # The cell at (0,1) should NOT have a blocked marker since there's a connection
        # The row y=1 should NOT contain █ because (0,1) is a frontier (has connection)
        # Note: The actual location North is in the world, so it will show with •
        # What we're testing is that frontier cells don't get blocked markers
        assert "█" not in row_y1, (
            f"Frontier cell row should not have blocked marker. Row: '{row_y1}'"
        )

    def test_non_adjacent_empty_stays_blank(self):
        """Cells not adjacent to any explored location remain blank.

        Spec: Empty cells that are not adjacent to any explored location
        should remain as blank space, not show blocked markers.
        """
        import re

        # Only player at (0,0)
        world = {
            "Center": Location(
                "Center",
                "Center location",
                {},  # No connections
                coordinates=(0, 0),
            ),
        }
        result = render_map(world, "Center")

        lines = result.split("\n")
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")

        # Find the row with y=3 (far from player, not adjacent)
        row_y3 = None
        for line in lines:
            clean_line = ansi_escape.sub("", line)
            # Match lines where y-coordinate is 3 (row label format: "│  3 ...")
            # The y-label is right-aligned in 3 chars, so " 3 "
            if "│" in clean_line:
                content = clean_line.split("│")[1] if "│" in clean_line else ""
                # Row label format: "  3 " (right-aligned to width 3, then space)
                if " 3 " in content[:5]:
                    row_y3 = clean_line
                    break

        assert row_y3 is not None, f"Row with y=3 should exist. Result:\n{result}"
        # This row should NOT have any blocked markers since it's not adjacent
        # to any explored location
        assert "█" not in row_y3, (
            f"Non-adjacent row y=3 should not have blocked markers. Row: '{row_y3}'"
        )

    def test_blocked_marker_in_legend(self):
        """Legend includes blocked marker explanation.

        Spec: The map legend should include an entry explaining the █ marker.
        """
        # Player at (0,0) with no connections (all adjacent cells blocked)
        world = {
            "Center": Location(
                "Center",
                "Center location",
                {},  # No connections - all adjacent cells are blocked
                coordinates=(0, 0),
            ),
        }
        result = render_map(world, "Center")

        # Check that legend contains blocked marker explanation
        assert "█" in result, "Legend should contain blocked marker █"
        assert "Blocked" in result or "Wall" in result, (
            "Legend should explain blocked marker"
        )
