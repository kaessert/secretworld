# Implementation Summary: Remove Terrain Logic from AI Location Generation

## What Was Implemented

The implementation removed AI-suggested connections from location generation, making WFC (Wave Function Collapse) the single source of truth for terrain structure. However, upon investigation, **most of this work was already done** in the codebase. The implementation was already in the correct state:

### Already Correct (No Changes Needed)
1. **`ai_config.py`**: Both `DEFAULT_LOCATION_PROMPT` and `DEFAULT_LOCATION_PROMPT_MINIMAL` already had no references to `connections` in their expected JSON output
2. **`ai_service.py`**: `_parse_location_response()` already didn't require connections and returned only `{name, description, category, npcs}`
3. **`ai_world.py`**: Already used grid-based expansion with all cardinal directions queued from each location (lines 295-299)

### Changes Made
Updated 5 obsolete tests in `tests/test_ai_world_generation.py` that were still testing the OLD behavior where AI suggestions drove connections:

| Old Test | New Test | Purpose |
|----------|----------|---------|
| `test_expand_world_preserves_ai_suggested_dangling_connections` | `test_expand_world_adds_dangling_connections` | Tests that new locations get dangling exits for future expansion |
| `test_create_ai_world_queues_suggested_connections` | `test_create_ai_world_queues_cardinal_directions` | Tests that all cardinal directions are queued for expansion |
| `test_expand_world_adds_bidirectional_connection_to_existing_target` | `test_expand_world_adds_bidirectional_connection` | Tests bidirectional connection between source and new location |
| `test_expand_world_preserves_existing_reverse_connection` | `test_expand_world_preserves_source_existing_connections` | Tests that source's existing connections are preserved |
| `test_create_ai_world_skips_suggested_name_already_in_grid` | `test_create_ai_world_skips_occupied_positions` | Tests that occupied grid positions are skipped |

## Test Results

- **All 11 terrain content separation tests pass**: Verify AI prompts have no connection references, parsing ignores connections, and returned data has no connections key
- **All 54 AI world generation tests pass**: Including the 5 updated tests
- **Full test suite: 3573 tests pass**

## Technical Details

The key architectural insight is:
- **AI's role**: Generate content only (name, description, category, NPCs)
- **WFC's role**: Handle terrain structure (exits, connections, passability)
- **WorldGrid**: Manages coordinates and bidirectional connections

The `expand_world()` function now:
1. Gets AI-generated content (no connections)
2. Adds bidirectional connection between source and new location
3. Adds a random dangling connection for future expansion
4. Never uses AI suggestions for connections

## E2E Tests Should Validate

1. Moving between AI-generated locations works correctly
2. New locations have at least one exit for expansion
3. Bidirectional connections are properly established
4. Location content (names, descriptions) are coherent with terrain type
