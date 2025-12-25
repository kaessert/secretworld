# Implementation Summary: Disable typewriter effects in non-interactive/JSON modes

## What was implemented

Added calls to `set_effects_enabled(False)` in `main.py` to disable typewriter text effects when running in `--non-interactive` or `--json` modes.

### Files modified

**`src/cli_rpg/main.py`**:
1. Added import: `from cli_rpg.text_effects import set_effects_enabled`
2. Added `set_effects_enabled(False)` in `run_json_mode()` after `set_colors_enabled(False)` (line 1475)
3. Added `set_effects_enabled(False)` in `run_non_interactive()` after `set_colors_enabled(False)` (line 1675)

### Technical Details

- The `text_effects` module already had the `set_effects_enabled()` function for controlling typewriter effects
- When set to `False`, `typewriter_print()` outputs text instantly without delays
- Updated comment to reflect both colors and effects being disabled for "machine-readable output"

## Test results

```
tests/test_text_effects.py: 14 passed
tests/test_main.py: 5 passed
```

The existing test `TestRespectsDisabledEffects::test_respects_disabled_effects_via_toggle` already verified that `set_effects_enabled(False)` prevents any sleep calls, confirming instant text output.

## E2E Validation

To validate end-to-end:
1. Run `cli-rpg --json` and verify output has no delays
2. Run `cli-rpg --non-interactive` and verify output has no delays
