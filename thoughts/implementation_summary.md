# Dream Frequency Fix - Implementation Summary

## What Was Implemented

### 1. Reduced Dream Trigger Rates (dreams.py)
- **DREAM_CHANCE**: Changed from 0.25 (25%) to 0.10 (10%)
- **CAMP_DREAM_CHANCE**: New constant set to 0.15 (15%), replacing the old 40%

### 2. Dream Cooldown System (dreams.py, game_state.py)
- Added **DREAM_COOLDOWN_HOURS = 12** constant
- Updated `maybe_trigger_dream()` to accept new parameters:
  - `dream_chance`: Optional override for trigger chance
  - `last_dream_hour`: Hour of last dream for cooldown check
  - `current_hour`: Current game hour for cooldown check
- Dreams are blocked if less than 12 hours have passed since the last dream

### 3. GameState Tracking (game_state.py)
- Added `last_dream_hour: Optional[int] = None` attribute
- Added serialization in `to_dict()` and deserialization in `from_dict()`
- Backward compatible: old saves without `last_dream_hour` default to None

### 4. Rest Command Updates (main.py)
- Added `--quick` / `-q` flag parsing to skip dream check entirely
- Updated to pass cooldown params to `maybe_trigger_dream()`
- Updates `last_dream_hour` when a dream triggers

### 5. Camp Command Updates (camping.py)
- Removed local `CAMP_DREAM_CHANCE = 0.40` constant
- Now imports `CAMP_DREAM_CHANCE` from dreams.py
- Updated to pass cooldown params to `maybe_trigger_dream()`
- Updates `last_dream_hour` when a dream triggers

## Files Modified
- `src/cli_rpg/dreams.py` - Constants and cooldown logic in maybe_trigger_dream()
- `src/cli_rpg/game_state.py` - last_dream_hour attribute and serialization
- `src/cli_rpg/main.py` - rest --quick flag, cooldown params
- `src/cli_rpg/camping.py` - CAMP_DREAM_CHANCE import, cooldown params
- `tests/test_dreams.py` - Updated and added 16 new tests
- `tests/test_camping.py` - Added 3 new tests for camp dream behavior

## Test Results
- All 47 dream tests pass
- All 48 camping tests pass
- Full test suite: **3635 tests passed**

## New Tests Added

### test_dreams.py
- TestDreamConstants: test_dream_chance_is_10_percent, test_camp_dream_chance_is_15_percent, test_dream_cooldown_is_12_hours
- TestMaybeTriggerDream: test_dream_chance_is_10_percent (updated statistical test)
- TestDreamCooldown: 4 tests for cooldown blocking/allowing dreams
- TestDreamChanceOverride: 3 tests for custom dream_chance parameter
- TestRestQuickFlag: 2 tests for --quick/-q flag skipping dreams
- TestLastDreamHourTracking: 4 tests for GameState tracking and serialization

### test_camping.py
- TestCampDreamChance: 3 tests for camp using 15% chance with cooldown

## E2E Validation Notes
To validate the implementation works end-to-end:
1. Start the game and damage character
2. Use `rest` multiple times - dreams should occur ~10% of the time
3. After a dream, use `rest` again within 12 game hours - no dream should occur
4. Use `rest --quick` - no dream should ever occur
5. Use `camp` in wilderness - dreams should occur ~15% of the time
6. Save/load game - `last_dream_hour` should persist correctly
