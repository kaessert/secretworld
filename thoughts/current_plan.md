# Plan: Push Test Coverage from 98.23% toward 100%

## Current State
- **Coverage**: 98.23% (1312 tests pass, 51 lines missing)
- **Goal**: Target testable runtime gaps, accept TYPE_CHECKING/import fallback lines as untestable

## Coverage Analysis

| Module | Miss | Lines | Notes |
|--------|------|-------|-------|
| ai_service.py | 15 | 9, 18-21, 252, 309, 338, 349, 353, 360, 399, 423, 455, 741 | TYPE_CHECKING + error handlers |
| models/character.py | 7 | 8-10, 69, 95, 111, 209 | TYPE_CHECKING + edge cases |
| game_state.py | 6 | 19-23, 45 | ImportError fallback |
| world.py | 4 | 18-21 | ImportError fallback |
| ai_world.py | 2 | 150-151 | Warning for non-grid direction |
| map_renderer.py | 1 | 37 | Edge case |
| combat.py | 2 | 12, 190 | Import + edge case |
| Others | 14 | Various | Mostly TYPE_CHECKING |

## Practical Targets (testable code)

### Priority 1: ai_service.py exception handlers (Lines 252, 309, 338, 349, 353, 360, 399, 423, 455, 741)
These are API error handling paths that can be triggered by mocking exceptions.

### Priority 2: models/character.py line 209
Generic consumable use without heal effect - testable runtime path.

### Priority 3: combat.py line 190
Combat edge case - likely testable.

## Implementation Steps

1. **Review ai_service.py uncovered lines** to identify which are truly testable vs TYPE_CHECKING
2. **Add tests for mockable exception paths** in `tests/test_ai_service.py`
3. **Add test for character.py line 209** - consumable without heal effect
4. **Run coverage** to verify improvements

## Files to Modify
- `tests/test_ai_service.py` - Add exception handling tests
- `tests/test_character.py` or `tests/test_character_inventory.py` - Consumable test

## Acceptance Criteria
- Coverage increases above 98.5%
- All new tests pass
- No regressions in existing tests
