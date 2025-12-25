"""Tests for ISSUES.md documentation accuracy.

These tests verify that ISSUES.md accurately reflects the current state of known issues.
Spec: Dead-end bug documented in ISSUES.md was fixed in commit 8d7f56f.
"""
from pathlib import Path


def test_issues_file_exists():
    """ISSUES.md should exist at project root.

    Spec: ISSUES.md should accurately reflect the current state of known issues.
    """
    project_root = Path(__file__).parent.parent
    issues_file = project_root / "ISSUES.md"
    assert issues_file.exists(), "ISSUES.md should exist at project root"


def test_resolved_issues_are_marked():
    """Resolved issues should be marked with [RESOLVED] status.

    Spec: The dead-end bug was fixed in commit 8d7f56f and should be marked resolved.
    """
    project_root = Path(__file__).parent.parent
    issues_file = project_root / "ISSUES.md"
    content = issues_file.read_text()

    # Check for the specific dead-end navigation bug (fixed in 8d7f56f)
    # This was a bug where players could get stuck with no exits - not the same as
    # uncompletable quests which is a separate active issue
    if "dead-end" in content.lower() and "navigation" in content.lower():
        assert "[RESOLVED]" in content, "Dead-end navigation issue should be marked as [RESOLVED]"
        assert "8d7f56f" in content, "Resolution commit should be referenced"


def test_no_active_resolved_issues():
    """File should not have issues marked CRITICAL that are actually resolved.

    Spec: Dead-end issue (which was critical) should now be marked resolved.
    """
    project_root = Path(__file__).parent.parent
    issues_file = project_root / "ISSUES.md"
    content = issues_file.read_text()

    # If contains "CRITICAL:" without [RESOLVED], check it's a real active issue
    lines = content.split('\n')
    for line in lines:
        if "CRITICAL:" in line and "[RESOLVED]" not in line:
            # This would be an active critical issue - fail if we know it's resolved
            assert "dead-end" not in content.lower() or "[RESOLVED]" in content
