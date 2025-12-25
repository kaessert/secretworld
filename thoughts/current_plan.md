# Fix: Silent fallback masks AI generation failures

## Problem
When AI area generation fails in `game_state.py` (lines 337-340), it silently falls back to template-based generation via `generate_fallback_location()`. Players should be informed when AI generation fails.

## Implementation

### 1. Modify `game_state.py` (lines 337-361)
Replace silent fallback with user notification:

**Before (lines 337-340):**
```python
except Exception as e:
    # Log error for debugging but don't expose to player
    logger.warning(f"AI area generation failed, using fallback: {e}")
    # Fall through to fallback generation below
```

**After:**
```python
except Exception as e:
    logger.warning(f"AI area generation failed: {e}")
    # Inform player and still use fallback for gameplay continuity
    # The message will be prepended to the move result
    ai_failed = True
```

Then modify the success path to return an informative message when `ai_failed` is True.

**Key changes:**
- Add `ai_failed = False` flag at the start of the else block (line 317)
- Set `ai_failed = True` in the exception handler
- After fallback generation succeeds, return a message indicating AI failed but fallback was used
- Return format: `(True, "AI world generation temporarily unavailable. Using template generation.")`

### 2. Test: `tests/test_game_state.py`
Add test `test_move_informs_player_when_ai_fails`:
```python
def test_move_informs_player_when_ai_fails(self):
    """Test that player is informed when AI generation fails during move.

    Spec: When AI area generation fails, player should see a message
    indicating fallback was used, not silent fallback.
    """
    # Setup: GameState with AI service that raises exception
    # Mock expand_area to raise AIGenerationError
    # Call move() in a direction requiring generation
    # Assert: success is True, message contains fallback notification
```

### 3. Optional enhancement: Add `warning()` helper to `colors.py`
```python
def warning(text: str) -> str:
    """Color text as a warning (yellow)."""
    return colorize(text, YELLOW)
```

## Files to modify
1. `src/cli_rpg/game_state.py` - Remove silent fallback, add player notification
2. `tests/test_game_state.py` - Add test for AI failure notification
3. `src/cli_rpg/colors.py` - Optional: add warning() helper

## Verification
```bash
pytest tests/test_game_state.py -v -k "ai_fails"
pytest tests/test_game_state.py -v
pytest --cov=src/cli_rpg
```
