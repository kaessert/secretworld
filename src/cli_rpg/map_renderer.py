"""Map renderer for displaying an ASCII map of explored locations."""

from typing import Optional

from wcwidth import wcswidth

from cli_rpg.models.location import Location
from cli_rpg import colors

# Category to marker mapping for location icons
CATEGORY_MARKERS = {
    "town": "🏠",
    "shop": "🏪",
    "dungeon": "⚔",
    "forest": "🌲",
    "cave": "🕳",
    "water": "🌊",
    None: "•",  # default for uncategorized
}


def get_category_marker(category: Optional[str]) -> str:
    """Get the marker icon for a location category.

    Args:
        category: The location category or None

    Returns:
        The corresponding marker character/emoji
    """
    return CATEGORY_MARKERS.get(category, "•")


def pad_marker(marker: str, target_width: int) -> str:
    """Right-pad marker to target_width based on display width.

    Uses wcwidth to calculate the actual display width of the marker,
    then adds appropriate padding so the cell occupies exactly target_width
    visual columns.

    Args:
        marker: The marker character/emoji to pad
        target_width: The desired display width for the cell

    Returns:
        The marker with left-padding to achieve target_width display columns
    """
    display_width = wcswidth(marker)
    if display_width < 0:  # non-printable or error
        display_width = 1
    padding = target_width - display_width
    return (" " * max(0, padding)) + marker


def render_map(world: dict[str, Location], current_location: str) -> str:
    """Render an ASCII map of the explored world.

    Args:
        world: Dictionary mapping location names to Location objects
        current_location: Name of the player's current location

    Returns:
        ASCII string representation of the map with legend
    """
    # Get current location to center the viewport
    current_loc = world.get(current_location)
    if current_loc is None or current_loc.coordinates is None:
        return "No map available - current location does not have coordinates."

    # Calculate 9x9 viewport centered on player (4 tiles in each direction)
    player_x, player_y = current_loc.coordinates
    min_x, max_x = player_x - 4, player_x + 4
    min_y, max_y = player_y - 4, player_y + 4

    # Extract locations with coordinates that are within the viewport
    locations_with_coords = []
    for name, location in world.items():
        if location.coordinates is not None:
            x, y = location.coordinates
            if min_x <= x <= max_x and min_y <= y <= max_y:
                locations_with_coords.append((name, location))

    # Build coordinate to location mapping
    # Note: locations_with_coords will always have at least the current location
    # since we already checked current_loc.coordinates is not None above
    coord_to_location: dict[tuple[int, int], tuple[str, Location]] = {}
    for name, location in locations_with_coords:
        coords = location.coordinates
        assert coords is not None  # We already filtered for non-None coordinates
        coord_to_location[coords] = (name, location)

    # Build the legend entries (vertical format)
    legend_entries = []
    for name, location in locations_with_coords:
        if name == current_location:
            # Current location marked with @
            legend_entries.append(f"  {colors.bold_colorize('@', colors.CYAN)} = You ({name})")
        else:
            # Use category marker
            marker = get_category_marker(location.category)
            legend_entries.append(f"  {marker} = {name}")

    # Create marker map for coordinates (uncolored for alignment calculations)
    coord_to_marker: dict[tuple[int, int], str] = {}
    for name, location in locations_with_coords:
        coords = location.coordinates
        assert coords is not None  # We already filtered for non-None coordinates
        if name == current_location:
            coord_to_marker[coords] = "@"
        else:
            coord_to_marker[coords] = get_category_marker(location.category)

    # Calculate column width for alignment (each cell needs space for marker + padding)
    # Use 4 to accommodate emoji markers which are typically 2 characters wide
    cell_width = 4

    # Build header with x-coordinates
    header_parts = ["    "]  # Space for y-axis label (adjusted for larger coords)
    for x in range(min_x, max_x + 1):
        header_parts.append(f"{x:>{cell_width}}")
    header = "".join(header_parts)

    # Calculate total content width (for box border)
    content_width = len(header)

    # Build map rows (y-axis inverted so higher y is at the top)
    map_rows = []
    for y in range(max_y, min_y - 1, -1):
        row_parts = [f"{y:>3} "]  # Y-axis label
        for x in range(min_x, max_x + 1):
            coord = (x, y)
            if coord in coord_to_marker:
                marker = coord_to_marker[coord]
                # Use width-aware padding to handle emoji display widths correctly
                padded = pad_marker(marker, cell_width)
                if coord == current_loc.coordinates:
                    # Colorize only the marker character, preserving padding
                    # The @ marker is width 1, so padding is cell_width - 1 spaces
                    padded = (" " * (cell_width - 1)) + colors.bold_colorize("@", colors.CYAN)
                row_parts.append(padded)
            else:
                row_parts.append(" " * cell_width)
        map_rows.append("".join(row_parts))

    # Get available exits from current location
    available_directions = current_loc.get_available_directions()
    if available_directions:
        exits_line = "Exits: " + ", ".join(available_directions)
    else:
        exits_line = "Exits: None"

    # Build box border
    border_width = content_width
    top_border = "┌" + "─" * border_width + "┐"
    bottom_border = "└" + "─" * border_width + "┘"

    # Pad header and rows to fit in box
    def pad_to_width(line: str, width: int) -> str:
        # Account for ANSI codes when calculating visible length
        import re
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        visible_len = len(ansi_escape.sub("", line))
        padding = width - visible_len
        return line + " " * max(0, padding)

    # Assemble the full output with box border
    lines = [
        "=== MAP ===",
        top_border,
        "│" + pad_to_width(header, border_width) + "│",
    ]

    for row in map_rows:
        lines.append("│" + pad_to_width(row, border_width) + "│")

    lines.append(bottom_border)
    lines.append("")
    lines.append("Legend:")
    lines.extend(legend_entries)
    lines.append(exits_line)

    return "\n".join(lines)
