# Plan: Add JSON Extraction from Markdown Code Blocks

## Overview
Add a utility function to extract JSON from markdown code blocks (```json...```) in AI responses. This is Quick Win #2 from the HIGH PRIORITY AI Location Generation issue.

## Spec
- Create `_extract_json_from_response(response_text: str) -> str` method
- Detect and extract JSON from markdown fenced code blocks (```json or ```)
- If no code blocks found, return original text unchanged
- Apply extraction before `json.loads()` in all parse methods

## Tests (tests/test_ai_service.py)

1. `test_extract_json_from_markdown_code_block` - Extract from ```json...```
2. `test_extract_json_from_plain_code_block` - Extract from ```...``` (no language)
3. `test_extract_json_returns_original_when_no_block` - No code block, return as-is
4. `test_generate_location_handles_markdown_wrapped_json` - Integration test

## Implementation Steps

1. **Add `_extract_json_from_response()` method** in `ai_service.py` (~line 349):
   ```python
   def _extract_json_from_response(self, response_text: str) -> str:
       """Extract JSON from markdown code blocks if present."""
       import re
       # Match ```json ... ``` or ``` ... ```
       pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
       match = re.search(pattern, response_text)
       if match:
           return match.group(1).strip()
       return response_text.strip()
   ```

2. **Update `_parse_location_response()`** (line 349):
   - Call `_extract_json_from_response()` before `json.loads()`

3. **Update `_parse_area_response()`** (line 745):
   - Call `_extract_json_from_response()` before `json.loads()`

4. **Update `_parse_enemy_response()`** (line 1023):
   - Call `_extract_json_from_response()` before `json.loads()`

5. **Update `_parse_item_response()`** (line 1360):
   - Call `_extract_json_from_response()` before `json.loads()`

6. **Update `_parse_quest_response()`** (line 1580):
   - Call `_extract_json_from_response()` before `json.loads()`

## Files Modified
- `src/cli_rpg/ai_service.py`: Add extraction method, update 5 parse methods
- `tests/test_ai_service.py`: Add 4 new tests
