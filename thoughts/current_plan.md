# Better Map Implementation Plan

## Spec

Enhance the map renderer to display a larger, more visually appealing map that:
1. Expands viewport from 5x5 to 9x9 (4 tiles in each direction from player)
2. Uses box-drawing characters for a proper border/frame
3. Displays location category icons instead of first-letter markers (e.g., ⚔ for combat, 🏠 for town)
4. Improves legend formatting with vertical layout
5. Shows path connections between adjacent locations

## Test Changes

Update `tests/test_map_renderer.py`:

1. **Update viewport size tests**: Change from 5x5 to 9x9
   - `test_map_shows_5x5_viewport` → `test_map_shows_9x9_viewport` (verify x/y range is ±4)
   - `test_map_centered_on_player` → update to verify 9x9 centering
   - `test_map_clips_locations_outside_viewport` → adjust distance threshold

2. **Add new tests for visual improvements**:
   - `test_map_has_box_border`: Verify box-drawing characters (┌┐└┘─│) present
   - `test_location_markers_show_category`: Verify category-based markers (⚔🏠🏪🌲 etc.)
   - `test_legend_vertical_format`: Verify legend entries on separate lines

## Implementation Changes

Modify `src/cli_rpg/map_renderer.py`:

### 1. Update viewport constants (line 22-25)
```python
# Change from 2 to 4 tiles in each direction
player_x, player_y = current_loc.coordinates
min_x, max_x = player_x - 4, player_x + 4
min_y, max_y = player_y - 4, player_y + 4
```

### 2. Add category-to-marker mapping (new, near top of file)
```python
CATEGORY_MARKERS = {
    "town": "🏠",
    "shop": "🏪",
    "dungeon": "⚔",
    "forest": "🌲",
    "cave": "🕳",
    "water": "🌊",
    None: "•",  # default for uncategorized
}
```

### 3. Update marker logic (around line 53-64)
- Replace first-letter markers with category-based markers
- Keep `@` for player position

### 4. Add box border rendering (lines 70-91)
```python
# Top border
top_border = "┌" + "─" * (width) + "┐"
# Row format: "│ {content} │"
# Bottom border
bottom_border = "└" + "─" * (width) + "┘"
```

### 5. Update legend format (lines 100-108)
- Display each legend entry on its own line
- Group by category type
- Format: "  🏠 Town Name"

### 6. Increase cell_width (line 67)
```python
cell_width = 4  # Accommodate emoji markers
```

## File Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/map_renderer.py` | Expand viewport, add borders, category markers, vertical legend |
| `tests/test_map_renderer.py` | Update viewport tests, add new visual tests |
