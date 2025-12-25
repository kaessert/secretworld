# Implementation Plan: Pause and Pacing for Dramatic Tension

## Summary
Add simple pause functions to `text_effects.py` that create dramatic pauses between text reveals. These build naturally on the existing typewriter effect system and follow the same patterns (global toggle, respects effects_enabled).

## Spec
1. `dramatic_pause(duration: float)` - Pause execution for dramatic effect
2. `pause_short()` - 0.5s pause for minor beats (e.g., between combat messages)
3. `pause_medium()` - 1.0s pause for moderate drama (e.g., combo announcements)
4. `pause_long()` - 1.5s pause for major moments (e.g., victory, quest completion)
5. All pauses skip instantly when `effects_enabled() == False`
6. Default durations are constants that can be customized

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/text_effects.py` | Add pause functions |
| `tests/test_text_effects.py` | Add pause tests |
| `src/cli_rpg/combat.py` | Add pauses to dramatic moments |
| `src/cli_rpg/dreams.py` | Add pause between intro/dream/outro |

## Implementation Steps

### 1. Add pause functions to `text_effects.py`

Add after `typewriter_print()`:

```python
# Pause duration constants (in seconds)
PAUSE_SHORT = 0.5
PAUSE_MEDIUM = 1.0
PAUSE_LONG = 1.5

def dramatic_pause(duration: float = PAUSE_MEDIUM) -> None:
    """Pause execution for dramatic effect.

    If effects are disabled, returns immediately.

    Args:
        duration: Pause duration in seconds. Defaults to PAUSE_MEDIUM.
    """
    if not effects_enabled():
        return
    time.sleep(duration)

def pause_short() -> None:
    """Short pause (0.5s) for minor dramatic beats."""
    dramatic_pause(PAUSE_SHORT)

def pause_medium() -> None:
    """Medium pause (1.0s) for moderate dramatic moments."""
    dramatic_pause(PAUSE_MEDIUM)

def pause_long() -> None:
    """Long pause (1.5s) for major dramatic moments."""
    dramatic_pause(PAUSE_LONG)
```

### 2. Add tests to `tests/test_text_effects.py`

Add new test classes:

```python
class TestDramaticPause:
    """Test: dramatic_pause() creates timed delays."""

    def test_dramatic_pause_sleeps_when_enabled(self):
        """dramatic_pause() should sleep for specified duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.dramatic_pause(0.75)

        mock_sleep.assert_called_once_with(0.75)

    def test_dramatic_pause_skips_when_disabled(self):
        """dramatic_pause() should skip sleep when effects disabled."""
        _reset_effects_state()
        text_effects.set_effects_enabled(False)

        with patch("time.sleep") as mock_sleep:
            text_effects.dramatic_pause(1.0)

        mock_sleep.assert_not_called()

    def test_pause_short_uses_correct_duration(self):
        """pause_short() should use PAUSE_SHORT duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_short()

        mock_sleep.assert_called_once_with(text_effects.PAUSE_SHORT)

    def test_pause_medium_uses_correct_duration(self):
        """pause_medium() should use PAUSE_MEDIUM duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_medium()

        mock_sleep.assert_called_once_with(text_effects.PAUSE_MEDIUM)

    def test_pause_long_uses_correct_duration(self):
        """pause_long() should use PAUSE_LONG duration."""
        _reset_effects_state()
        text_effects.set_effects_enabled(True)

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_long()

        mock_sleep.assert_called_once_with(text_effects.PAUSE_LONG)

    def test_pause_respects_color_disabled(self):
        """Pause functions should skip when colors are disabled."""
        _reset_effects_state()
        colors.set_colors_enabled(False)
        text_effects.set_effects_enabled(None)  # Follow color setting

        with patch("time.sleep") as mock_sleep:
            text_effects.pause_short()
            text_effects.pause_medium()
            text_effects.pause_long()

        mock_sleep.assert_not_called()
```

### 3. Integrate pauses into `combat.py`

Update display functions to add pauses:

```python
# In display_combat_start():
from cli_rpg.text_effects import typewriter_print, pause_short
typewriter_print(intro_text, delay=COMBAT_TYPEWRITER_DELAY)
pause_short()  # Brief pause after combat intro

# In display_combo():
from cli_rpg.text_effects import typewriter_print, pause_medium
typewriter_print(combo_text, delay=COMBAT_TYPEWRITER_DELAY)
pause_medium()  # Moderate pause after combo announcement

# In display_combat_end():
from cli_rpg.text_effects import typewriter_print, pause_long
for line in result_text.split("\n"):
    typewriter_print(line, delay=COMBAT_TYPEWRITER_DELAY)
pause_long()  # Long pause after combat resolution
```

### 4. Integrate pauses into `dreams.py`

Update display_dream to add pauses:

```python
# In display_dream():
from cli_rpg.text_effects import typewriter_print, pause_medium

for line in dream_text.split("\n"):
    typewriter_print(line, delay=DREAM_TYPEWRITER_DELAY)
pause_medium()  # Pause after dream ends for reflection
```

## Verification

```bash
pytest tests/test_text_effects.py -v
pytest tests/test_combat.py -v
pytest tests/test_dreams.py -v
pytest --cov=src/cli_rpg/text_effects
```
