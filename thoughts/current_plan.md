# Implementation Plan: Vertical Z-Level Navigation Scenario

**Task**: Add a YAML scenario to test vertical z-level movement inside SubGrids (dungeons going down, towers going up).

## Spec

This scenario validates that:
1. Player cannot use `go up`/`go down` on the overworld (returns appropriate error)
2. Player can enter a multi-level SubGrid location (dungeon/cave/tower)
3. The `go down` and `go up` commands work for vertical navigation inside SubGrids
4. Z-level changes are reflected in game state coordinates

## Test File

**File**: `scripts/scenarios/movement/vertical_navigation.yaml`
**Seed**: 42011 (next unique seed after 42001-42010)

## Implementation Steps

### 1. Create the scenario file
**File**: `scripts/scenarios/movement/vertical_navigation.yaml`

Scenario structure:
- Setup: `dump_state` to get initial state
- Step 1: Try `go down` on overworld - assert NARRATIVE_MATCH for "can only go up or down inside buildings and dungeons"
- Step 2: Try `go up` on overworld - assert same error
- Step 3-7: Navigate to find an enterable location
- Step 8: `look` to confirm location
- Step 9: Check if location is enterable
- Step 10: Enter the location (creates SubGrid)
- Step 11: `look` inside SubGrid
- Step 12: `dump_state` to verify SubGrid entry

### 2. Update test file
**File**: `tests/test_scenario_files.py`

In `test_movement_scenarios_exist()` (~line 213), add assertion for `vertical_navigation.yaml`.

### 3. Run tests
```bash
pytest tests/test_scenario_files.py -v
```

## Files Changed
- `scripts/scenarios/movement/vertical_navigation.yaml` (new)
- `tests/test_scenario_files.py` (update assertion count)

## Acceptance Criteria
- Scenario file parses without errors
- Seed 42011 is unique
- Scenario validates overworld blocks vertical movement
- Scenario enters a SubGrid location successfully
