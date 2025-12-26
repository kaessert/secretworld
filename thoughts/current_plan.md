# Implementation Plan: Split Generation Prompts (Step 5 of Layered Query Architecture)

## Objective
Add four new prompt templates to `ai_config.py` that use the existing `WorldContext` and `RegionContext` models, enabling smaller, focused AI prompts that reduce JSON parsing failures.

## Spec

### New Prompts to Add

1. **WORLD_CONTEXT_PROMPT** - Generates Layer 1 context (once per world)
   - Input: `{theme}`
   - Output JSON: `{ "theme_essence": str, "naming_style": str, "tone": str }`
   - Small, focused output (~100 tokens)

2. **REGION_CONTEXT_PROMPT** - Generates Layer 2 context (per region)
   - Input: `{theme}`, `{theme_essence}`, `{naming_style}`, `{tone}`, `{coordinates}`, `{terrain_hint}`
   - Output JSON: `{ "name": str, "theme": str, "danger_level": str, "landmarks": list[str] }`
   - Small, focused output (~150 tokens)

3. **LOCATION_PROMPT_MINIMAL** - Generates Layer 3 location (per location, no NPCs)
   - Input: `{theme}`, `{theme_essence}`, `{region_name}`, `{region_theme}`, `{direction}`, `{source_location}`
   - Output JSON: `{ "name": str, "description": str, "category": str, "connections": dict }`
   - Smaller than current `DEFAULT_LOCATION_PROMPT` by removing NPC generation

4. **NPC_PROMPT_MINIMAL** - Generates Layer 4 NPCs (optional, per location)
   - Input: `{theme}`, `{theme_essence}`, `{naming_style}`, `{location_name}`, `{location_description}`, `{location_category}`
   - Output JSON: `{ "npcs": [{ "name": str, "description": str, "dialogue": str, "role": str }] }`
   - Separate from location generation for reliability

### AIConfig Updates
- Add four new prompt attributes with defaults
- Update `to_dict()` and `from_dict()` to serialize/deserialize new prompts

## Tests

File: `tests/test_ai_config.py` (append)

1. `test_ai_config_world_context_prompt_exists` - Verify prompt is non-empty and contains `{theme}`
2. `test_ai_config_region_context_prompt_exists` - Verify prompt is non-empty and contains `{theme_essence}`
3. `test_ai_config_location_prompt_minimal_exists` - Verify prompt is non-empty and contains `{region_theme}`
4. `test_ai_config_npc_prompt_minimal_exists` - Verify prompt is non-empty and contains `{location_name}`
5. `test_ai_config_serialization_includes_new_prompts` - Verify round-trip for all 4 new prompts

## Implementation Steps

1. **Add prompt templates to `ai_config.py`** (lines ~260-340, after existing prompts):
   - `DEFAULT_WORLD_CONTEXT_PROMPT`
   - `DEFAULT_REGION_CONTEXT_PROMPT`
   - `DEFAULT_LOCATION_PROMPT_MINIMAL`
   - `DEFAULT_NPC_PROMPT_MINIMAL`

2. **Update `AIConfig` dataclass** (around line 344):
   - Add 4 new fields with `field(default=...)` for each prompt

3. **Update `to_dict()` method** (around line 471):
   - Add 4 new keys for the new prompts

4. **Update `from_dict()` method** (around line 503):
   - Add 4 new `.get()` calls with defaults

5. **Write tests in `tests/test_ai_config.py`** (append at end):
   - 5 new test functions as specified above

6. **Run tests**: `pytest tests/test_ai_config.py -v`
