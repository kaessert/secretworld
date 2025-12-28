# Terrain Immutability Implementation Summary

## What Was Implemented

### 1. Added `_synced` Flag to ChunkManager
**File:** `src/cli_rpg/wfc_chunks.py`

- Added `_synced: bool = False` attribute to the ChunkManager dataclass
- Flag is set to `True` at the end of `sync_with_locations()`
- This tracks whether initial world setup is complete

### 2. Added Defensive Warning in `set_tile_at()`
**File:** `src/cli_rpg/wfc_chunks.py`

- Modified `set_tile_at()` to log a warning if called after `_synced` is True
- Uses `logging.getLogger(__name__)` for proper logging integration
- Warning message: "Terrain modification at (x, y) after sync - this may violate terrain immutability contract"

### 3. Added `assert_terrain_unchanged()` Helper Method
**File:** `src/cli_rpg/wfc_chunks.py`

- New method to validate terrain at a coordinate matches expected value
- Raises `AssertionError` with detailed message if terrain doesn't match
- Can be used in tests and optionally at runtime with `__debug__`

### 4. Updated Serialization for `_synced` Flag
**File:** `src/cli_rpg/wfc_chunks.py`

- `to_dict()` now includes `"synced": self._synced`
- `from_dict()` now restores `_synced` with `data.get("synced", False)`
- Ensures immutability state persists across save/load

## Files Modified
- `src/cli_rpg/wfc_chunks.py` - Added `_synced` flag, warning, helper method, serialization

## Files Created
- `tests/test_terrain_immutability.py` - 14 new tests for terrain immutability

## Test Results

### New Tests (14 tests)
All pass in 0.25s:
- `test_synced_flag_initially_false` - Verifies `_synced` starts False
- `test_synced_flag_true_after_sync` - Verifies `_synced` becomes True after sync
- `test_set_tile_at_before_sync_no_warning` - No warning before sync
- `test_set_tile_at_after_sync_logs_warning` - Warning logged after sync
- `test_terrain_matches_chunk_on_location_sync` - Location terrain syncs correctly
- `test_location_terrain_matches_chunk_terrain` - Consistency verification
- `test_terrain_unchanged_after_repeated_access` - Access doesn't modify terrain
- `test_cached_chunk_terrain_immutable` - Cached chunks stay unchanged
- `test_terrain_unchanged_after_movement_simulation` - Player movement safe
- `test_synced_flag_serialized` - `_synced` included in `to_dict()`
- `test_synced_flag_deserialized` - `_synced` restored from `from_dict()`
- `test_unsynced_flag_deserialized` - Unsynced state preserved
- `test_assert_terrain_unchanged_passes_when_matching` - Helper passes
- `test_assert_terrain_unchanged_raises_when_different` - Helper raises

### Existing Tests
- All 5612 tests pass
- No regressions

## Design Decisions

1. **Warning instead of Error**: The `set_tile_at()` method logs a warning rather than raising an exception to avoid breaking existing code that might legitimately need to modify terrain (e.g., future features). The warning provides visibility into potential issues.

2. **`_synced` Flag Serialization**: The flag is persisted to ensure that loaded save games maintain the immutability contract from the point where they were saved.

3. **Default `_synced=False` on Deserialization**: Older save files without the `synced` key will default to `False`, which is safe - they just won't have the defensive warning enabled.

## E2E Validation

The following scenarios should validate terrain immutability in E2E tests:
1. Generate a world and move around - terrain at visited coordinates should remain consistent
2. Save and load a game - terrain should be identical after reload
3. If any code path logs a "terrain modification after sync" warning during gameplay, that indicates a potential bug to investigate
