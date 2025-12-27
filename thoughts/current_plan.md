# Add `world_theme_essence` to Location AI Prompt

## Summary
Add `{theme_essence}` parameter to `DEFAULT_LOCATION_PROMPT` in `ai_config.py` to enrich non-layered AI location generation with WorldContext theme information.

## Spec
- Modify `DEFAULT_LOCATION_PROMPT` to include `{theme_essence}` placeholder in the Context section
- Modify `generate_location()` to accept optional `world_context` parameter
- Modify `_build_location_prompt()` to extract and format `theme_essence` from WorldContext
- When no WorldContext is provided, use a sensible default based on theme

## Files to Modify

### 1. `src/cli_rpg/ai_config.py`
Update `DEFAULT_LOCATION_PROMPT` (lines 14-41):
```python
# Add theme_essence to context section:
Context:
- World Theme: {theme}
- Theme Essence: {theme_essence}  # NEW
- Existing Locations: {context_locations}
- Terrain Type: {terrain_type}
```

### 2. `src/cli_rpg/ai_service.py`
- `generate_location()` (line 153): Add optional `world_context: Optional[WorldContext] = None` parameter
- `_build_location_prompt()` (line 208): Add `world_context` parameter and extract `theme_essence`
  - If `world_context` provided: use `world_context.theme_essence`
  - Otherwise: use default from `DEFAULT_THEME_ESSENCES.get(theme, "")`

### 3. `src/cli_rpg/ai_world.py`
- `create_ai_world()` and initial location generation already call `generate_location()` without world context (acceptable - defaults will apply)
- No changes needed for now (world context is generated after initial world creation)

## Tests to Add/Modify

### `tests/test_ai_service.py` or new `tests/test_ai_location_theme_essence.py`
1. Test `generate_location()` includes theme_essence in prompt when WorldContext provided
2. Test `generate_location()` uses default theme_essence when no WorldContext
3. Test prompt format includes theme_essence field

### `tests/test_ai_config.py`
1. Verify `DEFAULT_LOCATION_PROMPT` contains `{theme_essence}` placeholder

## Implementation Order
1. Update `DEFAULT_LOCATION_PROMPT` in `ai_config.py` to add `{theme_essence}` placeholder
2. Update `_build_location_prompt()` in `ai_service.py` to accept and format `theme_essence`
3. Update `generate_location()` signature to accept optional `world_context`
4. Add/update tests to verify theme_essence is included in prompts
5. Run `pytest` to ensure all tests pass
