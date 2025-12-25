# Implementation Plan: Disable typewriter effects in non-interactive/JSON modes

## Summary
The `text_effects.py` module has `set_effects_enabled()` to control typewriter effects. Add calls to disable effects at startup for `--non-interactive` and `--json` modes.

## Spec
When `--non-interactive` or `--json` CLI flags are passed, typewriter text effects must be disabled so output is printed instantly (no delays in machine-readable output).

## Changes Required

### 1. Update `main.py` - Add effect disabling

**File:** `src/cli_rpg/main.py`

**Import:** Add to imports (line 17, after `from cli_rpg.companion_reactions import ...`):
```python
from cli_rpg.text_effects import set_effects_enabled
```

**run_json_mode()** (after line 1473 `set_colors_enabled(False)`):
```python
set_effects_enabled(False)
```

**run_non_interactive()** (after line 1671 `set_colors_enabled(False)`):
```python
set_effects_enabled(False)
```

### 2. Add test

**File:** `tests/test_text_effects.py`

Add test class:
```python
class TestNonInteractiveModeDisablesEffects:
    """Test: non-interactive modes disable typewriter effects."""

    def test_set_effects_enabled_false_disables_sleep(self):
        """Explicitly setting effects disabled prevents any sleep calls."""
        _reset_effects_state()
        text_effects.set_effects_enabled(False)

        output = io.StringIO()
        with patch("time.sleep") as mock_sleep:
            text_effects.typewriter_print("Test text", file=output)

        mock_sleep.assert_not_called()
        assert output.getvalue() == "Test text\n"
```

## Verification
```bash
pytest tests/test_text_effects.py -v
pytest tests/test_main.py -v  # Ensure no regressions
```
