# Implementation Plan: Improve ai_service.py Test Coverage (94% → 98%+)

## Overview
Add targeted tests to cover remaining 26 uncovered lines in `ai_service.py`, pushing coverage from 94% to 98%+.

## Target Lines Analysis

| Lines | Category | Description |
|-------|----------|-------------|
| 9, 18-21 | Not testable | TYPE_CHECKING import & Anthropic ImportError (static/defensive) |
| 261 | OpenAI auth | AuthenticationError no-retry path |
| 443, 475 | Cache | Early return when cache_file is None |
| 912-913, 920, 940, 947, 951 | Enemy parsing | JSON decode, missing field, length validation errors |
| 1063-1064, 1071 | Item parsing | JSON decode, missing field errors |
| 1222-1226, 1236 | Quest parsing | Quest name validation errors |
| 1281-1282, 1289, 1340 | Quest parsing | JSON decode, missing field, description errors |

## Tests to Add

### File: `tests/test_ai_service.py`

### 1. OpenAI AuthenticationError Test
**Covers**: Line 261
```python
@patch('cli_rpg.ai_service.OpenAI')
def test_openai_auth_error_raises_immediately(mock_openai_class, basic_config):
    """Test OpenAI authentication error raises immediately without retry."""
```

### 2. Enemy Parsing Error Tests (in test_ai_enemy_generation.py)
**Covers**: Lines 912-913, 920, 940, 947, 951

- `test_parse_enemy_response_invalid_json` - JSON decode error
- `test_parse_enemy_response_missing_field` - Missing required field
- `test_parse_enemy_response_description_too_long` - Description > 150 chars
- `test_parse_enemy_response_attack_flavor_too_short` - Attack flavor < 10 chars
- `test_parse_enemy_response_attack_flavor_too_long` - Attack flavor > 100 chars

### 3. Item Parsing Error Tests (in test_ai_item_generation.py)
**Covers**: Lines 1063-1064, 1071

- `test_parse_item_response_invalid_json` - JSON decode error
- `test_parse_item_response_missing_field` - Missing required field

### 4. Quest Parsing Error Tests (in test_ai_quest_generation.py)
**Covers**: Lines 1222-1226, 1236, 1281-1282, 1289, 1340

- `test_parse_quest_response_invalid_json` - JSON decode error
- `test_parse_quest_response_missing_field` - Missing required field
- `test_parse_quest_response_name_too_short` - Name < 2 chars
- `test_parse_quest_response_name_too_long` - Name > 30 chars
- `test_parse_quest_response_description_too_long` - Description > 200 chars

## Implementation Steps

1. Add `test_openai_auth_error_raises_immediately` to `tests/test_ai_service.py`
2. Add enemy parsing error tests to `tests/test_ai_enemy_generation.py`
3. Add item parsing error tests to `tests/test_ai_item_generation.py`
4. Add quest parsing error tests to `tests/test_ai_quest_generation.py`
5. Mark lines 9, 18-21 with `# pragma: no cover` (TYPE_CHECKING/ImportError)

## Verification
```bash
source venv/bin/activate && pytest tests/test_ai_*.py -v --cov=cli_rpg.ai_service --cov-report=term-missing
```
