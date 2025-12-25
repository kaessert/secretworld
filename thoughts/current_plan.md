# Implementation Plan: Integrate Typewriter Effect into Dreams

## Spec
Dream sequences displayed during rest should use the typewriter effect for atmospheric text reveal. The `dreams.py` module returns formatted dream text, and display happens in `main.py`. The typewriter effect should apply to the dream text output while respecting the existing effects_enabled() toggle.

## Approach
Add a new `display_dream()` function in `dreams.py` that wraps the formatted dream text with typewriter output. The caller in `main.py` will use this function instead of just appending the dream string to messages.

**Key Design Decision**: Since `maybe_trigger_dream()` returns a string that gets joined with other messages, we need a separate display function that directly prints with typewriter effect. The dream is a self-contained atmospheric moment that should be displayed separately from other rest messages.

## Implementation Steps

### 1. Add test for dream typewriter display
**File**: `tests/test_dreams.py`

Add new test class `TestDreamTypewriterDisplay`:
- Test that `display_dream()` exists and calls typewriter_print
- Test that display respects effects_enabled toggle
- Test that formatted dream text is passed to typewriter

### 2. Add display_dream function to dreams.py
**File**: `src/cli_rpg/dreams.py`

- Import `typewriter_print` from `text_effects`
- Add function `display_dream(dream_text: str) -> None` that:
  - Calls `typewriter_print()` for each line of the formatted dream
  - Uses a slower delay (0.04-0.05s) for more atmospheric effect

### 3. Update main.py to use display_dream
**File**: `src/cli_rpg/main.py` (around line 1250)

Change from:
```python
if dream:
    messages.append(dream)
```

To:
```python
if dream:
    from cli_rpg.dreams import display_dream
    display_dream(dream)
```

The dream is displayed directly with typewriter effect, not appended to messages.

## Test Commands
```bash
pytest tests/test_dreams.py -v
pytest tests/test_text_effects.py -v
pytest --cov=src/cli_rpg -v
```
