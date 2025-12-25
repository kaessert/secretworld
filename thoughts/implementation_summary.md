# Implementation Summary: Increase max_tokens Default

## What Was Implemented

Increased the default `max_tokens` value from 500 to 2000 in the AI configuration to prevent JSON truncation during AI area generation (5-7 locations with NPCs can require 1500-2000+ tokens).

## Files Modified

### 1. `src/cli_rpg/ai_config.py`
- **Line 270**: Updated docstring default value documentation
- **Line 284**: Changed dataclass field default from `max_tokens: int = 500` to `max_tokens: int = 2000`
- **Line 406**: Updated `from_env()` fallback from `"500"` to `"2000"`
- **Line 475**: Updated `from_dict()` fallback from `500` to `2000`

### 2. `tests/test_ai_config.py`
- **Line 54** (`test_ai_config_defaults`): Updated assertion to expect `max_tokens == 2000`
- **Line 202** (`test_ai_config_from_dict_with_defaults`): Updated assertion to expect `max_tokens == 2000`

## Test Results

All 20 tests in `tests/test_ai_config.py` pass:
```
============================== 20 passed in 0.55s ==============================
```

## Design Notes

- Users can still override via `AI_MAX_TOKENS` environment variable
- Explicit parameter values are unaffected
- Serialization/deserialization round-trips are preserved
