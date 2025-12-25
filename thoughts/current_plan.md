# Fix AI Area Generation JSON Truncation - Step 1: Increase max_tokens

## Spec
Increase `max_tokens` default from 500 to 2000 to prevent JSON truncation during AI area generation. Area generation (5-7 locations with NPCs) can require 1500-2000+ tokens.

## Changes

### 1. `src/cli_rpg/ai_config.py`

**Line 270 (docstring):** Change "default: 500" to "default: 2000"
```python
# Before:
max_tokens: Maximum response length (default: 500)

# After:
max_tokens: Maximum response length (default: 2000)
```

**Line 284 (dataclass field):** Change default value
```python
# Before:
max_tokens: int = 500

# After:
max_tokens: int = 2000
```

**Line 406 (env var default):** Change fallback in `from_env()`
```python
# Before:
max_tokens = int(os.getenv("AI_MAX_TOKENS", "500"))

# After:
max_tokens = int(os.getenv("AI_MAX_TOKENS", "2000"))
```

**Line 475 (from_dict default):** Change fallback value
```python
# Before:
max_tokens=data.get("max_tokens", 500),

# After:
max_tokens=data.get("max_tokens", 2000),
```

### 2. `tests/test_ai_config.py`

Update tests that assert `max_tokens == 500` to assert `max_tokens == 2000`:

**Line 54:** `test_ai_config_defaults`
```python
assert config.max_tokens == 2000  # Default (was 500)
```

**Line 202:** `test_ai_config_from_dict_with_defaults`
```python
assert config.max_tokens == 2000  # Default (was 500)
```

## Verification
```bash
pytest tests/test_ai_config.py -v
```
