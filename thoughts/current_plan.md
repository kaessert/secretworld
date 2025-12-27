# Issue 22: Location-Themed Hallucinations

## Spec

Extend `hallucinations.py` to use location-category-specific templates instead of the current 3 generic templates. Pattern follows `encounter_tables.py` (Issue 21).

**Categories to support:**
- `dungeon`: ghostly prisoners, skeletal warriors
- `forest`: twisted treants, shadow wolves
- `temple`: fallen priests, dark angels
- `cave`: eyeless horrors, dripping shadows
- Default: existing generic templates (Shadow Mimic, Phantom Shade, Nightmare Echo)

## Tests (TDD) - `tests/test_hallucinations.py`

Add new `TestCategoryHallucinations` class:

1. `test_dungeon_templates_exist` - `get_hallucination_templates("dungeon")` returns dungeon-themed templates
2. `test_forest_templates_exist` - `get_hallucination_templates("forest")` returns forest-themed templates
3. `test_temple_templates_exist` - `get_hallucination_templates("temple")` returns temple-themed templates
4. `test_cave_templates_exist` - `get_hallucination_templates("cave")` returns cave-themed templates
5. `test_unknown_category_uses_defaults` - Unknown category returns `HALLUCINATION_TEMPLATES`
6. `test_none_category_uses_defaults` - `None` returns `HALLUCINATION_TEMPLATES`
7. `test_spawn_with_dungeon_category` - `spawn_hallucination(5, "dungeon")` spawns dungeon-themed enemy
8. `test_spawn_with_forest_category` - `spawn_hallucination(5, "forest")` spawns forest-themed enemy
9. `test_spawn_with_no_category` - `spawn_hallucination(5)` spawns default-themed enemy
10. `test_check_uses_location_category` - Integration: cave location spawns cave-themed hallucination

## Implementation Steps

1. **Add `CATEGORY_HALLUCINATION_TEMPLATES` dict** after existing `HALLUCINATION_TEMPLATES` (line 36):
   - `"dungeon"`: Ghostly Prisoner, Skeletal Warrior
   - `"forest"`: Twisted Treant, Shadow Wolf
   - `"temple"`: Fallen Priest, Dark Angel
   - `"cave"`: Eyeless Horror, Dripping Shadow

2. **Add `get_hallucination_templates(category: str | None) -> list[dict]`** helper function

3. **Update `spawn_hallucination` signature** to accept optional `category` parameter:
   ```python
   def spawn_hallucination(level: int, category: str | None = None) -> Enemy:
   ```

4. **Update template selection in `spawn_hallucination`** (line 57):
   ```python
   templates = get_hallucination_templates(category)
   template = random.choice(templates)
   ```

5. **Update `check_for_hallucination`** call site (line ~101):
   ```python
   hallucination = spawn_hallucination(
       game_state.current_character.level,
       category=location.category if location else None
   )
   ```

6. **Run tests** and verify all 4550+ tests pass

7. **Update ISSUES.md** to mark Issue 22 as COMPLETED
