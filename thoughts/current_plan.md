# Implementation Plan: GameState Sub-Location Navigation (Phase 1, Step 3)

## Status: ✅ COMPLETE

All functionality verified and working. See `thoughts/implementation_summary.md` for details.

## Overview

Wire up GameState to use the new SubGrid system for sub-location navigation. The SubGrid class and Location fields (`is_exit_point`, `sub_grid`) are already implemented. This step updates GameState methods to properly handle interior grids.

## Spec

When a player enters an overworld location with a `sub_grid`:
1. Track that we're "inside" the sub-grid via new GameState fields
2. Use sub-grid coordinates for `move()` instead of overworld coordinates
3. Only allow `exit` from locations marked `is_exit_point=True`
4. `get_current_location()` must resolve from sub-grid when inside one

## Tests First

Create `tests/test_subgrid_navigation.py`:

```python
# Test GameState new fields
- test_game_state_has_in_sub_location_field (default False)
- test_game_state_has_current_sub_grid_field (default None)

# Test enter() with sub_grid
- test_enter_with_sub_grid_sets_in_sub_location_true
- test_enter_with_sub_grid_sets_current_sub_grid
- test_enter_with_sub_grid_moves_to_entry_location
- test_enter_with_target_name_goes_to_specific_sub_location

# Test move() inside sub_grid
- test_move_inside_sub_grid_uses_sub_grid_coordinates
- test_move_inside_sub_grid_blocks_at_bounds
- test_move_inside_sub_grid_respects_connections

# Test exit_location() with is_exit_point
- test_exit_from_exit_point_succeeds
- test_exit_from_non_exit_point_fails
- test_exit_clears_in_sub_location
- test_exit_clears_current_sub_grid
- test_exit_returns_to_parent

# Test get_current_location() with sub_grid
- test_get_current_location_inside_sub_grid_returns_sub_grid_location

# Test persistence
- test_in_sub_location_persists_in_save
- test_current_sub_grid_persists_in_save
```

## Implementation Steps

### 1. Add GameState fields (`src/cli_rpg/game_state.py`)

Add to `__init__`:
```python
self.in_sub_location: bool = False
self.current_sub_grid: Optional["SubGrid"] = None
```

### 2. Update `get_current_location()` (~line 280)

```python
def get_current_location(self) -> Location:
    if self.in_sub_location and self.current_sub_grid is not None:
        loc = self.current_sub_grid.get_by_name(self.current_location)
        if loc is not None:
            return loc
    return self.world[self.current_location]
```

### 3. Update `enter()` method (~line 665)

After finding matched_location, check if it has sub_grid:
```python
# Check if entering an overworld location with its own sub_grid
if sub_location.sub_grid is not None:
    self.in_sub_location = True
    self.current_sub_grid = sub_location.sub_grid
    # Find entry location at (0, 0) or by target_name
    entry_loc = sub_location.sub_grid.get_by_coordinates(0, 0)
    if target_name:
        entry_loc = sub_location.sub_grid.get_by_name(target_name) or entry_loc
    if entry_loc:
        self.current_location = entry_loc.name
```

### 4. Update `exit_location()` method (~line 734)

Add exit point check:
```python
def exit_location(self) -> tuple[bool, str]:
    if self.is_in_conversation:
        return (False, "You're in a conversation. Say 'bye' to leave first.")

    current = self.get_current_location()

    # Check if at exit point when in sub-location
    if self.in_sub_location and not current.is_exit_point:
        return (False, "You cannot exit from here. Find an exit point.")

    # Must have a parent location
    if current.parent_location is None:
        return (False, "You're not inside a landmark.")

    # ... existing code ...

    # Clear sub-location state
    self.in_sub_location = False
    self.current_sub_grid = None
```

### 5. Update `move()` method (~line 426)

Add sub-grid movement handling:
```python
def move(self, direction: str) -> tuple[bool, str]:
    # ... existing conversation check ...

    # Handle movement inside sub-location grid
    if self.in_sub_location and self.current_sub_grid is not None:
        return self._move_in_sub_grid(direction)

    # ... existing overworld movement code ...

def _move_in_sub_grid(self, direction: str) -> tuple[bool, str]:
    """Handle movement within a sub-location grid."""
    current = self.get_current_location()

    if direction not in {"north", "south", "east", "west"}:
        return (False, "Invalid direction. Use: north, south, east, or west.")

    if not current.has_connection(direction):
        return (False, "You can't go that way.")

    destination_name = current.get_connection(direction)
    destination = self.current_sub_grid.get_by_name(destination_name)

    if destination is None:
        return (False, "The path is blocked.")

    self.current_location = destination.name

    # Time advancement, dread updates, etc. (similar to overworld)
    self.game_time.advance(1)
    # ... other move side effects ...

    return (True, f"You head {direction} to {colors.location(self.current_location)}.")
```

### 6. Update `to_dict()` / `from_dict()` for persistence (~line 870)

Add to `to_dict()`:
```python
"in_sub_location": self.in_sub_location,
# current_sub_grid is not serialized directly - it's part of Location.sub_grid
```

Add to `from_dict()`:
```python
game_state.in_sub_location = data.get("in_sub_location", False)
# current_sub_grid is restored by finding it from the current location
if game_state.in_sub_location:
    # Find parent location and get its sub_grid
    current = game_state.world.get(game_state.current_location)
    if current and current.parent_location:
        parent = game_state.world.get(current.parent_location)
        if parent and parent.sub_grid:
            game_state.current_sub_grid = parent.sub_grid
```

### 7. Update map_renderer for interior maps (optional enhancement)

Add `_render_sub_grid_map()` function for bounded interior maps with exit markers.

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/game_state.py` | Add fields, update `enter()`, `exit_location()`, `move()`, `get_current_location()`, `to_dict()`, `from_dict()` |
| `tests/test_subgrid_navigation.py` | New test file for sub-grid navigation |

## Verification

1. Run `pytest tests/test_subgrid_navigation.py -v` - all new tests pass
2. Run `pytest tests/test_sub_grid.py tests/test_exit_points.py -v` - existing tests still pass
3. Run `pytest` - full suite passes (3209+ tests)
