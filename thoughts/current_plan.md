# Map Visibility Radius Implementation Plan

**Priority**: CRITICAL - BLOCKER
**Status**: PLANNED
**Issue**: Players can only see tiles they've physically visited, creating a "walking blind" experience

## Overview

Transform the map from "visited tiles only" to "visibility radius" mode. Players should see nearby terrain within a configurable radius, with terrain type affecting visibility distance and Perception stat providing bonuses.

## Spec

1. **Seen vs Visited Tracking**: Track two tile states separately:
   - `visited`: Player has physically moved to this tile (current behavior)
   - `seen`: Tile is visible (within radius OR previously visited)

2. **Visibility Radius by Terrain**: From current player position, calculate visibility:
   - Plains: 3 tiles (open terrain = far view)
   - Hills/Beach/Desert: 2 tiles (moderate obstacles)
   - Forest/Swamp/Foothills: 1 tile (blocked view)
   - Mountain: 0 tiles (only current tile visible)
   - Special: Standing ON a mountain grants +2 visibility in all directions

3. **Perception Stat Bonus**: `+1 visibility radius per 5 PER above 10`
   - Example: PER 15 = +1 radius, PER 20 = +2 radius

4. **Map Display**:
   - Visited tiles: Full detail (current behavior)
   - Seen-but-not-visited tiles: Show terrain symbol only (no location name in legend)

## Implementation Steps

### Step 1: Add visibility constants to `world_tiles.py`

```python
VISIBILITY_RADIUS: Dict[str, int] = {
    "plains": 3,
    "hills": 2,
    "beach": 2,
    "desert": 2,
    "forest": 1,
    "swamp": 1,
    "foothills": 1,
    "mountain": 0,
    "water": 2,
}

MOUNTAIN_VISIBILITY_BONUS = 2  # Extra radius when standing on mountain

def get_visibility_radius(terrain: str) -> int:
    """Get visibility radius for a terrain type."""
    return VISIBILITY_RADIUS.get(terrain, 2)
```

### Step 2: Add `get_tiles_in_radius()` helper to `world_grid.py`

```python
def get_tiles_in_radius(
    center_x: int,
    center_y: int,
    radius: int
) -> set[tuple[int, int]]:
    """Return all (x, y) coordinates within Manhattan distance radius."""
    tiles = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if abs(dx) + abs(dy) <= radius:
                tiles.add((center_x + dx, center_y + dy))
    return tiles
```

### Step 3: Add `seen_tiles` tracking to `game_state.py`

In `__init__`:
```python
self.seen_tiles: set[tuple[int, int]] = set()
```

Add methods:
```python
def calculate_visibility_radius(self, coords: tuple[int, int]) -> int:
    """Calculate visibility radius from terrain + PER bonus."""
    # Get terrain at current position
    terrain = "plains"
    if self.chunk_manager:
        terrain = self.chunk_manager.get_tile_at(*coords)

    # Base radius from terrain
    from cli_rpg.world_tiles import get_visibility_radius, MOUNTAIN_VISIBILITY_BONUS
    base_radius = get_visibility_radius(terrain)

    # Mountain standing bonus
    if terrain == "mountain":
        base_radius += MOUNTAIN_VISIBILITY_BONUS

    # Perception bonus: +1 per 5 PER above 10
    per_bonus = max(0, (self.current_character.perception - 10) // 5)

    return base_radius + per_bonus

def update_visibility(self, coords: tuple[int, int]) -> None:
    """Update seen_tiles based on current position and terrain."""
    from cli_rpg.world_grid import get_tiles_in_radius

    radius = self.calculate_visibility_radius(coords)
    visible = get_tiles_in_radius(coords[0], coords[1], radius)
    self.seen_tiles.update(visible)
```

Call `update_visibility()` at end of `move()` after successful movement.

### Step 4: Update `map_renderer.py` to use visibility

Modify `render_map()`:
1. Accept optional `seen_tiles: set[tuple[int, int]]` parameter
2. For tiles in `seen_tiles` but not in `world`: show terrain symbol from chunk_manager
3. Only add named locations in legend for visited tiles

```python
def render_map(
    world: dict[str, Location],
    current_location: str,
    sub_grid: Optional["SubGrid"] = None,
    chunk_manager: Optional["ChunkManager"] = None,
    seen_tiles: Optional[set[tuple[int, int]]] = None,
) -> str:
```

In the grid building loop:
```python
# Check if tile is seen but not visited
if coord not in coord_to_location and seen_tiles and coord in seen_tiles:
    if chunk_manager:
        terrain = chunk_manager.get_tile_at(*coord)
        marker = get_terrain_symbol(terrain)
        row_parts.append(pad_marker(marker, cell_width))
        continue
```

### Step 5: Serialize `seen_tiles` in persistence

In `to_dict()`:
```python
"seen_tiles": list(self.seen_tiles),
```

In `from_dict()`:
```python
game_state.seen_tiles = set(tuple(t) for t in data.get("seen_tiles", []))
```

## Test Plan

**File:** `tests/test_visibility_radius.py`

1. `test_get_tiles_in_radius_zero` - Returns only center tile for radius 0
2. `test_get_tiles_in_radius_one` - Returns 5 tiles (center + 4 adjacent)
3. `test_get_tiles_in_radius_two` - Returns 13 tiles (Manhattan diamond)
4. `test_visibility_radius_plains` - Plains terrain returns 3
5. `test_visibility_radius_forest` - Forest terrain returns 1
6. `test_visibility_radius_mountain` - Mountain terrain returns 0
7. `test_mountain_standing_bonus` - Standing on mountain grants +2 total
8. `test_perception_bonus_at_15` - PER 15 grants +1 radius
9. `test_perception_bonus_at_10` - PER 10 grants +0 radius
10. `test_update_visibility_marks_tiles` - Moving updates seen_tiles set
11. `test_seen_tiles_persist_save_load` - Seen tiles survive save/load cycle
12. `test_map_shows_seen_terrain` - Map displays terrain for seen-not-visited
13. `test_map_hides_unseen_tiles` - Tiles outside visibility remain blank

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/world_tiles.py` | Add `VISIBILITY_RADIUS`, `MOUNTAIN_VISIBILITY_BONUS`, `get_visibility_radius()` |
| `src/cli_rpg/world_grid.py` | Add `get_tiles_in_radius()` function |
| `src/cli_rpg/game_state.py` | Add `seen_tiles`, `update_visibility()`, `calculate_visibility_radius()`, persistence |
| `src/cli_rpg/map_renderer.py` | Accept `seen_tiles`, display terrain for seen-not-visited tiles |
| `tests/test_visibility_radius.py` | NEW - 13 visibility tests |

## Verification

```bash
pytest tests/test_visibility_radius.py -v
pytest tests/test_map_renderer.py -v
pytest tests/test_game_state.py -v
```
