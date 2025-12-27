# Implementation Plan: Wire Named Location Triggers

**Goal**: Make 95% of tiles use instant template-based terrain instead of expensive AI generation. Only trigger AI for named POIs (towns, dungeons, landmarks).

## Spec

- Track `tiles_since_named: int` in GameState (resets when entering a named location)
- When moving to unexplored tile, call `should_generate_named_location(tiles_since_named, terrain)`
- If FALSE → use `get_unnamed_location_template(terrain)` for instant generation (no AI)
- If TRUE → generate named location via AI (current behavior)
- Named locations have `is_named=True`, unnamed have `is_named=False`
- Persist `tiles_since_named` in save files

## Test Cases

1. **Counter tracking**:
   - `tiles_since_named` increments on move to unnamed location
   - `tiles_since_named` resets to 0 when generating named location
   - Counter persists through save/load

2. **Template usage for unnamed**:
   - When `should_generate_named_location()` returns False, new location uses template
   - Template locations have `is_named=False`
   - No AI call made for template locations

3. **AI usage for named**:
   - When `should_generate_named_location()` returns True, AI generates location
   - AI locations have `is_named=True`
   - Counter resets after named location generated

## Implementation Steps

### 1. Add `tiles_since_named` to GameState

**File**: `src/cli_rpg/game_state.py`

- Add field in `__init__` (after line 283): `self.tiles_since_named: int = 0`
- Add to `to_dict()` (after line 1072): `data["tiles_since_named"] = self.tiles_since_named`
- Add to `from_dict()` (after line 1175): `game_state.tiles_since_named = data.get("tiles_since_named", 0)`

### 2. Wire trigger into move() method

**File**: `src/cli_rpg/game_state.py`

In `move()` method (lines 515-570), replace the unconditional AI/fallback generation with:

1. Import `should_generate_named_location`, `get_unnamed_location_template`, `TERRAIN_TO_CATEGORY` from `world_tiles`
2. After getting terrain (line 520), check `should_generate_named_location()`
3. If FALSE: create Location from template, increment counter
4. If TRUE: use existing AI/fallback path, reset counter to 0 on success

### 3. Update generate_fallback_location for named locations

**File**: `src/cli_rpg/world.py`

Add `is_named: bool = False` parameter to `generate_fallback_location()` and use it when creating the Location.

### 4. Create integration tests

**File**: `tests/test_named_location_integration.py` (NEW)

- `test_tiles_since_named_increments_on_unnamed`
- `test_tiles_since_named_resets_on_named`
- `test_tiles_since_named_persists_save_load`
- `test_unnamed_location_uses_template_not_ai`
- `test_named_location_triggers_ai_or_fallback`

## File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/game_state.py` | Add `tiles_since_named` field, wire trigger in `move()`, update serialization |
| `src/cli_rpg/world.py` | Add `is_named` param to `generate_fallback_location()` |
| `tests/test_named_location_integration.py` | NEW - Integration tests |

## Verification

```bash
pytest tests/test_named_locations.py tests/test_unnamed_templates.py tests/test_named_location_integration.py -v
pytest  # Full suite
```
