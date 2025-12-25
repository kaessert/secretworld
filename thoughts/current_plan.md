# Map Alignment and Blocked Location Markers

## Problem
1. **Emoji width inconsistency**: Emoji markers (🏠, ⚔, 🌲) are 2-width characters but the code treats them as 1-width, causing column misalignment
2. **No blocked cell indication**: Players can't see which viewport cells are impassable/empty vs unexplored

## Spec

### Emoji Width Handling
- Use `wcwidth` library to calculate actual display width of each marker character
- Pad each cell to `cell_width` (4) based on actual display width, not string length
- Emojis typically render as width 2, so need 2 spaces padding; ASCII markers need 3 spaces

### Blocked/Empty Cell Markers
- Cells with no location but within viewport remain blank (current behavior - no change needed)
- The issue description mentions "blocked/impassable" cells, but examining the codebase shows no concept of blocked cells - cells either have a location or are empty
- Keep empty cells as spaces (no marker needed for unexplored territory)

## Implementation Steps

### 1. Add wcwidth dependency
**File**: `pyproject.toml`
- Add `wcwidth>=0.2.0` to dependencies list

### 2. Create width-aware padding helper
**File**: `src/cli_rpg/map_renderer.py`
- Add import: `from wcwidth import wcswidth`
- Add helper function:
```python
def pad_marker(marker: str, target_width: int) -> str:
    """Right-pad marker to target_width based on display width."""
    display_width = wcswidth(marker)
    if display_width < 0:  # non-printable
        display_width = 1
    padding = target_width - display_width
    return (" " * padding) + marker
```

### 3. Update render_map cell rendering
**File**: `src/cli_rpg/map_renderer.py` (lines 107-118)
- Replace `f"{marker:>{cell_width}}"` with `pad_marker(marker, cell_width)`
- Update the colorized @ marker logic to use `pad_marker("@", cell_width)` then colorize

### 4. Write tests first

**File**: `tests/test_map_renderer.py`
- Add test for emoji alignment:
```python
def test_emoji_markers_align_correctly(self):
    """Verify emoji markers align with ASCII markers using wcwidth."""
    world = {
        "Town": Location("Town", "A town", {}, coordinates=(0, 0), category="town"),
        "Forest": Location("Forest", "A forest", {}, coordinates=(1, 0), category="forest"),
    }
    result = render_map(world, "Town")
    lines = result.split("\n")
    # Find row y=0
    row_y0 = next(l for l in lines if l.strip("│").strip().startswith("0 "))
    # Strip ANSI, verify columns are aligned
    import re
    clean = re.compile(r"\x1b\[[0-9;]*m").sub("", row_y0)
    # @ at x=0, 🌲 at x=1 should be 4 chars apart (cell_width)
    at_pos = clean.find("@")
    tree_pos = clean.find("🌲")
    # Note: 🌲 is 1 char but displays as 2 width
    assert tree_pos - at_pos == 4, f"Gap should be 4, got {tree_pos - at_pos}"
```

## Verification
1. Run `pytest tests/test_map_renderer.py -v` - all tests should pass
2. Run `pytest` - full suite should pass (1558+ tests)
3. Manual test: `cli-rpg`, navigate to see emoji locations, verify columns align
