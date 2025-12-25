# Implementation Plan: Unique Map Location Symbols

## Problem
The map command shows all non-current locations with the same `•` symbol, making it impossible to distinguish between locations in the legend and on the map grid.

## Solution
Assign unique letter symbols (A-Z) to each location in both the map grid and legend, preserving special markers for the current location (`@`) and blocked cells (`█`).

---

## Spec

1. **Symbol Assignment**: Non-current locations get unique letters A-Z in alphabetical order by name
2. **Player Marker**: Current location remains `@` (cyan, bold)
3. **Category Icons**: Category icons (🏠, 🌲, etc.) move to legend only, not displayed on map grid
4. **Legend Format**: `A = 🏠 Town Square` (letter symbol, then category icon if present, then name)
5. **Capacity**: Support 26 locations (A-Z); if exceeded, wrap to lowercase a-z (52 total)

---

## Tests (in `tests/test_map_renderer.py`)

### New tests to add:

```python
class TestUniqueLocationSymbols:
    """Tests for unique letter symbols per location."""

    def test_unique_symbols_assigned_to_locations(self):
        """Each non-current location gets a unique letter symbol A-Z."""
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0)),
            "Forest": Location("Forest", "A forest", {}, coordinates=(1, 0)),
            "Cave": Location("Cave", "A cave", {}, coordinates=(2, 0)),
        }
        result = render_map(world, "Town")
        # Cave and Forest get A/B in alphabetical order
        assert "A = Cave" in result or "A =" in result and "Cave" in result
        assert "B = Forest" in result or "B =" in result and "Forest" in result

    def test_legend_shows_category_icon_with_letter(self):
        """Legend shows letter + category icon + name."""
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0), category="town"),
            "Forest": Location("Forest", "A forest", {}, coordinates=(1, 0), category="forest"),
        }
        result = render_map(world, "Town")
        # Legend should show "A = 🌲 Forest"
        assert "🌲" in result and "Forest" in result

    def test_map_grid_uses_letters_not_category_icons(self):
        """Map grid shows letters, not category emoji icons."""
        world = {
            "Town": Location("Town", "A town", {}, coordinates=(0, 0), category="town"),
            "Forest": Location("Forest", "A forest", {}, coordinates=(1, 0), category="forest"),
        }
        result = render_map(world, "Town")
        grid_section = result.split("Legend:")[0]
        # Grid should have letters, not emoji for non-current locations
        assert "🌲" not in grid_section
        assert "A" in grid_section

    def test_symbol_consistent_between_legend_and_grid(self):
        """Same letter appears in both legend and grid for each location."""
        world = {
            "Alpha": Location("Alpha", "First", {}, coordinates=(0, 0)),
            "Beta": Location("Beta", "Second", {}, coordinates=(0, 1)),
        }
        result = render_map(world, "Alpha")
        grid_section = result.split("Legend:")[0]
        # Beta should be A, and A should appear in grid
        assert "A = Beta" in result
        assert "A" in grid_section
```

---

## Implementation Steps

### Step 1: Modify `render_map()` in `src/cli_rpg/map_renderer.py`

1. **Add symbol assignment after collecting locations** (~line 103):
   ```python
   # Assign unique letter symbols to non-current locations (alphabetical by name)
   SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
   sorted_names = sorted(name for name, _ in locations_with_coords if name != current_location)
   location_symbols = {name: SYMBOLS[i] for i, name in enumerate(sorted_names) if i < len(SYMBOLS)}
   ```

2. **Update legend generation** (~line 105-112):
   ```python
   for name, location in locations_with_coords:
       if name == current_location:
           legend_entries.append(f"  {colors.bold_colorize('@', colors.CYAN)} = You ({name})")
       else:
           symbol = location_symbols.get(name, "?")
           category_icon = get_category_marker(location.category)
           if category_icon and category_icon != "•":
               legend_entries.append(f"  {symbol} = {category_icon} {name}")
           else:
               legend_entries.append(f"  {symbol} = {name}")
   ```

3. **Update coord_to_marker** (~line 116-122):
   ```python
   for name, location in locations_with_coords:
       coords = location.coordinates
       if name == current_location:
           coord_to_marker[coords] = "@"
       else:
           coord_to_marker[coords] = location_symbols.get(name, "?")
   ```

### Step 2: Update existing tests

Update tests that check for category icons in the map grid to expect letters instead:
- `test_location_markers_show_category` → check legend has icons, grid has letters
- `test_uncategorized_location_shows_default_marker` → expect letter, not `•`
- `test_legend_shows_category_markers` → verify new format

### Step 3: Run tests

```bash
pytest tests/test_map_renderer.py -v
```

---

## Files to Modify

1. `src/cli_rpg/map_renderer.py` - Core changes to symbol assignment and legend
2. `tests/test_map_renderer.py` - Add new tests, update existing tests
