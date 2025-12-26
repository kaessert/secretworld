# Implementation Plan: Add `generate_region_context()` to AIService

## Summary
Add the `generate_region_context()` method to `ai_service.py` as continuation of Step 6 of the Layered Query Architecture. This method generates Layer 2 region context (name, theme, danger_level, landmarks) using the existing `DEFAULT_REGION_CONTEXT_PROMPT` from `ai_config.py`.

## Spec

```python
def generate_region_context(
    self,
    theme: str,
    world_context: WorldContext,
    coordinates: tuple[int, int],
    terrain_hint: str = "wilderness"
) -> RegionContext:
    """Generate region-level thematic context using AI.

    Args:
        theme: Base theme keyword (e.g., "fantasy", "cyberpunk")
        world_context: Layer 1 context for consistency
        coordinates: Center coordinates of the region
        terrain_hint: Terrain type hint for the region (e.g., "mountains", "swamp")

    Returns:
        RegionContext with AI-generated name, theme, danger_level, landmarks

    Raises:
        AIGenerationError: If generation fails or response invalid
        AIServiceError: If API call fails
        AITimeoutError: If request times out
    """
```

**Expected JSON response format** (from `DEFAULT_REGION_CONTEXT_PROMPT`):
```json
{
  "name": "Region Name",
  "theme": "A brief description of this region's unique character.",
  "danger_level": "low|medium|high|deadly",
  "landmarks": ["Landmark 1", "Landmark 2", "Landmark 3"]
}
```

**Validation rules:**
- `name`: non-empty string, 1-50 chars
- `theme`: non-empty string, 1-200 chars
- `danger_level`: must be one of "low", "medium", "high", "deadly" (map to RegionContext values: "safe", "moderate", "dangerous", "deadly")
- `landmarks`: list of 0-5 strings, each 1-50 chars

## Implementation Steps

### 1. Write Tests (`tests/test_ai_service.py`)

Add after existing `generate_world_context` tests (around line 2544):

```python
# Tests: generate_region_context() (Layer 2 Region Context Generation)
# ============================================================================

@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_returns_valid_region_context(mock_openai_class, basic_config):
    """Test generate_region_context returns a valid RegionContext."""

@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_validates_required_fields(mock_openai_class, basic_config):
    """Test missing required fields raise AIGenerationError."""

@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_validates_danger_level(mock_openai_class, basic_config):
    """Test invalid danger_level raises AIGenerationError."""

@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_validates_field_lengths(mock_openai_class, basic_config):
    """Test name/theme length constraints."""

@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_handles_json_in_code_block(mock_openai_class, basic_config):
    """Test JSON extraction from markdown code blocks."""

@patch('cli_rpg.ai_service.OpenAI')
def test_generate_region_context_repairs_truncated_json(mock_openai_class, basic_config):
    """Test truncated JSON is repaired."""
```

### 2. Add Methods to AIService (`src/cli_rpg/ai_service.py`)

Add after `generate_world_context` method (around line 2256):

```python
def generate_region_context(
    self,
    theme: str,
    world_context: "WorldContext",
    coordinates: tuple[int, int],
    terrain_hint: str = "wilderness"
) -> "RegionContext":
    """Generate region-level thematic context using AI."""
    from cli_rpg.models.region_context import RegionContext

    prompt = self._build_region_context_prompt(theme, world_context, coordinates, terrain_hint)
    response_text = self._call_llm(prompt)
    return self._parse_region_context_response(response_text, coordinates)

def _build_region_context_prompt(
    self,
    theme: str,
    world_context: "WorldContext",
    coordinates: tuple[int, int],
    terrain_hint: str
) -> str:
    """Build prompt for region context generation."""
    return self.config.region_context_prompt.format(
        theme=theme,
        theme_essence=world_context.theme_essence,
        naming_style=world_context.naming_style,
        tone=world_context.tone,
        coordinates=f"({coordinates[0]}, {coordinates[1]})",
        terrain_hint=terrain_hint
    )

def _parse_region_context_response(
    self,
    response_text: str,
    coordinates: tuple[int, int]
) -> "RegionContext":
    """Parse and validate LLM response for region context generation."""
    # Extract JSON, repair if truncated, validate fields, return RegionContext
```

## Files Modified
- `tests/test_ai_service.py`: Add 6 tests for `generate_region_context()`
- `src/cli_rpg/ai_service.py`: Add `generate_region_context()`, `_build_region_context_prompt()`, `_parse_region_context_response()`
