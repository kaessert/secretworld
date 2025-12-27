# Implementation Plan: "Exits Disappear When Revisiting Locations" Bug Fix

## Problem Summary

Available exits change inconsistently when revisiting a location (e.g., Whispering Woods shows "east, north, west" initially, later shows only "east, west").

**Root Cause**: `get_available_directions()` only returns directions where a **Location object already exists** in the world dict. Since locations are generated on-demand when the player moves, directions where no location has been generated yet are hidden—even though the terrain is passable and the player could move there.

## Current Flow (Buggy)

```
Player at (0,0) "Whispering Woods"
├── Adjacent locations in world dict: only (1,0) and (-1,0) exist
├── get_available_directions() → ["east", "west"]  (only existing locations)
└── Exits displayed: "east, west" (missing "north" even if terrain is passable)
```

## Target Flow (Fixed)

```
Player at (0,0) "Whispering Woods"
├── get_valid_moves(chunk_manager, 0, 0) → ["east", "north", "south", "west"] (from WFC terrain)
├── Filter by terrain passability (already done in get_valid_moves)
└── Exits displayed: all passable directions, regardless of location existence
```

## Spec

For **overworld locations with WFC enabled**:
- Exits should be determined by WFC terrain passability (`get_valid_moves()`), NOT by existence of adjacent Location objects
- This ensures exits are stable across revisits (terrain doesn't change, exits don't change)
- For sub-grid locations (interiors), continue using `get_available_directions()` since interiors have bounded grids

## Test Plan

Add to `tests/test_wfc_exit_display.py`:

1. `test_exits_shown_for_unexplored_passable_directions` - Exits shown for passable terrain even when no location exists there
2. `test_exits_stable_across_revisits` - Exits remain consistent when revisiting after exploration
3. `test_subgrid_uses_location_based_exits` - SubGrid interiors still use bounded grid logic

## Implementation Steps

### 1. Modify `Location.get_filtered_directions()` in `src/cli_rpg/models/location.py`

**Change**: When `chunk_manager` is provided and we're in overworld (no sub_grid), use `get_valid_moves()` directly instead of filtering `get_available_directions()`.

```python
def get_filtered_directions(
    self,
    chunk_manager: Optional["ChunkManager"],
    world: Optional[dict] = None,
    sub_grid: Optional["SubGrid"] = None,
) -> list[str]:
    # For sub-grid locations (interiors), use existing location-based logic
    if sub_grid is not None:
        return self.get_available_directions(sub_grid=sub_grid)

    # For overworld WITH WFC: use terrain passability directly
    if chunk_manager is not None and self.coordinates is not None:
        from cli_rpg.world_tiles import get_valid_moves
        return get_valid_moves(chunk_manager, self.coordinates[0], self.coordinates[1])

    # Fallback (no WFC): use existing location-based logic
    return self.get_available_directions(world=world, sub_grid=sub_grid)
```

### 2. Add Tests in `tests/test_wfc_exit_display.py`

```python
def test_exits_shown_for_unexplored_passable_directions(self):
    """Exits should be shown for passable terrain even if no location exists there yet."""
    location = Location(name="Test", description="Test", coordinates=(0, 0))
    world = {"Test": location}  # Only current location exists

    chunk_manager = Mock()
    chunk_manager.get_tile_at = Mock(return_value="plains")  # All passable

    filtered = location.get_filtered_directions(chunk_manager, world=world)
    assert filtered == ["east", "north", "south", "west"]

def test_exits_stable_across_revisits(self):
    """Exits should not change when revisiting a location."""
    location = Location(name="Test", description="Test", coordinates=(5, 5))
    world_initial = {"Test": location}
    north_loc = Location(name="North", description="North", coordinates=(5, 6))
    world_later = {"Test": location, "North": north_loc}

    chunk_manager = Mock()
    def get_tile_at(x, y):
        if y == 4:  # South is water
            return "water"
        return "plains"
    chunk_manager.get_tile_at = get_tile_at

    exits_initial = location.get_filtered_directions(chunk_manager, world=world_initial)
    exits_later = location.get_filtered_directions(chunk_manager, world=world_later)

    assert exits_initial == exits_later == ["east", "north", "west"]

def test_subgrid_uses_location_based_exits(self):
    """SubGrid interiors should use location-based exits (bounded grid)."""
    from cli_rpg.world_grid import SubGrid

    sub_grid = SubGrid()
    loc = Location(name="Room1", description="A room", coordinates=(0, 0))
    loc2 = Location(name="Room2", description="Another room", coordinates=(0, 1))
    sub_grid.add_location(loc, 0, 0)
    sub_grid.add_location(loc2, 0, 1)

    chunk_manager = Mock()
    chunk_manager.get_tile_at = Mock(return_value="plains")

    exits = loc.get_filtered_directions(chunk_manager, sub_grid=sub_grid)
    assert exits == ["north"]  # Only Room2 exists at (0,1)
```

## Files to Modify

| File | Change |
|------|--------|
| `src/cli_rpg/models/location.py` | Update `get_filtered_directions()` to use `get_valid_moves()` for overworld WFC |
| `tests/test_wfc_exit_display.py` | Add 3 new test cases for stable exits |

## Success Criteria

- [ ] Exits remain consistent when revisiting overworld locations
- [ ] Exits to unexplored (but passable) terrain are shown
- [ ] SubGrid interiors still work correctly (location-based)
- [ ] All existing tests pass
- [ ] 3 new test cases pass
