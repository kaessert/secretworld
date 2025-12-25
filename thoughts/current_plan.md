# Implementation Plan: AI-Generated Lore and World History

## Spec
Add `AIService.generate_lore()` method that generates world history/lore snippets appropriate to the theme and location context. Returns a lore text string (50-500 chars) following the existing patterns for NPC dialogue, enemy, and item generation.

**Lore snippets provide:**
- Immersive world-building text about the game world's history, legends, or secrets
- Theme-appropriate content (fantasy -> ancient kingdoms, sci-fi -> colony history, etc.)
- Location-contextual flavor (graveyard -> ghost stories, temple -> deity lore)

## Implementation Steps

### 1. Add lore prompt template to `ai_config.py`
- Add `DEFAULT_LORE_GENERATION_PROMPT` constant with placeholders: `{theme}`, `{location_name}`, `{lore_category}`
- Add `lore_generation_prompt` field to `AIConfig` dataclass
- Update `to_dict()` and `from_dict()` methods

### 2. Add tests to `tests/test_ai_lore_generation.py`
Tests (following pattern from `test_ai_conversations.py` and `test_ai_item_generation.py`):
- `test_generate_lore_returns_string` - Returns non-empty string
- `test_generate_lore_uses_theme_in_prompt` - Prompt includes theme
- `test_generate_lore_uses_location_in_prompt` - Prompt includes location
- `test_generate_lore_respects_category` - Category (history/legend/secret) in prompt
- `test_generate_lore_validates_min_length` - Raises AIGenerationError if < 50 chars
- `test_generate_lore_truncates_long_responses` - Truncates to 500 chars with "..."
- `test_ai_config_has_lore_prompt` - AIConfig field exists
- `test_ai_config_lore_prompt_serialization` - to_dict/from_dict works

### 3. Implement `generate_lore()` in `ai_service.py`
```python
def generate_lore(
    self,
    theme: str,
    location_name: str = "",
    lore_category: str = "history"  # history, legend, secret
) -> str:
```
- Build prompt using `self.config.lore_generation_prompt`
- Call `_call_llm(prompt)`
- Validate response length (50-500 chars)
- Strip quotes, truncate if needed

### 4. Update ISSUES.md
Mark "Lore and world history" as completed

## Files to Modify
- `src/cli_rpg/ai_config.py` - Add prompt template and config field
- `src/cli_rpg/ai_service.py` - Add `generate_lore()` method
- `tests/test_ai_lore_generation.py` - New test file
- `ISSUES.md` - Mark complete
