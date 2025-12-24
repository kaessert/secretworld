# Implementation Summary: Fix Save/Load Validation for Leveled-Up Characters

## Problem Solved
Saved games were failing to load after a character leveled up because `Character.__post_init__()` enforced a 1-20 stat limit during deserialization. When `from_dict()` created a character with stats > 20 (from level-ups), validation rejected it with "strength must be at most 20".

## Changes Made

### 1. Modified `Character.from_dict()` in `src/cli_rpg/models/character.py`
- Added stat capping to pass initial validation (lines 279-283)
- After construction, restored actual stats from save data (lines 294-297)
- Recalculated derived stats (`max_health`, `constitution`) based on actual strength (lines 299-301)
- Health is now capped at `max_health` when restored (line 304-305)

**Key insight**: The 1-20 stat limit is a **character creation** rule, not a game state rule. Leveled-up characters legitimately have stats > 20.

### 2. Added Tests in `tests/test_character_leveling.py`
- `test_from_dict_allows_stats_above_20_from_level_ups`: Verifies loading a character with stats > 20 works
- `test_serialization_roundtrip_preserves_high_stats`: Verifies a leveled-up character survives save/load roundtrip

### 3. Updated Test in `tests/test_persistence.py`
- Replaced `test_load_character_invalid_stat_values` (which expected stats > 20 to fail) with:
  - `test_load_character_allows_high_stats_from_level_ups`: Verifies high stats load correctly
  - `test_load_character_rejects_stats_below_minimum`: Verifies stats < 1 still raise ValueError

## Test Results
- All 716 tests pass (1 skipped)
- New tests verify the specific fix
- Existing tests confirm no regressions

## Technical Details
- `max_health` is recalculated from strength on load (not taken from saved value)
- This ensures consistency with the game formula: `BASE_HEALTH + strength * HEALTH_PER_STRENGTH`
- Saved `health` is capped at calculated `max_health` to prevent invalid states

## E2E Validation
To manually verify:
1. Create a character with 20 STR
2. Level up (gain 100 XP)
3. Verify STR is now 21
4. Save game
5. Quit and reload
6. Verify STR is still 21 and character loads successfully
