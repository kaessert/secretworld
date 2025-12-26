# Implementation Plan: AI Generation Retry Before Fallback

## Problem Summary
When AI location generation fails, the game silently falls back to template generation, showing "[AI world generation temporarily unavailable. Using template generation.]". This creates inconsistent world feel when AI locations mix with template locations.

**Current behavior:**
1. `game_state.py:518-543` calls `expand_area()` once
2. On exception, sets `ai_fallback_used = True` and immediately uses `generate_fallback_location()`
3. `ai_service.py:230-285` already has retry logic at the LLM API call level (`_call_openai`/`_call_anthropic`), but...
4. High-level generation functions (`generate_location`, `generate_area`) catch exceptions and bubble them up as single failures

**Problem**: The retry logic in `ai_service.py` only handles transient API errors (timeout, rate limit). It does NOT retry on:
- JSON parsing failures (`AIGenerationError`)
- Validation failures (name too short, missing fields)
- Truncated responses that can't be repaired

## Solution Design

Add retry logic at the **location generation level** (not API call level), with configurable retry count. This allows:
1. Second attempt with the same prompt (may succeed if first was unlucky truncation)
2. Different AI response on each retry (probabilistic success)
3. User visibility into retry attempts

## Implementation Steps

### 1. Add retry configuration to AIConfig (`ai_config.py`)
- Add `generation_max_retries: int = 2` field (separate from API `max_retries`)
- This controls retries at generation level, not API call level
- Default: 2 retries = 3 total attempts before fallback

### 2. Add retry wrapper to AIService (`ai_service.py`)
- Create `_generate_with_retry()` method that wraps generation methods
- On `AIGenerationError` (parse/validation), retry up to `generation_max_retries`
- Log each retry attempt at DEBUG level
- Return final exception if all retries fail

### 3. Update location generation methods to use retry wrapper
- `generate_location()` → wrap LLM call + parse in retry logic
- `generate_area()` → wrap LLM call + parse in retry logic
- `generate_location_with_context()` → wrap LLM call + parse in retry logic

### 4. Update game_state.py move() to retry AI generation
- Before setting `ai_fallback_used = True`, retry `expand_area()` call
- Use `AIConfig.generation_max_retries` for retry count
- Log retry attempts and final failure reason

### 5. Add tests for retry behavior
- Test that generation retries on `AIGenerationError`
- Test that retries are limited to `generation_max_retries`
- Test that API-level retries still work for transient errors
- Test that fallback still works after all retries exhausted

## Files to Modify

1. `src/cli_rpg/ai_config.py`:
   - Add `generation_max_retries: int = 2` field
   - Add to `to_dict()` / `from_dict()` serialization

2. `src/cli_rpg/ai_service.py`:
   - Add `_generate_with_retry()` wrapper method
   - Update `generate_location()`, `generate_area()`, `generate_location_with_context()` to use retry wrapper

3. `src/cli_rpg/game_state.py`:
   - No changes needed - retries happen inside AIService

4. `tests/test_ai_service.py`:
   - Add test for retry on AIGenerationError
   - Add test for retry count limit
   - Add test for successful retry after initial failure

## Test Plan

```python
# Test: Retry on parse failure
def test_generate_location_retries_on_parse_failure(mock_ai_service):
    """First call returns invalid JSON, second returns valid."""
    mock_ai_service.client.chat.completions.create.side_effect = [
        Mock(choices=[Mock(message=Mock(content="invalid json"))]),
        Mock(choices=[Mock(message=Mock(content='{"name": "Test", ...}'))])
    ]
    result = mock_ai_service.generate_location(theme="fantasy")
    assert result["name"] == "Test"
    assert mock_ai_service.client.chat.completions.create.call_count == 2

# Test: Retry limit respected
def test_generate_location_respects_retry_limit(mock_ai_service):
    """All retries fail, should raise AIGenerationError."""
    mock_ai_service.config.generation_max_retries = 2
    mock_ai_service.client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="invalid json"))]
    )
    with pytest.raises(AIGenerationError):
        mock_ai_service.generate_location(theme="fantasy")
    assert mock_ai_service.client.chat.completions.create.call_count == 3  # 1 + 2 retries
```

## Implementation Notes

- Retry only on `AIGenerationError` (parse/validation failures)
- Do NOT retry on `AIServiceError` (API failures) - those already have API-level retries
- Add exponential backoff between retries (0.5s, 1s) to avoid rate limiting
- Log full response on final failure for debugging

## Scope Boundaries

**In scope:**
- Retry logic for location/area generation parse failures
- Configuration for retry count
- Logging of retry attempts

**Out of scope:**
- Changing the fallback behavior (still falls back after all retries)
- User prompting on failure (would break non-interactive mode)
- Retry for other generation types (enemies, items, quests) - can add later
