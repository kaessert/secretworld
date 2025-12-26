# Implementation Summary: Split Generation Prompts (Step 5 of Layered Query Architecture)

## What Was Implemented

Added 4 new prompt templates to `ai_config.py` to support the layered query architecture for more reliable AI content generation with smaller, focused prompts.

### New Prompt Templates Added

1. **DEFAULT_WORLD_CONTEXT_PROMPT** (Layer 1)
   - Purpose: Generates world-level thematic context once per world
   - Input: `{theme}`
   - Output JSON: `{ "theme_essence", "naming_style", "tone" }`
   - Location: Lines 262-275

2. **DEFAULT_REGION_CONTEXT_PROMPT** (Layer 2)
   - Purpose: Generates region-level context per region
   - Inputs: `{theme}`, `{theme_essence}`, `{naming_style}`, `{tone}`, `{coordinates}`, `{terrain_hint}`
   - Output JSON: `{ "name", "theme", "danger_level", "landmarks" }`
   - Location: Lines 278-302

3. **DEFAULT_LOCATION_PROMPT_MINIMAL** (Layer 3)
   - Purpose: Generates location without NPCs
   - Inputs: `{theme}`, `{theme_essence}`, `{region_name}`, `{region_theme}`, `{direction}`, `{source_location}`
   - Output JSON: `{ "name", "description", "connections", "category" }`
   - Location: Lines 305-333

4. **DEFAULT_NPC_PROMPT_MINIMAL** (Layer 4)
   - Purpose: Generates NPCs separately from location
   - Inputs: `{theme}`, `{theme_essence}`, `{naming_style}`, `{location_name}`, `{location_description}`, `{location_category}`
   - Output JSON: `{ "npcs": [...] }`
   - Location: Lines 336-364

### AIConfig Dataclass Updates

- Added 4 new fields with defaults:
  - `world_context_prompt: str = field(default=DEFAULT_WORLD_CONTEXT_PROMPT)`
  - `region_context_prompt: str = field(default=DEFAULT_REGION_CONTEXT_PROMPT)`
  - `location_prompt_minimal: str = field(default=DEFAULT_LOCATION_PROMPT_MINIMAL)`
  - `npc_prompt_minimal: str = field(default=DEFAULT_NPC_PROMPT_MINIMAL)`

### Serialization Updates

- **to_dict()**: Added 4 new keys for the new prompts
- **from_dict()**: Added 4 new `.get()` calls with defaults

## Files Modified

- `src/cli_rpg/ai_config.py` - Added prompts, dataclass fields, and serialization support
- `tests/test_ai_config.py` - Added 5 new tests

## Test Results

All 25 tests pass (20 existing + 5 new):
- `test_ai_config_world_context_prompt_exists` - Verifies prompt exists with `{theme}`
- `test_ai_config_region_context_prompt_exists` - Verifies prompt exists with `{theme_essence}`
- `test_ai_config_location_prompt_minimal_exists` - Verifies prompt exists with `{region_theme}`
- `test_ai_config_npc_prompt_minimal_exists` - Verifies prompt exists with `{location_name}`
- `test_ai_config_serialization_includes_new_prompts` - Verifies round-trip serialization

## E2E Validation Points

When E2E testing, verify:
1. AIConfig can be instantiated with custom values for all 4 new prompts
2. Saving and loading game state preserves custom prompt values
3. AI service can format prompts using the new templates with appropriate context
