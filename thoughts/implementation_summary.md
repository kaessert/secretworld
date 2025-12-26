# Implementation Summary: AI Generation Retry Before Fallback

## What Was Implemented

### 1. New Configuration Field: `generation_max_retries` (AIConfig)

Added a new configuration field `generation_max_retries` (default: 2) to `AIConfig` that controls retry behavior at the generation/parsing level. This is separate from `max_retries` which handles API-level retries.

**Files Modified:**
- `src/cli_rpg/ai_config.py`:
  - Added `generation_max_retries: int = 2` field to the dataclass
  - Added validation in `__post_init__` to ensure non-negative value
  - Added to `to_dict()` serialization
  - Added to `from_dict()` deserialization with default value
  - Added `AI_GENERATION_MAX_RETRIES` environment variable support in `from_env()`
  - Updated docstrings

### 2. Retry Wrapper Method: `_generate_with_retry()` (AIService)

Added a new method `_generate_with_retry(generation_func, *args, **kwargs)` that:
- Wraps generation functions and retries on `AIGenerationError` (parse/validation failures)
- Does NOT retry on `AIServiceError` or `AITimeoutError` (API failures already have their own retry)
- Uses exponential backoff: 0.5s, 1s, 2s, etc. between retries
- Logs retry attempts at DEBUG level
- Logs final failure at WARNING level

**Files Modified:**
- `src/cli_rpg/ai_service.py`:
  - Added `Callable` import from typing
  - Added `_generate_with_retry()` method after `_call_anthropic()`

### 3. Updated Generation Methods to Use Retry Wrapper

Three key location generation methods now use the retry wrapper:

1. **`generate_location()`** - Single location generation
2. **`generate_area()`** - Area/cluster generation
3. **`generate_location_with_context()`** - Layered generation (Layer 3)

Each method now defines an inner `_do_generate()` function that performs the LLM call + parsing, then wraps it with `_generate_with_retry()`.

**Design Decision:** Caching logic remains outside the retry loop, so only successful results are cached.

### 4. New Tests for Retry Behavior

Added 9 new tests to `tests/test_ai_service.py`:

| Test | Description |
|------|-------------|
| `test_generate_location_retries_on_parse_failure` | First call returns invalid JSON, second succeeds |
| `test_generate_location_respects_retry_limit` | All retries fail, verifies correct attempt count |
| `test_generate_location_does_not_retry_api_errors` | Verifies API errors pass through without generation retry |
| `test_generate_area_retries_on_parse_failure` | Area generation also retries on parse failures |
| `test_generate_location_with_context_retries_on_parse_failure` | Layer 3 generation retries |
| `test_generation_max_retries_zero_disables_retry` | Setting to 0 disables retry |
| `test_generate_location_retries_on_validation_failure` | Retries when name too short |
| `test_ai_config_generation_max_retries_serialization` | Config field serializes correctly |
| `test_ai_config_generation_max_retries_from_env` | Environment variable works |

## Test Results

- All 94 tests in `test_ai_service.py` pass
- All 25 tests in `test_ai_config.py` pass
- Full test suite: 3417 tests pass

## Technical Details

### Retry Behavior

```python
# Default configuration
generation_max_retries = 2  # = 3 total attempts (1 initial + 2 retries)

# Retry delays (exponential backoff)
# Attempt 1: immediate
# Attempt 2: 0.5s delay
# Attempt 3: 1.0s delay
```

### Error Handling

- **`AIGenerationError`**: Retried up to `generation_max_retries` times
  - JSON parse failures
  - Validation failures (name too short, missing fields, etc.)
  - Truncated responses that can't be repaired

- **`AIServiceError`**: NOT retried at generation level
  - Already has API-level retries via `max_retries`
  - Authentication failures
  - Rate limits

- **`AITimeoutError`**: NOT retried at generation level
  - Already has API-level retries via `max_retries`

### Configuration

```bash
# Environment variable
export AI_GENERATION_MAX_RETRIES=3

# Programmatic
config = AIConfig(
    api_key="...",
    generation_max_retries=3
)
```

## E2E Testing Notes

When testing the retry feature end-to-end:
1. Set up logging at DEBUG level to see retry attempts
2. Use a low `generation_max_retries` value (like 1) to test faster
3. Consider mocking the AI response to force parse failures
4. Verify that fallback behavior still works after all retries are exhausted

## What This Fixes

Previously, when AI generation failed (e.g., truncated JSON, validation failure), the game would immediately fall back to template generation, showing "[AI world generation temporarily unavailable. Using template generation.]".

Now, the system will retry the AI request up to `generation_max_retries` times before falling back, significantly reducing the chance of mixing AI-generated and template content.
