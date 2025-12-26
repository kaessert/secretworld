# Implementation Plan: AI-Generated Whispers

## Summary
Implement AI-generated whispers for the Whisper System. The `_generate_ai_whisper()` method is currently stubbed with `NotImplementedError`. This feature adds dynamic, context-aware atmospheric whispers via the AI service.

## Spec
- AI-generated whispers are single-sentence atmospheric text (10-100 characters)
- Context-aware: uses location category and world theme
- Graceful fallback to templates on AI failure (already handled in caller)
- Follows existing AI service patterns (prompt template, response parsing, error handling)

## Implementation Steps

### 1. Add whisper prompt to ai_config.py
**File**: `src/cli_rpg/ai_config.py`
- Add `DEFAULT_WHISPER_GENERATION_PROMPT` constant (similar to dream/lore prompts)
- Add `whisper_generation_prompt` field to `AIConfig` dataclass
- Update `to_dict()` and `from_dict()` methods

### 2. Add generate_whisper() to AIService
**File**: `src/cli_rpg/ai_service.py`
- Add `generate_whisper(theme, location_category)` method
- Build prompt using config template
- Call LLM and validate response (10-100 chars)
- Return whisper string

### 3. Implement _generate_ai_whisper() in whisper.py
**File**: `src/cli_rpg/whisper.py`
- Remove `NotImplementedError`
- Call `self.ai_service.generate_whisper(theme, category)`
- Return generated whisper string

### 4. Write tests
**File**: `tests/test_whisper.py`
- Test AI whisper generation when AI service available
- Test fallback behavior when AI returns short/long text
- Test error handling when AI raises exception

**File**: `tests/test_ai_service.py`
- Test `generate_whisper()` method with mocked LLM
- Test response validation (length checks)

## Test Commands
```bash
pytest tests/test_whisper.py tests/test_ai_service.py -v
pytest --cov=src/cli_rpg -k "whisper"
```
