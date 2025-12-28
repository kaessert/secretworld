# Implementation Plan: Phase 5 Step 17 - Update Fallback Paths

## Summary
Update `ai_world.py` to use centralized `FallbackContentProvider` instead of scattered inline fallback templates for consistent deterministic fallback behavior.

## Scope Analysis

### Fallback paths to update:
1. **`_generate_fallback_interior()`** (lines 1119-1211): Uses inline hardcoded templates for room names/descriptions. Should use `FallbackContentProvider.get_room_content()`.

2. **`_create_treasure_chest()`** (lines 179-222): Uses local `TREASURE_CHEST_NAMES` and `TREASURE_LOOT_TABLES`. Should use templates from `fallback_content.py` (already has `ITEM_TEMPLATES`).

### Already centralized (no changes needed):
- `ContentLayer._generate_fallback_content()` - Already uses `FallbackContentProvider`
- `ContentLayer.generate_npc_content()` - Already uses `FallbackContentProvider`
- `ContentLayer.generate_quest_content()` - Already uses `FallbackContentProvider`
- `_create_default_merchant_shop()` - Terrain-specific shop logic, keep as-is (not content generation)

### Templates that should stay in ai_world.py:
- `SECRET_TEMPLATES` - Secrets are procedural game mechanics, not content templates
- `PUZZLE_TEMPLATES` - Puzzles are procedural game mechanics, not content templates
- `TERRAIN_SHOP_ITEMS` - Shop inventory configuration, not content templates

## Implementation Steps

### Step 1: Update _generate_fallback_interior() to use FallbackContentProvider

**File**: `src/cli_rpg/ai_world.py`

Modify `_generate_fallback_interior()` to:
1. Import `FallbackContentProvider` and `RoomType` at module level
2. Create a provider with seed derived from location coordinates
3. Use `provider.get_room_content()` for names/descriptions
4. Keep coordinate layout logic (this is structural, not content)

### Step 2: Add treasure item templates to FallbackContentProvider

**File**: `src/cli_rpg/fallback_content.py`

Add `get_treasure_content()` method that:
1. Takes category, distance, z_level as parameters
2. Returns chest name, description, and items list
3. Uses existing `ITEM_TEMPLATES` for loot

### Step 3: Update _create_treasure_chest() to use FallbackContentProvider

**File**: `src/cli_rpg/ai_world.py`

Modify `_create_treasure_chest()` to:
1. Create provider with seed from category + distance + z_level
2. Use `provider.get_treasure_content()` for chest name/description/items

### Step 4: Remove duplicated constants from ai_world.py

**File**: `src/cli_rpg/ai_world.py`

Remove:
- `TREASURE_LOOT_TABLES` (lines 341-367) - Moved to fallback_content.py
- `TREASURE_CHEST_NAMES` (lines 370-376) - Moved to fallback_content.py

### Step 5: Update existing tests

**File**: `tests/test_enterable_sublocations.py`

Update tests for `_generate_fallback_interior()` to verify:
1. Content is generated via FallbackContentProvider
2. Deterministic output with same seed
3. Category-specific content is returned

## Files to Modify
- `src/cli_rpg/ai_world.py` - Update fallback functions, remove duplicated constants
- `src/cli_rpg/fallback_content.py` - Add `get_treasure_content()` method

## Files to Test
- `tests/test_enterable_sublocations.py` - Existing tests for `_generate_fallback_interior()`
- `tests/test_fallback_content.py` - Add tests for `get_treasure_content()`

## Test Commands
```bash
# Run affected tests
pytest tests/test_enterable_sublocations.py tests/test_fallback_content.py -v

# Run full suite to verify no regressions
pytest tests/ -v
```

## Success Criteria
1. All 5205+ existing tests continue to pass
2. `_generate_fallback_interior()` uses `FallbackContentProvider` for content
3. `_create_treasure_chest()` uses `FallbackContentProvider` for content
4. Same seed produces identical fallback content (determinism)
5. No duplicated template constants between modules
