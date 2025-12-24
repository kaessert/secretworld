# Implementation Plan: Fix AI Generation Failure Handling

## Problem Analysis

**Root Cause Identified**: The game has intentional silent fallback behavior in `world.py:create_world()` (lines 120-134):
- When AI service is provided but generation fails, it catches ALL exceptions and silently falls back to the default world
- This masks AI configuration issues, API failures, and other problems
- Players get the default "Town Square/Forest/Cave" world without knowing AI generation failed

**Issue Chain**:
1. `main.py:636-648` - Loads AI config, creates AIService if key exists, prints "AI world generation enabled!"
2. `main.py:574` - Calls `create_world(ai_service=ai_service, theme=theme)`
3. `world.py:120-130` - If AI fails for ANY reason, silently returns `create_default_world()`
4. Player sees default world with no indication that AI failed

## Spec

1. **When AI service is configured and provided, AI generation failures must raise an exception** (no silent fallback)
2. **The caller (`main.py`) should handle the exception** and display a clear error to the user
3. **Add a configuration option** `CLI_RPG_REQUIRE_AI=true/false` to control strict vs. fallback mode (default: strict when AI service is provided)
4. **Existing tests that expect fallback behavior must be updated** to reflect the new strict-by-default behavior

## Implementation Steps

### Step 1: Add Strict Mode Configuration
**File**: `src/cli_rpg/config.py`
- Add `is_ai_strict_mode() -> bool` function
- Returns `True` if `CLI_RPG_REQUIRE_AI` env var is not set or is "true"
- Returns `False` only if explicitly set to "false"

### Step 2: Modify create_world() to Fail Hard by Default
**File**: `src/cli_rpg/world.py`
- Add `strict: bool = True` parameter to `create_world()`
- When `strict=True` and `ai_service` is provided: let exceptions propagate (no try/except)
- When `strict=False`: keep existing fallback behavior for backward compatibility
- Log clearly when AI fails and fallback is used (only in non-strict mode)

### Step 3: Update main.py to Handle AI Failures
**File**: `src/cli_rpg/main.py`
- In `main()`: read strict mode from config
- In `start_game()`: add `strict` parameter, pass to `create_world()`
- Catch `AIServiceError` and subclasses, display clear error message
- Offer user options: retry, use default world, or exit

### Step 4: Update Tests
**File**: `tests/test_world.py`
- Update `test_create_world_falls_back_on_ai_error` to test strict vs. non-strict modes
- Add test for strict mode raising exception on AI failure
- Add test for non-strict mode falling back gracefully

**File**: `tests/test_main.py` (or create new test file)
- Add integration test for AI failure handling in main()
- Test user-facing error messages

### Step 5: Update Tests in test_ai_world_generation.py
- Review and update any tests that assume silent fallback
- Ensure `create_world_with_fallback` tests still pass (it's documented to raise)

## Test Plan

1. **Unit test**: `create_world(ai_service, strict=True)` raises exception on AI failure
2. **Unit test**: `create_world(ai_service, strict=False)` falls back to default on AI failure
3. **Unit test**: `is_ai_strict_mode()` returns correct values based on env var
4. **Integration test**: `start_game()` displays error when AI fails in strict mode
5. **Verify**: All 723 existing tests still pass

## Files to Modify

1. `src/cli_rpg/config.py` - Add `is_ai_strict_mode()` function
2. `src/cli_rpg/world.py` - Add `strict` parameter to `create_world()`
3. `src/cli_rpg/main.py` - Handle AI failures gracefully with user feedback
4. `tests/test_world.py` - Update fallback test, add strict mode tests
5. `tests/test_config.py` - Add tests for `is_ai_strict_mode()`
