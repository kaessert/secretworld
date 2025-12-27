# Issue 19: Multi-Level Dungeon Generation

## Spec

Generate dungeon/cave/ruins SubGrids across multiple z-levels (not just flat 2D) using the existing z-axis infrastructure. Entry at z=0, descending to min_z defined in `SUBGRID_BOUNDS`. Deeper levels have increased danger and better loot. Boss placed at lowest level.

**In Scope:**
- Extend `_generate_area_layout()` to return 3D coordinates `(x, y, z)` for multi-level categories
- Place stairs/ladders connecting levels with appropriate descriptions
- Scale treasure difficulty and secret thresholds by depth (z)
- Place boss at lowest z-level (not just furthest Manhattan distance)
- Add level indicator to map command (already exists: "Level {player_z}")

**Out of Scope (future work):**
- Vertical shortcuts via hidden passages (Issue 20)
- Category-specific procedural layouts (Issue 20)

## Tests (tests/test_multi_level_generation.py)

### Unit Tests

1. `test_generate_area_layout_3d_returns_z_coords_for_dungeon` - Layout for "dungeon" category returns 3-tuple coords with z from 0 to min_z
2. `test_generate_area_layout_3d_returns_z_coords_for_cave` - Layout for "cave" category returns 3-tuple coords
3. `test_generate_area_layout_3d_single_level_for_town` - Layout for "town" (min_z=max_z=0) returns 2D coords only
4. `test_generate_area_layout_3d_entry_at_z0` - First coordinate is always (0, 0, 0)
5. `test_generate_area_layout_3d_stairs_connect_levels` - Adjacent z-levels share (x, y) coordinate for stair connection

### Integration Tests

6. `test_expand_area_dungeon_uses_3d_layout` - `expand_area()` for dungeon places locations at multiple z-levels
7. `test_expand_area_places_stairs_locations` - Stair/ladder locations created between z-levels
8. `test_generate_subgrid_for_location_uses_3d` - `generate_subgrid_for_location()` creates multi-level SubGrid for dungeon
9. `test_boss_placed_at_lowest_z_level` - Boss room is at min_z, not just furthest x/y distance
10. `test_treasure_difficulty_scales_with_depth` - Treasures at z=-2 have higher difficulty than z=0
11. `test_secrets_threshold_scales_with_depth` - Secrets at lower z have higher thresholds
12. `test_map_shows_level_indicator_for_multilevel` - Map command shows "Level -1" etc. (existing functionality, verify)

## Implementation Steps

### 1. Extend `_generate_area_layout()` to support 3D (ai_service.py)

**File:** `src/cli_rpg/ai_service.py`

Add new method `_generate_area_layout_3d()`:
```python
def _generate_area_layout_3d(
    self,
    size: int,
    entry_direction: str,
    category: Optional[str] = None
) -> list[tuple[int, int, int]]:
    """Generate 3D coordinates for multi-level areas.

    For categories with z-depth (dungeon, cave, ruins), generates
    coords descending from z=0 to min_z with stairs connecting levels.

    Args:
        size: Number of locations to generate
        entry_direction: Direction player entered from
        category: Location category (dungeon, cave, etc.)

    Returns:
        List of (x, y, z) coordinate tuples
    """
```

Logic:
- Get z bounds from `get_subgrid_bounds(category)`
- If `min_z == max_z == 0`, delegate to existing 2D `_generate_area_layout()`
- For multi-level: distribute locations across z-levels
- Each level transition shares an (x, y) coord (stair placement)
- Entry always at (0, 0, 0)

### 2. Add stair location generation helper (ai_world.py)

**File:** `src/cli_rpg/ai_world.py`

Add `_create_stair_location()`:
```python
def _create_stair_location(
    from_z: int,
    to_z: int,
    category: str,
    coords: tuple[int, int, int]
) -> dict:
    """Create a stair/ladder location connecting two z-levels."""
```

Stair templates by category:
- dungeon: "Stone Stairway", "Spiral Stairs", "Crumbling Steps"
- cave: "Rope Ladder", "Natural Shaft", "Narrow Passage Down"
- ruins: "Ancient Stairs", "Collapsed Stairwell"

### 3. Modify `expand_area()` to use 3D layout (ai_world.py)

**File:** `src/cli_rpg/ai_world.py`

In `expand_area()`:
- Get category from first location or category_hint
- Call `ai_service._generate_area_layout_3d()` instead of `_generate_area_layout()`
- Handle 3-tuple coords when placing in SubGrid
- Existing `sub_grid.add_location(loc, rel_x, rel_y, rel_z)` already supports z

### 4. Modify `generate_subgrid_for_location()` to use 3D layout (ai_world.py)

**File:** `src/cli_rpg/ai_world.py`

Similar changes to `generate_subgrid_for_location()`:
- Call 3D layout generator for multi-level categories
- Handle z-coordinate when placing locations

### 5. Update boss placement for z-depth (ai_world.py)

**File:** `src/cli_rpg/ai_world.py`

Modify `_find_furthest_room()`:
```python
def _find_furthest_room(placed_locations: dict, prefer_lowest_z: bool = True) -> Optional[str]:
    """Find room for boss placement.

    For multi-level dungeons, prioritizes lowest z-level.
    Among locations at lowest z, picks furthest by Manhattan distance.
    """
```

### 6. Scale treasure/secret difficulty by z-depth (ai_world.py)

**File:** `src/cli_rpg/ai_world.py`

Modify `_create_treasure_chest()`:
```python
def _create_treasure_chest(category: str, distance: int, z_level: int = 0) -> dict:
    # difficulty = distance + abs(z_level) + random(0,1)
```

Modify `_generate_secrets_for_location()`:
```python
def _generate_secrets_for_location(category: str, distance: int = 0, z_level: int = 0) -> list[dict]:
    # threshold += abs(z_level) for deeper secrets
```

### 7. Update placed_locations tracking for z (ai_world.py)

In `expand_area()` and `generate_subgrid_for_location()`:
```python
placed_locations[name] = {
    "location": new_loc,
    "relative_coords": (rel_x, rel_y, rel_z),  # 3-tuple
    "is_entry": is_entry,
}
```

## Summary of File Changes

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_service.py` | Add `_generate_area_layout_3d()` method |
| `src/cli_rpg/ai_world.py` | Add `_create_stair_location()`, update `expand_area()`, `generate_subgrid_for_location()`, `_find_furthest_room()`, `_create_treasure_chest()`, `_generate_secrets_for_location()` |
| `tests/test_multi_level_generation.py` | NEW - 12 tests covering all acceptance criteria |
