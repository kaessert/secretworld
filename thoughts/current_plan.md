# Implementation Plan: Log AI-Generated Content for Review

## Summary
Add AI content logging to `GameplayLogger` so AI-generated content (locations, NPCs, dialogue, quests, etc.) can be reviewed from session transcripts.

## Design Approach
**Callback pattern**: Pass an optional `ai_content_logger` callback to `AIService` during initialization. The logger callback is invoked after each successful AI generation, avoiding tight coupling between AIService and GameplayLogger.

## Specification
- New log entry type: `ai_content` with fields:
  - `generation_type`: string (e.g., "location", "npc", "enemy", "quest", "dialogue", "dream", "whisper")
  - `prompt_hash`: string (SHA256 first 16 chars - for deduplication/caching analysis)
  - `content`: parsed object (the actual generated content)
  - `raw_response`: string (optional, full raw LLM response for debugging)
- Logger callback signature: `Callable[[str, str, Any, str], None]` (generation_type, prompt_hash, content, raw_response)
- Only log when logger callback is set (no-op otherwise)

## Files to Modify

### 1. `src/cli_rpg/logging_service.py`
Add method:
```python
def log_ai_content(
    self,
    generation_type: str,
    prompt_hash: str,
    content: Any,
    raw_response: Optional[str] = None
) -> None:
```

### 2. `src/cli_rpg/ai_service.py`
- Add `content_logger` callback param to `__init__`
- Add helper `_log_content(generation_type, prompt, content, raw_response)` that:
  - Computes prompt hash
  - Calls callback if set
- Call `_log_content` in `_call_llm` after successful response (pass through to callers)
- Modify key generation methods to pass parsed content to logger

### 3. `src/cli_rpg/main.py`
- In `run_game_non_interactive()` and `run_game_interactive()`:
  - Create logger callback that wraps `GameplayLogger.log_ai_content`
  - Pass callback to `AIService` constructor when logger is active

## Tests

### `tests/test_ai_content_logging.py`
1. `test_log_ai_content_writes_entry`: Verify `log_ai_content` writes correct JSON structure
2. `test_ai_service_calls_logger_on_generation`: Mock AIService response, verify callback invoked with correct args
3. `test_no_logging_when_callback_not_set`: Verify no errors when callback is None
4. `test_prompt_hash_is_consistent`: Same prompt produces same hash

## Implementation Steps

1. Add `log_ai_content` method to `GameplayLogger`
2. Write tests for `log_ai_content`
3. Add `content_logger` callback to `AIService.__init__`
4. Add `_log_content` helper method to `AIService`
5. Modify `_call_llm` to capture and pass raw response for logging
6. Wire up logger callback in `main.py` entry points
7. Write integration test verifying end-to-end flow
8. Run full test suite
