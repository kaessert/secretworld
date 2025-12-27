# Implementation Summary: Remove NPCs from Unnamed Overworld Locations

## What Was Implemented

Unnamed locations (`is_named=False`) now skip NPC generation. NPCs belong only in named sub-locations (villages, dungeons) - "you don't find shopkeepers standing in random forests."

### Files Modified

1. **`src/cli_rpg/ai_world.py`**
   - **`expand_world()` (lines 459-471)**: Added conditional check for `is_named` field before generating NPCs. If `is_named=False`, sets `location_data["npcs"] = []` and skips the `generate_npcs_for_location()` call.
   - **`expand_area()` (lines 686-691)**: Added conditional check for `is_named` field before populating NPCs from `loc_data`. Unnamed locations in areas now have empty NPC lists.

2. **`tests/test_unnamed_no_npcs.py`** (NEW)
   - 7 tests covering the spec:
     - `test_unnamed_location_from_template_has_no_npcs`: Verifies Location model creates unnamed locations with empty NPCs
     - `test_named_location_can_have_npcs`: Verifies named locations can still have NPCs
     - `test_expand_world_unnamed_skips_npcs`: Verifies `expand_world` skips NPC generation for unnamed locations
     - `test_expand_world_named_generates_npcs`: Verifies `expand_world` generates NPCs for named locations
     - `test_expand_world_defaults_to_named_when_not_specified`: Verifies backward compatibility (default `is_named=True`)
     - `test_expand_area_unnamed_skips_npcs`: Verifies `expand_area` skips NPC population for unnamed sub-locations
     - `test_expand_area_defaults_named_for_npcs`: Verifies backward compatibility for areas

### Design Decisions

1. **Backward Compatibility**: Both functions default `is_named` to `True` when the field is missing (`location_data.get("is_named", True)`). This ensures existing AI responses without the field continue to generate NPCs.

2. **SubGrid Architecture**: The `expand_area` tests correctly handle the fact that sub-locations are stored in the entry location's SubGrid, not directly in the world dict.

## Test Results

```
tests/test_unnamed_no_npcs.py: 7 passed
Full test suite: 3687 passed in 103.02s
```

## E2E Validation

To validate in gameplay:
1. Navigate to an unnamed location (e.g., "Dense Forest (0,1)")
2. Use `look` command - should show no NPCs
3. Navigate to a named location (e.g., a village)
4. Use `look` command - should show NPCs normally
