# Dream Frequency Fix Implementation Plan

## Spec

**Problem**: Dreams trigger too frequently (25% on rest, 40% on camp), causing them to feel mundane rather than atmospheric.

**Fix**:
1. Reduce base rates: rest 25%→10%, camp 40%→15%
2. Add cooldown: track `last_dream_hour` in GameState, require 12+ game-hours between dreams
3. Add `--quick` flag to `rest` command to skip dream check entirely

## Test Plan

Update `tests/test_dreams.py`:
1. `test_dream_chance_is_10_percent` - Update statistical test for new 10% rate
2. `test_camp_dream_chance_is_15_percent` - New test for camp-specific rate
3. `test_dream_cooldown_blocks_frequent_dreams` - Cooldown blocks dream if <12 hours since last
4. `test_dream_cooldown_allows_dream_after_threshold` - Cooldown allows dream after 12+ hours
5. `test_cooldown_resets_on_dream_trigger` - `last_dream_hour` updates when dream triggers
6. `test_rest_quick_flag_skips_dream` - `rest --quick` or `rest -q` skips dream check

Update `tests/test_camping.py`:
7. `test_camp_uses_camp_dream_chance` - Verify camp uses 15% (not 25%)

## Implementation Steps

### 1. Update `src/cli_rpg/dreams.py`
- Change `DREAM_CHANCE = 0.25` to `DREAM_CHANCE = 0.10`
- Add `CAMP_DREAM_CHANCE = 0.15` constant (for export)
- Add `DREAM_COOLDOWN_HOURS = 12` constant
- Update `maybe_trigger_dream()` signature to accept `dream_chance: float = DREAM_CHANCE` and `last_dream_hour: Optional[int] = None`, `current_hour: Optional[int] = None`
- Add cooldown logic: if `last_dream_hour` provided and `current_hour - last_dream_hour < DREAM_COOLDOWN_HOURS`, return None

### 2. Update `src/cli_rpg/game_state.py`
- Add `last_dream_hour: Optional[int] = None` attribute in `__init__`
- Add to `to_dict()` serialization
- Add to `from_dict()` deserialization

### 3. Update `src/cli_rpg/main.py` (rest command)
- Parse `--quick` or `-q` flag from args
- If quick flag set, skip `maybe_trigger_dream()` call entirely
- Pass `dream_chance=DREAM_CHANCE`, `last_dream_hour=game_state.last_dream_hour`, `current_hour=game_state.game_time.hour` to `maybe_trigger_dream()`
- If dream triggers, update `game_state.last_dream_hour = game_state.game_time.hour`

### 4. Update `src/cli_rpg/camping.py`
- Import `CAMP_DREAM_CHANCE` from dreams (or define locally as 0.15)
- Pass `dream_chance=CAMP_DREAM_CHANCE`, `last_dream_hour`, `current_hour` to `maybe_trigger_dream()`
- If dream triggers, update `game_state.last_dream_hour`

### 5. Update tests
- Update `test_dream_chance_is_25_percent` → `test_dream_chance_is_10_percent` with new bounds (5-20% range)
- Add new tests as listed in Test Plan

## Files Modified
- `src/cli_rpg/dreams.py` - Rate constants, cooldown logic
- `src/cli_rpg/game_state.py` - `last_dream_hour` attribute and serialization
- `src/cli_rpg/main.py` - `rest --quick` flag, pass cooldown params
- `src/cli_rpg/camping.py` - Use `CAMP_DREAM_CHANCE`, pass cooldown params
- `tests/test_dreams.py` - Update and add dream trigger tests
