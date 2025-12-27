# Map Display - Terrain Symbols for Unnamed Locations

## Spec

Show terrain-specific symbols for unnamed locations (`is_named=False`) on the map, while preserving letter identifiers only for named locations (`is_named=True`). This makes the sparse world design visible to players.

**Current behavior**: All locations show letters (A, B, C...) regardless of type
**Target behavior**:
- Unnamed terrain tiles: Show terrain symbol (`.` for plains, `T` for forest, etc.)
- Named locations: Show letter identifier (A, B, C...) + category icon in legend

### Terrain Symbols (ASCII-safe)
| Terrain | Symbol | Passable |
|---------|--------|----------|
| forest | `T` | Yes |
| plains | `.` | Yes |
| hills | `n` | Yes |
| desert | `:` | Yes |
| swamp | `%` | Yes |
| beach | `,` | Yes |
| foothills | `^` | Yes |
| mountain | `M` | Yes |
| water | `~` | No |

## Tests

### File: `tests/test_terrain_map_symbols.py`

1. `test_terrain_map_symbols_constant_exists` - Verify `TERRAIN_MAP_SYMBOLS` dict exists in world_tiles.py with all 9 terrain types
2. `test_get_terrain_symbol_returns_correct_symbol` - Test `get_terrain_symbol()` function returns expected symbol for each terrain
3. `test_get_terrain_symbol_unknown_terrain_returns_default` - Unknown terrain returns `.` (plains default)
4. `test_unnamed_location_shows_terrain_symbol_on_map` - Map grid shows `T` for unnamed forest, not letter
5. `test_named_location_shows_letter_on_map` - Map grid shows letter (A, B...) for named locations
6. `test_legend_excludes_unnamed_locations` - Legend lists only named locations, not terrain descriptions
7. `test_legend_includes_terrain_symbol_key` - Legend explains terrain symbols (`T = forest`, etc.)
8. `test_mixed_named_unnamed_locations` - Grid correctly distinguishes named (letters) vs unnamed (terrain symbols)
9. `test_water_symbol_consistent` - Water terrain uses existing `~` symbol (already implemented)

## Implementation

### 1. Add terrain symbols to `world_tiles.py`

```python
# ASCII-safe terrain map symbols
TERRAIN_MAP_SYMBOLS: Dict[str, str] = {
    "forest": "T",
    "plains": ".",
    "hills": "n",
    "desert": ":",
    "swamp": "%",
    "beach": ",",
    "foothills": "^",
    "mountain": "M",
    "water": "~",
}

def get_terrain_symbol(terrain: str) -> str:
    """Get ASCII map symbol for a terrain type.

    Args:
        terrain: Terrain type name (e.g., "forest", "water")

    Returns:
        Single-character ASCII symbol for map display
    """
    return TERRAIN_MAP_SYMBOLS.get(terrain, ".")
```

### 2. Modify `map_renderer.py` - `render_map()` function

**Lines ~127-151**: Change symbol assignment logic to:
1. Check `location.is_named` before assigning letter symbol
2. For `is_named=False`: Use `get_terrain_symbol(location.terrain)`
3. For `is_named=True`: Use existing letter assignment (A, B, C...)

**Lines ~153-169**: Update legend building:
1. Only add named locations (`is_named=True`) to legend entries
2. Add terrain symbol key at end of legend (after location entries)

### 3. Key code changes

```python
# In render_map(), when building coord_to_marker:
for name, location in locations_with_coords:
    coords = location.coordinates
    if name == current_location:
        coord_to_marker[coords] = "@"
    elif location.is_named:
        # Named locations get letter symbols
        reachable_names.add(name)
    else:
        # Unnamed locations get terrain symbols
        terrain = location.terrain or "plains"
        coord_to_marker[coords] = get_terrain_symbol(terrain)

# Only assign letters to named locations
sorted_names = sorted(name for name in reachable_names
                      if name != current_location)
location_symbols = {name: SYMBOLS[i] for i, name in enumerate(sorted_names)
                    if i < len(SYMBOLS)}

# In legend building - only include named locations
for name, location in locations_with_coords:
    if not location.is_named:
        continue  # Skip unnamed terrain
    # ... existing legend logic ...

# Add terrain symbol key to legend
lines.append("")
lines.append("Terrain: T=forest .=plains n=hills :=desert %=swamp ,=beach ^=foothills M=mountain")
```

### Files to Modify
- `src/cli_rpg/world_tiles.py`: Add `TERRAIN_MAP_SYMBOLS` constant and `get_terrain_symbol()` function
- `src/cli_rpg/map_renderer.py`: Update symbol assignment and legend logic in `render_map()`
