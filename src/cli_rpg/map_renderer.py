"""Map renderer for displaying an ASCII map of explored locations."""

from cli_rpg.models.location import Location
from cli_rpg import colors


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

    # Calculate 5x5 viewport centered on player (2 tiles in each direction)
    player_x, player_y = current_loc.coordinates
    min_x, max_x = player_x - 2, player_x + 2
    min_y, max_y = player_y - 2, player_y + 2

    # Extract locations with coordinates that are within the viewport
    locations_with_coords = []
    for name, location in world.items():
        if location.coordinates is not None:
            x, y = location.coordinates
            if min_x <= x <= max_x and min_y <= y <= max_y:
                locations_with_coords.append((name, location))

    # Handle case where no locations have coordinates (legacy saves)
    if not locations_with_coords:
        return "No map available - locations do not have coordinates."

    # Build coordinate to location mapping
    coord_to_location: dict[tuple[int, int], tuple[str, Location]] = {}
    for name, location in locations_with_coords:
        coord_to_location[location.coordinates] = (name, location)

    # Build the legend entries
    legend_entries = []
    for name, location in locations_with_coords:
        if name == current_location:
            # Current location marked with @
            marker = "@"
            legend_entries.append(f"{colors.bold_colorize('@', colors.CYAN)} = You ({name})")
        else:
            # Use first letter of location name as marker
            marker = name[0].upper()
            legend_entries.append(f"{marker} = {name}")

    # Create marker map for coordinates (uncolored for alignment calculations)
    coord_to_marker: dict[tuple[int, int], str] = {}
    for name, location in locations_with_coords:
        if name == current_location:
            coord_to_marker[location.coordinates] = "@"
        else:
            coord_to_marker[location.coordinates] = name[0].upper()

    # Calculate column width for alignment (each cell needs space for marker + padding)
    cell_width = 3

    # Build header with x-coordinates
    header_parts = ["   "]  # Space for y-axis label
    for x in range(min_x, max_x + 1):
        header_parts.append(f"{x:>{cell_width}}")
    header = "".join(header_parts)

    # Build map rows (y-axis inverted so higher y is at the top)
    map_rows = []
    for y in range(max_y, min_y - 1, -1):
        row_parts = [f"{y:>2} "]  # Y-axis label
        for x in range(min_x, max_x + 1):
            coord = (x, y)
            if coord in coord_to_marker:
                marker = coord_to_marker[coord]
                # Pad first, then colorize to avoid ANSI codes breaking alignment
                padded = f"{marker:>{cell_width}}"
                if coord == current_loc.coordinates:
                    # Colorize only the marker character, preserving padding
                    padded = padded[:-1] + colors.bold_colorize("@", colors.CYAN)
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

    # Assemble the full output
    lines = [
        "=== MAP ===",
        header,
        *map_rows,
        "",
        "Legend: " + ", ".join(legend_entries),
        exits_line,
    ]

    return "\n".join(lines)
