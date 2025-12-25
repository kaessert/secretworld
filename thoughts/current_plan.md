# Fix: test_generate_quest_uses_context failing due to caching

## Problem
The test `test_ai_quest_generation.py::TestAIServiceGenerateQuest::test_generate_quest_uses_context` fails because `call_args` is `None` - the mock's `chat.completions.create` method is never called.

**Root cause**: `AIConfig` defaults to `enable_caching=True`. The `generate_quest()` method checks cache before calling the LLM. If a cached result exists (from persistent file cache at `~/.cli_rpg/cache/ai_cache.json` or from a prior test), the mock is bypassed.

## Fix
Update the `basic_config` fixture to disable caching explicitly:

**File**: `tests/test_ai_quest_generation.py`, lines 21-30

```python
@pytest.fixture
def basic_config():
    """Create a basic AIConfig for testing."""
    return AIConfig(
        api_key="test-key-123",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
        max_retries=3,
        retry_delay=0.1,  # Short delay for tests
        enable_caching=False  # Disable caching to ensure mock is called
    )
```

## Verification
Run the failing test:
```bash
pytest tests/test_ai_quest_generation.py::TestAIServiceGenerateQuest::test_generate_quest_uses_context -v
```

Then run all AI quest generation tests to ensure no regressions:
```bash
pytest tests/test_ai_quest_generation.py -v
```
