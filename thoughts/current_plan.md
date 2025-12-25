# Implementation Plan: Improve AI Module Test Coverage

## Goal
Increase test coverage for `ai_service.py` (85%→92%+) and `ai_world.py` (85%→92%+) by adding edge case tests for uncovered code paths.

## Analysis of Missing Coverage

### ai_service.py (lines 278-306, 1361-1382, 1409-1422, etc.)
- **Lines 15-18, 69**: Anthropic import failure and initialization when unavailable
- **Lines 278-306**: `_call_anthropic()` retry/error handling paths (timeout, rate limit, auth errors)
- **Lines 1361-1382**: `generate_conversation_response()` method
- **Lines 1409-1422**: `_build_conversation_prompt()` method (conversation history formatting)

### ai_world.py (lines 142-186, 343-518)
- **Lines 142-186**: Error handling in `create_ai_world()` (skip non-grid directions, duplicate names)
- **Lines 343-518**: `expand_area()` function (area generation with coordinate placement)

---

## Implementation Steps

### 1. Add Anthropic provider edge case tests (tests/test_ai_service.py)

Add tests for:
- `test_anthropic_timeout_error_raises_ai_timeout_error` - Anthropic API timeout handling
- `test_anthropic_rate_limit_error_retries_and_fails` - Rate limit with retry exhaustion
- `test_anthropic_auth_error_raises_immediately` - Auth error (no retry)
- `test_anthropic_provider_not_available_raises_error` - Anthropic package not installed

### 2. Add conversation response tests (tests/test_ai_conversations.py)

Add tests for:
- `test_generate_conversation_response_success` - Basic successful conversation
- `test_generate_conversation_response_with_history` - Includes formatted history
- `test_generate_conversation_response_too_short_raises_error` - Response validation
- `test_generate_conversation_response_truncates_long_response` - 200 char limit

### 3. Add expand_area tests (tests/test_ai_world_generation.py)

Add tests for:
- `test_expand_area_generates_area_cluster` - Basic area generation
- `test_expand_area_places_locations_at_correct_coordinates` - Coordinate validation
- `test_expand_area_connects_entry_to_source` - Bidirectional connection check
- `test_expand_area_fallback_to_single_location_on_empty_response` - Fallback behavior
- `test_expand_area_skips_occupied_coordinates` - Collision handling
- `test_expand_area_skips_duplicate_names` - Name collision handling

### 4. Add create_ai_world edge case tests (tests/test_ai_world_generation.py)

Add tests for:
- `test_create_ai_world_skips_non_grid_direction` - Filters non-cardinal directions
- `test_create_ai_world_handles_generation_failure_in_expansion` - Exception handling in loop

---

## Test Verification

After implementation, run:
```bash
pytest tests/test_ai_service.py tests/test_ai_world_generation.py tests/test_ai_conversations.py -v --cov=src/cli_rpg/ai_service --cov=src/cli_rpg/ai_world --cov-report=term-missing
```

Target: Both modules at 92%+ coverage (up from 85%).
