# Implementation Plan: Support Anthropic API Key

## Spec

Add Anthropic as an alternative AI provider alongside OpenAI. Users can set `ANTHROPIC_API_KEY` to use Claude for world generation instead of OpenAI.

**Behavior**:
- If both `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are set, prefer Anthropic
- `AI_PROVIDER` environment variable can explicitly select: `anthropic` or `openai`
- Config stores the provider type so service knows which client to use
- Maintain all existing OpenAI functionality unchanged when no Anthropic key is present

## Tests (write first)

**`tests/test_ai_config.py`** - Add:
1. `test_ai_config_from_env_with_anthropic_key` - detects `ANTHROPIC_API_KEY`, sets provider to "anthropic"
2. `test_ai_config_from_env_prefers_anthropic_over_openai` - when both keys set, defaults to anthropic
3. `test_ai_config_from_env_explicit_provider_selection` - `AI_PROVIDER=openai` overrides preference
4. `test_ai_config_from_env_no_api_key_raises_error` - neither key set raises AIConfigError

**`tests/test_ai_service.py`** - Add:
5. `test_ai_service_initialization_with_anthropic` - creates Anthropic client when provider is "anthropic"
6. `test_generate_location_with_anthropic` - calls Anthropic API correctly, returns valid location

## Implementation Steps

### 1. Modify `ai_config.py`

- Add `provider: str` field to `AIConfig` dataclass (default: "openai")
- Update `from_env()`:
  - Check for `ANTHROPIC_API_KEY` environment variable
  - Check for `AI_PROVIDER` environment variable for explicit selection
  - Logic: If `AI_PROVIDER` is set, use that. Otherwise, prefer Anthropic if key exists, else OpenAI
  - Raise `AIConfigError` if neither key is available
  - Set appropriate default model: `claude-3-5-sonnet-latest` for anthropic, `gpt-3.5-turbo` for openai
- Update `to_dict()` and `from_dict()` to include provider

### 2. Modify `ai_service.py`

- Add `import anthropic` at top (conditionally import to handle missing package)
- Modify `__init__()`:
  - Check `config.provider` to decide which client to instantiate
  - Store `self.provider = config.provider`
- Modify `_call_llm()`:
  - If provider is "anthropic", call `self.client.messages.create()` with appropriate format
  - If provider is "openai", keep existing logic
  - Handle Anthropic-specific exceptions (map to existing error types)

### 3. Update `config.py`

- Modify `load_ai_config()` log message to include which provider is active

### 4. Add `anthropic` dependency

- Add to `pyproject.toml` (verify package manager used)
