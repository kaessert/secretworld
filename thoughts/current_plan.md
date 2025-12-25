# Implementation Plan: Typewriter Effect in Combat

## Spec
Add typewriter effect to dramatic combat moments for enhanced atmosphere. Integrate `text_effects.typewriter_print` into `combat.py` for:
- Combat start (enemy appearance)
- Combo triggers (FRENZY!, REVENGE!, ARCANE BURST!)
- Victory/defeat messages

## Implementation Steps

### 1. Add tests for typewriter combat display
**File:** `tests/test_combat.py`

Add test class `TestCombatTypewriterDisplay`:
- `test_display_combat_start_uses_typewriter`: Verify `display_combat_start` calls `typewriter_print` with combat intro
- `test_display_combo_uses_typewriter`: Verify combo announcements use typewriter effect
- `test_display_combat_end_uses_typewriter`: Verify victory/defeat uses typewriter
- `test_combat_typewriter_delay_constant`: Verify `COMBAT_TYPEWRITER_DELAY` exists (0.025 - faster than dreams)

### 2. Add combat display functions with typewriter
**File:** `src/cli_rpg/combat.py`

Add at top after imports:
```python
# Faster delay for combat (action-paced)
COMBAT_TYPEWRITER_DELAY = 0.025
```

Add display functions (following whisper.py pattern):
```python
def display_combat_start(intro_text: str) -> None:
    """Display combat start with typewriter effect."""
    from cli_rpg.text_effects import typewriter_print
    typewriter_print(intro_text, delay=COMBAT_TYPEWRITER_DELAY)

def display_combo(combo_text: str) -> None:
    """Display combo announcement with typewriter effect."""
    from cli_rpg.text_effects import typewriter_print
    typewriter_print(combo_text, delay=COMBAT_TYPEWRITER_DELAY)

def display_combat_end(result_text: str) -> None:
    """Display combat end with typewriter effect."""
    from cli_rpg.text_effects import typewriter_print
    for line in result_text.split("\n"):
        typewriter_print(line, delay=COMBAT_TYPEWRITER_DELAY)
```

### 3. Wire up display functions in main.py combat handling
**File:** `src/cli_rpg/main.py`

Find where `combat.start()`, combo messages, and `combat.end_combat()` results are printed. Replace direct `print()` calls with the new display functions:
- `display_combat_start(combat.start())`
- `display_combo(...)` for combo trigger lines
- `display_combat_end(combat.end_combat(victory))`

## Test Commands
```bash
pytest tests/test_combat.py::TestCombatTypewriterDisplay -v
pytest tests/test_combat.py -v
```
