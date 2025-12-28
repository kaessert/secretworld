# Implementation Summary: ContentLayer NPC and Quest Generation

## What Was Implemented

Added two new methods to `ContentLayer` class in `src/cli_rpg/content_layer.py`:

### 1. `generate_npc_content()`
- Generates NPC name, description, and dialogue
- Tries AI generation first if `ai_service.generate_npc_content()` is available
- Falls back to `FallbackContentProvider.get_npc_content()` on AI failure or when AI unavailable
- Takes role, category, coordinates, ai_service, generation_context, and rng parameters
- Returns dict with 'name', 'description', 'dialogue' keys

### 2. `generate_quest_content()`
- Generates quest name, description, objective_type, and target
- Tries AI generation via `ai_service.generate_quest()` when both ai_service and generation_context are provided
- Falls back to `FallbackContentProvider.get_quest_content()` on AI failure
- Takes category, coordinates, ai_service, generation_context, rng, and optional npc_name, valid_locations, valid_npcs parameters
- Returns dict with 'name', 'description', 'objective_type', 'target' keys (or None on failure)

## Files Modified
- `src/cli_rpg/content_layer.py` - Added `generate_npc_content()` and `generate_quest_content()` methods

## Files Created
- `tests/test_content_layer_npc_quest.py` - 10 integration tests for the new methods

## Test Results
- All 10 new tests pass
- All 5205 existing tests pass (no regressions)
- Related test files verified:
  - `tests/test_content_layer.py` (8 tests pass)
  - `tests/test_fallback_content.py` (18 tests pass)

## Tests Cover
1. NPC generation with fallback when AI unavailable
2. Quest generation with fallback when AI unavailable
3. NPC content determinism (same seed = same output)
4. Quest content determinism (same seed = same output)
5. AI-generated NPC content used when available
6. AI-generated quest content used when available
7. AI failure gracefully falls back for NPCs
8. AI failure gracefully falls back for quests
9. NPC content varies by role
10. Quest content varies by category

## Design Decisions
- Uses `hasattr()` check before calling `ai_service.generate_npc_content()` since AIService may not have this method yet
- Both methods create a new `FallbackContentProvider` with a seed derived from the RNG for deterministic fallback
- Quest generation requires both ai_service and generation_context for AI path; otherwise uses fallback
- NPC generation only requires ai_service (generation_context is optional but passed if available)

## E2E Validation Notes
- No E2E tests required for this change as it's internal API
- Integration is validated through the 10 unit tests
- Future work can call these methods from `ai_world.py` when generating SubGrid NPCs/quests
