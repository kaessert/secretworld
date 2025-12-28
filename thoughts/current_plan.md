# Implementation Plan: Complete Movement/Navigation Scenario Validation

## Summary
Complete the movement/navigation scenarios so the checkbox in ISSUES.md can be marked done. The existing scenarios are incomplete - they don't actually test SubGrid entry/exit or vertical navigation inside dungeons.

## Current State
- 3 movement scenarios exist: `basic_navigation.yaml`, `subgrid_entry_exit.yaml`, `vertical_navigation.yaml`
- Static validation tests pass (scenario file parsing)
- **Gap 1**: `subgrid_entry_exit.yaml` never uses `enter` or `exit` commands
- **Gap 2**: `vertical_navigation.yaml` only tests failure on overworld, never success inside SubGrid
- **Gap 3**: Test world fixture (`tests/fixtures/test_world.json`) has SubGrid with only z=0 level (no multi-level for vertical testing)

## Implementation Steps

### 1. Update test world fixture to support vertical navigation
**File**: `tests/fixtures/test_world.json`
- Add z=-1 level locations to the Dark Cave SubGrid
- Add `allowed_exits` connections between rooms (including "down" and "up")
- Ensure Cave Entrance connects to a lower level room

### 2. Enhance `subgrid_entry_exit.yaml` scenario
**File**: `scripts/scenarios/movement/subgrid_entry_exit.yaml`
- Use `demo_mode: true` config to load test world with known enterable location
- Add step to move to Dark Cave location (go east from Peaceful Village at [0,0] to [1,0])
- Add step: `enter` command to enter the cave
- Add assertion: verify we're inside via narrative containing "Cave"
- Add step: `exit` command to return to overworld
- Add assertion: verify we're back on overworld

### 3. Enhance `vertical_navigation.yaml` scenario
**File**: `scripts/scenarios/movement/vertical_navigation.yaml`
- Use `demo_mode: true` config to load updated test world
- Keep existing steps that test overworld failure
- Add steps to navigate to Dark Cave and enter
- Add step: `go down` inside the cave
- Add assertion: verify successful movement via narrative
- Add step: `go up` to return
- Add assertion: verify successful movement via narrative

### 4. Add demo mode support to ScenarioRunner
**File**: `scripts/validation/scenarios.py`
- Check for `demo_mode: true` in scenario config
- When `demo_mode: true`, add `--demo` flag to GameSession command
- This ensures test world is loaded instead of random generation

### 5. Update GameSession to support demo mode flag
**File**: `scripts/ai_agent.py`
- Add `demo_mode: bool = False` parameter to `GameSession.__init__`
- When `demo_mode=True`, add `--demo` to command line args in `start()`

### 6. Update ISSUES.md to mark movement checkbox complete
**File**: `ISSUES.md`
- Change `[ ] Movement and navigation` to `[x] Movement and navigation`

## Test Verification
```bash
# Run scenario file tests
pytest tests/test_scenario_files.py -v

# Run scenario runner tests
pytest tests/test_scenario_runner.py -v

# Verify test world loads correctly
python -c "from cli_rpg.test_world import create_demo_game_state; gs = create_demo_game_state(); print('OK')"
```
