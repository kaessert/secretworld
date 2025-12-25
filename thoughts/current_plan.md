# Implementation Plan: Improve test coverage for ai_service.py uncovered lines

## Overview
Add tests for 14 uncovered lines in `ai_service.py` to push coverage closer to 100%.

## Target Lines Analysis

| Lines | Description | Testability |
|-------|-------------|-------------|
| 9 | TYPE_CHECKING import of ItemType | Not runtime-reachable; exclude from coverage |
| 18-21 | Anthropic ImportError fallback | Already tested via `test_anthropic_provider_not_available_raises_error` |
| 253-257 | OpenAI RateLimitError retry path | Needs new test |
| 272 | Defensive raise after OpenAI retry loop | Unreachable with normal retry behavior |
| 329 | Defensive raise after Anthropic retry loop | Unreachable with normal retry behavior |
| 443 | _load_cache_from_file early return | Already tested via `test_load_cache_no_cache_file_configured` |
| 475 | _save_cache_to_file early return | Already tested via `test_save_cache_no_cache_file_configured` |

## Tests to Add

### 1. OpenAI RateLimitError Retry Test
**File**: `tests/test_ai_service.py`
**Test name**: `test_openai_rate_limit_error_retries_and_fails`
**Covers**: Lines 253-257

```python
@patch('cli_rpg.ai_service.OpenAI')
def test_openai_rate_limit_error_retries_and_fails(mock_openai_class, basic_config):
    """Test OpenAI rate limit error retries and raises AIServiceError when exhausted."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Simulate rate limit on all attempts
    import openai
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        message="Rate limit exceeded",
        response=Mock(),
        body=None
    )

    service = AIService(basic_config)

    with pytest.raises(AIServiceError, match="API call failed"):
        service.generate_location(theme="fantasy")

    # Should have retried (initial + max_retries attempts)
    assert mock_client.chat.completions.create.call_count == basic_config.max_retries + 1
```

### 2. OpenAI RateLimitError Retry Success Test
**File**: `tests/test_ai_service.py`
**Test name**: `test_openai_rate_limit_error_retries_then_succeeds`
**Covers**: Lines 253-256 (retry path)

```python
@patch('cli_rpg.ai_service.OpenAI')
def test_openai_rate_limit_error_retries_then_succeeds(mock_openai_class, basic_config, mock_openai_response):
    """Test OpenAI rate limit error retries and succeeds on subsequent attempt."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    import openai
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(mock_openai_response)

    # First call rate limited, second succeeds
    mock_client.chat.completions.create.side_effect = [
        openai.RateLimitError(message="Rate limit", response=Mock(), body=None),
        mock_response
    ]

    service = AIService(basic_config)
    result = service.generate_location(theme="fantasy")

    assert result is not None
    assert mock_client.chat.completions.create.call_count == 2
```

## Lines Not Testable

### Line 9: TYPE_CHECKING import
This import only runs during static type checking, not at runtime. Add to coverage exclusion.

### Lines 272, 329: Defensive fallback raises
These are unreachable "should not reach here" fallback lines in the retry loop. The loop will always either:
- Return successfully
- Raise an exception on the final retry attempt

These lines exist for defensive programming but cannot be reached through normal execution. Options:
1. Mark as `# pragma: no cover`
2. Remove them (the raise in the except block already handles the failure case)

**Recommendation**: Add `# pragma: no cover` comment since they serve as defensive coding.

## Implementation Steps

1. Add `test_openai_rate_limit_error_retries_and_fails` test to `tests/test_ai_service.py`
2. Add `test_openai_rate_limit_error_retries_then_succeeds` test to `tests/test_ai_service.py`
3. Add `# pragma: no cover` to line 272 and 329 (defensive fallback raises)
4. (Optional) Add `# type: ignore` comment or coverage exclusion for TYPE_CHECKING block

## Verification
```bash
source venv/bin/activate && pytest tests/test_ai_service.py -v --cov=cli_rpg.ai_service --cov-report=term-missing
```
