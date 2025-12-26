# Plan: Add JSON Repair for Truncated AI Responses

## Overview
Add try/except with JSON repair for truncated responses in `ai_service.py`. This is Quick Win #3 from the HIGH PRIORITY AI Location Generation issue.

## Spec
- When `json.loads()` fails with `JSONDecodeError`, attempt to repair truncated JSON
- Repair strategies (in order):
  1. Count unclosed brackets (`{`, `[`) and append matching closers
  2. Remove trailing incomplete string/value (e.g., truncated `"name": "Foo` -> `"name": "Foo"`)
- If repair succeeds, return parsed data; if not, raise original error
- Log repairs for debugging

## Tests (tests/test_ai_service.py)

1. `test_repair_truncated_json_unclosed_object` - Repairs `{"name": "Test"` -> `{"name": "Test"}`
2. `test_repair_truncated_json_unclosed_array` - Repairs `[{"name": "A"}` -> `[{"name": "A"}]`
3. `test_repair_truncated_json_nested_brackets` - Repairs `{"items": [{"a": 1}` -> `{"items": [{"a": 1}]}`
4. `test_repair_truncated_string_value` - Repairs `{"name": "Trunc` -> `{"name": "Trunc"}`
5. `test_repair_json_fails_gracefully` - Unrepairable JSON still raises AIGenerationError
6. `test_generate_location_with_truncated_response` - Integration: truncated location JSON is repaired

## Implementation Steps

1. **Add `_repair_truncated_json()` method** in `ai_service.py` (after `_extract_json_from_response`):
   ```python
   def _repair_truncated_json(self, json_text: str) -> str:
       """Attempt to repair truncated JSON by closing unclosed brackets.

       Args:
           json_text: Potentially truncated JSON string

       Returns:
           Repaired JSON string, or original if repair not possible
       """
       # Count unclosed brackets
       open_braces = json_text.count('{') - json_text.count('}')
       open_brackets = json_text.count('[') - json_text.count(']')

       if open_braces <= 0 and open_brackets <= 0:
           return json_text  # No unclosed brackets

       repaired = json_text.rstrip()

       # Handle truncated string value (ends with unclosed quote)
       # Pattern: ends with "key": "value without closing quote
       if repaired and repaired[-1] not in '",}]':
           # Try to close an unclosed string
           in_string = False
           escaped = False
           for char in repaired:
               if escaped:
                   escaped = False
               elif char == '\\':
                   escaped = True
               elif char == '"':
                   in_string = not in_string
           if in_string:
               repaired += '"'

       # Close brackets in reverse order of opening
       # We need to track the order brackets were opened
       closers = []
       for char in json_text:
           if char == '{':
               closers.append('}')
           elif char == '[':
               closers.append(']')
           elif char in '}]' and closers and closers[-1] == char:
               closers.pop()

       repaired += ''.join(reversed(closers))
       return repaired
   ```

2. **Update all 5 parse methods** to use repair on JSONDecodeError:

   For each `_parse_*_response()` method, change:
   ```python
   try:
       data = json.loads(json_text)
   except json.JSONDecodeError as e:
       raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
   ```

   To:
   ```python
   try:
       data = json.loads(json_text)
   except json.JSONDecodeError as e:
       # Attempt to repair truncated JSON
       repaired = self._repair_truncated_json(json_text)
       if repaired != json_text:
           try:
               data = json.loads(repaired)
               logger.warning(f"Repaired truncated JSON response")
           except json.JSONDecodeError:
               raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
       else:
           raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
   ```

3. **Methods to update**:
   - `_parse_location_response()` (line 382-385)
   - `_parse_area_response()` (line 782-785)
   - `_parse_enemy_response()` (line 1063-1066)
   - `_parse_item_response()` (line 1405-1408)
   - `_parse_quest_response()` (line 1626-1629)

## Files Modified
- `src/cli_rpg/ai_service.py`: Add repair method, update 5 parse methods
- `tests/test_ai_service.py`: Add 6 new tests
