# Implementation Plan: Typewriter-Style Text Reveal

## Spec

Add a typewriter-style text reveal effect for dramatic moments in the game. The effect prints text character-by-character with configurable delays, enhancing atmosphere for:
- Dream sequences (via `dreams.py`)
- Whispers (via `whisper.py`)
- Combat announcements (boss encounters, combo triggers)

**Requirements:**
1. Create `text_effects.py` module with `typewriter_print()` function
2. Configurable delay between characters (default ~30ms)
3. Respects `CLI_RPG_NO_COLOR` / non-interactive mode (instant print when disabled)
4. Supports ANSI color codes (prints codes instantly, delays only visible chars)
5. Can be interrupted by keyboard (Ctrl+C falls back to instant print)

## Tests

Create `tests/test_text_effects.py`:

1. `test_typewriter_outputs_all_text` - Complete text is output
2. `test_respects_disabled_effects` - Prints instantly when effects disabled
3. `test_handles_ansi_codes` - Color codes don't add delay
4. `test_empty_string` - Empty input produces no crash
5. `test_multiline` - Newlines are respected
6. `test_custom_delay` - Custom delay parameter works
7. `test_effects_enabled_respects_color_setting` - Follows color_enabled()

## Implementation Steps

### Step 1: Create `src/cli_rpg/text_effects.py`

New module with:
- `DEFAULT_TYPEWRITER_DELAY = 0.03`
- `_effects_enabled: bool` global flag
- `set_effects_enabled(enabled: bool)` - Global toggle
- `effects_enabled() -> bool` - Check if effects active (respects color_enabled())
- `typewriter_print(text, delay, file)` - Main function

Key logic:
- Skip effect if `not effects_enabled()`, print instantly
- Detect ANSI sequences (`\x1b[...m`) and print them instantly without delay
- Delay only for visible characters
- Handle KeyboardInterrupt to print remaining text instantly

### Step 2: Create `tests/test_text_effects.py`

Test all scenarios from spec with mocked time.sleep and captured stdout.

### Step 3: Integrate into `dreams.py`

In `format_dream()`, optionally call typewriter for content. Or add `display_dream()` helper.

### Step 4: Integrate into `whisper.py`

Add `display_whisper()` that uses typewriter with faster delay (0.02s).

### Step 5: Integrate into `combat.py`

Boss introduction uses typewriter for dramatic effect in `CombatEncounter.start()`.

### Step 6: Update `main.py`

Call `set_effects_enabled(False)` when `--non-interactive` or `--json` mode is active.

### Step 7: Run tests

```bash
pytest tests/test_text_effects.py -v
pytest tests/test_dreams.py -v
pytest -x  # Full suite to verify no regressions
```
