# Implementation Plan: Ollama Local Model Support

## Overview
Add Ollama as a third AI provider option alongside OpenAI and Anthropic, allowing users to run the game with AI features using local models without external API keys or costs.

## Spec

Ollama is a local LLM runner that exposes an OpenAI-compatible API at `http://localhost:11434/v1`. The integration will:

1. Add `"ollama"` as a valid provider option
2. Use the OpenAI client library pointed at the local Ollama endpoint (API-compatible)
3. Allow configuration via environment variables:
   - `AI_PROVIDER=ollama` - Select Ollama as provider
   - `OLLAMA_BASE_URL` - Custom Ollama endpoint (default: `http://localhost:11434/v1`)
   - `OLLAMA_MODEL` - Model to use (default: `llama3.2`)
4. Ollama requires no API key (use placeholder value for OpenAI client)
5. Handle Ollama-specific connection errors gracefully (service not running)

## Tests (TDD)

### File: `tests/test_ai_ollama.py`

```python
# Test cases to implement:

1. test_ai_config_from_env_with_ollama_provider
   - Set AI_PROVIDER=ollama
   - Verify config.provider == "ollama"
   - Verify config.api_key is set to placeholder "ollama"
   - Verify default model is "llama3.2"

2. test_ai_config_from_env_ollama_with_custom_base_url
   - Set OLLAMA_BASE_URL=http://custom:8080/v1
   - Verify config.ollama_base_url is set correctly

3. test_ai_config_from_env_ollama_with_custom_model
   - Set OLLAMA_MODEL=mistral
   - Verify config.model == "mistral"

4. test_ai_service_initialization_with_ollama
   - Create config with provider="ollama"
   - Verify AIService creates OpenAI client with custom base_url
   - Verify service.provider == "ollama"

5. test_generate_location_with_ollama
   - Mock OpenAI client for Ollama
   - Verify generate_location works and returns valid structure

6. test_ollama_connection_error_raises_service_error
   - Simulate connection refused (Ollama not running)
   - Verify AIServiceError is raised with helpful message

7. test_ai_config_serialization_with_ollama
   - Create config with provider="ollama" and custom base_url
   - Verify to_dict() includes ollama_base_url
   - Verify from_dict() restores ollama_base_url
```

## Implementation Steps

### Step 1: Update `ai_config.py`

1. Add `ollama_base_url` field to AIConfig dataclass:
   ```python
   ollama_base_url: Optional[str] = None
   ```

2. Update `from_env()` to handle Ollama provider:
   - Check for `AI_PROVIDER=ollama`
   - Read `OLLAMA_BASE_URL` (default: `http://localhost:11434/v1`)
   - Read `OLLAMA_MODEL` for custom model (default: `llama3.2`)
   - Set api_key to `"ollama"` placeholder (Ollama doesn't require auth)

3. Update `to_dict()` to include `ollama_base_url`

4. Update `from_dict()` to restore `ollama_base_url`

5. Update `__post_init__()` validation:
   - Skip API key validation when provider is "ollama" (allow placeholder)

### Step 2: Update `ai_service.py`

1. Add Ollama client initialization in `__init__`:
   ```python
   elif self.provider == "ollama":
       self.client = OpenAI(
           api_key=config.api_key,  # placeholder
           base_url=config.ollama_base_url or "http://localhost:11434/v1"
       )
   ```

2. Add `_call_ollama()` method (delegates to `_call_openai()` since API is compatible)

3. Update `_call_llm()` to route "ollama" to `_call_openai()` (they're compatible)

4. Handle Ollama-specific connection errors:
   - Catch `openai.APIConnectionError` in retry logic
   - Provide helpful message about Ollama not running

### Step 3: Update `.env.example`

Add Ollama configuration section:
```bash
# Ollama (Local AI) Configuration
# Set AI_PROVIDER=ollama to use local Ollama
# OLLAMA_BASE_URL=http://localhost:11434/v1
# OLLAMA_MODEL=llama3.2
```

### Step 4: Update `docs/AI_FEATURES.md`

Add Ollama setup section under "Setup":
- Prerequisites: Install Ollama, pull a model
- Configuration examples
- Note about no API key required
- Troubleshooting for "Ollama not running" error

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_config.py` | Add `ollama_base_url` field, update `from_env()`, `to_dict()`, `from_dict()`, relax API key validation for ollama |
| `src/cli_rpg/ai_service.py` | Add Ollama client initialization, route to OpenAI-compatible calls |
| `tests/test_ai_ollama.py` | New file with 7 test cases |
| `.env.example` | Add Ollama configuration section |
| `docs/AI_FEATURES.md` | Add Ollama setup and troubleshooting documentation |

## Verification

1. Run new tests: `pytest tests/test_ai_ollama.py -v`
2. Run full test suite: `pytest`
3. Verify coverage maintained: `pytest --cov=src/cli_rpg`
4. Manual test (if Ollama installed): Run game with `AI_PROVIDER=ollama`
