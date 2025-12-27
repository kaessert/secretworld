"""Map renderer for displaying an ASCII map of explored locations."""

from typing import Optional, TYPE_CHECKING
import re

from wcwidth import wcswidth

from cli_rpg.models.location import Location
from cli_rpg import colors
from cli_rpg.world_tiles import get_terrain_symbol

if TYPE_CHECKING:
    from cli_rpg.world_grid import SubGrid
    from cli_rpg.wfc_chunks import ChunkManager

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

# Water terrain marker (impassable water from WFC)
WATER_MARKER = "~"

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


def render_map(
    world: dict[str, Location],
    current_location: str,
    sub_grid: Optional["SubGrid"] = None,
    chunk_manager: Optional["ChunkManager"] = None,
    seen_tiles: Optional[set[tuple[int, int]]] = None,
) -> str:
    """Render an ASCII map of the explored world or interior sub-grid.

    Args:
        world: Dictionary mapping location names to Location objects
        current_location: Name of the player's current location
        sub_grid: Optional SubGrid for interior rendering. When provided,
                  renders a bounded interior map instead of the overworld.
        chunk_manager: Optional ChunkManager for WFC terrain-based exit filtering.
                      When provided, exits to impassable terrain are hidden.
        seen_tiles: Optional set of (x, y) coordinates that the player has seen
                   (within visibility radius). Tiles in this set but not visited
                   will show terrain symbols.

    Returns:
        ASCII string representation of the map with legend
    """
    # If sub_grid is provided, delegate to interior map rendering
    if sub_grid is not None:
        return _render_sub_grid_map(sub_grid, current_location)

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

    # Create marker map for coordinates (uncolored for alignment calculations)
    # Only include locations that are REACHABLE from current location
    # (adjacent locations without connection are shown as blocked instead)
    coord_to_marker: dict[tuple[int, int], str] = {}
    unreachable_locations: set[tuple[int, int]] = set()
    # Only track named locations for letter assignment
    named_reachable: set[str] = set()
    if world.get(current_location) and world[current_location].is_named:
        named_reachable.add(current_location)

    for name, location in locations_with_coords:
        coords = location.coordinates
        assert coords is not None  # We already filtered for non-None coordinates
        if name == current_location:
            coord_to_marker[coords] = "@"
        elif location.is_named:
            # Named locations get letter symbols - track them for letter assignment
            named_reachable.add(name)
        else:
            # Unnamed locations get terrain symbols directly
            terrain = location.terrain or "plains"
            coord_to_marker[coords] = get_terrain_symbol(terrain)

    # Assign unique letter symbols only to NAMED non-current locations
    SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    sorted_names = sorted(name for name in named_reachable if name != current_location)
    location_symbols = {name: SYMBOLS[i] for i, name in enumerate(sorted_names) if i < len(SYMBOLS)}

    # Add markers for named locations (with letters)
    for name, location in locations_with_coords:
        if name != current_location and name in named_reachable:
            coords = location.coordinates
            assert coords is not None
            coord_to_marker[coords] = location_symbols.get(name, "?")

    # Build the legend entries (vertical format) - only for NAMED locations
    legend_entries = []
    for name, location in locations_with_coords:
        if not location.is_named:
            continue  # Skip unnamed terrain locations
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

            # Check for unreachable locations (adjacent to player but no connection)
            if coord in unreachable_locations:
                row_parts.append(pad_marker(BLOCKED_MARKER, cell_width))
            elif coord in coord_to_marker:
                marker = coord_to_marker[coord]
                # Use width-aware padding to handle emoji display widths correctly
                padded = pad_marker(marker, cell_width)
                if coord == current_loc.coordinates:
                    # Colorize only the marker character, preserving padding
                    # The @ marker is width 1, so padding is cell_width - 1 spaces
                    padded = (" " * (cell_width - 1)) + colors.bold_colorize("@", colors.CYAN)
                row_parts.append(padded)
            else:
                # Check if tile is in seen_tiles (seen but not visited)
                is_seen = seen_tiles is not None and coord in seen_tiles
                # Check WFC terrain for water or seen terrain display
                terrain = None
                if chunk_manager is not None:
                    terrain = chunk_manager.get_tile_at(x, y)

                if terrain == "water":
                    # Always show water (impassable)
                    row_parts.append(pad_marker(WATER_MARKER, cell_width))
                elif is_seen and terrain is not None:
                    # Seen but not visited: show terrain symbol
                    marker = get_terrain_symbol(terrain)
                    row_parts.append(pad_marker(marker, cell_width))
                else:
                    # Unexplored / unseen cells are empty
                    row_parts.append(" " * cell_width)
        map_rows.append("".join(row_parts))

    # Get available exits from current location, filtered by WFC terrain passability
    available_directions = current_loc.get_filtered_directions(chunk_manager, world=world)
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
    lines.append(f"  {WATER_MARKER} = Water (impassable)")
    lines.append("")
    lines.append("Terrain: T=forest .=plains n=hills :=desert %=swamp ,=beach ^=foothills M=mountain")
    lines.append(exits_line)

    return "\n".join(lines)


