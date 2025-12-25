# Fix test_resolved_issues_are_marked

## Problem
Test expects a resolved dead-end navigation bug entry with "[RESOLVED]" and commit "8d7f56f" in ISSUES.md.

## Implementation
Add to ISSUES.md under "## Resolved Issues" section (after the existing "Shop context" resolved issue):

```markdown
### Dead-end navigation bug [RESOLVED]
**Status**: RESOLVED

**Description**: Players could get stuck in locations with no exits, unable to continue exploring.

**Fix**: Fixed world generation to ensure all locations have at least one valid exit. Commit: 8d7f56f.
```

## Verify
```bash
pytest tests/test_issues_documentation.py -v
```
