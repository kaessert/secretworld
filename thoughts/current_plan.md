# Plan: Fix Ruff Linting Errors

**Task**: Clean up 103 ruff linting errors in test files

## Issue Summary
- 74 F401 (unused imports) - auto-fixable
- 25 F841 (unused variables) - requires unsafe-fixes
- 2 E402 (import not at top) - manual review needed
- 2 F811 (redefined while unused) - auto-fixable

## Implementation Steps

1. **Auto-fix safe errors** (76 fixable):
   ```bash
   ruff check . --fix
   ```

2. **Review and fix F841 (unused variables)**:
   - Run: `ruff check . --select F841` to list remaining
   - Manually review each - some may be intentional (e.g., unpacking)
   - Apply `--unsafe-fixes` if appropriate after review

3. **Fix E402 (import order) manually**:
   - Check which files have this issue
   - Reorganize imports to top of file or add `# noqa` if intentional

4. **Verify**:
   ```bash
   ruff check .
   pytest -q
   ```

## Files Affected
Primarily `tests/` directory based on error output.
