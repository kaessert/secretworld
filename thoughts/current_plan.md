# Implementation Plan: Validate TALK Quest Targets Against World NPCs

## Summary
Add validation in `ai_service.py:_parse_quest_response()` to check TALK quest targets against existing NPC names in the game world, following the same pattern as EXPLORE quest validation (requires passing `valid_npcs` parameter).

## Spec
- TALK quest targets must match an existing NPC name in the game world (case-insensitive)
- Add `valid_npcs: Optional[set[str]]` parameter to `generate_quest()` and `_parse_quest_response()`
- Invalid TALK targets raise `AIGenerationError`, triggering quest regeneration
- When `valid_npcs=None`, validation is skipped (backward compatibility)
- Main.py collects NPC names from `game_state.world` and passes them to quest generation

## Test Plan (TDD - write tests first)

**File: `tests/test_talk_quest_validation.py`**

| Test | Description |
|------|-------------|
| `test_valid_talk_target_accepted` | TALK quest with existing NPC name parses successfully |
| `test_invalid_talk_target_rejected` | TALK quest with "Elder Mage Aldous" raises `AIGenerationError` when not in valid_npcs |
| `test_talk_target_case_insensitive` | "merchant" matches "Merchant" in valid_npcs |
| `test_talk_validation_skipped_when_no_npcs` | No validation when `valid_npcs=None` (backward compatibility) |
| `test_kill_quest_unchanged` | KILL quests still validate against `VALID_ENEMY_TYPES` |
| `test_explore_quest_unchanged` | EXPLORE quests still validate against `valid_locations` |
| `test_collect_quest_unchanged` | COLLECT quests still validate against `OBTAINABLE_ITEMS` |
| `test_generate_quest_accepts_valid_npcs_param` | `generate_quest()` accepts `valid_npcs` parameter |

## Implementation Steps

1. **Create test file** `tests/test_talk_quest_validation.py`
   - Tests follow the pattern of `tests/test_explore_quest_validation.py`
   - Tests should initially fail (TDD)

2. **Modify `ai_service.py:generate_quest()`** (line 1767-1773)
   - Add `valid_npcs: Optional[set[str]] = None` parameter
   - Pass `valid_npcs` to `_parse_quest_response()`

   ```python
   def generate_quest(
       self,
       theme: str,
       npc_name: str,
       player_level: int,
       location_name: str = "",
       valid_locations: Optional[set[str]] = None,
       valid_npcs: Optional[set[str]] = None  # NEW
   ) -> dict:
   ```

3. **Modify `ai_service.py:_parse_quest_response()`** (line 1849-1853)
   - Add `valid_npcs: Optional[set[str]] = None` parameter
   - Add validation block after COLLECT validation (around line 1950):

   ```python
   # Validate TALK quest targets against world NPCs
   if objective_type == "talk" and valid_npcs is not None:
       if target.lower() not in valid_npcs:
           raise AIGenerationError(
               f"Invalid TALK quest target '{target}'. Must be an existing NPC."
           )
   ```

4. **Modify `main.py`** (line 1263-1270)
   - Build `valid_npcs` set from all NPCs in `game_state.world`
   - Pass to `generate_quest()`

   ```python
   # Build set of valid location names for EXPLORE quest validation
   valid_locations = {loc.lower() for loc in game_state.world.keys()}
   # Build set of valid NPC names for TALK quest validation
   valid_npcs = {
       npc.name.lower()
       for location in game_state.world.values()
       for npc in location.npcs
   }
   quest_data = game_state.ai_service.generate_quest(
       theme=game_state.theme,
       npc_name=npc.name,
       player_level=game_state.current_character.level,
       location_name=game_state.current_location,
       valid_locations=valid_locations,
       valid_npcs=valid_npcs  # NEW
   )
   ```

5. **Run tests** to verify all pass

## Files to Modify

| File | Change |
|------|--------|
| `tests/test_talk_quest_validation.py` | NEW - Tests for TALK validation |
| `src/cli_rpg/ai_service.py` | Add `valid_npcs` param to `generate_quest()` and `_parse_quest_response()`, add TALK validation |
| `src/cli_rpg/main.py` | Collect NPC names from world and pass `valid_npcs` to `generate_quest()` |
