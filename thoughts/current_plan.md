# Implementation Plan: Update ISSUES.md to Mark Dead-End Issue as Resolved

## Spec
- ISSUES.md should accurately reflect the current state of known issues
- The dead-end bug documented in ISSUES.md was fixed in commit `8d7f56f`
- The file should be updated to show resolved status with commit reference

## Tests

**File:** `tests/test_issues_documentation.py`

```python
"""Tests for ISSUES.md documentation accuracy."""
import os
from pathlib import Path

def test_issues_file_exists():
    """ISSUES.md should exist at project root."""
    project_root = Path(__file__).parent.parent
    issues_file = project_root / "ISSUES.md"
    assert issues_file.exists(), "ISSUES.md should exist at project root"

def test_resolved_issues_are_marked():
    """Resolved issues should be marked with [RESOLVED] status."""
    project_root = Path(__file__).parent.parent
    issues_file = project_root / "ISSUES.md"
    content = issues_file.read_text()

    # If file mentions dead-end issue, it should be marked resolved
    if "dead-end" in content.lower() or "stuck" in content.lower():
        assert "[RESOLVED]" in content, "Dead-end issue should be marked as [RESOLVED]"
        assert "8d7f56f" in content, "Resolution commit should be referenced"

def test_no_active_resolved_issues():
    """File should not have issues marked CRITICAL that are actually resolved."""
    project_root = Path(__file__).parent.parent
    issues_file = project_root / "ISSUES.md"
    content = issues_file.read_text()

    # If contains "CRITICAL:" without [RESOLVED], check it's a real active issue
    lines = content.split('\n')
    for line in lines:
        if "CRITICAL:" in line and "[RESOLVED]" not in line:
            # This would be an active critical issue - fail if we know it's resolved
            assert "dead-end" not in content.lower() or "[RESOLVED]" in content
```

---

## Implementation Steps

### Step 1: Create test file
**File:** `tests/test_issues_documentation.py`

Create tests as specified above.

### Step 2: Update ISSUES.md
**File:** `ISSUES.md`

Replace entire contents with:

```markdown
# Known Issues

## [RESOLVED] Dead-End in AI-Generated Locations

**Status:** Fixed in commit `8d7f56f`

**Original Issue:** Game generates a world with only three locations and the player gets stuck with no way to expand the world.

**Resolution:** Implemented world expansion when player approaches edge of explored area. The world now dynamically expands as players explore, preventing dead-ends.

---

*No active issues at this time.*
```

### Step 3: Verify
```bash
pytest tests/test_issues_documentation.py -v
```
