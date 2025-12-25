# Implementation Summary: Fix test_resolved_issues_are_marked

## What was implemented

Fixed a false positive in `tests/test_issues_documentation.py::test_resolved_issues_are_marked`.

**File modified:** `tests/test_issues_documentation.py`

**Change:** Updated the condition on line 30-32 from checking for `"dead-end" or "stuck"` to checking for `"dead-end" and "navigation"`. This makes the test more specific to the actual dead-end navigation bug that was fixed in commit 8d7f56f, rather than triggering on the word "stuck" appearing in an unrelated context (the quest system issue).

## Test results

All 3 tests in `tests/test_issues_documentation.py` pass:
- `test_issues_file_exists` - PASSED
- `test_resolved_issues_are_marked` - PASSED
- `test_no_active_resolved_issues` - PASSED

## Technical details

The original test was too broad - it checked if either "dead-end" OR "stuck" appeared anywhere in ISSUES.md. The word "stuck" appears on line 18 in the context of uncompletable quests ("players will be stuck with uncompletable quests"), which is an unrelated active issue. By requiring both "dead-end" AND "navigation" to appear, the test now correctly targets only the specific resolved navigation bug.
