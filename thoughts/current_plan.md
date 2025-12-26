# Implementation Plan: Add `generate_world_context()` to AIService

## Task Summary
Add the `generate_world_context()` method to `ai_service.py` as Step 6 of the Layered Query Architecture. This method generates Layer 1 world context (theme essence, naming conventions, tone) using the existing `DEFAULT_WORLD_CONTEXT_PROMPT`.

## Specification

### Method Signature
```python
def generate_world_context(self, theme: str) -> WorldContext:
    """Generate world-level thematic context using AI.

    Args:
        theme: Base theme keyword (e.g., "fantasy", "cyberpunk")

    Returns:
        WorldContext with AI-generated theme_essence, naming_style, and tone

    Raises:
        AIGenerationError: If generation fails or response is invalid
        AIServiceError: If API call fails
        AITimeoutError: If request times out
    """
```

### Expected JSON Response Format
```json
{
  "theme_essence": "A brief description of the world's core atmosphere and feel.",
  "naming_style": "A guide for how names should sound and feel.",
  "tone": "The overall emotional tone of the world."
}
```

### Validation Rules
- `theme_essence`: Required, non-empty string, 1-200 characters
- `naming_style`: Required, non-empty string, 1-100 characters
- `tone`: Required, non-empty string, 1-100 characters

## Implementation Steps

### 1. Add Tests (`tests/test_ai_service.py`)
Add tests for the new method:
- `test_generate_world_context_returns_valid_world_context`: Mock LLM response, verify WorldContext returned
- `test_generate_world_context_validates_required_fields`: Missing field raises AIGenerationError
- `test_generate_world_context_validates_field_lengths`: Too short/long raises AIGenerationError
- `test_generate_world_context_handles_json_in_code_block`: Extract JSON from ```json...```
- `test_generate_world_context_repairs_truncated_json`: Truncated JSON is repaired

### 2. Add `generate_world_context()` Method (`src/cli_rpg/ai_service.py`)

Location: After `generate_dream()` method (around line 2059)

```python
def generate_world_context(self, theme: str) -> "WorldContext":
    """Generate world-level thematic context using AI."""
    from cli_rpg.models.world_context import WorldContext

    prompt = self._build_world_context_prompt(theme)
    response_text = self._call_llm(prompt)
    return self._parse_world_context_response(response_text, theme)

def _build_world_context_prompt(self, theme: str) -> str:
    """Build prompt for world context generation."""
    return self.config.world_context_prompt.format(theme=theme)

def _parse_world_context_response(self, response_text: str, theme: str) -> "WorldContext":
    """Parse and validate LLM response for world context generation."""
    # Extract and parse JSON (reuse existing helpers)
    # Validate required fields
    # Return WorldContext instance
```

### 3. Add Import Statement
Add `from datetime import datetime` if not present (for `generated_at` field)

### 4. Run Tests
```bash
pytest tests/test_ai_service.py -v -k "world_context"
```

## Files to Modify
- `src/cli_rpg/ai_service.py`: Add `generate_world_context()`, `_build_world_context_prompt()`, `_parse_world_context_response()`
- `tests/test_ai_service.py`: Add 5 test cases for the new method
