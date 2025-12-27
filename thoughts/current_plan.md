# Implementation Plan: Add Neighboring Locations to Location Prompts

## Summary
Add `neighboring_locations` context to the minimal location generation prompt (Phase 1, item 4 of World Generation Immersion). This provides the AI with context about nearby locations for spatial coherence.

**Note**: The `region_theme` task (line 1314 in ISSUES.md) is already complete - it's implemented in `ai_config.py:306` and `ai_service.py:2655`. ISSUES.md should be updated to check it off.

---

## Spec

**Goal**: Pass a list of neighboring location names/descriptions to the location generation prompt so AI can generate locations that fit spatially with their surroundings.

**Input**:
- Existing prompt parameters plus `neighboring_locations: list[dict]` where each dict has `name`, `description`, `direction`

**Output**:
- Location generation prompt includes "Nearby:" section listing what's nearby

**Constraints**:
- Only include existing neighbors (not all 4 directions)
- Keep neighbor info concise (name + direction)
- Optional parameter - "none yet" if no neighbors exist

---

## Implementation Steps

### 1. Update `DEFAULT_LOCATION_PROMPT_MINIMAL` in `ai_config.py`

Add `{neighboring_locations}` placeholder after terrain_type (line ~307):

```python
Region Context:
- Region Name: {region_name}
- Region Theme: {region_theme}
- Terrain: {terrain_type}
- Nearby: {neighboring_locations}
```

### 2. Update `_build_location_with_context_prompt` in `ai_service.py`

Modify signature (line ~2627) and implementation (line ~2647):

- Add parameter: `neighboring_locations: Optional[list[dict]] = None`
- Format as comma-separated "Name (direction)" or "none yet" if empty
- Pass to template format call

### 3. Update `generate_location_with_context` in `ai_service.py`

Add parameter (line ~2564) and pass through to prompt builder (line ~2594).

### 4. Update `expand_world` in `ai_world.py`

Gather neighbor info before calling `generate_location_with_context` (line ~436):

```python
neighboring_locations = []
if target_coords:
    for dir_name, (dx, dy) in DIRECTION_OFFSETS.items():
        neighbor_coords = (target_coords[0] + dx, target_coords[1] + dy)
        for loc in world.values():
            if loc.coordinates == neighbor_coords:
                neighboring_locations.append({
                    "name": loc.name,
                    "direction": dir_name
                })
                break
```

### 5. Add test in `tests/test_ai_config.py`

```python
def test_ai_config_location_prompt_minimal_has_neighboring():
    """Test location_prompt_minimal includes {neighboring_locations} placeholder."""
    config = AIConfig(api_key="test-key")
    assert "{neighboring_locations}" in config.location_prompt_minimal
```

### 6. Update ISSUES.md (line ~1311-1315)

Mark both tasks complete:
```markdown
1. **Enrich Location Prompts** (Complete)
   - [x] Add `terrain_type` from ChunkManager ✓ (2025-12-26)
   - [x] Add `world_theme_essence` from WorldContext ✓ (2025-12-27)
   - [x] Add `region_theme` from RegionContext ✓ (2025-12-27)
   - [x] Add `neighboring_locations` names for coherence ✓ (2025-12-27)
```

---

## Files Modified

1. `src/cli_rpg/ai_config.py` - Add `{neighboring_locations}` to prompt template
2. `src/cli_rpg/ai_service.py` - Add parameter to generation methods, format neighbors
3. `src/cli_rpg/ai_world.py` - Gather neighbor info in `expand_world`
4. `tests/test_ai_config.py` - Add test for new placeholder
5. `ISSUES.md` - Mark tasks complete
