# Dream Sequences - Implementation Summary

## What Was Implemented

### New Module: `src/cli_rpg/dreams.py`
Created a new dream system module with the following components:

1. **Constants**:
   - `DREAM_CHANCE = 0.25` (25% trigger rate on rest)
   - `NIGHTMARE_DREAD_THRESHOLD = 50` (dread level for nightmares)

2. **Dream Content Pools**:
   - `PROPHETIC_DREAMS`: 4 foreshadowing dreams
   - `ATMOSPHERIC_DREAMS`: 4 surreal mood-setting dreams
   - `CHOICE_DREAMS`: 2 choice-based categories (combat_flee, combat_kill)
   - `NIGHTMARES`: 6 horror-themed nightmares

3. **Core Functions**:
   - `maybe_trigger_dream(dread, choices, theme)`: Main entry point, returns formatted dream or None
   - `_select_dream(choices)`: Internal function to select dream based on player choices
   - `format_dream(dream_text)`: Formats dream with decorative borders and intro/outro

### Modified: `src/cli_rpg/main.py`
- Added import for `maybe_trigger_dream` at top of file
- Modified `handle_exploration_command()` rest command handler to:
  - Call `maybe_trigger_dream()` after healing/dread reduction
  - Pass current dread, player choices, and theme to the dream function
  - Append dream output to rest messages when triggered

### New Tests: `tests/test_dreams.py`
Created comprehensive test suite with 19 tests covering:
- Dream constants and configuration
- `maybe_trigger_dream()` behavior (return types, trigger rates)
- Nightmare triggering at high dread (50%+)
- Choice-based dream selection (flee/kill influences)
- Dream content pools existence and content
- `format_dream()` formatting with borders and intro/outro
- Integration with rest command in `handle_exploration_command()`

## Test Results
- All 19 new dream tests pass
- Full test suite: **1961 tests passed** (no regressions)

## Key Design Decisions
1. **25% trigger rate**: Matches original spec, balanced for occasional atmosphere without annoyance
2. **Dread integration**: Nightmares at 50%+ dread for psychological horror feel
3. **Choice tracking**: Uses `game_state.choices` to personalize dreams (flee >= 3, kill >= 10 thresholds)
4. **Graceful fallback**: Uses `getattr()` for choices/theme in case attributes don't exist
5. **Formatting**: ANSI colors (magenta intro/outro, cyan dream text) with ═ borders

## E2E Validation Checklist
1. [ ] Rest with health < max and verify dream can appear (check for "═" or "sleep" in output)
2. [ ] Rest at full health/no dread and verify early return without dream
3. [ ] Rest with high dread (50+) and verify nightmare content appears
4. [ ] Verify dream output has proper formatting with borders and intro/outro text
5. [ ] Verify no regressions in existing rest functionality (healing, dread reduction)
