# Implementation Plan: Fix Mypy Type Errors

## Summary
The project has 100% test coverage (1424 tests) and passes all linting. The next improvement opportunity is addressing **68 mypy type errors** across 7 files to improve type safety.

## Scope
Fix type annotations in these files (ordered by complexity):
- `src/cli_rpg/combat.py` (1 error)
- `src/cli_rpg/world.py` (2 errors)
- `src/cli_rpg/ai_service.py` (5 errors)
- `src/cli_rpg/game_state.py` (4 errors)
- `src/cli_rpg/main.py` (56 errors)

## Implementation Steps

### 1. `combat.py` - Fix float/int assignment (line 236)
- Change variable type hint or add explicit int conversion

### 2. `world.py` - Fix Optional type handling (lines 20-21)
- Use `Optional[Type[AIService]]` for lazy import variable
- Use `Optional[Callable[...]]` for function reference

### 3. `ai_service.py` - Fix type mismatches (lines 305, 318, 328, 790, 805)
- Add isinstance check before accessing `.text` attribute
- Use `Optional[Union[APIConnectionError, RateLimitError, Exception]]` for retry variable
- Fix return type annotation for cache method
- Fix deepcopy argument type annotation

### 4. `game_state.py` - Fix Optional and import handling (lines 21-23, 308)
- Use `Optional` for lazy import fallback types
- Add proper type narrowing for Optional[str]

### 5. `main.py` - Add type guards for Optional access (56 errors)
- All errors are `union-attr` - accessing attributes on `Optional` types
- Add `assert` statements or `if` guards before accessing `.name`, `.is_merchant`, etc.
- Group fixes by function for efficiency

## Verification
```bash
source venv/bin/activate && mypy src/cli_rpg --ignore-missing-imports
pytest  # Ensure no regressions
```
