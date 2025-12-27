# Fix Map Visibility Radius Integration

## Bug Summary
The visibility system is fully implemented but not wired up at the command handler level. `seen_tiles` is populated during movement but never passed to the map renderer.

## Root Cause
In `main.py`, the `map` and `worldmap` commands call `render_map()` without passing `game_state.seen_tiles`.

## Implementation Steps

### 1. Fix `map` command (main.py line 1810-1815)
Pass `seen_tiles` to `render_map()`:
```python
map_output = render_map(
    game_state.world,
    game_state.current_location,
    game_state.current_sub_grid,
    game_state.chunk_manager,
    game_state.seen_tiles,  # ADD THIS
)
```

### 2. Fix `render_worldmap` function signature (map_renderer.py line 439)
Add `seen_tiles` parameter:
```python
def render_worldmap(
    world: dict[str, Location],
    current_location: str,
    seen_tiles: Optional[set[tuple[int, int]]] = None,
) -> str:
```

### 3. Pass `seen_tiles` in `render_worldmap` body (map_renderer.py line 480)
```python
map_output = render_map(overworld_locations, map_center_location, seen_tiles=seen_tiles)
```

### 4. Fix `worldmap` command (main.py line 1824)
Pass `seen_tiles` to `render_worldmap()`:
```python
worldmap_output = render_worldmap(game_state.world, worldmap_location, game_state.seen_tiles)
```

## Verification
```bash
pytest tests/test_visibility_radius.py tests/test_map_renderer.py -v
```

## Files Changed

| File | Line | Change |
|------|------|--------|
| `src/cli_rpg/main.py` | 1810-1815 | Add `game_state.seen_tiles` parameter to `render_map()` |
| `src/cli_rpg/map_renderer.py` | 439 | Add `seen_tiles` parameter to `render_worldmap()` signature |
| `src/cli_rpg/map_renderer.py` | 480 | Pass `seen_tiles` to `render_map()` call |
| `src/cli_rpg/main.py` | 1824 | Add `game_state.seen_tiles` parameter to `render_worldmap()` |
