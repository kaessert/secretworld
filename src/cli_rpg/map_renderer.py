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

# Blocked cell marker (wall/impassable adjacent cell)
BLOCKED_MARKER = "█"

# Direction deltas for checking adjacent cells
DIRECTION_DELTAS = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0),
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

    # Assign unique letter symbols to non-current locations (alphabetical by name)
    SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    sorted_names = sorted(name for name, _ in locations_with_coords if name != current_location)
    location_symbols = {name: SYMBOLS[i] for i, name in enumerate(sorted_names) if i < len(SYMBOLS)}

    # Build the legend entries (vertical format)
    legend_entries = []
    for name, location in locations_with_coords:
        if name == current_location:
            # Current location marked with @
            legend_entries.append(f"  {colors.bold_colorize('@', colors.CYAN)} = You ({name})")
        else:
            # Use letter symbol + category icon in legend
            symbol = location_symbols.get(name, "?")
            category_icon = get_category_marker(location.category)
            if category_icon and category_icon != "•":
                legend_entries.append(f"  {symbol} = {category_icon} {name}")
            else:
                legend_entries.append(f"  {symbol} = {name}")

    # Create marker map for coordinates (uncolored for alignment calculations)
    coord_to_marker: dict[tuple[int, int], str] = {}
    for name, location in locations_with_coords:
        coords = location.coordinates
        assert coords is not None  # We already filtered for non-None coordinates
        if name == current_location:
            coord_to_marker[coords] = "@"
        else:
            coord_to_marker[coords] = location_symbols.get(name, "?")

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
                # Check if this empty cell is adjacent to an explored location
                # If adjacent but no connection exists TO this cell, mark as blocked
                is_blocked = False
                for name, location in locations_with_coords:
                    if location.coordinates is None:
                        continue
                    lx, ly = location.coordinates
                    # Check if coord is adjacent to this location
                    for direction, (dx, dy) in DIRECTION_DELTAS.items():
                        if (lx + dx, ly + dy) == coord:
                            # coord is adjacent - check if connection exists
                            if direction not in location.connections:
                                is_blocked = True
                                break
                    if is_blocked:
                        break

                if is_blocked:
                    row_parts.append(pad_marker(BLOCKED_MARKER, cell_width))
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
    lines.append(f"  {BLOCKED_MARKER} = Blocked/Wall")
    lines.append(exits_line)

    return "\n".join(lines)


def render_worldmap(world: dict[str, Location], current_location: str) -> str:
    """Render an ASCII map showing only overworld locations.

    Filters the world to only is_overworld=True locations and displays
    those on a map. When the player is in a sub-location, uses the parent
    location for positioning and shows a context message.

    Args:
        world: Dictionary mapping location names to Location objects
        current_location: Name of the player's current location

    Returns:
        ASCII string representation of the overworld map with legend
    """
    # Get current location
    current_loc = world.get(current_location)
    if current_loc is None:
        return "No overworld map available - current location not found."

    # Check if player is in a sub-location
    parent_context_message = ""
    map_center_location = current_location

    if not current_loc.is_overworld and current_loc.parent_location:
        # Player is in a sub-location - use parent for map centering
        parent_name = current_loc.parent_location
        parent_loc = world.get(parent_name)
        if parent_loc and parent_loc.is_overworld:
            parent_context_message = f"(You are inside {parent_name})\n\n"
            map_center_location = parent_name

    # Filter world to only overworld locations
    overworld_locations = {
        name: loc for name, loc in world.items() if loc.is_overworld
    }

    # Check if any overworld locations exist
    if not overworld_locations:
        return "No overworld map available - no overworld locations discovered."

    # Call render_map with filtered world, then replace header
    map_output = render_map(overworld_locations, map_center_location)

    # Replace header to indicate this is the world map
    map_output = map_output.replace("=== MAP ===", "=== WORLD MAP ===")

    # Add parent context message if applicable
    if parent_context_message:
        # Insert after the header
        lines = map_output.split("\n")
        if lines and lines[0] == "=== WORLD MAP ===":
            lines.insert(1, parent_context_message.strip())
            map_output = "\n".join(lines)

    return map_output
