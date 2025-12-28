# Fix: test_ai_json_parse_error_uses_fallback serialization failure

## Problem
The test fails because the Mock `ai_service` leaks into GameState serialization during autosave. The conftest.py `mock_autosave_directory` fixture still calls real autosave, which tries to JSON serialize the game state including Mock objects from `generate_world_context().to_dict()`.

## Solution
Patch `cli_rpg.game_state.autosave` in the affected tests to prevent serialization during move() - same pattern used by other tests in the codebase (see test_layered_context_integration.py, test_terrain_movement.py, etc.).

## Implementation Steps

1. **Edit `tests/test_ai_failure_fallback.py`**:
   - Add `@patch("cli_rpg.game_state.autosave")` decorator to `test_ai_json_parse_error_uses_fallback`
   - Add `mock_autosave` parameter to method signature
   - Same fix for `test_ai_service_error_uses_fallback` and `test_ai_generation_error_uses_fallback` which have identical mock patterns

## Verification
```bash
pytest tests/test_ai_failure_fallback.py -v
```
