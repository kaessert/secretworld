# Implementation Summary: Add `is_exit_point` and `sub_grid` to Location Model

## What Was Implemented

Added two new fields to the `Location` model to support the SubGrid-based sub-location system:

### New Fields (in `src/cli_rpg/models/location.py`)

1. **`is_exit_point: bool = False`**
   - Marks locations where the `exit` command is allowed
   - Defaults to `False` (interior rooms that don't allow exit)
   - Only serialized when `True` for minimal save file size

2. **`sub_grid: Optional["SubGrid"] = None`**
   - Contains the bounded interior grid for overworld landmarks
   - Uses forward reference with `TYPE_CHECKING` to avoid circular imports
   - Only serialized when not `None` for backward compatibility

### Changes Made

1. **Forward Reference Import** (line 11)
   - Added `from cli_rpg.world_grid import SubGrid` under `TYPE_CHECKING`

2. **Field Definitions** (lines 53-54, after `hidden_secrets`)
   - Added `is_exit_point: bool = False`
   - Added `sub_grid: Optional["SubGrid"] = None`

3. **Serialization in `to_dict()`** (lines 314-317)
   - Conditionally includes `is_exit_point` only when `True`
   - Conditionally includes `sub_grid` only when not `None`

4. **Deserialization in `from_dict()`** (lines 362-368, 388-389)
   - Parses `is_exit_point` with default `False`
   - Parses `sub_grid` using `SubGrid.from_dict()` when present
   - Added both fields to constructor call

### Tests Created

New test file: `tests/test_exit_points.py` with 16 tests covering:

- `TestIsExitPointField` (6 tests): Default value, setting value, serialization/deserialization
- `TestSubGridField` (5 tests): Default value, setting SubGrid, serialization/deserialization
- `TestBackwardCompatibility` (2 tests): Old saves without new fields still load correctly
- `TestRoundTrip` (3 tests): Full serialization cycle preserves all data

## Test Results

- **New tests**: 16 passed
- **Existing Location tests**: 58 passed (no regressions)
- **SubGrid tests**: 23 passed (no regressions)
- **Full test suite**: 3209 passed

## E2E Tests Should Validate

1. Creating a location with `is_exit_point=True` and saving/loading the game
2. Creating an overworld location with a `sub_grid` containing interior rooms
3. Loading old saves without the new fields (backward compatibility)
4. Entering a landmark and having the sub_grid available for navigation
