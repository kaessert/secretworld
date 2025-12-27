# Implementation Plan: Layered AI Integration for Area Generation

## Summary
Add `generate_area_with_context()` method to `AIService` that orchestrates layered AI generation (Layers 1-4) for named location clusters, completing Item 4 of the WFC World Generation Overhaul.

## Problem
Currently `expand_area()` in `ai_world.py` calls `generate_area()` which uses a monolithic prompt ignoring `WorldContext` and `RegionContext`. The layered context is only used when falling back to single location generation. Area clusters (4-7 locations) should also benefit from coherent layered generation.

## Architecture

```
Current (broken for areas):
  expand_area() → generate_area() [monolithic, no context]
                → fallback: expand_world() → generate_location_with_context() [layered]

Target (coherent for all):
  expand_area() → generate_area_with_context() [layered, coherent]
                → for each location: generate_location_with_context() + generate_npcs_for_location()
```

## Implementation Steps

### 1. Add `generate_area_with_context()` to `ai_service.py`

**Location**: After `generate_npcs_for_location()` (around line 2754)

```python
def generate_area_with_context(
    self,
    world_context: "WorldContext",
    region_context: "RegionContext",
    entry_direction: str,
    size: int = 5,
    terrain_type: Optional[str] = None
) -> list[dict]:
    """Generate an area of connected locations using layered context.

    Orchestrates Layer 3 (location) and Layer 4 (NPC) generation for
    each location in the area, ensuring coherence with world/region themes.

    Args:
        world_context: Layer 1 WorldContext with theme essence, naming style, tone
        region_context: Layer 2 RegionContext with region name, theme, danger level
        entry_direction: Direction player is coming from
        size: Target number of locations (4-7, default 5)
        terrain_type: Optional terrain type for coherent generation

    Returns:
        List of location dicts with relative_coords, name, description, category, npcs
    """
```

**Implementation approach**:
1. Generate area layout (coordinates for N locations) using simple geometry
2. For each position, call `generate_location_with_context()` (Layer 3)
3. For each location, call `generate_npcs_for_location()` (Layer 4)
4. Return combined list with relative coordinates

### 2. Update `expand_area()` in `ai_world.py` to use layered generation

**Location**: Lines 573-595 in `expand_area()`

**Current code** (lines 573-581):
```python
area_data = ai_service.generate_area(
    theme=theme,
    sub_theme_hint=sub_theme,
    entry_direction=direction,
    context_locations=list(world.keys()),
    size=size
)
```

**Replace with**:
```python
if world_context is not None and region_context is not None:
    # Use layered generation for coherent areas
    area_data = ai_service.generate_area_with_context(
        world_context=world_context,
        region_context=region_context,
        entry_direction=direction,
        size=size,
        terrain_type=terrain_type
    )
else:
    # Fall back to monolithic generation
    area_data = ai_service.generate_area(
        theme=theme,
        sub_theme_hint=sub_theme,
        entry_direction=direction,
        context_locations=list(world.keys()),
        size=size
    )
```

### 3. Add tests

**File**: `tests/test_generate_area_with_context.py`

Tests to add:
1. `test_generate_area_with_context_returns_list_of_locations` - Returns list of dicts
2. `test_generate_area_with_context_includes_entry_at_origin` - Entry location at (0,0)
3. `test_generate_area_with_context_each_location_has_required_fields` - name, description, category, npcs, relative_coords
4. `test_generate_area_with_context_uses_world_context_theme` - Location names follow naming style
5. `test_generate_area_with_context_uses_region_context` - Locations match region theme
6. `test_generate_area_with_context_generates_npcs_for_each_location` - NPCs present
7. `test_expand_area_uses_layered_generation_when_contexts_provided` - Integration test

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_service.py` | Add `generate_area_with_context()` method (~50 lines) |
| `src/cli_rpg/ai_world.py` | Update `expand_area()` to conditionally use layered generation (~10 lines) |
| `tests/test_generate_area_with_context.py` | New file with 7 tests |

## Success Criteria

1. `generate_area_with_context()` exists and passes all tests
2. `expand_area()` uses layered generation when contexts are provided
3. Generated area locations show coherence with world/region themes
4. All existing 3648 tests continue to pass
5. ISSUES.md Item 4 can be marked complete

## Cost Analysis

Per ISSUES.md table:
- Named area (SubGrid): Layers 1, 2, 3+, 4+ = 3+ AI calls
- With new method: 1 call per location for Layer 3, 1 call per location for Layer 4
- For 5-location area: ~10 AI calls (vs 1 monolithic call before)
- Tradeoff: More calls but better coherence and smaller prompts (less likely to fail)

## Out of Scope

- Modifying world_context or region_context generation
- Changes to Layer 1-2 caching logic (already working)
- Changes to named location trigger logic (already working)
