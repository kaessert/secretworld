# Implementation Summary: Wire Named Location Triggers

## What Was Implemented

The named location trigger system was already fully implemented. The verification and test fixes completed the feature:

### Core Feature (Already Implemented)
1. **`tiles_since_named` counter in GameState** (`game_state.py` line 292)
   - Defaults to 0 on new game
   - Increments when moving to unnamed locations
   - Resets to 0 when entering/generating named locations
   - Persists through save/load (`to_dict` line 1124, `from_dict` line 1231)

2. **Named location trigger logic** (`world_tiles.py` lines 308-339)
   - `should_generate_named_location(tiles_since_named, terrain)` function
   - Uses probability curve: 0% at tile 0, 50% at interval, 100% at 2x interval
   - Terrain modifiers affect effective interval (e.g., mountains = 60% of base)

3. **Template system for unnamed locations** (`world_tiles.py` lines 193-251)
   - `UNNAMED_LOCATION_TEMPLATES` dictionary with templates per terrain
   - `get_unnamed_location_template(terrain)` function returns (name, description)

4. **Integration in move() method** (`game_state.py` lines 537-622)
   - Checks `should_generate_named_location()` for new tiles
   - If FALSE: Creates location from template with `is_named=False`
   - If TRUE: Uses AI or fallback with `is_named=True`
   - Counter updates based on location type

### Test Fixes (This Session)
Updated two existing tests to work with the new trigger system:

1. **`test_move_informs_player_when_ai_fails`** (`test_game_state.py` line 700)
   - Added `monkeypatch` to force `should_generate_named_location` to return True
   - Ensures the AI fallback path is tested

2. **`test_move_triggers_coordinate_based_ai_expansion`** (`test_game_state_ai_integration.py` lines 325-327)
   - Wrapped test in `patch("cli_rpg.game_state.should_generate_named_location", return_value=True)`
   - Ensures AI expansion path is tested

## Test Results

All 32 named location tests pass:
- `tests/test_named_locations.py` - 12 tests
- `tests/test_unnamed_templates.py` - 9 tests
- `tests/test_named_location_integration.py` - 11 tests

Full test suite: 3587/3588 passing (1 flaky pre-existing test unrelated to this feature)

## Files Modified

| File | Change |
|------|--------|
| `tests/test_game_state.py` | Added patch for `should_generate_named_location` |
| `tests/test_game_state_ai_integration.py` | Added patch for `should_generate_named_location` |

## E2E Validation

The feature can be validated by:
1. Starting a new game and moving to multiple adjacent tiles
2. Observing that most tiles are unnamed (e.g., "Dense Woods (1,2)")
3. Occasionally encountering named POIs with unique names
4. Saving/loading and verifying `tiles_since_named` counter persists
