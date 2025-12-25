# Code Quality & Linting Fixes

## Summary
Fix 24 ruff linting errors including unused imports, undefined names, and f-strings without placeholders.

## Fixes Required

### 1. `src/cli_rpg/ai_service.py`
- **Lines 914, 918, 925, 929**: Remove `f` prefix from f-strings without placeholders
- **Lines 956, 996**: Add `ItemType` import to TYPE_CHECKING block:
  ```python
  from typing import Optional, TYPE_CHECKING
  if TYPE_CHECKING:
      from cli_rpg.models.item import ItemType
  ```

### 2. `src/cli_rpg/ai_world.py`
- **Line 5**: Remove unused import `AIServiceError`
- **Line 352**: Remove or use `source_loc` variable

### 3. `src/cli_rpg/game_state.py`
- **Line 5**: Remove unused import `ClassVar`
- **Line 10**: Remove unused import `spawn_enemy`

### 4. `src/cli_rpg/main.py`
- **Lines 71, 129, 141, 833, 835, 857, 1120**: Remove `f` prefix from f-strings without placeholders

### 5. `src/cli_rpg/map_renderer.py`
- **Line 3**: Remove unused import `Optional`

### 6. `src/cli_rpg/models/character.py`
- **Line 3**: Remove unused import `Optional`
- **Line 46**: Add `Inventory` to TYPE_CHECKING block

### 7. `src/cli_rpg/models/item.py`
- **Line 2**: Remove unused import `field`

### 8. `src/cli_rpg/persistence.py`
- **Line 3**: Remove unused import `os`
- **Line 6**: Remove unused import `Optional`

### 9. `src/cli_rpg/world.py`
- **Line 4**: Remove unused import `Union`

## Verification
```bash
ruff check src/  # Should report 0 errors
pytest           # All tests should still pass
```
