# Implementation Summary: AI-Generated Dreams

## What Was Implemented

Added AI-generated dreams to the existing dream system. When a dream triggers during rest (25% chance), the system now attempts AI generation first with graceful fallback to existing template dreams.

### Files Modified

1. **`src/cli_rpg/ai_config.py`**
   - Added `DEFAULT_DREAM_GENERATION_PROMPT` constant (lines 245-262)
   - Added `dream_generation_prompt` field to `AIConfig` dataclass (line 328)
   - Updated `to_dict()` to include the new field (line 483)
   - Updated `from_dict()` to restore the field (lines 527-529)

2. **`src/cli_rpg/ai_service.py`**
   - Added `generate_dream()` method (lines 1857-1900) that:
     - Takes theme, dread level, choices, location name, and is_nightmare flag
     - Calls LLM with contextual prompt
     - Validates response (20-300 chars)
     - Raises `AIGenerationError` if validation fails
   - Added `_build_dream_prompt()` helper (lines 1902-1944) that:
     - Summarizes player choices (flee/kill counts)
     - Determines dream type based on nightmare flag

3. **`src/cli_rpg/dreams.py`**
   - Updated imports to include logging and TYPE_CHECKING (lines 7-19)
   - Extended `maybe_trigger_dream()` signature to accept `ai_service` and `location_name` parameters
   - Added AI generation path that tries AI first and falls back to templates on any error (lines 89-108)

4. **`src/cli_rpg/main.py`**
   - Updated the rest command to pass `ai_service` and `location_name` to `maybe_trigger_dream()` (lines 1284-1286)

5. **`tests/test_dreams.py`**
   - Added `TestAIDreamGeneration` class with 9 tests:
     - `test_generate_dream_exists_in_ai_service` - Verifies method exists
     - `test_dream_generation_prompt_in_config` - Verifies config field exists
     - `test_maybe_trigger_dream_uses_ai_when_available` - AI called when service provided
     - `test_maybe_trigger_dream_falls_back_on_ai_failure` - Fallback on error
     - `test_maybe_trigger_dream_uses_templates_without_ai` - Templates used without AI
     - `test_ai_dream_content_is_validated` - Length validation (20-300 chars)
     - `test_ai_nightmare_at_high_dread` - is_nightmare=True at 50%+ dread
     - `test_ai_dream_prompt_includes_context` - Prompt has theme/location
     - `test_ai_config_dream_prompt_serialization` - to_dict/from_dict works

## Test Results

All tests pass:
- **32 dream tests** passed (including 9 new AI dream tests)
- **77 AI config/service tests** passed
- **5 main module tests** passed

## Key Design Decisions

1. **Graceful Fallback**: AI failures (any exception) silently fall back to template dreams, ensuring the game continues smoothly.

2. **Context-Aware**: Dreams are personalized based on:
   - World theme
   - Dread level (0-100%)
   - Player choices (flee/kill counts)
   - Current location name
   - Whether it's a nightmare (dread >= 50)

3. **Backward Compatible**: When `ai_service=None`, behavior is identical to before - template dreams are used.

4. **Validation**: AI-generated dreams must be 20-300 characters. Too short raises an error (triggers fallback), too long is truncated.

## E2E Test Validation

The implementation should be tested end-to-end by:
1. Starting the game with AI enabled (set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
2. Playing until rest is needed
3. Using the `rest` command repeatedly (or with dread at various levels)
4. Verifying AI-generated dreams appear (they'll be unique and context-aware)
5. Disabling AI and confirming template dreams still work
