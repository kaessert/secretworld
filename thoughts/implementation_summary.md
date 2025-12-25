# Implementation Summary: Integrate Typewriter Effect into Dreams

## What Was Implemented

### 1. New `display_dream()` Function (src/cli_rpg/dreams.py)
- Added import for `typewriter_print` from `text_effects`
- Added constant `DREAM_TYPEWRITER_DELAY = 0.04` for slower atmospheric effect
- Added `display_dream(dream_text: str) -> None` function that:
  - Splits the formatted dream text into lines
  - Calls `typewriter_print()` for each line with the slower delay
  - Typewriter handles the `effects_enabled()` toggle internally

### 2. Updated main.py Integration (src/cli_rpg/main.py)
- Modified import to include `display_dream` alongside `maybe_trigger_dream`
- Changed rest command behavior when a dream triggers:
  - Rest message is printed first via `print()`
  - Dream is displayed via `display_dream()` with typewriter effect
  - Returns empty message to avoid double-printing

### 3. Tests Added (tests/test_dreams.py)
- `TestDreamTypewriterDisplay` class with 4 tests:
  - `test_display_dream_function_exists`: Verifies function is importable
  - `test_display_dream_calls_typewriter_print`: Verifies typewriter is used
  - `test_display_dream_respects_effects_toggle`: Verifies toggle integration
  - `test_display_dream_uses_slower_delay`: Verifies delay >= 0.04

### 4. Updated Existing Test
- `TestDreamIntegration.test_rest_can_trigger_dream`: Updated to use `capsys` to capture stdout since dream is now printed directly rather than returned in message

## Files Modified
1. `src/cli_rpg/dreams.py` - Added typewriter_print import and display_dream function
2. `src/cli_rpg/main.py` - Updated import and rest command dream handling
3. `tests/test_dreams.py` - Added 4 new tests, updated 1 existing test

## Test Results
- All 23 dreams tests pass
- All 14 text_effects tests pass
- Full test suite: 2279 tests pass

## Design Decisions
- The typewriter delay of 0.04s (vs default 0.03s) provides a slower, more atmospheric reveal appropriate for dream sequences
- Dreams are printed directly to stdout with typewriter effect rather than returned as a message, allowing the effect to play in real-time
- The `typewriter_print` function already handles the `effects_enabled()` toggle internally, so `display_dream` doesn't need special handling for disabled effects

## E2E Validation
To manually verify:
1. Run the game with `cli-rpg`
2. Issue the `rest` command multiple times (25% dream trigger rate)
3. When a dream triggers, observe the typewriter effect displaying the dream text character-by-character
4. Test with `--no-color` flag to verify effect is disabled when colors are off
