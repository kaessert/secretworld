# Issue 7: LLM Streaming Support

## Spec

Add streaming support to `AIService` for live text display during AI generation. When streaming is enabled, display generated text character-by-character as it arrives from the LLM, replacing the spinner-based progress indicator with real-time content reveal.

**Behavior:**
- When `stream=True` is passed to generation methods (or enabled via config), stream tokens directly to stdout
- Use typewriter effect (`text_effects.py`) for displaying streamed content
- Fall back to non-streaming behavior when streaming is disabled or for JSON-structured responses
- Streaming only applies to free-form text generation (dialogue, lore, dreams, whispers, ASCII art) - NOT to JSON responses that require parsing

**Scope:**
- Primary file: `src/cli_rpg/ai_service.py`
- Secondary files: `src/cli_rpg/ai_config.py` (add `enable_streaming` config option)

## Tests

Create `tests/test_ai_streaming.py`:

1. **Test streaming config option**: Verify `AIConfig.enable_streaming` defaults to `False`
2. **Test OpenAI streaming call**: Mock `stream=True` in `client.chat.completions.create()`, verify chunks are yielded
3. **Test Anthropic streaming call**: Mock streaming with `with client.messages.stream()`, verify chunks are yielded
4. **Test Ollama streaming call**: Verify Ollama uses OpenAI-compatible streaming interface
5. **Test streaming disabled for JSON methods**: Verify `generate_location`, `generate_area`, `generate_quest` never use streaming (they need full JSON response for parsing)
6. **Test streaming enabled for text methods**: Verify `generate_dialogue`, `generate_lore`, `generate_dream`, `generate_whisper` can stream
7. **Test streaming respects `effects_enabled()`**: No output when effects disabled (--no-color, --json modes)
8. **Test streaming fallback on error**: If streaming fails, fall back to non-streaming call

## Implementation Steps

### Step 1: Add config option
In `src/cli_rpg/ai_config.py`:
- Add `enable_streaming: bool = False` field to `AIConfig` dataclass
- Add `AI_ENABLE_STREAMING` environment variable support in `from_env()`
- Include in `to_dict()` and `from_dict()` serialization

### Step 2: Add streaming LLM methods
In `src/cli_rpg/ai_service.py`:

Add `_call_llm_streaming()` method:
```python
def _call_llm_streaming(self, prompt: str, output: TextIO = sys.stdout) -> str:
    """Call LLM with streaming, printing tokens as they arrive.

    Returns the complete response text after streaming completes.
    """
```

Add `_call_openai_streaming()` method:
```python
def _call_openai_streaming(self, prompt: str, output: TextIO, is_ollama: bool = False) -> str:
    response = self.client.chat.completions.create(
        model=self.config.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=self.config.temperature,
        max_tokens=self.config.max_tokens,
        stream=True  # Enable streaming
    )
    full_text = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            output.write(token)
            output.flush()
            full_text += token
    output.write("\n")
    return full_text
```

Add `_call_anthropic_streaming()` method:
```python
def _call_anthropic_streaming(self, prompt: str, output: TextIO) -> str:
    with self.client.messages.stream(
        model=self.config.model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=self.config.max_tokens
    ) as stream:
        full_text = ""
        for text in stream.text_stream:
            output.write(text)
            output.flush()
            full_text += text
    output.write("\n")
    return full_text
```

### Step 3: Create streamable wrapper method
Add `_call_llm_streamable()` method that:
- Checks `self.config.enable_streaming` and `effects_enabled()`
- If streaming enabled: calls `_call_llm_streaming()`
- If streaming disabled: calls existing `_call_llm()` with progress indicator

### Step 4: Apply streaming to text-only methods
Update these methods to use `_call_llm_streamable()`:
- `generate_npc_dialogue()` (line ~1252)
- `generate_lore()` (line ~1814)
- `generate_dream()` (line ~2329)
- `generate_whisper()` (line ~2365)
- `generate_ascii_art()` (line ~1459)
- `generate_location_ascii_art()` (line ~1555)
- `generate_npc_ascii_art()` (line ~2230)

**Do NOT apply to JSON methods** (they need complete response for parsing):
- `generate_location()`
- `generate_area()`
- `generate_quest()`
- `generate_enemy()`
- `generate_item()`
- All methods that call `_parse_*_response()`

### Step 5: Handle streaming errors gracefully
In `_call_llm_streaming()`:
- Wrap streaming logic in try/except
- On streaming failure, log warning and fall back to `_call_llm()`
- Ensure partial output is not left dangling (clear line on failure)
