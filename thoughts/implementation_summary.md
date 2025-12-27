# Environmental Storytelling - Implementation Summary

## Status: COMPLETE

All 11 tests pass in `tests/test_environmental_storytelling.py`.

## What Was Implemented

Added environmental storytelling elements (corpses, bloodstains, journals) to SubGrid location descriptions for dungeon/cave/ruins/temple categories.

### New File: `src/cli_rpg/environmental_storytelling.py`

Created module with:

- **STORYTELLING_CATEGORIES**: frozenset of categories that receive details (`dungeon`, `cave`, `ruins`, `temple`)
- **BASE_STORYTELLING_CHANCE**: 40% base chance for details to appear
- **ENVIRONMENTAL_DETAILS**: Category-specific detail pools with 3 types:
  - **Corpses**: Previous adventurer remains (skeletons, mauled hunters, preserved bodies)
  - **Bloodstains**: Combat evidence (dried blood, splatter patterns, trails)
  - **Journals**: Lore hints and warnings (scratched messages, torn pages, stone tablets)

- **`get_environmental_details(category, distance, z_level)`**: Main function that:
  - Returns empty list for non-storytelling categories
  - Calculates scaled chance: `base + (distance * 5%) + (depth * 8%)`
  - Returns 0-2 randomly selected thematic details

### Modified: `src/cli_rpg/models/location.py`

- Added field: `environmental_details: List[str] = field(default_factory=list)`
- Updated `to_dict()`: Only includes field when non-empty (backward compat)
- Updated `from_dict()`: Parses field with empty list fallback
- Updated `get_layered_description()`: Displays details after main description, before NPCs

### Modified: `src/cli_rpg/ai_world.py`

Integrated environmental storytelling into SubGrid generation:

- **`generate_subgrid_for_location()`**: Adds environmental details to non-entry rooms (line 1098-1101)
- **`expand_area()`**: Adds environmental details to non-entry SubGrid rooms (line 1794-1797)

Both functions call `get_environmental_details()` with distance and z_level for scaling.

## Test Results

```
tests/test_environmental_storytelling.py - 11 passed
tests/test_location.py - 73 passed
tests/test_world_grid.py - 20 passed
tests/test_persistence.py - 37 passed
```

All related tests pass, confirming no regressions.

## Design Decisions

1. **Always visible**: Environmental details appear immediately (not gated by look_count like `details` and `secrets` layers)
2. **Distance + Depth scaling**: Chance increases with distance (5% per unit) and depth (8% per unit of |z|), capped at 95%
3. **Category-specific pools**: Each dungeon type has thematic detail pools
4. **Compact display**: Details appear as single lines after the main description

## E2E Test Validation

To manually verify:
1. Run `cli-rpg --demo`
2. Enter a dungeon or cave location with `enter <name>`
3. Navigate to non-entry rooms (away from the entrance)
4. Run `look` command
5. Environmental details (corpses, bloodstains, journals) should appear after the main description
