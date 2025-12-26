# Implementation Plan: SubGrid Interior Map Rendering (Phase 1, Step 4)

## Status: PENDING

## Overview

Add interior map rendering to `map_renderer.py` so players can visualize their position inside sub-grids. When inside a SubGrid, the `map` command should display a bounded interior map with exit point markers, instead of the infinite overworld view.

## Spec

When `render_map()` is called while inside a sub-grid:
1. Display a header "=== INTERIOR MAP ===" (vs "=== MAP ===" for overworld)
2. Show the bounded grid based on `sub_grid.bounds` (not 9x9 viewport)
3. Mark exit points with "E" in the legend (locations where `is_exit_point=True`)
4. Use letter symbols for locations, @ for current position (same as overworld)
5. Show blocked cells (█) at grid boundaries
6. Legend should include "E = Exit point" entry

## Tests First

Create tests in `tests/test_map_renderer.py` or new `tests/test_subgrid_map.py`:

```python
class TestSubGridMapRendering:
    """Tests for interior map rendering when inside a SubGrid."""

    def test_render_map_with_sub_grid_shows_interior_header(self):
        """When sub_grid is provided, header should say 'INTERIOR MAP'."""
        # Create a SubGrid with locations
        # Call render_map(world, current, sub_grid=sub_grid)
        # Assert "=== INTERIOR MAP ===" in result

    def test_render_sub_grid_uses_bounds_not_viewport(self):
        """Interior map shows full bounded grid, not 9x9 viewport."""
        # SubGrid with bounds (-2, 2, -2, 2) = 5x5
        # Map should show exactly those coordinates

    def test_render_sub_grid_shows_exit_markers(self):
        """Locations with is_exit_point=True get special marker in legend."""
        # Create SubGrid with one exit point location
        # Legend should show "E = Exit point" or similar

    def test_render_sub_grid_shows_current_location_at_symbol(self):
        """Current location inside sub-grid uses @ marker."""
        # Standard behavior, @ for current position

    def test_render_sub_grid_shows_blocked_at_bounds(self):
        """Cells outside SubGrid bounds show as blocked (█)."""
        # Edge cells at boundary should show walls

    def test_render_sub_grid_shows_parent_context(self):
        """Interior map should mention parent location for context."""
        # e.g., "(Inside: Town Square)" or similar header

    def test_render_sub_grid_legend_shows_exit_indicator(self):
        """Legend distinguishes exit points from regular locations."""
        # Exit points should have visual indicator (E suffix or icon)
```

## Implementation Steps

### 1. Add `sub_grid` parameter to `render_map()` (~line 66)

```python
def render_map(
    world: dict[str, Location],
    current_location: str,
    sub_grid: Optional["SubGrid"] = None  # NEW parameter
) -> str:
    """Render an ASCII map of the explored world or interior sub-grid.

    Args:
        world: Dictionary mapping location names to Location objects
        current_location: Name of the player's current location
        sub_grid: Optional SubGrid for interior rendering

    Returns:
        ASCII string representation of the map with legend
    """
    if sub_grid is not None:
        return _render_sub_grid_map(sub_grid, current_location)

    # ... existing overworld rendering code ...
```

### 2. Create `_render_sub_grid_map()` function

```python
def _render_sub_grid_map(sub_grid: "SubGrid", current_location: str) -> str:
    """Render a bounded interior map with exit markers.

    Args:
        sub_grid: The SubGrid to render
        current_location: Name of the player's current location

    Returns:
        ASCII string representation of the interior map
    """
    # Get bounds
    min_x, max_x, min_y, max_y = sub_grid.bounds

    # Get current location for positioning
    current_loc = sub_grid.get_by_name(current_location)
    if current_loc is None or current_loc.coordinates is None:
        return "No interior map available."

    # Build coordinate to location mapping
    coord_to_location: dict[tuple[int, int], Location] = {}
    for loc in sub_grid._by_name.values():
        if loc.coordinates is not None:
            coord_to_location[loc.coordinates] = loc

    # Assign letter symbols (same logic as overworld)
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

    # Build legend entries
    legend_entries = []
    for name, loc in sub_grid._by_name.items():
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

    # Build map grid (similar to render_map but with fixed bounds)
    cell_width = 4

    # Header with x-coordinates
    header_parts = ["    "]
    for x in range(min_x, max_x + 1):
        header_parts.append(f"{x:>{cell_width}}")
    header = "".join(header_parts)
    content_width = len(header)

    # Build rows (y descending for north=up)
    map_rows = []
    for y in range(max_y, min_y - 1, -1):
        row_parts = [f"{y:>3} "]
        for x in range(min_x, max_x + 1):
            coord = (x, y)
            if coord in coord_to_location:
                loc = coord_to_location[coord]
                if loc.name == current_location:
                    padded = (" " * (cell_width - 1)) + colors.bold_colorize("@", colors.CYAN)
                else:
                    marker = location_symbols.get(loc.name, "?")
                    padded = pad_marker(marker, cell_width)
                row_parts.append(padded)
            else:
                # Inside bounds but no location = blocked/wall
                row_parts.append(pad_marker(BLOCKED_MARKER, cell_width))
        map_rows.append("".join(row_parts))

    # Get exits
    available_directions = current_loc.get_available_directions()
    exits_line = f"Exits: {', '.join(available_directions)}" if available_directions else "Exits: None"

    # Build box border
    top_border = "┌" + "─" * content_width + "┐"
    bottom_border = "└" + "─" * content_width + "┘"

    def pad_to_width(line: str, width: int) -> str:
        import re
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        visible_len = len(ansi_escape.sub("", line))
        padding = width - visible_len
        return line + " " * max(0, padding)

    # Assemble output
    lines = [
        f"=== INTERIOR MAP === (Inside: {sub_grid.parent_name})",
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
```

### 3. Update `main.py` map command to pass sub_grid

Find where `render_map()` is called in the map command handler and update:

```python
# When handling 'map' command
if game_state.in_sub_location and game_state.current_sub_grid is not None:
    output = render_map(
        game_state.world,
        game_state.current_location,
        sub_grid=game_state.current_sub_grid
    )
else:
    output = render_map(game_state.world, game_state.current_location)
```

### 4. Add import for SubGrid type hint

At top of `map_renderer.py`:
```python
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.world_grid import SubGrid
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/map_renderer.py` | Add `sub_grid` param to `render_map()`, create `_render_sub_grid_map()` function |
| `src/cli_rpg/main.py` | Update map command to pass `sub_grid` when inside one |
| `tests/test_map_renderer.py` | Add tests for interior map rendering |

## Verification

1. Run `pytest tests/test_map_renderer.py -v` - all tests pass including new ones
2. Run `pytest tests/test_subgrid_navigation.py -v` - existing sub-grid tests still pass
3. Run `pytest` - full suite passes (3230+ tests)
4. Manual test: Start game, enter a location with sub_grid, run `map` command

## Example Output

```
=== INTERIOR MAP === (Inside: Ancient Temple)
┌────────────────────────────┐
│      -2  -1   0   1   2    │
│   2   █   █   A   █   █    │
│   1   █   B   @   C   █    │
│   0   █   █   D   █   █    │
│  -1   █   █   █   █   █    │
│  -2   █   █   █   █   █    │
└────────────────────────────┘

Legend:
  @ = You (Temple Hall)
  A = Altar Room
  B = West Chamber
  C = East Chamber [EXIT]
  D = Crypt Entrance
  █ = Wall/Boundary
Exits: north, south, east, west
```