def _render_sub_grid_map(sub_grid: "SubGrid", current_location: str) -> str:
    """Render a player-centered interior map with exit markers.

    This renders a 2D slice of the 3D SubGrid at the player's current z-level.
    Multi-level navigation (up/down) is indicated in the legend.

    Args:
        sub_grid: The SubGrid to render
        current_location: Name of the player's current location

    Returns:
        ASCII string representation of the interior map
    """
    # Get SubGrid bounds (6-tuple: min_x, max_x, min_y, max_y, min_z, max_z)
    # Handle both legacy 4-tuple and new 6-tuple bounds
    if len(sub_grid.bounds) == 6:
        bound_min_x, bound_max_x, bound_min_y, bound_max_y, bound_min_z, bound_max_z = sub_grid.bounds
    else:
        bound_min_x, bound_max_x, bound_min_y, bound_max_y = sub_grid.bounds
        bound_min_z, bound_max_z = 0, 0

    # Get current location for positioning
    current_loc = sub_grid.get_by_name(current_location)
    if current_loc is None or current_loc.coordinates is None:
        return "No interior map available."

    # Get player position (handle both 2D and 3D coordinates)
    if len(current_loc.coordinates) == 3:
        player_x, player_y, player_z = current_loc.coordinates
    else:
        player_x, player_y = current_loc.coordinates
        player_z = 0

    # Center viewport on player (same 9x9 as overworld)
    viewport_radius = 4
    view_min_x = player_x - viewport_radius
    view_max_x = player_x + viewport_radius
    view_min_y = player_y - viewport_radius
    view_max_y = player_y + viewport_radius

    # Build coordinate to location mapping for current z-level only
    # Map 2D coords (x, y) to locations at the player's z-level
    coord_to_location: dict[tuple[int, int], Location] = {}
    for loc in sub_grid._by_name.values():
        if loc.coordinates is not None:
            loc_x, loc_y = loc.coordinates[:2]
            loc_z = loc.coordinates[2] if len(loc.coordinates) == 3 else 0
            # Only include locations at the same z-level as the player
            if loc_z == player_z:
                coord_to_location[(loc_x, loc_y)] = loc

    # Assign letter symbols (same logic as overworld) - alphabetical order
    SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    sorted_names = sorted(
        name for name in sub_grid._by_name.keys()
        if name != current_location
    )
    location_symbols = {
        name: SYMBOLS[i]
        for i, name in enumerate(sorted_names)
        if i < len(SYMBOLS)
    }

    # Build legend entries (only for locations in viewport)
    legend_entries = []
    locations_in_viewport = set()
    for y in range(view_max_y, view_min_y - 1, -1):
        for x in range(view_min_x, view_max_x + 1):
            coord = (x, y)
            if coord in coord_to_location:
                locations_in_viewport.add(coord_to_location[coord].name)

    for name, loc in sub_grid._by_name.items():
        if name not in locations_in_viewport:
            continue
        if name == current_location:
            legend_entries.append(f"  {colors.bold_colorize('@', colors.CYAN)} = You ({name})")
        else:
            symbol = location_symbols.get(name, "?")
            exit_indicator = " [EXIT]" if loc.is_exit_point else ""
            category_icon = get_category_marker(loc.category)
            if category_icon and category_icon != "•":
                legend_entries.append(f"  {symbol} = {category_icon} {name}{exit_indicator}")
            else:
                legend_entries.append(f"  {symbol} = {name}{exit_indicator}")

    # Build map grid centered on player
    cell_width = 4

    # Header with x-coordinates
    header_parts = ["    "]
    for x in range(view_min_x, view_max_x + 1):
        header_parts.append(f"{x:>{cell_width}}")
    header = "".join(header_parts)
    content_width = len(header)

    # Build rows (y descending for north=up)
    map_rows = []
    for y in range(view_max_y, view_min_y - 1, -1):
        row_parts = [f"{y:>3} "]
        for x in range(view_min_x, view_max_x + 1):
            coord = (x, y)
            # Check if coordinate is within SubGrid bounds
            in_bounds = (bound_min_x <= x <= bound_max_x and
                         bound_min_y <= y <= bound_max_y)

            if coord in coord_to_location:
                loc = coord_to_location[coord]
                if loc.name == current_location:
                    padded = (" " * (cell_width - 1)) + colors.bold_colorize("@", colors.CYAN)
                else:
                    marker = location_symbols.get(loc.name, "?")
                    padded = pad_marker(marker, cell_width)
                row_parts.append(padded)
            elif in_bounds:
                # Inside bounds but no location = blocked/wall
                row_parts.append(pad_marker(BLOCKED_MARKER, cell_width))
            else:
                # Outside SubGrid bounds = empty (beyond the interior)
                row_parts.append(" " * cell_width)
        map_rows.append("".join(row_parts))

    # Get exits from current location using sub_grid for coordinate lookup
    available_directions = current_loc.get_available_directions(sub_grid=sub_grid)
    exits_line = f"Exits: {', '.join(available_directions)}" if available_directions else "Exits: None"

    # Build box border
    top_border = "┌" + "─" * content_width + "┐"
    bottom_border = "└" + "─" * content_width + "┘"

    # Helper for padding with ANSI code awareness
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")

    def pad_to_width(line: str, width: int) -> str:
        visible_len = len(ansi_escape.sub("", line))
        padding = width - visible_len
        return line + " " * max(0, padding)

    # Assemble output - include level info if multi-level
    is_multi_level = bound_min_z != bound_max_z
    if is_multi_level:
        level_info = f", Level {player_z}"
    else:
        level_info = ""
    lines = [
        f"=== INTERIOR MAP === (Inside: {sub_grid.parent_name}{level_info})",
        top_border,
        "│" + pad_to_width(header, content_width) + "│",
    ]

    for row in map_rows:
        lines.append("│" + pad_to_width(row, content_width) + "│")

    lines.append(bottom_border)
    lines.append("")
    lines.append("Legend:")
    lines.extend(sorted(legend_entries))  # Sort for consistency
    lines.append(f"  {BLOCKED_MARKER} = Wall/Boundary")
    lines.append(exits_line)

    return "\n".join(lines)


def render_worldmap(
    world: dict[str, Location],
    current_location: str,
    seen_tiles: Optional[set[tuple[int, int]]] = None,
) -> str:
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
    map_output = render_map(overworld_locations, map_center_location, seen_tiles=seen_tiles)

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
