# Implementation Plan: Fix ai_world.py expand_area() to Use SubGrid (Phase 1, Step 5)

## Status: PENDING

## Problem Statement

The `expand_area()` function in `ai_world.py` (lines 667-668) adds ALL generated locations to the overworld grid:

```python
# Current bug (lines 667-668):
for name, data in placed_locations.items():
    world[name] = data["location"]  # ALL locations added to same grid!
```

This means interior/sub-locations get overworld coordinates, appearing on the worldmap and enabling cardinal direction movement (`go north`) between what should be interior rooms. Players should use `enter`/`exit` commands for these.

## Spec

### Behavior Change

**Before (broken):**
- Entry location + all sub-locations added to overworld `world` dict with coordinates
- All locations show on worldmap
- Players move between rooms with `go north/south/east/west`

**After (fixed):**
- Entry location added to overworld `world` dict with coordinates
- Sub-locations added to entry's `sub_grid` (no overworld coordinates)
- Only entry shows on worldmap
- Players use `enter <name>` to go inside, `exit` to leave
- Cardinal movement works inside the SubGrid

### Key Rules

1. Entry location (at relative 0,0): Added to overworld with `is_exit_point=True` and a `sub_grid`
2. Sub-locations: Added to entry's SubGrid, NOT to overworld
3. Entry point in SubGrid at (0,0): The first sub-location, marked `is_exit_point=True`
4. SubGrid bounds: (-3, 3, -3, 3) for 7x7 areas (enough for 4-7 locations)

## Tests First

**File:** `tests/test_ai_world_subgrid.py`

```python
class TestExpandAreaSubGrid:
    """Tests for expand_area() SubGrid integration."""

    def test_expand_area_creates_subgrid_for_entry(self):
        """Entry location should have sub_grid attached."""

    def test_expand_area_sublocations_not_in_world(self):
        """Sub-locations should NOT be in world dict."""

    def test_expand_area_sublocations_in_subgrid(self):
        """Sub-locations should be in entry's sub_grid."""

    def test_expand_area_entry_has_is_exit_point_true(self):
        """Entry location is marked as exit point."""

    def test_expand_area_first_sublocation_is_exit_point(self):
        """First sub-location at (0,0) in SubGrid is exit point."""

    def test_expand_area_sublocations_have_parent_location(self):
        """Sub-locations have parent_location set to entry name."""

    def test_expand_area_subgrid_has_connections(self):
        """SubGrid locations have bidirectional connections."""

    def test_expand_area_only_entry_has_overworld_coords(self):
        """Only entry has overworld coordinates."""
```

## Implementation Steps

### Step 1: Store Relative Coordinates During First Pass

Modify first pass (around line 607) to store relative coordinates:

```python
placed_locations[loc_data["name"]] = {
    "location": new_loc,
    "connections": loc_data["connections"],
    "coords": (abs_x, abs_y),
    "relative_coords": (rel_x, rel_y),  # NEW: for SubGrid placement
    "is_entry": is_entry
}
```

### Step 2: Replace Lines 666-668 with SubGrid Logic

Replace:
```python
# Add locations to world
for name, data in placed_locations.items():
    world[name] = data["location"]
```

With:
```python
# Create SubGrid for sub-locations
from cli_rpg.world_grid import SubGrid

if entry_name is not None and len(placed_locations) > 1:
    entry_loc = placed_locations[entry_name]["location"]

    # Create SubGrid for interior
    sub_grid = SubGrid(bounds=(-3, 3, -3, 3), parent_name=entry_name)

    # Add sub-locations to SubGrid (not to world)
    first_subloc = True
    for name, data in placed_locations.items():
        if data.get("is_entry", False):
            continue  # Skip entry, it goes to world

        loc = data["location"]
        rel_x, rel_y = data["relative_coords"]

        # Clear overworld coordinates (sub-locations get SubGrid coords)
        loc.coordinates = None

        # First sub-location is exit point
        loc.is_exit_point = first_subloc
        first_subloc = False

        sub_grid.add_location(loc, rel_x, rel_y)

    # Attach sub_grid to entry
    entry_loc.sub_grid = sub_grid
    entry_loc.is_exit_point = True  # Can exit from entry

    # Only add entry to world
    world[entry_name] = entry_loc
else:
    # Single location or no entry - add all to world (legacy behavior)
    for name, data in placed_locations.items():
        world[name] = data["location"]
```

### Step 3: Clean Up Hierarchy Setup Code

The existing code (lines 636-650) already sets `parent_location` and `sub_locations`. Adjust to work with SubGrid:

```python
# Set up hierarchy relationships (already exists, adjust as needed)
if entry_name is not None:
    entry_loc = placed_locations[entry_name]["location"]
    sub_location_names = []

    for name, data in placed_locations.items():
        if not data.get("is_entry", False):
            sub_location_names.append(name)

    # Set entry's sub_locations list and entry_point
    entry_loc.sub_locations = sub_location_names
    if sub_location_names:
        entry_loc.entry_point = sub_location_names[0]
```

### Step 4: Ensure Connections Work Correctly

The second pass (lines 652-664) adds connections. SubGrid.add_location() automatically creates bidirectional connections within the SubGrid. Update:

```python
# Second pass: add connections
for name, data in placed_locations.items():
    loc = data["location"]
    connections = data["connections"]

    for conn_dir, conn_target in connections.items():
        if conn_target == "EXISTING_WORLD":
            conn_target = from_location

        # Only add connections to entry for sub-locations
        if data.get("is_entry", False):
            # Entry connects to overworld
            if conn_target in world:
                loc.add_connection(conn_dir, conn_target)
        # SubGrid locations get connections automatically via add_location()
```

## Files to Modify

| File | Change |
|------|--------|
| `src/cli_rpg/ai_world.py` | Modify expand_area() lines 550-668 |
| `tests/test_ai_world_subgrid.py` | NEW: Tests for SubGrid integration |

## Verification

```bash
pytest tests/test_ai_world_subgrid.py -v
pytest tests/test_subgrid_navigation.py -v
pytest tests/test_ai_world_hierarchy.py -v
pytest tests/ -v  # Full suite
```
