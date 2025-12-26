# Implementation Plan: Add `is_exit_point` and `sub_grid` to Location Model

**Priority**: P0 BLOCKER (Phase 1, Step 2 of Sub-Location Grid System)

## Spec

Add two new fields to the `Location` model to support the SubGrid-based sub-location system:

1. **`is_exit_point: bool`** - Marks locations where `exit` command is allowed (entrance rooms)
2. **`sub_grid: Optional[SubGrid]`** - Contains the bounded interior grid for overworld landmarks

This enables:
- Interior locations only allow `exit` from marked exit points (not from deep within dungeons)
- Overworld landmarks can contain bounded SubGrid interiors with their own coordinate system
- Clear separation between overworld grid and interior sub-grids

## Implementation Steps

### Step 1: Add fields to Location model
**File**: `src/cli_rpg/models/location.py`

Add after line 51 (after `hidden_secrets` field):
```python
is_exit_point: bool = False  # Only these rooms allow 'exit' command
sub_grid: Optional["SubGrid"] = None  # Interior grid for landmarks (overworld only)
```

Add forward reference import at top (TYPE_CHECKING already exists):
```python
if TYPE_CHECKING:
    from cli_rpg.world_grid import SubGrid
```

### Step 2: Update Location.to_dict()
**File**: `src/cli_rpg/models/location.py` (around line 311)

Add serialization for new fields after `hidden_secrets`:
```python
if self.is_exit_point:
    data["is_exit_point"] = self.is_exit_point
if self.sub_grid is not None:
    data["sub_grid"] = self.sub_grid.to_dict()
```

### Step 3: Update Location.from_dict()
**File**: `src/cli_rpg/models/location.py` (around line 354-374)

Add deserialization after `hidden_secrets`:
```python
is_exit_point = data.get("is_exit_point", False)
sub_grid = None
if "sub_grid" in data:
    from cli_rpg.world_grid import SubGrid
    sub_grid = SubGrid.from_dict(data["sub_grid"])
```

Add `is_exit_point` and `sub_grid` to constructor call.

### Step 4: Create tests for new Location fields
**File**: `tests/test_exit_points.py` (new file)

Tests to write:
1. `test_location_is_exit_point_default_false` - default value
2. `test_location_is_exit_point_can_be_true` - setting to True
3. `test_location_sub_grid_default_none` - default value
4. `test_location_sub_grid_can_be_set` - setting SubGrid instance
5. `test_location_to_dict_includes_is_exit_point` - serialization when True
6. `test_location_to_dict_excludes_is_exit_point_when_false` - not serialized when False
7. `test_location_to_dict_includes_sub_grid` - serialization with SubGrid
8. `test_location_from_dict_restores_is_exit_point` - deserialization
9. `test_location_from_dict_restores_sub_grid` - deserialization with SubGrid
10. `test_location_serialization_backward_compatible` - old saves without new fields still load

## Test Commands

```bash
# Run new tests
pytest tests/test_exit_points.py -v

# Run existing Location tests to verify no regressions
pytest tests/test_location.py -v

# Run SubGrid tests to ensure integration works
pytest tests/test_sub_grid.py -v

# Full test suite
pytest
```
