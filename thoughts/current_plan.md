# Fix 66 Failing Tests - Implementation Plan

## Root Cause Analysis

**Primary Issue (64 tests):** `AttributeError: 'ChunkManager' object has no attribute 'seed'`

The `ChunkManager` dataclass in `wfc_chunks.py` uses `world_seed` as its attribute name (line 35), but `game_state.py` accesses it as `.seed` in two locations:
- Line 323: `world_seed = chunk_manager.seed if chunk_manager else random.randint(0, 2**31)`
- Line 2152: `world_seed=game_state.chunk_manager.seed`

**Secondary Issues (2 tests):**
1. `test_weather_affects_dread_rain` - Expects dread=7, got dread=10 (likely unrelated calculation issue)
2. `test_maze_layout_has_dead_ends` - Non-deterministic layout generation (0 dead ends found)

## Implementation Steps

### Step 1: Fix ChunkManager attribute access (Primary Fix)

**File:** `src/cli_rpg/game_state.py`

**Change 1 - Line 323:**
```python
# FROM:
world_seed = chunk_manager.seed if chunk_manager else random.randint(0, 2**31)
# TO:
world_seed = chunk_manager.world_seed if chunk_manager else random.randint(0, 2**31)
```

**Change 2 - Line 2152:**
```python
# FROM:
world_seed=game_state.chunk_manager.seed
# TO:
world_seed=game_state.chunk_manager.world_seed
```

### Step 2: Run tests to verify fix

```bash
pytest tests/test_wfc_integration.py tests/test_non_interactive.py tests/test_json_output.py -v
```

### Step 3: Investigate remaining failures (if any)

After the primary fix, re-run full test suite to identify any remaining failures that may need separate fixes.

## Expected Outcome

The attribute name fix should resolve ~64 of the 66 failing tests. The remaining 2 tests (weather dread calculation and maze dead-end detection) appear to be unrelated issues that may require separate investigation.
