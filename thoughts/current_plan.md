# Implementation Plan: NPCs in AI-Generated Locations

## Problem
Currently, NPCs only exist in the starting location. When AI generates new locations via `generate_location()`, `expand_world()`, or `expand_area()`, the locations are created without any NPCs, making exploration feel empty.

## Solution Overview
1. Extend AI prompts to request NPC generation alongside location generation
2. Parse NPC data from AI responses and create NPC objects
3. Attach NPCs to newly generated locations

## Implementation Steps

### Step 1: Add NPC Generation Prompt to Location Prompts

**File: `src/cli_rpg/ai_config.py`**

Update `DEFAULT_LOCATION_PROMPT` to include NPC generation:
- Add requirement for 0-2 NPCs appropriate to the location
- Specify NPC fields: name, description, dialogue, role (villager/merchant/quest_giver)
- Add "npcs" key to the expected JSON response format

### Step 2: Update AI Service to Parse NPCs

**File: `src/cli_rpg/ai_service.py`**

Update `_parse_location_response()`:
- Add parsing for optional "npcs" field in response
- Validate NPC data (name 2-30 chars, description 1-200 chars)
- Handle missing or empty npcs field gracefully (default to empty list)
- Return npcs list in the location data dict

Update `_validate_area_location()`:
- Same NPC parsing logic for area generation responses

### Step 3: Update AI World Module to Create NPC Objects

**File: `src/cli_rpg/ai_world.py`**

Update `create_ai_world()`:
- After creating Location from AI data, create NPC objects from npcs list
- Add NPCs to the location's npcs attribute
- Keep existing merchant/quest_giver in starting location (they're special)

Update `expand_world()`:
- Same NPC creation logic for expanded locations

Update `expand_area()`:
- Same NPC creation logic for area locations

### Step 4: Add Tests

**File: `tests/test_ai_service.py`**

Add tests:
- `test_generate_location_parses_npcs`: Verify NPC data is parsed from response
- `test_generate_location_handles_empty_npcs`: Verify empty/missing npcs field returns empty list
- `test_generate_location_validates_npc_name_length`: Invalid NPC data is handled
- `test_generate_area_parses_npcs`: Same for area generation

**File: `tests/test_ai_world_generation.py`**

Add tests:
- `test_expand_world_creates_npcs`: Verify NPCs are attached to expanded locations
- `test_expand_area_creates_npcs`: Verify NPCs are attached to area locations
- `test_ai_generated_locations_have_npcs`: Integration test

## Key Design Decisions

1. **NPCs are optional** - If AI doesn't return NPCs, location is still valid (empty list)
2. **Validation is lenient** - Invalid NPC data is logged and skipped, not fatal
3. **Role mapping** - Map "villager" to default NPC, "merchant" gets is_merchant=True, "quest_giver" gets is_quest_giver=True
4. **No shops/quests for AI NPCs** - Only flags are set; shops/quests can be added separately later

## Files to Modify

1. `src/cli_rpg/ai_config.py` - Update prompts
2. `src/cli_rpg/ai_service.py` - Parse NPC data
3. `src/cli_rpg/ai_world.py` - Create NPC objects
4. `tests/test_ai_service.py` - New tests
5. `tests/test_ai_world_generation.py` - New tests
