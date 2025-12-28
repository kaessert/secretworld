# ContentLayer Mediator Implementation Plan

## Spec

Create `src/cli_rpg/content_layer.py` - a mediator class that bridges procedural layout generators (`RoomTemplate` from `procedural_interiors.py`) with AI content generation (`ai_service.py`), producing fully populated `SubGrid` instances with deterministic spatial structure and AI-generated thematic content.

### Interface
```python
class ContentLayer:
    def populate_subgrid(
        self,
        room_templates: list[RoomTemplate],
        parent_location: Location,
        ai_service: Optional[AIService],
        generation_context: Optional[GenerationContext],
        seed: int
    ) -> SubGrid
```

### Responsibilities
1. Transform `RoomTemplate` → `Location` for each room
2. Generate AI content (name, description) based on room type and spatial context
3. Apply procedural augmentation (treasures, puzzles, secrets, hazards)
4. Handle AI fallback gracefully when service unavailable
5. Ensure determinism via seed parameter

---

## Tests First

**File:** `tests/test_content_layer.py`

### Test Cases
1. `test_content_layer_transforms_templates_to_locations` - Verifies RoomTemplate list → SubGrid with matching coordinates
2. `test_content_layer_entry_room_is_exit_point` - Entry template → Location with `is_exit_point=True`
3. `test_content_layer_boss_room_gets_boss_enemy` - BOSS_ROOM template → Location with `boss_enemy` set
4. `test_content_layer_treasure_room_gets_treasures` - TREASURE template → Location with treasures list
5. `test_content_layer_hazards_from_template` - `suggested_hazards` → Location `hazards`
6. `test_content_layer_deterministic_with_seed` - Same seed → same output
7. `test_content_layer_fallback_without_ai` - AI unavailable → fallback names/descriptions by room type
8. `test_content_layer_ai_content_used_when_available` - Mock AI → Location has AI-generated content

---

## Implementation Steps

### Step 1: Create test file
**File:** `tests/test_content_layer.py`
- Import RoomTemplate, RoomType, Location, SubGrid
- Create fixtures for sample room templates
- Write 8 test cases (initially failing)

### Step 2: Create ContentLayer class skeleton
**File:** `src/cli_rpg/content_layer.py`
- Define ContentLayer class
- Define `populate_subgrid()` method signature
- Add room type → fallback content mapping dict

### Step 3: Implement template → location transformation
- Iterate room_templates
- Create Location with coordinates from template
- Set `is_exit_point` from `is_entry`
- Set `hazards` from `suggested_hazards`

### Step 4: Implement room type handling
- BOSS_ROOM → set `boss_enemy` based on parent category
- TREASURE → add treasures via `_place_treasures()` pattern
- PUZZLE → add puzzles via `_generate_puzzles_for_location()` pattern

### Step 5: Implement AI content generation
- Build prompt context from room template + generation context
- Call `ai_service.generate_room_content()` (new method needed)
- OR call existing `generate_location_with_context()` with room hints

### Step 6: Implement fallback content
- Fallback names: "Entrance Chamber", "Dark Corridor", "Ancient Chamber", "Boss Lair", "Treasure Vault", "Puzzle Room"
- Fallback descriptions: Procedural based on room type + parent category

### Step 7: Wire into ai_world.py
**File:** `src/cli_rpg/ai_world.py`
- Import ContentLayer
- In `generate_subgrid_for_location()`:
  - Call `generate_interior_layout()` for room templates
  - Call `ContentLayer.populate_subgrid()` to create SubGrid
  - Replace current AI area generation flow

---

## Files Modified

| File | Change |
|------|--------|
| `tests/test_content_layer.py` | New - 8 test cases |
| `src/cli_rpg/content_layer.py` | New - ContentLayer class |
| `src/cli_rpg/ai_world.py` | Integrate ContentLayer in `generate_subgrid_for_location()` |
