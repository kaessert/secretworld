# Fix: enter() incorrectly rejects locations with existing sub_grid/sub_locations

## Problem
Commit `b008bb2` broke SubGrid navigation by adding an overly strict check:
```python
can_enter = is_enterable_category(current.category)
if not can_enter:
    return (False, "There's nothing to enter here. This is open wilderness.")
```

This rejects entry even when:
1. Location already has a `sub_grid` set
2. Location has `sub_locations` in world dict (legacy)
3. Location lacks a `category` field but has enterable content

## Fix
In `src/cli_rpg/game_state.py` lines 1218-1220, change the logic to:
```python
# Determine if location has enterable content
from cli_rpg.world_tiles import is_enterable_category
can_generate_subgrid = is_enterable_category(current.category)
has_existing_content = current.sub_grid is not None or bool(current.sub_locations)

if not can_generate_subgrid and not has_existing_content:
    return (False, "There's nothing to enter here. This is open wilderness.")
```

The check should only block entry when there's NO existing content AND the category doesn't support generation.

## Test Verification
Run: `pytest tests/test_game_state.py tests/test_subgrid_navigation.py -v`
All 83 tests should pass.
