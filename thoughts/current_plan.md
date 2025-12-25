# Implementation Plan: AI-Generated Dreams

## Spec

Add AI-generated dreams to the existing dream system in `dreams.py`. When a dream triggers (25% on rest), attempt AI generation first with graceful fallback to existing template dreams.

**Behavior:**
1. On dream trigger, if `ai_service` is available, call `generate_dream()`
2. Dream content is personalized based on: theme, dread level, player choices, current location
3. If AI fails or is unavailable, fall back to existing template pools (prophetic/atmospheric/choice/nightmare)
4. Generated dreams follow same length/format constraints as templates

## Tests First (TDD)

Add tests to `tests/test_dreams.py`:

### Test 1: AI dream generation method exists
```python
def test_generate_dream_exists_in_ai_service():
    """AIService has generate_dream method."""
```

### Test 2: AI dream prompt configuration
```python
def test_dream_generation_prompt_in_config():
    """AIConfig has dream_generation_prompt field."""
```

### Test 3: AI dream called when service available
```python
def test_maybe_trigger_dream_uses_ai_when_available():
    """When ai_service is passed, attempts AI generation."""
```

### Test 4: Fallback when AI fails
```python
def test_maybe_trigger_dream_falls_back_on_ai_failure():
    """Falls back to template when AI raises exception."""
```

### Test 5: Fallback when no AI service
```python
def test_maybe_trigger_dream_uses_templates_without_ai():
    """Uses templates when ai_service is None (current behavior)."""
```

### Test 6: Dream content validation
```python
def test_ai_dream_content_is_validated():
    """AI-generated dream text is validated (length 20-300 chars)."""
```

### Test 7: Nightmare AI generation at high dread
```python
def test_ai_nightmare_at_high_dread():
    """AI generates nightmare-style content at 50%+ dread."""
```

## Implementation Steps

### Step 1: Add dream generation prompt to `ai_config.py`
- Add `DEFAULT_DREAM_GENERATION_PROMPT` constant
- Add `dream_generation_prompt` field to `AIConfig` dataclass
- Update `to_dict()` and `from_dict()` methods

### Step 2: Add `generate_dream()` to `ai_service.py`
- Add method signature: `generate_dream(theme, dread, choices, location_name, is_nightmare) -> str`
- Build prompt with context (dread level, choice history, location)
- Call LLM and validate response (20-300 chars, no JSON needed)
- Raise `AIGenerationError` if validation fails

### Step 3: Update `maybe_trigger_dream()` in `dreams.py`
- Add optional `ai_service` parameter (default None)
- Add optional `location_name` parameter for context
- If `ai_service` is provided, try AI generation first
- Catch exceptions and fall back to template selection
- Maintain existing template path when AI unavailable

### Step 4: Update rest command integration in `main.py`
- Pass `ai_service` to `maybe_trigger_dream()` when available
- Pass current location name for context

## Files to Modify

1. `src/cli_rpg/ai_config.py` - Add prompt template and config field
2. `src/cli_rpg/ai_service.py` - Add `generate_dream()` method
3. `src/cli_rpg/dreams.py` - Update `maybe_trigger_dream()` signature and logic
4. `src/cli_rpg/main.py` - Pass ai_service to dream trigger in rest handler
5. `tests/test_dreams.py` - Add AI dream tests
