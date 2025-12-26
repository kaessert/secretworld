# Implementation Plan: Remove Terrain Logic from AI Location Generation

## Summary
Remove connections/exits generation from AI prompts and parsing. AI should only generate content (name, description, NPCs, category), while WFC is the single source of truth for terrain structure (exits/connections).

## Spec

**Current State (Incorrect):**
- AI prompts ask for `connections: {direction: location_name}`
- AI decides which exits exist
- `_parse_location_response()` validates and filters connections
- `expand_world()` uses AI-generated connections to determine navigation

**Target State (Correct):**
- AI prompts have NO reference to exits, directions, or connections
- AI receives terrain type as INPUT (from WFC)
- AI returns ONLY: `{name, description, category, npcs}`
- All exits determined by WFC terrain adjacency in ChunkManager

## Test Plan (TDD)

**File: `tests/test_terrain_content_separation.py`**

| Test | Description |
|------|-------------|
| `test_minimal_location_prompt_no_connections` | Minimal prompt has no `connections` field in example JSON |
| `test_minimal_location_prompt_no_exits` | Minimal prompt contains no word "exit" or "direction" |
| `test_parse_location_response_no_connections_required` | Parsing succeeds without `connections` in response |
| `test_parse_location_response_ignores_connections` | If AI includes connections, they are ignored |
| `test_location_data_has_no_connections_key` | Returned dict has no `connections` key |
| `test_generate_location_with_context_no_connections` | Full generation returns no connections |

## Implementation Steps

### Step 1: Update AI Prompts (ai_config.py)

**Modify `DEFAULT_LOCATION_PROMPT` (line 14-49):**
Remove requirements #3, #4 about connections. Remove `connections` from JSON example.

```python
DEFAULT_LOCATION_PROMPT = """You are a creative game world designer. Generate a new location for a {theme} RPG game.

Context:
- World Theme: {theme}
- Existing Locations: {context_locations}
- Terrain Type: {terrain_type}

Requirements:
1. Create a unique location name (2-50 characters) appropriate for {terrain_type} terrain
2. Write a vivid description (1-500 characters) that reflects the terrain and theme
3. Include a category for the location type (one of: town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
4. Generate 0-2 NPCs appropriate for this location (optional)
   - Each NPC needs: name (2-30 chars), description (1-200 chars), dialogue (a greeting), role (villager, merchant, or quest_giver)

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Location Name",
  "description": "A detailed description of the location.",
  "category": "wilderness",
  "npcs": [
    {{
      "name": "NPC Name",
      "description": "Brief description of the NPC.",
      "dialogue": "What the NPC says when greeted.",
      "role": "villager"
    }}
  ]
}}"""
```

**Modify `DEFAULT_LOCATION_PROMPT_MINIMAL` (line 306-335):**
Remove requirements about connections and back-connection to source.

```python
DEFAULT_LOCATION_PROMPT_MINIMAL = """Generate a location for a {theme} RPG.

World Context:
- Theme Essence: {theme_essence}

Region Context:
- Region Name: {region_name}
- Region Theme: {region_theme}
- Terrain: {terrain_type}

Requirements:
1. Create a unique location name (2-50 characters) that fits the region theme and terrain
2. Write a vivid description (1-500 characters) that reflects the {terrain_type} terrain
3. Assign a category (town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
4. Ensure the location makes sense for {terrain_type} terrain (e.g., oasis for desert, clearing for forest)

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Location Name",
  "description": "A detailed description of the location.",
  "category": "wilderness"
}}"""
```

### Step 2: Update Parsing (ai_service.py)

**Modify `_parse_location_response()` (around line 586-650):**
- Remove `connections` from required_fields
- Remove connection validation/filtering logic
- Return dict without `connections` key

```python
def _parse_location_response(self, response_text: str) -> dict:
    # ... JSON parsing logic unchanged ...

    # Validate required fields (NO connections)
    required_fields = ["name", "description"]
    for field in required_fields:
        if field not in data:
            raise AIGenerationError(f"Response missing required field: {field}")

    # ... name/description validation unchanged ...

    # Extract and validate category (optional field)
    category = data.get("category")
    # ... category validation unchanged ...

    # Parse NPCs (optional field)
    npcs = self._parse_npcs(data.get("npcs", []), name)

    # Return validated data WITHOUT connections
    return {
        "name": name,
        "description": description,
        "category": category,
        "npcs": npcs
    }
```

**Modify `generate_location()` return type docstring (line 168-169):**
Update to reflect no connections.

```python
Returns:
    Dictionary with keys: name, description, category, npcs
```

### Step 3: Update ai_world.py to Not Use AI Connections

**Modify `create_ai_world()` (line 184-399):**
- Remove code that queues AI-generated connections (lines 295-299)
- Remove code that uses `location_data["connections"]` (line 369)
- All expansion now driven by WFC terrain, not AI suggestions

Key change at line 296:
```python
# OLD: for direction, target_name in starting_data["connections"].items():
# NEW: Queue ALL cardinal directions for exploration (WFC will filter passability)
for direction in DIRECTION_OFFSETS:
    dx, dy = DIRECTION_OFFSETS[direction]
    coord_queue.append((starting_location.name, 0 + dx, 0 + dy, direction, None))
```

**Modify `expand_world()` (around line 520-545):**
- Remove code at lines 525-533 that adds AI-suggested connections
- Bidirectional connection at lines 520-523 stays (this is terrain-based, not AI)

Remove this block:
```python
# OLD: Add suggested dangling connections (keep them even if targets don't exist)
# for new_dir, target_name in location_data["connections"].items():
#     ...
```

### Step 4: Update Area Generation Prompts (ai_service.py)

**Modify `_build_area_prompt()` (around line 913-963):**
- Remove requirement #9 about valid directions
- Remove requirement #10 about internal consistency of connections
- Remove `connections` from JSON example
- Change focus to generating themed locations with relative positions

This is more complex since areas have internal connectivity. However, for areas:
- Use `relative_coords` to establish spatial layout
- Derive connections FROM coordinates, not AI

**Modify `_parse_area_response()` and `_validate_area_location()` (lines 1028-1099):**
- Remove `connections` from required_fields
- Remove connection filtering logic
- Derive connections from relative_coords in caller (ai_world.py)

## Files to Modify

| File | Changes |
|------|---------|
| `tests/test_terrain_content_separation.py` | NEW - Tests for content-only AI generation |
| `src/cli_rpg/ai_config.py` | Remove connections from prompts (lines 14-49, 306-335) |
| `src/cli_rpg/ai_service.py` | Remove connections from parsing (lines 586-650, 1028-1099) |
| `src/cli_rpg/ai_world.py` | Stop using AI connections (lines 295-299, 369, 525-533) |

## Success Criteria

- [ ] AI prompts contain zero references to exits, directions, or connections
- [ ] `_parse_location_response()` does not require or return `connections`
- [ ] `create_ai_world()` expands based on grid positions, not AI suggestions
- [ ] `expand_world()` adds only bidirectional terrain connections
- [ ] All existing tests pass
- [ ] New tests verify content-only generation
