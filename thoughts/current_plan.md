# Multi-Level Dungeon Navigation (Z-Coordinate Support)

## Spec

Add vertical navigation (`up`/`down` commands) to SubGrid locations, enabling multi-level dungeons with z-coordinate support. The z-axis represents vertical levels (0 = ground floor, positive = upper floors, negative = basement/depths).

**Constraints:**
- Z-coordinate only applies to SubGrid (interior locations), NOT overworld
- Overworld remains 2D (x, y) - no changes to ChunkManager/WFC
- Backward compatible: existing 2D saves auto-upgrade to z=0

## Tests First

### `tests/test_vertical_navigation.py` (new file)

```python
# Location model tests
- test_location_coordinates_can_have_z_component  # (x, y, z) tuple support
- test_location_coordinates_default_to_2d  # backward compat: (x, y) stays (x, y)
- test_location_serialization_includes_z  # to_dict includes 3rd element
- test_location_deserialization_upgrades_2d_to_3d  # from_dict adds z=0 if missing

# Direction offset tests
- test_direction_up_offset_is_0_0_1
- test_direction_down_offset_is_0_0_minus1
- test_opposite_of_up_is_down
- test_opposite_of_down_is_up

# SubGrid 3D tests
- test_subgrid_bounds_include_z_axis  # (min_x, max_x, min_y, max_y, min_z, max_z)
- test_subgrid_add_location_with_z_coordinate
- test_subgrid_get_by_coordinates_with_z
- test_subgrid_is_within_bounds_checks_z
- test_subgrid_serialization_preserves_z_bounds
- test_subgrid_deserialization_upgrades_4tuple_to_6tuple

# Movement tests
- test_move_up_in_subgrid_increases_z
- test_move_down_in_subgrid_decreases_z
- test_move_up_blocked_at_max_z
- test_move_down_blocked_at_min_z
- test_up_direction_only_works_in_subgrid  # blocked on overworld
- test_down_direction_only_works_in_subgrid

# Command parsing tests
- test_go_up_command_calls_move_up
- test_go_down_command_calls_move_down
```

## Implementation Steps

### Step 1: Extend coordinate types in `world_grid.py`

```python
# Add 3D direction offsets for SubGrid navigation
SUBGRID_DIRECTION_OFFSETS: Dict[str, Tuple[int, int, int]] = {
    "north": (0, 1, 0),
    "south": (0, -1, 0),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
}

# Add to OPPOSITE_DIRECTIONS
OPPOSITE_DIRECTIONS["up"] = "down"
OPPOSITE_DIRECTIONS["down"] = "up"
```

### Step 2: Update `SUBGRID_BOUNDS` in `world_grid.py`

Change from 4-tuple to 6-tuple format: `(min_x, max_x, min_y, max_y, min_z, max_z)`

```python
SUBGRID_BOUNDS: Dict[str, Tuple[int, int, int, int, int, int]] = {
    "house": (-1, 1, -1, 1, 0, 0),      # single level
    "shop": (-1, 1, -1, 1, 0, 0),
    "cave": (-1, 1, -1, 1, -1, 0),      # goes down
    "dungeon": (-3, 3, -3, 3, -2, 0),   # multi-level down
    "tower": (-1, 1, -1, 1, 0, 3),      # multi-level up
    "temple": (-3, 3, -3, 3, -1, 1),    # basement + main + upper
    "city": (-8, 8, -8, 8, 0, 0),
    "town": (-5, 5, -5, 5, 0, 0),
    "village": (-5, 5, -5, 5, 0, 0),
    "tavern": (-2, 2, -2, 2, 0, 1),     # main floor + upstairs
    "ruins": (-2, 2, -2, 2, -1, 0),     # basement
    "settlement": (-2, 2, -2, 2, 0, 0),
    "forest": (-3, 3, -3, 3, 0, 0),
    "wilderness": (-3, 3, -3, 3, 0, 0),
    "default": (-2, 2, -2, 2, 0, 0),
}

def get_subgrid_bounds(category: Optional[str]) -> Tuple[int, int, int, int, int, int]:
    """Get SubGrid bounds for a location category (returns 6-tuple with z)."""
```

### Step 3: Update `SubGrid` class in `world_grid.py`

- Change `_grid: Dict[Tuple[int, int], Location]` → `Dict[Tuple[int, int, int], Location]`
- Change `bounds: Tuple[int, int, int, int]` → `Tuple[int, int, int, int, int, int]`
- Update `add_location(location, x, y, z=0)`
- Update `get_by_coordinates(x, y, z=0)`
- Update `is_within_bounds(x, y, z=0)`
- Update `to_dict()` / `from_dict()` with backward compat for 4-tuple bounds

### Step 4: Update `Location.coordinates` in `models/location.py`

Use Union type for 2D or 3D coordinates:
- `coordinates: Optional[Union[Tuple[int, int], Tuple[int, int, int]]] = None`
- Helper: `get_z() -> int` returns z or 0 if 2D tuple
- Update `to_dict()`: serialize 2 or 3 elements based on length
- Update `from_dict()`: keep as-is (don't upgrade 2D to 3D automatically)

### Step 5: Update `_move_in_sub_grid()` in `game_state.py`

```python
def _move_in_sub_grid(self, direction: str) -> tuple[bool, str]:
    from cli_rpg.world_grid import SUBGRID_DIRECTION_OFFSETS

    if direction not in {"north", "south", "east", "west", "up", "down"}:
        return (False, "Invalid direction. Use: north, south, east, west, up, or down.")

    dx, dy, dz = SUBGRID_DIRECTION_OFFSETS[direction]
    x, y = current.coordinates[:2]
    z = current.coordinates[2] if len(current.coordinates) > 2 else 0
    target_coords = (x + dx, y + dy, z + dz)

    if not self.current_sub_grid.is_within_bounds(*target_coords):
        if dz != 0:
            return (False, "There's no way to go that direction.")
        return (False, "You've reached the edge of this area.")

    destination = self.current_sub_grid.get_by_coordinates(*target_coords)
    # ... rest of existing logic
```

### Step 6: Update `move()` in `game_state.py`

Add guard for up/down on overworld:
```python
def move(self, direction: str) -> tuple[bool, str]:
    # Handle sub-grid movement (includes up/down)
    if self.in_sub_location and self.current_sub_grid is not None:
        return self._move_in_sub_grid(direction)

    # Overworld only allows 2D movement
    if direction in ("up", "down"):
        return (False, "You can only go up or down inside buildings and dungeons.")

    # ... existing overworld logic
```

### Step 7: Update command parsing in `main.py`

Update help text in go command:
```python
elif command == "go":
    if not args:
        return (True, "\nGo where? Specify a direction (north, south, east, west, up, down)")
```

## Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/world_grid.py` | SUBGRID_DIRECTION_OFFSETS, 6-tuple bounds, SubGrid 3D support |
| `src/cli_rpg/models/location.py` | 3-tuple coordinates support, get_z() helper, serialization |
| `src/cli_rpg/game_state.py` | `_move_in_sub_grid()` z-movement, `move()` up/down guard |
| `src/cli_rpg/main.py` | Update go command help text |
| `tests/test_vertical_navigation.py` | New test file (~22 tests) |
