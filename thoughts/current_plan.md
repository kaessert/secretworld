# Fix Map Alignment and Show Available Exits

## Issue
The map display is misaligned because ANSI color codes in the `@` marker (14 chars with escapes vs 1 display char) break Python's string formatting width calculation. Additionally, available exits from the current location should be visible on the map.

## Implementation

### 1. Fix column alignment for colored markers
**File:** `src/cli_rpg/map_renderer.py`

The fix: Pad markers BEFORE applying color codes, not after. Change line 82 from:
```python
row_parts.append(f"{marker:>{cell_width}}")
```
To building the marker with pre-calculated padding, then applying color only to the character itself.

Specifically:
- Store uncolored markers in `coord_to_marker`
- Apply padding to the uncolored marker
- Only colorize the actual character, not the padding

### 2. Show available exits on the map
**File:** `src/cli_rpg/map_renderer.py`

Add "Exits: north, east" line after the legend showing available directions from current location.

### 3. Update tests
**File:** `tests/test_map_renderer.py`

Add tests to verify:
- Colored markers align correctly with uncolored markers
- Exits are displayed for current location

## Step-by-step Implementation

1. Modify `render_map()` to separate marker character from color application:
   - Keep `coord_to_marker` as plain characters (no ANSI codes)
   - Create separate function/logic to colorize after padding
   - Apply padding first, then wrap player marker in color

2. Add exits display:
   - Get `current_loc.get_available_directions()`
   - Add "Exits: {directions}" line after legend

3. Add test for alignment (verify @ marker aligns with other markers)

4. Add test for exits display

5. Run tests: `pytest tests/test_map_renderer.py -v`
