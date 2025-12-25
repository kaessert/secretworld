# Plan: Fix test_resolved_issues_are_marked

## Problem
The test checks if "dead-end" or "stuck" appears in ISSUES.md, then requires "[RESOLVED]" and commit "8d7f56f". The word "stuck" appears in an unrelated context (line 18: "players will be stuck with uncompletable quests"), triggering the assertion.

## Solution
Update the test to be more specific - check for the actual dead-end navigation bug context, not just the word "stuck" in any context.

## Implementation

### File: `tests/test_issues_documentation.py`

**Change lines 30-32** from:
```python
if "dead-end" in content.lower() or "stuck" in content.lower():
    assert "[RESOLVED]" in content, "Dead-end issue should be marked as [RESOLVED]"
    assert "8d7f56f" in content, "Resolution commit should be referenced"
```

to:
```python
# Check for the specific dead-end navigation bug (fixed in 8d7f56f)
# This was a bug where players could get stuck with no exits - not the same as
# uncompletable quests which is a separate active issue
if "dead-end" in content.lower() and "navigation" in content.lower():
    assert "[RESOLVED]" in content, "Dead-end navigation issue should be marked as [RESOLVED]"
    assert "8d7f56f" in content, "Resolution commit should be referenced"
```

## Verification
```bash
pytest tests/test_issues_documentation.py -v
```

All three tests in the file should pass.
