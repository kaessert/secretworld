# Implementation Plan: Add Basic Crafting Scenario

## Task
Add a crafting validation scenario (`scripts/scenarios/crafting/basic_crafting.yaml`) that tests the `gather`, `craft`, and `recipes` commands.

## Spec
Test the crafting system by:
1. View available recipes with `recipes` command
2. Attempt to gather resources in a valid location (forest/wilderness/cave)
3. Check inventory for gathered resources
4. Attempt to craft an item using resources
5. Verify crafted item appears in inventory

## Files to Create

### 1. `scripts/scenarios/crafting/__init__.py`
Empty package init file.

### 2. `scripts/scenarios/crafting/basic_crafting.yaml`
Scenario with seed: 42012, covering:
- `recipes` command validation (COMMAND_VALID)
- `gather` command (may need wilderness/forest location)
- `inventory` to verify resources
- `craft` command attempt
- State assertions for health range, location presence

## Test Updates

### 3. `tests/test_scenario_files.py`
Add "crafting" to `expected_dirs` in `test_all_subdirectories_have_scenarios()` and add `test_crafting_scenarios_exist()` method.

## Implementation Steps

1. Create `scripts/scenarios/crafting/__init__.py` (empty)
2. Create `scripts/scenarios/crafting/basic_crafting.yaml` with:
   - seed: 42012
   - config: max_commands: 25, timeout: 90
   - Steps: recipes, gather (may fail if wrong location), inventory, craft attempt
3. Update `tests/test_scenario_files.py`:
   - Add "crafting" to expected_dirs set
   - Add `test_crafting_scenarios_exist()` test method
4. Run tests: `pytest tests/test_scenario_files.py -v`
