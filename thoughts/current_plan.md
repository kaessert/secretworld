# Implementation Plan: Improve world.py Test Coverage to 98%+

## Goal
Cover lines 18-21 in `world.py` (the `except ImportError` block for AI components).

## The Problem
Lines 18-21 execute at module import time when AI imports fail:
```python
try:
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_world import create_ai_world
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False      # Line 19
    AIService = None          # Line 20
    create_ai_world = None    # Line 21
```

Current test at line 320 patches `AI_AVAILABLE` at runtime, but this doesn't cover the except block.

## Implementation Steps

### 1. Add test to cover ImportError branch (lines 18-21)
- **File**: `tests/test_world.py`
- **Strategy**: Use `importlib` and `sys.modules` manipulation to force re-import with mocked ImportError
- **Test**: Create new test class `TestAIImportFallback` with a test that:
  1. Remove `cli_rpg.world` and related modules from `sys.modules`
  2. Mock `cli_rpg.ai_service` to raise `ImportError`
  3. Re-import `cli_rpg.world`
  4. Verify `AI_AVAILABLE=False`, `AIService=None`, `create_ai_world=None`
  5. Clean up and restore original module

### 2. Run tests to verify coverage
- Run `pytest tests/test_world.py --cov=cli_rpg.world --cov-report=term-missing`
- Verify lines 18-21 are now covered
- Verify world.py coverage is 98%+
