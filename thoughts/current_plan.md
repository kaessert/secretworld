# Implementation Plan: Add AIService Methods for Content Generation (Phase 4, Step 14)

## Overview
Add new AIService methods that bridge procedural generators with AI-generated content, specifically `generate_room_content()` which ContentLayer already calls but doesn't exist.

## Spec
1. `AIService.generate_room_content(room_type, category, connections, is_entry, context)` → `{"name": str, "description": str}`
2. Methods use existing `_call_llm()` pattern for API calls
3. Uses `progress_indicator()` for generation type "location"
4. Graceful fallback: returns `None` on failure (ContentLayer handles fallback via FallbackContentProvider)

## Files to Modify

### 1. `src/cli_rpg/ai_config.py`
Add prompts:
- `DEFAULT_ROOM_CONTENT_PROMPT` - room name/description generation
- `room_content_prompt` field in AIConfig dataclass
- Serialization in `to_dict()`/`from_dict()`

### 2. `src/cli_rpg/ai_service.py`
Add method:
- `generate_room_content()` - JSON response with name/description
- Uses existing `_call_llm()` pattern for API calls
- Uses `progress_indicator()` for generation type "location"
- Validates response has required keys before returning

## Tests

### `tests/test_ai_room_content.py` (new file)
1. `test_generate_room_content_returns_name_and_description` - mock LLM returns valid JSON
2. `test_generate_room_content_passes_room_type_to_prompt` - verify room_type in prompt
3. `test_generate_room_content_passes_category_to_prompt` - verify category in prompt
4. `test_generate_room_content_returns_none_on_invalid_json` - graceful degradation
5. `test_generate_room_content_returns_none_on_missing_keys` - graceful degradation
6. `test_generate_room_content_uses_context_theme` - generation context used

## Implementation Steps

1. Add `DEFAULT_ROOM_CONTENT_PROMPT` to `ai_config.py` (template for room name/description)
2. Add `room_content_prompt` field to `AIConfig` dataclass with serialization
3. Create `tests/test_ai_room_content.py` with 6 test cases
4. Add `generate_room_content()` method to `AIService` class
5. Run tests to verify implementation

## Detailed Prompt Template

```python
DEFAULT_ROOM_CONTENT_PROMPT = """Generate a room for a {theme} RPG interior location.

Room Context:
- Room Type: {room_type}
- Location Category: {category}
- Connected Directions: {connections}
- Is Entry Point: {is_entry}

World Context:
- Theme Essence: {theme_essence}

Requirements:
1. Create a unique room name (2-40 characters) fitting the room type and category
2. Write a vivid description (50-200 characters) that creates atmosphere

Room Type Guidelines:
- entry: Entrance/exit areas with hints of what lies ahead
- corridor: Connecting passages with ambient details
- chamber: Standard rooms for exploration
- boss_room: Imposing chambers for major encounters
- treasure: Rooms with valuable items or hidden caches
- puzzle: Rooms with interactive challenges or mysteries

Respond with valid JSON in this exact format:
{{
  "name": "Room Name",
  "description": "A vivid description of the room."
}}"""
```
