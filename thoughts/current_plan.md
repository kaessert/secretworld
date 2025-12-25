# Blocked Location Markers on Map

## Spec

Show visual markers on the map for adjacent cells that are **blocked/impassable** - cells within the viewport that are adjacent to explored locations but have no connection (wall/barrier).

**Marker**: `█` (blocked) or empty space (unexplored frontier)

**Distinction**:
- **Blocked cell**: Adjacent to an explored location but no exit exists in that direction (wall)
- **Unexplored frontier**: Adjacent cell that has a connection pointing to it (pending exploration)
- **Empty cell**: Not adjacent to any explored location (show as blank space)

## Tests

Add tests to `tests/test_map_renderer.py`:

1. `test_blocked_adjacent_cell_shows_marker` - Cell adjacent to player with no connection shows `█`
2. `test_frontier_cell_shows_empty` - Cell with connection to it (unexplored) shows blank (existing behavior)
3. `test_non_adjacent_empty_stays_blank` - Cells not adjacent to any location remain blank
4. `test_blocked_marker_in_legend` - Legend includes blocked marker explanation

## Implementation

### 1. Add blocked marker constant to `src/cli_rpg/map_renderer.py`

```python
BLOCKED_MARKER = "█"  # Wall/impassable adjacent cell
```

### 2. Modify `render_map()` to identify blocked cells

In the main rendering loop (lines 130-143), after checking `coord in coord_to_marker`:

```python
# Check if this empty cell is adjacent to an explored location
# If adjacent but no connection exists TO this cell, mark as blocked
is_blocked = False
for name, location in locations_with_coords:
    if location.coordinates is None:
        continue
    lx, ly = location.coordinates
    # Check if coord is adjacent to this location
    for direction, (dx, dy) in [("north", (0,1)), ("south", (0,-1)),
                                  ("east", (1,0)), ("west", (-1,0))]:
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
```

### 3. Add blocked marker to legend (optional enhancement)

After the location legend entries, add:
```python
legend_entries.append(f"  {BLOCKED_MARKER} = Blocked/Wall")
```

## Files Changed

- `src/cli_rpg/map_renderer.py` - Add blocked marker logic
- `tests/test_map_renderer.py` - Add tests for blocked markers
