# Fix: Sub-locations not visitable from overworld (CRITICAL)

## Problem Summary
The `enter` command fails with "You're not at an overworld location" for AI-generated terrain tiles because `is_overworld` defaults to `False` and is never set to `True` during location generation.

## Root Cause
Three location creation paths don't set `is_overworld=True`:
1. **Unnamed locations** (`game_state.py:567-574`) - terrain filler tiles
2. **Fallback locations** (`world.py:202-209`) - named POIs when AI unavailable

The `enter()` method (`game_state.py:852`) checks `if not current.is_overworld:` and rejects entry.

## Spec
- All overworld locations (both unnamed terrain tiles and named POIs) must have `is_overworld=True`
- SubGrid interior locations remain `is_overworld=False` (correctly set in `ai_world.py:900-910`)
- The `enter` command should work from any overworld tile that displays an "Enter:" option

## Implementation Steps

### 1. Add test for overworld flag on dynamically generated locations
**File**: `tests/test_game_state.py`
- Add test that verifies unnamed locations have `is_overworld=True`
- Add test that verifies fallback named locations have `is_overworld=True`
- Add test that verifies `enter` command works from dynamically generated overworld tile

### 2. Fix unnamed location generation
**File**: `src/cli_rpg/game_state.py`, lines 567-574
- Add `is_overworld=True` to the `Location()` constructor call

### 3. Fix fallback location generation
**File**: `src/cli_rpg/world.py`, lines 202-209
- Add `is_overworld=True` to the `Location()` constructor call in `generate_fallback_location()`

### 4. Run tests to verify
```bash
pytest tests/test_game_state.py tests/test_enter_entry_point.py -v
pytest --cov=src/cli_rpg
```
