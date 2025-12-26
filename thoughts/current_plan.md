# Implementation Plan: SubGrid Persistence Serialization

**Priority**: P0 BLOCKER - Phase 1 Step 7 of ISSUES.md
**Scope**: Update persistence for SubGrid serialization so games with sub-location grids can be saved/loaded

## Current State Analysis

**Already implemented**:
- `SubGrid.to_dict()` and `SubGrid.from_dict()` exist in `world_grid.py` (lines 136-174)
- `Location.to_dict()` serializes `sub_grid` when present (line 316-317)
- `Location.from_dict()` deserializes `sub_grid` when present (lines 364-368)
- `GameState.to_dict()` includes `in_sub_location` flag (line 992)
- `GameState.from_dict()` restores `in_sub_location` and `current_sub_grid` (lines 1020, 1026-1048)

**Gap identified**: The `current_sub_grid` state is restored by searching through world locations, but there's no test coverage for the complete save/load cycle with SubGrid, and we need to verify the current implementation is correct.

## Spec

When a game state is saved while player is inside a SubGrid:
1. `in_sub_location: true` is persisted
2. `current_location` contains the name of the location within the SubGrid
3. Parent location's `sub_grid` data is persisted with all interior locations
4. On load, `in_sub_location`, `current_sub_grid`, and `current_location` are fully restored
5. Player can continue navigating within the SubGrid after load

## Tests

### File: `tests/test_persistence_game_state.py` (extend existing)

Add new test class `TestSubGridPersistence`:

1. **`test_save_game_state_with_subgrid`**: Verify SubGrid data is included in save file
2. **`test_load_game_state_restores_subgrid`**: Verify SubGrid is restored with locations
3. **`test_save_load_while_inside_subgrid`**: Verify player position inside SubGrid persists
4. **`test_subgrid_roundtrip_preserves_connections`**: Verify bidirectional connections within SubGrid survive save/load
5. **`test_subgrid_roundtrip_preserves_exit_points`**: Verify `is_exit_point` markers survive
6. **`test_backward_compat_no_subgrid`**: Verify old saves without SubGrid still load

## Implementation Steps

1. **Add tests to `tests/test_persistence_game_state.py`**:
   - Import `SubGrid` from `world_grid`
   - Create test class `TestSubGridPersistence`
   - Add 6 test methods as specified above

2. **Verify current implementation** (or fix if tests fail):
   - `GameState.to_dict()` serializes world locations which include `sub_grid`
   - `GameState.from_dict()` restores world, finds parent SubGrid for current location

3. **Fix any gaps found by tests** in:
   - `src/cli_rpg/game_state.py` - `to_dict()` / `from_dict()`
   - No changes needed in `persistence.py` (it delegates to GameState)

## Files to Modify

| File | Action | Changes |
|------|--------|---------|
| `tests/test_persistence_game_state.py` | EXTEND | Add `TestSubGridPersistence` class with 6 tests |
| `src/cli_rpg/game_state.py` | VERIFY/FIX | Ensure `to_dict`/`from_dict` handle SubGrid correctly |

## Verification

```bash
pytest tests/test_persistence_game_state.py::TestSubGridPersistence -v
pytest tests/test_sub_grid.py -v
pytest -x  # Full test suite still passes
```
