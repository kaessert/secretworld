# Implementation Plan: Validate EXPLORE Quest Targets

## Summary
Add validation in `ai_service.py:_parse_quest_response()` to check EXPLORE quest targets against known location names, following the same pattern as the existing KILL quest validation.

## Spec
- EXPLORE quest targets must match an existing location name (case-insensitive)
- Valid locations are passed as an optional parameter through the call chain
- When no valid locations are provided, EXPLORE validation is skipped (backward compatibility)
- Invalid EXPLORE targets raise `AIGenerationError`, triggering quest regeneration

## Test Plan (TDD - write tests first)

**File: `tests/test_explore_quest_validation.py`**

| Test | Description |
|------|-------------|
| `test_valid_explore_target_accepted` | EXPLORE quest with existing location name parses successfully |
| `test_invalid_explore_target_rejected` | EXPLORE quest with non-existent location raises `AIGenerationError` |
| `test_explore_target_case_insensitive` | "town square" matches "Town Square" |
| `test_explore_validation_skipped_when_no_locations` | No validation when `valid_locations=None` (backward compat) |
| `test_kill_quest_unchanged` | KILL quests still validate against `VALID_ENEMY_TYPES` |
| `test_collect_quest_unchanged` | COLLECT quests not validated against locations |

## Implementation Steps

1. **Create test file** `tests/test_explore_quest_validation.py`
   - Add tests for EXPLORE validation following the pattern of `tests/test_quest_validation.py`
   - Tests should initially fail (TDD)

2. **Modify `ai_service.py:generate_quest()`** (lines 1718-1768)
   - Add `valid_locations: Optional[set[str]] = None` parameter
   - Pass it to `_parse_quest_response()`

3. **Modify `ai_service.py:_parse_quest_response()`** (lines 1795-1905)
   - Add `valid_locations: Optional[set[str]] = None` parameter
   - After line 1875 (KILL validation), add EXPLORE validation:
   ```python
   # Validate EXPLORE quest targets against known locations
   if objective_type == "explore" and valid_locations is not None:
       if target.lower() not in valid_locations:
           raise AIGenerationError(
               f"Invalid EXPLORE quest target '{target}'. Must be an existing location."
           )
   ```

4. **Modify `main.py:talk` command handler** (lines 1263-1268)
   - Pass `valid_locations=set(loc.lower() for loc in game_state.world.keys())` to `generate_quest()`

5. **Run tests** to verify all pass
