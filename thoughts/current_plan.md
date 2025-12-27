# Issue 6: Progress Feedback System

## Summary
Add visual progress indicators and thematic loading messages during AI content generation to improve user experience when waiting for AI responses.

## Spec

The progress system should:
1. Display a spinner/progress indicator during AI generation calls
2. Show thematic loading messages appropriate to the generation context (e.g., "Weaving ancient tales..." for lore, "Summoning creatures..." for enemies)
3. Work in both terminal and non-interactive modes (disabled when `--no-color` or `--json` flags are used)
4. Be non-blocking and integrate cleanly with existing AI service flow

## Implementation

### 1. Create `src/cli_rpg/progress.py`

New module with:
- `ProgressIndicator` class using threading for non-blocking spinner
- Thematic message sets by generation type: `LOCATION_MESSAGES`, `NPC_MESSAGES`, `LORE_MESSAGES`, `AREA_MESSAGES`, `ENEMY_MESSAGES`
- Context manager pattern: `with progress_indicator("location"):`
- Graceful disable when effects are disabled (check `text_effects.effects_enabled()`)
- Simple ASCII spinner (no external dependencies): `['|', '/', '-', '\\']`

### 2. Modify `src/cli_rpg/ai_service.py`

Add progress indicator calls in:
- `_call_llm()`: Wrap API call with progress indicator
- Pass generation context type to indicator

### 3. Add Tests in `tests/test_progress.py`

Test cases:
- Spinner thread starts and stops correctly
- Messages cycle through for each generation type
- No output when effects disabled
- Context manager properly cleans up on exception
- Thread safety of start/stop

## Files to Create
- `src/cli_rpg/progress.py`
- `tests/test_progress.py`

## Files to Modify
- `src/cli_rpg/ai_service.py` - Add progress indicator around `_call_llm()` calls

## Notes
- No external dependencies needed - use built-in threading and sys.stdout
- Reuses existing pattern from `text_effects.py` for checking if effects are enabled
- Spinner uses carriage return (`\r`) to overwrite line, not newline
