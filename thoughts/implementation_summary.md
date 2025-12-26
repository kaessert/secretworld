# Implementation Summary: Make WFC Default

## What Was Implemented

Replaced `--wfc` flag with `--no-wfc` flag so WFC (Wave Function Collapse) terrain generation is enabled by default. WFC is now wired to all game modes.

### Files Modified

1. **`src/cli_rpg/main.py`**
   - Changed `start_game()` default parameter: `use_wfc: bool = True` (was `False`)
   - Changed argument flag from `--wfc` to `--no-wfc`
   - Updated interactive mode: `use_wfc = not parsed_args.no_wfc` (was `parsed_args.wfc`)
   - Wired WFC ChunkManager to `run_json_mode()` - now creates ChunkManager and passes to GameState
   - Wired WFC ChunkManager to `run_non_interactive()` - same pattern as json mode
   - Extracted `parse_args()` function to make argument parsing testable

2. **`tests/test_wfc_integration.py`**
   - Added `TestWFCDefaultBehavior` test class with 3 tests:
     - `test_wfc_enabled_by_default_in_start_game` - verifies `start_game` defaults `use_wfc=True`
     - `test_no_wfc_flag_disables_wfc` - verifies `--no-wfc` sets `no_wfc=True`
     - `test_no_wfc_flag_not_set_by_default` - verifies `no_wfc=False` by default

## Test Results

All 47 WFC-related tests pass:
- `tests/test_wfc_integration.py`: 13 tests passed
- `tests/test_wfc.py`: 17 tests passed
- `tests/test_wfc_chunks.py`: 17 tests passed

Main module tests also pass (5/5).

## Technical Details

### WFC Initialization Pattern (used in json/non-interactive modes)
```python
import random as rnd
from cli_rpg.wfc_chunks import ChunkManager
from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY
chunk_manager = ChunkManager(
    tile_registry=DEFAULT_TILE_REGISTRY,
    world_seed=rnd.randint(0, 2**32 - 1),
)
```

### Usage Change
- **Before**: `cli-rpg --wfc` to enable WFC
- **After**: `cli-rpg --no-wfc` to disable WFC (WFC is on by default)

## E2E Testing

The following should be validated:
1. Running `cli-rpg` without flags should start with WFC enabled (terrain generation works)
2. Running `cli-rpg --no-wfc` should start with fixed world (no terrain generation)
3. Running `cli-rpg --json` should work with WFC terrain
4. Running `cli-rpg --non-interactive` should work with WFC terrain
