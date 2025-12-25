# Implementation Plan: game_state.py Coverage Gaps (Lines 19-23, 45)

## Spec

Cover the 6 uncovered lines in `game_state.py`:
- **Lines 19-23**: Import fallback block when `ai_service`/`ai_world` imports fail
- **Line 45**: `parse_command("")` returning `("unknown", [])` for empty input

## Tests

### File: `tests/test_game_state_import_fallback.py`

Test import fallback behavior using subprocess with coverage (same pattern as `test_world_import_fallback.py`):

```python
def test_ai_import_failure_sets_fallback_values():
    """When ai_service/ai_world imports fail in game_state.py:
    - AI_AVAILABLE should be False
    - AIService should be None
    - AIServiceError should be Exception
    - expand_area should be None
    """
```

### File: `tests/test_game_state.py` (add to TestParseCommand class)

```python
def test_parse_command_empty_string():
    """Spec: Empty string should return ("unknown", [])"""
    cmd, args = parse_command("")
    assert cmd == "unknown"
    assert args == []

def test_parse_command_whitespace_only():
    """Spec: Whitespace-only string should return ("unknown", [])"""
    cmd, args = parse_command("   ")
    assert cmd == "unknown"
    assert args == []
```

## Implementation Steps

1. **Add empty input tests to `tests/test_game_state.py`**
   - Add `test_parse_command_empty_string` to `TestParseCommand` class
   - Add `test_parse_command_whitespace_only` to `TestParseCommand` class

2. **Create `tests/test_game_state_import_fallback.py`**
   - Follow same subprocess+coverage pattern as `test_world_import_fallback.py`
   - Mock imports for `cli_rpg.ai_service` and `cli_rpg.ai_world` to raise ImportError
   - Import `cli_rpg.game_state` and verify fallback values
   - Source: `cli_rpg.game_state` (not `cli_rpg.world`)

3. **Run tests to verify coverage increase**
   - `pytest tests/test_game_state.py::TestParseCommand -v`
   - `pytest tests/test_game_state_import_fallback.py -v`
   - `pytest --cov=src/cli_rpg/game_state --cov-report=term-missing`
